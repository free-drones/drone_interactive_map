"""By running this file the back-end server will be started. It will also start
threads specified in the file thread_handler.py and start the database.

This file contains the functionallity of ALL api calls that can be performed by
front-end. This file also contains the functiallity of how front-end can get any
image from the database, back-end hosts a URL where an image can be retrieved.
"""
import flask

from IMM.thread_handler import ThreadHandler
from config_file import SERVER_PORT, SERVER_LOG_OUTPUT, SERVER_CORS_ALLOWED_ORIGINS
from flask import Flask, jsonify, request, send_from_directory, send_file, abort
import time
from flask_socketio import SocketIO, join_room, emit
from IMM.database.database import session_scope, UserSession, Client, Drone, Coordinate, Image, PrioImage, AreaVertex, func, \
    coordinate_from_json, coordinate_from_list, use_production_db
from config_file import BACKEND_BASE_URL
from utility.helper_functions import is_overlapping, get_path_from_root, check_keys_exists, create_logger
import os
from IMM.error_handler import check_client_id, check_coordinates_list, check_coords_in_list, check_coord_dict, \
    check_type, check_mode, emit_error_response
from sqlalchemy import select, update, delete, and_

"""Initiate the flask application and the socketIO wrapper"""
app = Flask(__name__)
app.config["IMAGE_STORE_PATH"] = 'IMM/images' # Relative path
socketio = SocketIO(app, cors_allowed_origins=SERVER_CORS_ALLOWED_ORIGINS)

"""Initiate the thread_handler"""
thread_handler = ThreadHandler(socketio) # Passing the socketio to other threads.

"""Holds the mode which is currently active in front-end."""
current_mode = None

_logger = create_logger("IMM_app")

@app.route("/get_image/<int:image_id>")
def send_image_to_gui(image_id):
    """This functions is called when a HTTP request is performed on the URL
    specified above. It will return a image with the ID specified in the path.

    Keywords arguments:
    image_id -- A unique integer for a specific image. (Specified in the URL)
    """
    _logger.debug(f"Received get_image API call for image {image_id}")
    root_dir = os.path.dirname(os.getcwd())
    full_path = os.path.join(root_dir, "back-end", "IMM", "images")
    with session_scope() as session:
        image = session.get(Image, image_id)
        if image is not None:
            try:
                return send_from_directory(full_path, image.file_name)
            except FileNotFoundError as e:
                _logger.error(f"Image with id '{image_id}' not found in path '{full_path}'.")
                _logger.error(e)
                abort(404, description="Resource not found")
        else:
            abort(404, description="Resource not found")


""" Functions defined below are socketio API calls that front-end (the GUI) can
perform. These functions will execute automatically when front-end calls for
them trough SocketIO. The functions will retrieve the request from front-end and
assamble a response to front-end and possibly a request to RDS."""


@socketio.on("connect")
def on_connect(unused_data):
    """
    This function is called automatically by SocketIO on each new connection 
    This functions initiates a new client, sets up a socketIO room for that 
    client and responds with a unique client ID.
    """

    # case 1: No priority user and no area set.
    #    -->  Return client ID
    #
    # case 2: Area is set AND Priority user exists
    #    -->  Return client ID and the set area/bounds
    #    -->  emit 'set_client_id'
    #    -->  emit 'set_priority'  (prio, area, bounds)
    #
    # case 3: Area is set AND No priority user is set
    #    -->  Return client ID and the set area/bounds
    #    -->  Set current client to priority client
    #    -->  emit 'set_client_id'
    #    -->  emit 'set_priority'  (prio, area, bounds)
    #
    #

    client_id = None
    with session_scope() as session:
        # Create UserSession if needed and new Client for this connection
        user_session = session.query(UserSession).first()
        if user_session is None:
            user_session = UserSession(start_time=1, drone_mode="MAN")
        session.add(user_session)
        session.commit()
        new_client = Client(session_id=user_session.id, sid=request.sid)
        session.add(new_client)
        session.commit()
        client_id = new_client.id
        join_room(room=user_session.id)

        
        stmt = select(Client).where((and_(Client.session_id == user_session.id, Client.is_prio_client == True)))
        prioritized_client = session.scalars(stmt).first()
        
        stmt = select(AreaVertex).where(AreaVertex.session_id == user_session.id)
        area_vertex = session.scalars(stmt).first()
    
    
    client_id_response = { "client_id": client_id }
    emit("set_client_id", client_id_response)

    _logger.debug(f"Received connect call, client id: {client_id}, sid: {request.sid}")


@socketio.on("disconnect")
def on_disconnect():
    with session_scope() as session:
        session.execute(delete(Client).where(Client.sid == request.sid))

    _logger.debug(f"Received disconnect call without data")


@socketio.on("check_alive")
def on_check_alive(unused_data):
    """This function can be called when front-end wants to make sure that the
    connection to back-end still holds. This function will respond with an
    acknowledgement.

    Keyword arguments:
    unused_data -- N/A
    """
    _logger.debug(f"Received check_alive API call with data: {unused_data}")
    response = {}
    response["fcn"] = "ack"
    response["fcn_name"] = "check_alive"

    _logger.debug(response)
    emit("response", response)


@socketio.on("quit")
def on_quit(unused_data):
    """This function can be called when front-end wants to exit and quit the
    program. This function will respond with an acknowledgement and send
    a QUIT request to RDS.

    Keyword arguments:
    unused_data -- N/A
    """
    _logger.debug(f"Received quit API call with data: {unused_data}")
    request_to_rds = {}
    request_to_rds["fcn"] = "quit"
    request_to_rds["arg"] = ""
    thread_handler.get_rds_pub_thread().add_request(request_to_rds)

    response = {}
    response["fcn"] = "ack"
    response["fcn_name"] = "quit"

    _logger.debug(f"quit resp: {response}")
    emit("response", response)


@socketio.on("set_area")
def on_set_area(data):
    """This function should be called immediately after INIT_CONNECTION, RDS
    will not listen to any requests before this function is called. This
    function will respond with an acknowledgement and send a SET_AREA request to
    RDS with the data specified.

    Keyword arguments:
    data -- Will specify the AREA. See internal document (API.md) for details.
    """

    _logger.debug(f"Received set_area API call with data: {data}")
    keys_exists = check_keys_exists(data, [("arg", "coordinates"), ("arg", "client_id"), ("arg", "bounds")],)

    if keys_exists:
        if not check_client_id(data["arg"]["client_id"], "set_area", _logger):
            return
        if not check_coordinates_list(data["arg"]["coordinates"], "set_area", _logger):
            return
        if not check_coords_in_list(data["arg"]["coordinates"], "set_area", _logger):
            return
        # TODO: do a similar check for bounds argument as well

        sessionID = None
        with session_scope() as session:
            client = session.get(Client, data["arg"]["client_id"])

            if client is None:
                client_id=data["arg"]["client_id"]
                emit_error_response("set_area", f"Could not retrieve a client with that ID {client_id}, try calling 'init_connection' again.", _logger)
                return
            
            sessionID = client.session_id  # Save ID so it's accesible outside scope.
            
            # Retrieve the prioritized client for current user session
            stmt = select(Client).where((and_(Client.session_id == sessionID, Client.is_prio_client == True)))
            prioritized_client = session.scalars(stmt).first()
            
            if prioritized_client and prioritized_client.id != client.id:
                # Tried to set area as an unprioritized client, send back correct area and prio info to client.

                stmt = select(UserSession).where(UserSession.id == sessionID)
                user_session = session.scalars(stmt).first()
                
                # Prepare to send area and prio information back to frontend (one client only)
                high_priority_client_id = prioritized_client.id
                reply_bounds = [user_session.bounds1.to_list(), user_session.bounds2.to_list()]
                reply_coordinates = [vertex.coordinate.to_json() for vertex in user_session.area_vertices]
                broadcast = False
            else:
                
                if prioritized_client is None:
                    client.is_prio_client = True
                else: # we are already prioritized, thus we are redefining area
                    # Delete old area vertices before adding the new ones.
                    session.execute(delete(AreaVertex).where(AreaVertex.session_id == sessionID))
                
                # Prepare to send area and prio information back to frontend
                high_priority_client_id = data["arg"]["client_id"]
                reply_bounds = data["arg"]["bounds"]
                reply_coordinates = data["arg"]["coordinates"]

                # Save the received area information in database.
                stmt = (
                    update(UserSession)
                    .where(UserSession.id == sessionID)
                    .values(bounds1=coordinate_from_list(reply_bounds[0]), bounds2=coordinate_from_list(reply_bounds[1])))
                session.execute(stmt)
            
                for i, coord in enumerate(reply_coordinates, 1):
                    vertex = AreaVertex(session_id=sessionID, vertex_no=i, coordinate=coordinate_from_json(coord))
                    session.add(vertex)
                session.commit()


                # Prepare to send area and prio information back to frontend
                high_priority_client_id = data["arg"]["client_id"]
                reply_bounds = data["arg"]["bounds"]
                reply_coordinates = data["arg"]["coordinates"]
                broadcast = True


        # Send set_area to RDS, for some reason
        request_to_rds = {}
        request_to_rds["fcn"] = "set_area"
        request_to_rds["arg"] = {}
        request_to_rds["arg"]["client_id"] = sessionID

        coordinates_to_rds = {}
        index_base = "wp"

        for i in range(len(data["arg"]["coordinates"])):
            index_unique = index_base + str(i)
            coordinates_to_rds[index_unique] = data["arg"]["coordinates"][i]

        request_to_rds["arg"]["coordinates"] = coordinates_to_rds
        thread_handler.get_rds_pub_thread().add_request(request_to_rds)

        # Send acknowledgement to frontend
        response = {}
        response["fcn"] = "ack"
        response["fcn_name"] = "set_area"

        _logger.debug(f"set_area resp: {response}")
        emit("response", response)

        # Send area info and which user has priority to frontend
        set_prio_response = {
            "high_priority_client": high_priority_client_id,
            "bounds": reply_bounds,
            "coordinates": reply_coordinates
        }
        
        _logger.debug(f"sending ({'broadcast' if broadcast else 'not broadcast'}) set_priority: {set_prio_response}")
        if broadcast:
            emit("set_priority", set_prio_response, room=sessionID)
        else:
            #TODO: check if this really only sends to one guy, and that the broadcasts are sent to ALL 
            emit("set_priority", set_prio_response)

        


@socketio.on("request_view")
def on_request_view(data):
    """This function will respond with images that overlap with the area
    specified in data and send a POI (non-prioritized) request to the RDS which
    in turn respond with images over that view.

    Keyword arguments:
    data -- Will specify the current VIEW. See internal document (API.md) for details.
    """

    

    _logger.debug(f"Received request_view API call with data: {data}")
    # Check arguments
    keys_exists = check_keys_exists(data, [("arg", "coordinates"), ("arg", "client_id")])
    if keys_exists:
        if not check_client_id(data["arg"]["client_id"], "request_view", _logger):
            return
        if not check_coord_dict(data["arg"]["coordinates"], "request_view", _logger):
            return
        if not check_type(data["arg"]["type"], "request_view", _logger):
            return

        sessionID = None
        requested_view = data["arg"]["coordinates"]
        client_id = data["arg"]["client_id"]
        with session_scope() as session:
            client = session.get(Client, client_id)
            if client is not None:
                sessionID = client.session_id  # Save ID so it's accesible outside scope.
            else:
                emit_error_response("request_view", f"Could not retrieve a client with that ID ({client_id}), try calling 'init_connection' again.", _logger)
                return

        # Assemble request to RDS.
        request_to_rds = {}
        request_to_rds["fcn"] = "add_poi"
        request_to_rds["arg"] = {}
        request_to_rds["arg"]["client_id"] = sessionID
        request_to_rds["arg"]["force_que_id"] = 0 # Not a prioritized image
        request_to_rds["arg"]["coordinates"] = requested_view
        thread_handler.get_rds_pub_thread().add_request(request_to_rds)

        view = [
                 (requested_view["down_left"]["long"], requested_view["down_left"]["lat"]),
                 (requested_view["up_left"]["long"], requested_view["up_left"]["lat"]),
                 (requested_view["up_right"]["long"], requested_view["up_right"]["lat"]),
                 (requested_view["down_right"]["long"], requested_view["down_right"]["lat"])
               ]

        img_data = []
        with session_scope() as session:
            all_images = session.query(Image).filter(Image.type==data["arg"]["type"], Image.is_covered==False).all()
            if len(all_images) > 0:
                for img in all_images:

                    img_view = [
                                 (img.down_left.long, img.down_left.lat),
                                 (img.up_left.long, img.up_left.lat),
                                 (img.up_right.long, img.up_right.lat),
                                 (img.down_right.long, img.down_right.lat)
                               ]

                    if is_overlapping(view, img_view):
                        # Assemble new data.
                        new_data = {"type": img.type,
                                    "prioritized": img.prio_image is not None,
                                    "image_id": img.id,
                                    "time_taken": img.time_taken,
                                    "url": BACKEND_BASE_URL + "/get_image/"+str(img.id),
                                    "coordinates": {
                                                      "up_left": {"long":img.up_left.long,
                                                                  "lat":img.up_left.lat},
                                                      "up_right": {"long":img.up_right.long,
                                                                  "lat":img.up_right.lat},
                                                      "down_left": {"long":img.down_left.long,
                                                                  "lat":img.down_left.lat},
                                                      "down_right": {"long":img.down_right.long,
                                                                  "lat":img.down_right.lat},
                                                      "center": {"long": img.center.long,
                                                                "lat": img.center.lat}
                                                   }
                                    }
                        img_data.append(new_data)

        # Assemble response to GUI.
        response={}
        response["fcn"] = "ack"
        response["fcn_name"] = "request_view"
        response["arg"] = {}
        response["arg"]["image_data"] = img_data

        _logger.debug(f"request_view resp: {response}")
        emit("response", response)

@socketio.on("request_priority_view")
def on_request_priority_view(data):
    """This function will NOT respond with images that overlap with the area.
    Instead it will send a POI (prioritized) request to the RDS which will respond
    later to back-end. It will respond with an acknowledgement.
    When the priotized image is then recieved it will be sent seperately to front-end.

    Keyword arguments:
    data -- Will specify the current VIEW. See internal document (API.md) for details.
    """
    _logger.debug(f"Received request_priority_view API call with data: {data}")
    # Check arguments
    keys_exists = check_keys_exists(data, [("arg", "client_id")])
    if keys_exists:
        if not check_client_id(data["arg"]["client_id"], "request_priority_view", _logger):
            return
        if not check_coord_dict(data["arg"]["coordinates"], "request_priority_view", _logger):
            return
        if not check_type(data["arg"]["type"], "request_priority_view", _logger):
            return

        sessionID = None
        prio_imageID = None
        client_id = data["arg"]["client_id"]
        with session_scope() as session:
            client = session.get(Client, client_id)
            if client is not None:
                sessionID = client.session_id  # Save ID so it's accesible outside scope.
            else:
                emit_error_response("request_view", f"Could not retrieve a client with that ID ({client_id}), try calling 'init_connection' again.", _logger)
                return

            priority_image = PrioImage(
                session_id=sessionID,
                time_requested=int(time.time()),
                status="PENDING",
                center=coordinate_from_json(data["arg"]["coordinates"]["center"]),
                up_left=coordinate_from_json(data["arg"]["coordinates"]["up_left"]),
                up_right=coordinate_from_json(data["arg"]["coordinates"]["up_right"]),
                down_right=coordinate_from_json(data["arg"]["coordinates"]["down_right"]),
                down_left=coordinate_from_json(data["arg"]["coordinates"]["down_left"])
            )

            session.add(priority_image)
            session.commit()
            prio_imageID = priority_image.id # Save ID so it's accesible.


        # Assemble request to RDS.
        request_to_rds = {}
        request_to_rds["fcn"] = "add_poi"
        request_to_rds["arg"] = {}
        request_to_rds["arg"]["client_id"] = sessionID
        request_to_rds["arg"]["force_que_id"] = prio_imageID
        request_to_rds["arg"]["coordinates"] = data["arg"]["coordinates"]
        request_to_rds["arg"]["type"] = data["arg"]["type"]
        thread_handler.get_rds_pub_thread().add_request(request_to_rds)

        # Assemble response to GUI.
        response={}
        response["fcn"] = "ack"
        response["fcn_name"] = "request_priority_view"
        response["arg"] = {}
        response["arg"]["force_que_id"] = prio_imageID

        _logger.debug(f"request_priority_view resp: {response}")
        emit("response", response)


@socketio.on("clear_que")
def on_clear_queue(unused_data):
    """This function will cancell all PRIOTIZED images that previously have been
    requested but not yet delivered. It will respond with an acknowledgement and
    send a CLEAR_QUE request to RDS.

    Keyword arguments:
    unused_data -- N/A
    """
    _logger.debug(f"Received clear_que API call with data: {unused_data}")
    # Sends request to rds pub thread
    request_to_rds = {}
    request_to_rds["fcn"] = "clear_que"
    request_to_rds["arg"] = ""
    thread_handler.get_rds_pub_thread().add_request(request_to_rds)

    # Set the status of all PrioImages which are pending in the database to "CANCELLED".
    with session_scope() as session:
        prio_images = session.query(PrioImage).filter(PrioImage.status == "PENDING").\
            update({PrioImage.status:"CANCELLED"})

    response = {}
    response["fcn"] = "ack"
    response["fcn_name"] = "clear_que"

    _logger.debug(f"clear_que resp: {response}")
    emit("response", response)


@socketio.on("set_mode")
def on_set_mode(data):
    """This function will change the current mode of the system, it can change
    between "AUTO" or "MAN". This function will respond with and acknowledgement
    and send a SET_MODE request to RDS.

    Keyword arguments:
    data -- Will specify the MODE. See internal document (API.md) for details.
    """
    _logger.debug(f"Received set_mode API call with data: {data}")
        # Check arguments.
    keys_exists = check_keys_exists(data, [("arg", "mode"), ("arg", "zoom")])
    if keys_exists:
        if not check_coord_dict(data["arg"]["zoom"], "set_mode", _logger):
            return
        if not check_mode(data["arg"]["mode"], "set_mode", _logger):
            return

        request_to_rds = {}
        request_to_rds["fcn"] = "set_mode"
        request_to_rds["arg"] = {}
        request_to_rds["arg"]["mode"] = data["arg"]["mode"]
        request_to_rds["arg"]["zoom"] = data["arg"]["zoom"]
        thread_handler.get_rds_pub_thread().add_request(request_to_rds)

        # Update the global mode.
        current_mode = data["arg"]["mode"]

        response = {}
        response["fcn"] = "ack"
        response["fcn_name"] = "set_mode"

        _logger.debug(f"set_mode resp: {response}")
        emit("response", response)


@socketio.on("get_info")
def on_get_info(unused_data):
    """This function will respond with information about the drones.
    It will not send a request to RDS since this information is regularly fetched.

    Keyword arguments:
    unused_data -- N/A
    """
    _logger.debug(f"Received get_info API call with data: {unused_data}")
    all_drones = None
    with session_scope() as session:
        all_drones = session.query(Drone).all()

        if len(all_drones) != 0:
            response = {}
            response["fcn"] = "ack"
            response["fcn_name"] = "get_info"
            response["arg"] = {}
            response["arg"]["data"] = []
            for drone in all_drones:
                new_drone_data = {}
                new_drone_data["drone-id"] = drone.id
                new_drone_data["time2bingo"] = drone.time2bingo
                response["arg"]["data"].append(new_drone_data)

            # Response is assembled
            _logger.debug(f"get_info resp: {response}")
            emit("response", response)

        else:
            emit_error_response("get_info", "Unable to find drones", _logger)
            return


@socketio.on("que_ETA")
def que_ETA(unused_data):
    """This function will respond with the ETA for the next item.
    It will not send a request to RDS since this information is regularly fetched.

    Keyword arguments:
    unused_data -- N/A
    """
    _logger.debug(f"Received que_ETA API call with data: {unused_data}")
    next_eta_drone = None  # Holds drone with next ETA.
    with session_scope() as session:
        next_eta_image = session.query(func.min(PrioImage.eta)).first()

        # Proceed if a drone is found.
        if next_eta_image is not None:
            response = {}
            response["fcn"] = "ack"
            response["fcn_name"] = "que_ETA"
            response["arg"] = {}
            response["arg"]["ETA"] = next_eta_image[0]

            _logger.debug(f"que_ETA resp: {response}")
            emit("response", response)

        else:
            emit_error_response("que_ETA", "Unable to find drone", _logger)
            return


def run_imm():
    """Starts the application.

    Note that the server is currently running on the built in Werkzeug
    development server in Flask.

    port -- Specify at which port to run the application.
    log_output -- Specify if the server should log information in the terminal.
    """
    socketio.run(app, host="0.0.0.0", port=SERVER_PORT, log_output=SERVER_LOG_OUTPUT)


def stop_imm():
    """Not yet implemented - Does nothing"""
    pass


if __name__=="__main__":
    thread_handler.start_threads()
    use_production_db()
    run_imm()
