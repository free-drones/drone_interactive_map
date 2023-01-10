# Interactive Map Module Server (back-end)

This project is the back-end server for the Interactive Map Module developed for RISE
Drone System (RDS). The back-end server is written in **Python3**.

This server is the link between the systems front-end and RDS. This
server handles all communication with RDS and saves important information in a
database which in turn is used to answer requests from front-end. This server
also handles processing of images.

Here follows an overview and development guide of the Interactive Map Module (IMM) back-end.
- [Interactive Map Module Server (back-end)](#interactive-map-module-server-back-end)
  - [Installation](#installation)
    - [Python dependencies](#python-dependencies)
    - [Tile server](#tile-server)
  - [How to start the server](#how-to-start-the-server)
  - [File Overview](#file-overview)
      - [IMM](#imm)
        - [Database](#database)
        - [Threads](#threads)
      - [Server startup and communication with front-end](#server-startup-and-communication-with-front-end)
      - [RDS_emulator](#rds_emulator)
      - [Tests](#tests)
      - [Utility](#utility)
      - [Other](#other)
  - [Getting started](#getting-started)
      - [Adding more API calls between front-end and back-end](#adding-more-api-calls-between-front-end-and-back-end)
      - [Adding more API calls between back-end and RDS](#adding-more-api-calls-between-back-end-and-rds)
      - [Image Processing](#image-processing)
      - [Sending images through zeroMQ](#sending-images-through-zeromq)
  - [Future development](#future-development)
      - [Note about production server](#note-about-production-server)
          - [Why is a new method for tranfer messages needed?](#why-is-a-new-method-for-tranfer-messages-needed)
          - [Possible solutions](#possible-solutions)
          - [Suggestion: New method for transfering messages that currently originate from back-end.](#suggestion-new-method-for-transfering-messages-that-currently-originate-from-back-end)

## Installation

This section provides back-end installation instructions.

### Python dependencies
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all
dependencies for this project. It's recommended to use a virtual enviroment for
this project.

```bash
python/python3 -m venv env
source env/bin/activate
pip/pip3 install -r requirements.txt
```

All dependencies can be found in the requirements.txt file.

### Tile server
The tile server in required to run image processing on incoming images. It is possible to run the back-end without
tile server by setting TILE_SERVER_AVAILABLE to False in the config file. The following instructions has only
been verified to work for Ubuntu. Text within <>-brackets should be replaced according to you local setup.

The tile server installation instructions were created based on this tutorial:
https://www.linuxbabe.com/ubuntu/openstreetmap-tile-server-ubuntu-18-04-osm

First, install all necessary dependencies.

```bash
sudo add-apt-repository ppa:osmadmins/ppa
sudo apt update
sudo apt upgrade
sudo apt install postgresql postgresql-contrib postgis postgresql-10-postgis-2.4
sudo apt install git
sudo apt install acl
sudo apt install osm2pgsql
sudo apt install software-properties-common
sudo apt install libapache2-mod-tile renderd #click 'yes' in the popup
sudo apt install curl unzip gdal-bin mapnik-utils libmapnik-dev python3-pip
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt install nodejs
sudo npm install -g carto
sudo -H pip3 install psycopg2
sudo apt install ttf-dejavu
sudo apt install fonts-noto-cjk fonts-noto-hinted fonts-noto-unhinted ttf-unifont
```

Download stylesheets and map data.

```bash
sudo adduser --system osm
cd /home/osm/
sudo setfacl -R -m u:<username>:rwx /home/osm/
wget https://download.geofabrik.de/europe/sweden-latest.osm.pbf
git clone https://github.com/gravitystorm/openstreetmap-carto.git
cd /home/osm/openstreetmap-carto
git checkout bd22cf5
```

Next, setup the the psql database where the osm data will be stored and import map data
to psql database and generate Mapnik stylesheet. The commands osm2pgsql and get-shapefiles might take a while.

```bash
sudo -u postgres -i
createuser osm
createdb -E UTF8 -O osm gis
psql -c "CREATE EXTENSION postgis;" -d gis
psql -c "CREATE EXTENSION hstore;" -d gis
psql -c "ALTER TABLE spatial_ref_sys OWNER TO osm;" -d gis
osm2pgsql --slim -d gis --hstore --multi-geometry --number-processes <number of CPU cores> --tag-transform-script /home/osm/openstreetmap-carto/openstreetmap-carto.lua --style /home/osm/openstreetmap-carto/openstreetmap-carto.style -C <80% of available RAM in MB> /home/osm/sweden-latest.osm.pbf
psql -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO osm;" -d gis
setfacl -R -m u:postgres:rwx /home/osm/
cd /home/osm/openstreetmap-carto/
python3 scripts/get-shapefiles.py
carto project.mml > style.xml # It is normal if this command produces many warnings
exit
```

Now, we must configure renderd and apache. The config files should be opened with
```bash
sudo nano <textfile>
```
In /etc/renderd.conf:
1. Under [renderd] set num_threads=<number of CPU cores>
2. Under [mapnik] set plugins_dir=/usr/lib/mapnik/3.0/input/
3. Under [mapnik] set font_dir=/usr/share/fonts/truetype
4. Under [mapnik] set font_dir_recurse=true
5. Under [default] set XML=/home/osm/openstreetmap-carto/style.xml
6. Under [default] set HOST=<domain name> and remove the leading ;

In /etc/init.d/renderd, set RUNASUSER=osm.

In /etc/apache2/sites-available/tileserver_site.conf set ServerName=<domain name>

Restart renderd and apache services.
```bash
sudo chown osm /var/lib/mod_tile/ -R
sudo systemctl daemon-reload
sudo systemctl restart renderd
sudo systemctl restart apache2
```

Check the system log to ensure no renderd errors occured. If there are errors, check that you configured
renderd correctly above.
```bash
sudo journalctl -eu renderd
```

Now, you should be able to view a view of the earth at http://<domain name>/osm/0/0/0.png.


## How to start the server

Start the server by running the following script in the terminal when located
at the root level of the project. This will start the back-end server, it's threads and the database.

```bash
python3 -m IMM.IMM_app
```

## File Overview

Under this section a overview of the program is given.

#### IMM
This is the folder where the main program is located. The following can be found in this folder.
* The database (`/database/database.py`).
* All images which have been saved and retrieved from RDS (`/images`).
* All threads for the server (`/threads/..`).
* Error handling of requests (`error_handler.py`).
* Image processing of recieved images (`image_processing.py`)
* The server, startup of server and communication with front-end. (`IMM_app.py`)
* Thread handler for easy handling of threads (`thread_handler.py`)

##### Database
The database is contains all tables used for the database aswell as other functions such as `use_test_database`, `use_production_db` and `session_scope`. `use_test_database` and `use_production_db` specify for the program which database should be used. `session_scope` must be used when accessing the database, for example:

```python
with session_scope() as session:
  user_session = UserSession(start_time=1, drone_mode="MAN")
  session.add(user_session)
  session.commit()
  # Must commit before accessing its ID
  Client = Client(session_id=user_session.id)
  session.add(new_client)
  session.commit()
  # Note that commit() is also performed automatically when exiting the session scope.
```
##### Threads
The following threads in `/threads/..` are:
* `thread_gui_pub.py`: This threads sends data and messages to front-end. The threads listen to a queue and when a new request (message) is appended this thread will send it to front-end.
* `thread_info_fetcher.py`: This thread regularly requests information from RDS (using the defined API) and saves retrieved information to the database which then can be used when front-end performs a request.
* `thread_rds_pub.py`: This thread sends requests to RDS. New requests which are to be sent to RDS can be added by calling `add_request` which will append the request to a queue.
* `thread_rds_sub.py`: This thread listens and recievs responses and messages from RDS and saves related information to the database. This thread will recieve images from RDS and perform image processing on them.

#### Server startup and communication with front-end
The main file of the server is `IMM_app.py`. In this file the following is performed.

* ALL threads listed above are initiated (`thread_handler.start_threads()`).
* The database is started (`use_production_db()` or `use_test_database()`).
* The web-application/server is started (`run_imm()`).
* functionallity of ALL API calls that front-end can perform trough socketio. It also hosts a URL where front-end can retrieve any image that is saved in the database.


#### RDS_emulator
This folder contains all code for running a emulator for RDS. It has a separate database data and information related to RDS. Communication between the emulator and server is done trough ZeroMQ sockets.

This is an example on how to run just the RDS emulator:
```python
rds_handler = RDSThreadHandler()
rds_handler.start_threads()
use_test_database_rds(False)
```
To run the RDS emulator and the Server (Note that it does not run any tests).
```bash
python/python3 -m run_RDS_and_IMM
```

#### Tests
the folder **tests** contains all tests for the system. All tests in the folder **unittests** can be
executed automatically by running the command below. Tests located in **manual** requires
that the front-end and back-end is running and that certain requests and actions are performed.
`database_tests.py` and `flask_tester.py` are unit tests for testing the database and the communinication
between this server and the front-end.

```bash
python/python3 -m path_to_test
# Example:
python3 -m tests.unittests.flask_tester
```

#### Utility
In the folder **utility** various help functions can be found. For example functions
checking if squares overlapp, for testing and image processing.

* **calculate_coordinates.py**: Contains functions for calculating coordinates from image metadata.
* **helper_functions.py**: Contains functions for calculating if polygons overlap and other various help functions for example `get_path_from_root`, `check_keys` and `coordinates_list_to_json`.
* **image_util.py**: Contains functions functions that are used in the image processing.
* **test_helper_function.py**: Contains functions which can be used when performing tests on the systems.

#### Other
* **config_file.py**: Contains options such as the URLs for the server and URLs for the zeroMQ sockets.
* **api.md**: Contains the API used between front-end and back-end.

## Getting started

#### Adding more API calls between front-end and back-end

The API calls between front-end and back-end are implemented using the Flask-SocketIO library, [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/). All API calls are implemented in `/IMM/IMM_app.py`. To create a new API call create a new function with a Flask-SocketIO decorator. See example below:

```python
  @socketio.on("new_api_call")
  def on_new_api_call():
    #Implement new api call.
    # This function will automatically be called when "new_api_call" is called
    # trough SocketIO.

    # Implement functionallity here.

    # Example on how to respond to the client who made the API call.
    # "response" is the channel where the response is sent
    # "response" can be modified if the same is done for front-end).
    emit("response", the_response_to_be_sent)
```

#### Adding more API calls between back-end and RDS

The API calls between back-end and RDS are implemnted using the Python version of
ZeroMQ, [PyZMQ](https://pyzmq.readthedocs.io/en/latest/api/zmq.html). These API
calls are located in `/IMM/threads/thread_rds_pub.py`, `/IMM/threads/thread_rds_sub.py` and
`/IMM/threads/thread_info_fetcher.py`.

* `/IMM/threads/thread_rds_sub.py`: Will listen/subscribe to messages from RDS, such as `new_pic`. To implement handling of more API calls implement this in the `run` function.
* `/IMM/threads/thread_rds_pub.py`: Will send/publish requests to RDS, such as `add_POI`. To implement handling of more API calls implement this in the `run` function.
* `/IMM/threads/thread_info_fetcher.py`: Will regularly send/publish requests to RDS, such as `get_info`.
To implement handling of more API calls implement this in the `run` function.

It is also possible to add more threads. To add more threads to the system do the following:

   1. Create a *NewThread* using the Python *threading* library.
  ```python
  from threading import Thread.

  class NewThread(Thread):
    def __init__(self):
        # Intiate.
        super().__init__()
        self.running = True
        self.requests_available = Event()
        self.request_queue = []

    def run(self):
      # Main loop of the thread.
        while running:
          self.requests_available.wait()
          request = self.request_queue.pop(0)

          # Handle requests here.

          if len(self.request_queue) == 0:
              self.requests_available.clear()
          #Implement code the be executed.

    def stop(self):
        # Stop the thread.
        self.running = False
        self.requests_available.set()
  ```

  2. Import *NewThread* thread in `IMM/thread_handler.py`.
  3. Add *NewThread* to functions in `IMM/thread_handler.py`.

#### Image Processing

Image processing is currently performed in the following files, see them for
documentation.

* `/IMM/image_processing.py`
* `/IMM/thread/thread_rds_sub.py`


#### Sending images through zeroMQ

Images are sent to IMM by first sending metadata of the image and then the image array itself.

Metadata contains the usual arguments like
- coordinates
- force_que_id
- etc....

On top of this, information about how the image array (variable *image_array* in the code below) shall be
interpreted are also provided. These are:
- dtype: Describes what range of numbers *image_array* will contain (usually it is uint8 (0 to 255)).
- shape: A tuple that contains width, height and depth of the image. If the image is RGB then the depth will be 3.


Example on how the metadata could look like:

```json
{
    "fcn": "new_pic",
    "arg":
        {
        "drone_id": "one",
        "type": "RGB",
        "force_que_id": "1",
        "coordinates": {"up_left": {"lat": 12, "long": 133}, ...}
        }
    "array_info":
        {"dtype": "uint8",
         "shape": (3000, 4000, 3)
         }
}
```
 - `shape`:  # height =3000, width=4000, depth=3


Example on how the image_array variable could look like:

- First row (0 to 3999) represents the width.
- First column (0 to 2999) represents the height.
- The tuples contain RGB values (depth = 3).

|  | 0 | 1 | . | . | . | 3999 |
| --- | --- | ----  | --- | --- | --- | --- |
|  0  | (0,0,0) | (123,32,211) | . | . | . | (123,23,22) |
|  1  | (0,0,0) | (123,32,211) | . | . | . | (123,23,22) |
|  .  | . | . | . | . | . | . |
|  .  | . | . | . | . | . | . |
|  .  | . | . | . | . | . | . |
|2999 | (0,10,0) | (13,32,11) | . | . | . | (3,232,212) |


image_array is a numpy array that is generated from the image. In the RDS emulator,
image_array and the metadata is extracted with the following code:

*File: RDS_emulator/RDS_emu.py*

```python

def new_pic(self, image):
    """
    Called when a new picture is taken, send this to the client that wanted it.

    Keyword arguments:
    image -- An instance of the image from the rds database to be sent to IMM.
    """

    image_array = cv2.imread(image.image_path)
    metadata = {
        "fcn": "new_pic",
        "arg": {
            "drone_id": "one",
            "type": "RGB",
            "force_que_id": image.force_que_id,
            "coordinates": image.coordinates
        }
    }
    self.send_image(metadata, image_array)

```

*image_array* is converted to a numpy_array via opencv (cv2).
*image.image_path* is the file path of the saved image.
- NOTE: The function is tested on *jpg* images only.

**Sending image from RDS**

In the RDS emulator, metadata and the image_array are send with the following code:

*File: RDS_emulator/RDS_emu.py*

- The following method is localized in IMMPubThread class.
```python
def send_image(self, metadata, image_array, flags=0, copy=True, track=False):
    """
    Sends the image to IMM.
    It first sends the metadata of the image and then the image array itself.

    Keyword arguments:
    metadata -- A dictionary/json representing the metadata of the image. Info about shape of the
                image array (width and height) is added to the json here.

    image_array -- The numpy 2d array representing the image.

    See pyzmq for additional information
    https://pyzmq.readthedocs.io/en/latest/api/zmq.html.
    flags -- Integer that sets flags for zeroMQ: 0 or NOBLOCK
    copy -- A boolean that tells zeroMQ to copy the received image: True or False.
    track -- Tells zeroMQ to track the message: True or False. (ignored if copy=True).

    """
    array_info = dict(
                dtype=str(image_array.dtype),
                shape=image_array.shape,
            )

    metadata["array_info"] = array_info

    self.socket.send_json(metadata, flags | zmq.SNDMORE)
    self.socket.send(image_array, flags, copy=copy, track=track)
```

What happens is that the RDS first sends the metadata to IMM and this message is sent with the
flag: *zmq.SNDMORE* that tells the receiver that more data will be sent.
After this, the image_array itself is sent.


***Receiving images in IMM***


*File: IMM/thread_rds_sub.py*

- The following method is localized in RDSSubThread class.

```python
 def run(self):
        """
        Handles images received by the RDS.
        """
        while self.running:
            request = self.RDS_sub_socket.recv_json()
            keys_exists = check_keys_exists(request, [("arg", "coordinates"), ("arg", "type"), ("arg", "force_que_id")])

            if keys_exists and "array_info" in request:
                # We have a new image
                image_array = self.recv_image_array(request["array_info"])
```

In the case that a new image is sent to IMM, metadata of the image will be sent first.
An if statement makes sure that the key "array_info" exists in the metadata, this
information is later used to receive the image_array which is described below.

*File: IMM/thread_rds_sub.py*
- The following method is localized in RDSSubThread class.

```python
def recv_image_array(self, metadata, flags=0, copy=True, track=False):
    """Receives and returns the image converted to a numpy array

    Keyword arguments:
    metadata -- A json containing information about the image that will be
                received.

    See pyzmq for additional information
    https://pyzmq.readthedocs.io/en/latest/api/zmq.html.
    flags -- Integer that sets flags for zeroMQ: 0 or NOBLOCK
    copy -- A boolean that tells zeroMQ to copy the received image: True or False.
    track -- Tells zeroMQ to track the message: True or False. (ignored if copy=True).

    Returns a numpy 2d array representing the received image.
    """

    image_raw = self.RDS_sub_socket.recv(flags=flags, copy=copy, track=track)
    self.RDS_sub_socket.send_json(json.dumps({"msg": "ack"}))
    buf = memoryview(image_raw)
    image_array = numpy.frombuffer(buf, dtype=metadata["dtype"])
    return image_array.reshape(metadata["shape"])
```

Here the image is received as raw data. This data is then converted (with the help of
numpy-library, dtype and shape) to a numpy array that is the same as the *image_array*
variable sent from the RDS.


## Future development

Here follows an overview of the future development goals for this product.

 - [ ] Implemnt so the server is using a production server (Currently using a Werkzeug development server which is included in Flask). See [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/) for options.
 - [ ] Make the server more secure from attacks, using a production server is a logical first step to achieve this and modyfing SERVER_CORS_ALLOWED_ORIGINS.
 - [ ] Improve which images are sent to front-end when front-end calls `request_view`. (Currently all images that overlap with specified area are sent).
 - [ ] Add functionallity to support other types of objects to be saved in the database. (For example position of firemen etc.)
 - [ ] Implement support for WebSockets when communicating with front-end. (Currently only *Long-polling* is performed). See [Flask-SocketIO](https://flask-socketio.readthedocs.io/en/latest/) for options.
 - [ ] Implement support for authentication of users connecting to the system.
 - [ ] Implement support for multiple sessions. (Currently only one sessions can be active on the system). Work has been done on this subject but more is needed to fully support multiple sessions.
 - [ ] Improve the image processing of images and their position on the map.
 - [ ] Implement a more robust RDS simulator.
 - [ ] Implement functionallity to make the server more stable (Error handling).
 - [ ] Implement a way to stop the main server thread (see function stop_imm() in `/IMM/IMM_app.py`)


 #### Note about production server

 Efforts have been made to implement Eventlet ([Eventlet](https://eventlet.net/)) as a productions server instead of the builtin Werkzeug development server. To use eventlet it must only be installed and the server (Flask-SocketIO) will automatically use it.

 To support Eventlet as a productions server a new method might be needed to transfer messages that originate from back-end to front-end. Currently only one type of message originates from back-end (message: notifes front-end when a new picture is recieved from RDS). The message is transmitted in the file `/IMM/threads/thread_gui_pub.py` and sent using the function `send_to_gui()`. The message and new pictures from RDS originates from `/IMM/threads/thread_rds_sub.py`, the message is created in the function `notify_gui()`.

 ###### Why is a new method for tranfer messages needed?
 Emit is not working as inteded when used in a separate thread when using Eventlet and Flask-SocketIO. Calling emit in that situation will block Flask-SocketIO completely.

 ###### Possible solutions

 * See [Emitting from an External Process](https://flask-socketio.readthedocs.io/en/latest/#emitting-from-an-external-process) from the Flask-SocketIO documentation.

 * Using one of the other suggested production servers, see [Deployment](https://flask-socketio.readthedocs.io/en/latest/#deployment) from the Flask-SocketIO documentation.

 * A new method for transfering information from back-end to front-end. See below.


 ###### Suggestion: New method for transfering messages that currently originate from back-end.

 Implement a new API call between front-end and back-end which returns new information that back-end ''wants'' to send to front-end. Let front-end regularly call this function to recieve this information.
