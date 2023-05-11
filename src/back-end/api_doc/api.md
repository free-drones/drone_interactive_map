z<!-- TOC -->

<!-- /TOC -->

**JSONtypes used in this API**
----
* **RECTANGLE:**
```json
  "COORDINATE" =
        {
        	"up_left":
                  {
                    "lat": 51.12356,
                    "long": 16.123456
                  },
        	"up_right":
                  {
                    "lat": 51.12356,
                    "long": 16.123456
                  },
        	"down_right":
                  {
                    "lat": 51.12356,
                    "long": 16.123456
                  },
        	"down_left":
                  {
                    "lat": 51.12356,
                    "long": 16.123456
                  },
        	"center":
                  {
                    "lat": 51.12356,
                    "long": 16.123456
                  }
        }

```

* **COORDINATE:**
```json
  "COORDINATE" =
        {
          "lat": 51.12356,
          "long": 16.123456
        }
```

  - `lat` and `long` are floats.

---
**GENERAL**
----
Front-end have to listen/use two channels for communinication:
  * Back-end will answer requests on `"response"` channel, see data contents for more information.
  * Back-end will notify front-end on `"notify"` channel, see data contents for more information.
  * To listen to these channels use `socketio.on` or `socketio.once`


An example on how to call the functions defined below:
-  `socketio.emit(Event name, data that should be sent)`

---
# **Error Responses**

Functions will return an error response if something goes wrong.

The error response are in following format and will be returned in the `"response"` channel.
  * **Channel:**
    `"response"`

  * **Data Content:**
```json
    {
     "fcn" : "error",
     "fcn_name" : "function_call",
     "error_report" : "Description of what went wrong. This is used for debugging purposes."
    }
```


---
# **API calls from front-end to back-end:**


**Connect to back-end**
----
To connect to back-end call `init_connection`, it will do the following:

1. Create a new client linked to this connection.
2. Client/this connection will join a `socketio room` linked to a `session`.

This function will then return a `client_id` which is a unique identifier for this client,
the `client_id` must be saved since it is required for future calls to the back-end.


* **Event name:**

     `init_connection`

* **Data to be sent (JSON format)**
     `N/A`

* **Success Response**
    * **Channel:**
      `"response"`
    * **Data Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "connect",
         "arg" : {
                   "client_id" : "integer(1, -)"
                 }
        }
    ```
    * `client_id` is a unique identifier for a client.


----
**Check that the connection to back-end is alive**
----
  Check so that the connection to the back-end is till alive and working.

* **Event Name**
  `"check_alive"`

* **Data to be sent (JSON format):** `N/A`

* **Response:**
    * **Channel:** `"response"`
    * **Data Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "check_alive"
        }
    ```
* **Supports Error Responses:**
`False`


----
**Disconnect from back-end**
----
  Disconnect from back-end which in turn disconnects from the RDS.
  After this is called communication will come to a halt.

* **Event Name**
  `"quit"`

* **Data to be sent (JSON format)**
  `N/A`

* **Success Response:**
  * **Channel:** `"response"`

  *  **Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "quit"
        }
    ```


----
**Define area**
----
Define an area of interest (boundaries).
Must be called after `/function/connect` before back-end will listen to any other instructions.

* **Event Name**
`"set_area"`

* **Data to be sent (JSON format)**

```json
{
  "fcn" : "set_area",
  "arg" :
    {
      "client_id" : "integer(1,-)",

      "coordinates" : [
                          {
                            "lat": 51.12356,
                            "long": 16.123456
                          },
                          {
                            "lat": 51.12356,
                            "long": 16.123456
                          },
                          {
                            "lat": 51.12356,
                            "long": 16.123456
                          }
                      ]
      }

}
```
* **Success Response:**
  * **Channel:** `"response"`

  * **Content:**
  ```json
      {
       "fcn" : "ack",
       "fcn_name" : "set_area",
      }
  ```

----
**Request view**
----
Request images from this area (non prioritized). Back-end will return image ID's
which cover specified area (this is to allow front-end to cache images).

`set_area` must be called once before this function is called.

* **Event Name**
  `"request_view"`

* **Data to be sent (JSON format)**

  ```json
  {
    "fcn" : "request_view",
    "arg" :
      {
        "client_id" : "integer(1, -)",
        "type" : "RGB/IR",
        "coordinates" : {
                          "up_left":
                                {
                                  "lat" : 58.123456,
                                  "long":16.123456
                                },
                        "up_right":
                                {
                                  "lat":59.123456,
                                  "long":17.123456
                                },
                        "down_left":
                                {
                                  "lat":60.123456,
                                  "long":18.123456
                                },
                        "down_right":
                                {
                                  "lat":61.123456,
                                  "long":19.123456
                                },
                        "center":
                                {
                                  "lat":61.123456,
                                  "long":19.123456
                                }
                      }
      }

  }

  ```
  - `type` must specify if the image is `"RGB"` or `"IR"`.

* **Success Response:**
    * **channel:** `response`
    * **Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "request_view",
         "arg" : { "image_data" : [
                                    {
                                      "type" : "RGB/IR",
                                      "prioritized" : "True/False",
                                      "image_id" : "integer(1, -)",
                                      "url": "http:ADRESS:PORT/get_image/<int:image_id>",
                                      "time_taken" : "integer(1,-)",
                                      "coordinates" :
                                                        {
                                                        "up_left":
                                                                {
                                                                  "lat" : 58.123456,
                                                                  "long":16.123456
                                                                },
                                                        "up_right":
                                                                {
                                                                  "lat":59.123456,
                                                                  "long":17.123456
                                                                },
                                                        "down_left":
                                                                {
                                                                  "lat":60.123456,
                                                                  "long":18.123456
                                                                },
                                                        "down_right":
                                                                {
                                                                  "lat":61.123456,
                                                                  "long":19.123456
                                                                },
                                                        "center":
                                                                {
                                                                  "lat":61.123456,
                                                                  "long":19.123456
                                                                }
                                                        }
                                    }
                                  ]
                 }
      }
    ```



- `image_data` will contain as many images that are recommended.
- `type` will specify if the image is `"RGB"` or `"IR"`.
- `prioritized` will specify if the image was requested as a priority image.
- `image_id` will specify a unique integer for that image
- `url` will specify the adress where the image can be retrieved. `ADRESS` and `PORT` is where the server can be reached. `<int:image_id>` is the unique identifier of an image.


----
**Request priority view**
----
Request prioritized images from specified area. Back-end will return image ID's
which cover specified area (this is to allow front-end to cache images).

`set_area` must be called once before this function is called.

* **Event Name**
  `"request_priority_view"`

* **Data to be sent (JSON format)**

  ```json
  {
    "fcn" : "request_priority_view",
    "arg" :
      {
        "client_id" : "integer(1, -)",
        "type" : "RGB/IR",
        "coordinates" :
                  {
                    "up_left":
                          {
                            "lat" : 58.123456,
                            "long":16.123456
                          },
                  "up_right":
                          {
                            "lat":59.123456,
                            "long":17.123456
                          },
                  "down_left":
                          {
                            "lat":60.123456,
                            "long":18.123456
                          },
                  "down_right":
                          {
                            "lat":61.123456,
                            "long":19.123456
                          },
                  "center":
                          {
                            "lat":61.123456,
                            "long":19.123456
                          }
                  }
      }
  }
  ```
  - `type` must specify if the image is `"RGB"` or `"IR"`.

* **Success Response:**
  * **Channel:** `"response"`
  * **Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "request_priority_view",
         "arg" :
            {
              "force_queue_id" : "integer(1,-)"
            }
        }
    ```
    - Note that the images will be sent later in a separate request to front-end.
    - `force_queue_id` is a unique identifier for the requested view.

----
**Clear queue of prioritized views.**
----
  Clear the queue of previously prioritized views.

* **Event Name**

  `"clear_queue"`

* **Data to be sent (JSON format)**
  `N/A`


* **Success Response:**
  * **Channel:** `"response"`
  *  **Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "clear_queue"
        }
    ```

----
**Change settings (mode).**
----
  Change the mode to `AUTO` or `MAN`

* **Event Name**
  `"set_mode"`


* **Data to be sent (JSON format)**

  ```json
  {"fcn" : "set_mode",
   "arg" :
      {
        "mode" : "AUTO/MAN",
        "zoom" :
            {
              "up_left":
                    {
                      "lat" : 58.123456,
                      "long":16.123456
                    },
            "up_right":
                    {
                      "lat":59.123456,
                      "long":17.123456
                    },
            "down_left":
                    {
                      "lat":60.123456,
                      "long":18.123456
                    },
            "down_right":
                    {
                      "lat":61.123456,
                      "long":19.123456
                    },
            "center":
                    {
                      "lat":61.123456,
                      "long":19.123456
                    }
            }
      }
  }
  ```
  - `mode` must specify if the mode is `"AUTO"` or `"MAN"`.

* **Success Response:**
    * **Channel:** `"response"`
    * **Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "set_mode"
        }
    ```

----
**Get queue_ETA**
----
  Get time until next item is completed (seconds).

* **Event Name**
  `"queue_ETA"`

* **Data to be sent (JSON format)**
  `N/A`


* **Success Response:**
  * **Channel:** `"response"`
  *  **Content:**
    ```json
        {
         "fcn" : "ack",
         "fcn_name" : "queue_ETA",
         "arg" : {"ETA" : "integer(1,-)"}
        }
    ```

----
# **API CALLS FROM BACK-END TO FRONT-END:**

----
**Notify about new images (including prioritized).**
----
  Notifies front-end when new images are sent by the RDS, including prioritized images.

* **Channel front-end listen to:**  `"notify"`
* **Function name:**  `"new_pic"`

* **Data to be sent (JSON format)**

  ```json
  {"fcn" : "new_pic",
   "arg" :
   {
     "type" : "RGB/IR",
     "prioritized" : "True/False",
     "image_id" : "integer(1, -)",
     "url": "http:ADRESS:PORT/get_image/<int:image_id>",
     "time_taken" : "integer(1,-)",
     "coordinates" :
                       {
                         "up_left":
                               {
                                 "lat" : 58.123456,
                                 "long":16.123456
                               },
                       "up_right":
                               {
                                 "lat":59.123456,
                                 "long":17.123456
                               },
                       "down_left":
                               {
                                 "lat":60.123456,
                                 "long":18.123456
                               },
                       "down_right":
                               {
                                 "lat":61.123456,
                                 "long":19.123456
                               },
                       "center":
                               {
                                 "lat":61.123456,
                                 "long":19.123456
                               }
                       }
   }
  }
  ```
  - `type` will specify if the image is `"RGB"` or `"IR"`.
  - `prioritized` will specify if the image was requested as a priority image.
  - `image_id` will specify a unique integer for that image.
  - `url` will specify the adress where the image can be retrieved. `ADRESS` and `PORT` is where the server can be reached. `<int:image_id>` is the unique identifier of an image.

* **Success Response:**

  * **Event Name**
  `"ack"`

  * **Data to be sent (JSON format)**
  `{"fcn": "ack", "fcn_name" : "new_pic"}`


----
**Notify about drone information**
----
  Notifies front-end of updated drone information, including location and mode.

* **Channel front-end listen to:**  `"notify"`
* **Function name:**  `"new_drones"`

* **Data to be sent (JSON format)**

  ```json
  {
    "fcn": "new_drones",
    "arg": {
      "drones": {
        "drone1": {
          "drone_id": "drone1",
          "location": {
            "lat": 59.123,
            "long": 18.123
          },
          "mode": "AUTO"
        },
        "drone2": {
          "drone_id": "drone2",
          "location": {
            "lat": 59.133,
            "long": 18.133
          },
          "mode": "MAN"
        },
        "drone3": {
          "drone_id": "drone3",
          "location": {
            "lat": 59.143,
            "long": 18.143
          },
          "mode": "PHOTO"
        }
      }
    }
  }
  ```
  Each drone in `drones` is specified by a key of the drone's id, e.g. `"drone1"`. For each drone the following information is provided:
  - `drone_id` specifies the id of the drone. The id is a string such as `"drone2"` and is equal to the key for the drone.
  - `location` specifies the current location of the drone in coordinates `lat`and `long`.
  - `mode` specifies the current flying mode of the drone and is one of `AUTO`, `MAN` or `PHOTO`

<br>

* **Success Response:**
  The frontend does not respond to these calls.
