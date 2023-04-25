/**
 * Redux storage file.
 */

import { createAction, createReducer, configureStore } from "@reduxjs/toolkit";
import { connect as unboundConnect } from "react-redux";
import Axis from "axis.js";
import frontendConfig from "../frontendConfig.json";

const DEFAULT_ZOOM_LEVEL = 14;

const DEFAULT_CONFIG = sessionStorage.getItem("config")
  ? JSON.parse(sessionStorage.getItem("config"))
  : frontendConfig;

const startView = {
  upLeft: {
    lat: 58.402859,
    lng: 15.5644576,
  },
  upRight: {
    lat: 58.402859,
    lng: 15.5918166,
  },
  downLeft: {
    lat: 58.394982,
    lng: 15.5644576,
  },
  downRight: {
    lat: 58.394982,
    lng: 15.5918166,
  },
  center: {
    lat: 58.39938,
    lng: 15.5753366,
  },
};

/**
 * Structure for the request queue.
 * 
 * {
    size: (int),
    items: [
        {
            time: (timestamp),
            id: (int)
        },
        {
            time: (timestamp),
            id: (int)
        },
        ...
    ]
    }
 */

/* Elements are structured like following example:
{
    "type" : #Choice "RGB/IR",
    "prioritized" : #Choice: "True/False",
    "image_id" : "integer(1, -)", # Id of image
    "url": tbd: "URL",
    "time_taken" : "integer(1,-)",
    "coordinates" :
        {
            "up_left": # It is a COORDINATE.
                {
                "lat" : 58.123456,
                "long":16.123456
                },
            "up_right": # It is a COORDINATE.
                {
                "lat":59.123456,
                "long":17.123456
                },
            "down_left": # It is a COORDINATE.
                {
                "lat":60.123456,
                "long":18.123456
                },
            "down_right": # It is a COORDINATE.
                {
                "lat":61.123456,
                "long":19.123456
                },
            "center": # It is a COORDINATE.
                {
                "lat":61.123456,
                "long":19.123456
                }
        }
        
}
*/
var initialActivePictures = [];

const initialUserPriority = 1;

/**
 * ====================================================================================================
 *                                             Actions
 * ====================================================================================================
 */

/**
 * Actions related to waypoints defining the area of interest.
 */
export const addAreaWaypoint = createAction(
  "ADD_AREA_WAYPOINT",
  function prepare(waypoint) {
    if (
      waypoint.lat !== undefined &&
      waypoint.lng !== undefined &&
      !isNaN(waypoint.lat) &&
      !isNaN(waypoint.lng)
    ) {
      return {
        payload: waypoint,
      };
    } else {
      throw new Error("Invalid waypoint!");
    }
  }
);

export const removeAreaWaypoint = createAction(
  "REMOVE_AREA_WAYPOINT",
  function prepare(index) {
    if (0 <= index && !isNaN(index)) {
      return {
        payload: index,
      };
    } else {
      throw new Error("Index not found in waypoints.");
    }
  }
);

export const clearAreaWaypoints = createAction("CLEAR_AREA_WAYPOINTS");

/**
 * Client ID, restricted to a number.
 */
export const setClientID = createAction(
  "SET_CLIENT_ID",
  function prepare(token) {
    if (!isNaN(token)) {
      return {
        payload: token,
      };
    } else {
      throw new Error("Client ID must be a number.");
    }
  }
);

export const setConfigValue = createAction(
  "SET_CONFIG_VALUE",
  function prepare(key, value) {
    return {
      payload: {
        key: key,
        value: value,
      },
    };
  }
);

/**
 * User Priority, restricted to a number.
 * Determines which permissions a user has
 */
export const setUserPriority = createAction(
  "SET_USER_PRIORITY",
  function prepare(token) {
    if (!isNaN(token)) {
      return {
        payload: token,
      };
    } else {
      throw new Error("User Priority must be a number.");
    }
  }
);

/**
 * Map zoom level, restricted to 0-22.
 */
export const setZoomLevel = createAction(
  "SET_ZOOM_LEVEL",
  function prepare(level) {
    if (0 <= level && level <= 22) {
      return {
        payload: level,
      };
    } else if (0 > level) {
      return {
        payload: 0,
      };
    } else {
      return {
        payload: 22,
      };
    }
  }
);

/**
 * Current map view. Stored as stringified JSON.
 */
export const setMapPosition = createAction(
  "SET_MAP_POSITION",
  function prepare(view) {
    if (
      view.upLeft !== undefined &&
      view.upRight !== undefined &&
      view.downLeft !== undefined &&
      view.downRight !== undefined &&
      view.center !== undefined &&
      !isNaN(view.upLeft.lat) &&
      !isNaN(view.upRight.lat) &&
      !isNaN(view.downLeft.lat) &&
      !isNaN(view.downRight.lat) &&
      !isNaN(view.upLeft.lng) &&
      !isNaN(view.upRight.lng) &&
      !isNaN(view.downLeft.lng) &&
      !isNaN(view.downRight.lng) &&
      !isNaN(view.center.lat) &&
      !isNaN(view.center.lng)
    ) {
      return {
        payload: view,
      };
    } else {
      throw new Error("Invalid view!");
    }
  }
);

/**
 * Actions related to priority picture request queue.
 */
export const clearPictureRequestQueue = createAction(
  "CLEAR_PICTURE_REQUEST_QUEUE"
);

export const addPictureRequest = createAction(
  "ADD_PICTURE_REQUEST",
  function prepare(id, view, isUrgent) {
    if (!isNaN(id)) {
      return {
        payload: {
          id: id,
          requestTime: Date.now(),
          receiveTime: null,
          received: false,
          view: view,
          isUrgent: isUrgent,
        },
      };
    } else {
      throw new Error("Invalid request ID!");
    }
  }
);

export const removePictureRequest = createAction(
  "REMOVE_REQUEST",
  function prepare(index) {
    if (0 <= index && !isNaN(index)) {
      return {
        payload: index,
      };
    } else {
      throw new Error("Invalid index!");
    }
  }
);

export const receivePictureRequest = createAction(
  "RECEIVE_REQUEST",
  function prepare(id) {
    if (!isNaN(id)) {
      return {
        payload: id,
      };
    } else {
      throw new Error("Invalid image ID.");
    }
  }
);

/**
 * Actions related to current active pictures.
 */
export const addActivePicture = createAction(
  "ADD_ACTIVE_PICTURE",
  function prepare(picture) {
    let type = picture.type;
    let prioritized = picture.prioritized;
    let imageID = picture.imageID;
    let url = picture.url;
    let timeTaken = picture.timeTaken;
    let view = picture.coordinates;
    if (type !== undefined && (type === "RGB" || type === "IR")) {
    } else {
      throw new Error("Type invalid!");
    }
    if (prioritized !== undefined && Axis.isBoolean(prioritized)) {
    } else {
      throw new Error("Prioritized invalid!");
    }
    if (imageID !== undefined && !isNaN(imageID)) {
    } else {
      throw new Error("imageID invalid!");
    }
    if (url !== undefined && typeof url == "string") {
    } else {
      throw new Error("URL invalid!");
    }
    if (timeTaken !== undefined && !isNaN(timeTaken)) {
    } else {
      throw new Error("timeTaken invalid!");
    }
    if (
      view !== undefined &&
      view.upLeft !== undefined &&
      view.upRight !== undefined &&
      view.downLeft !== undefined &&
      view.downRight !== undefined &&
      view.center !== undefined &&
      !isNaN(view.upLeft.lat) &&
      !isNaN(view.upRight.lat) &&
      !isNaN(view.downLeft.lat) &&
      !isNaN(view.downRight.lat) &&
      !isNaN(view.upLeft.lng) &&
      !isNaN(view.upRight.lng) &&
      !isNaN(view.downLeft.lng) &&
      !isNaN(view.downRight.lng) &&
      !isNaN(view.center.lat) &&
      !isNaN(view.center.lng)
    ) {
    } else {
      throw new Error("Coordinates invalid!");
    }
    return {
      payload: picture,
    };
  }
);

export const removeActivePicture = createAction("REMOVE_ACTIVE_PICTURE");
export const clearActivePictures = createAction("CLEAR_ACTIVE_PICTURES");

/**
 * Actions related map bounds
 */
export const setMapBounds = createAction(
  "SET_MAP_BOUNDS",
  function prepare(bounds) {
    if (
      bounds instanceof Array &&
      bounds[0] instanceof Array &&
      bounds[1] instanceof Array &&
      !isNaN(bounds[0][0]) &&
      !isNaN(bounds[1][0]) &&
      !isNaN(bounds[0][1]) &&
      !isNaN(bounds[1][1])
    ) {
      return {
        payload: bounds,
      };
    } else {
      throw new Error(
        "Bounds should be a pair of coordinates. Ex: [[1,2], [2,1]]"
      );
    }
  }
);

export const clearMapBounds = createAction("CLEAR_MAP_BOUNDS");

/**
 * Action related to Mode (Manual or Auto).
 */
export const setMode = createAction("SET_MODE", function prepare(text) {
  if (text === "MAN" || text === "AUTO") {
    return {
      payload: text,
    };
  } else {
    throw new Error("Mode must be either MAN or AUTO.");
  }
});

/**
 * Action related to map state (Main or StartUp).
 */
export const setMapState = createAction(
  "SET_MAP_STATE",
  function prepare(text) {
    if (text === "Main" || text === "StartUp") {
      return {
        payload: text,
      };
    } else {
      throw new Error("State must be either Main or StartUp.");
    }
  }
);

/**
 * Actions related to LayerType mode (RGB, IR or Map).
 */
export const setLayerType = createAction(
  "SET_LAYER_TYPE",
  function prepare(layerType) {
    if (layerType === "RGB" || layerType === "IR" || layerType === "Map") {
      return {
        payload: layerType,
      };
    } else {
      throw new Error("LayerType must be either RGB, IR or Map.");
    }
  }
);

/**
 * Actions related to messages.
 */
export const MESSAGE_TYPES = ["error", "message", "exception"];

export const addMessage = createAction(
  "ADD_MESSAGE",
  function prepare(type, heading, message) {
    if (MESSAGE_TYPES.find((value) => type === value) === -1)
      throw new Error(
        "Message type must be one of the following types: " +
          MESSAGE_TYPES.join(", ") +
          "."
      );

    if (!Axis.isNull(heading) && !Axis.isString(heading))
      throw new Error("Heading must be null or string.");

    if (!Axis.isNull(message) && !Axis.isString(message))
      throw new Error("Message must be null or string.");

    return {
      payload: {
        type: type,
        heading: heading,
        message: message,
      },
    };
  }
);
export const removeMessage = createAction("REMOVE_MESSAGE");
export const clearMessages = createAction("CLEAR_MESSAGES");

/**
 * Action related to crossing lines message (showWarning)
 */
export const setShowWarning = createAction(
  "SET_SHOW_ERROR",
  function prepare(shouldShow) {
    return { payload: shouldShow };
  }
);

/**
 * ====================================================================================================
 *                                             Reducers
 * ====================================================================================================
 */

export const _areaWaypoints = createReducer([], (builder) => {
  builder
    .addCase(addAreaWaypoint, (state, action) => {
      const newWaypoint = action.payload;
      return [...state, newWaypoint];
    })
    .addCase(removeAreaWaypoint, (state, action) => {
      const index = action.payload;
      return [...state.slice(0, index), ...state.slice(index + 1)];
    })
    .addCase(clearAreaWaypoints, (state, action) => {
      return [];
    });
});

export const _clientID = createReducer(null, (builder) => {
  builder.addCase(setClientID, (state, action) => {
    const newID = action.payload;
    return newID;
  });
});

export const _userPriority = createReducer(initialUserPriority, (builder) => {
  builder.addCase(setUserPriority, (state, action) => {
    const newUserPriority = action.payload;
    return newUserPriority;
  });
});

export const _config = createReducer(DEFAULT_CONFIG, (builder) => {
  builder.addCase(setConfigValue, (state, action) => {
    state[action.payload.key] = action.payload.value;
    sessionStorage.setItem("config", JSON.stringify(state));
    return state;
  });
});

export const _zoomLevel = createReducer(DEFAULT_ZOOM_LEVEL, (builder) => {
  builder.addCase(setZoomLevel, (state, action) => {
    const newZoom = action.payload;
    return newZoom;
  });
});

export const _mapPosition = createReducer(startView, (builder) => {
  builder.addCase(setMapPosition, (state, action) => {
    const newPosition = action.payload;
    return newPosition;
  });
});

export const _pictureRequestQueue = createReducer([], (builder) => {
  builder
    .addCase(addPictureRequest, (state, action) => {
      const newState = [...state, action.payload];
      return newState;
    })
    .addCase(removePictureRequest, (state, action) => {
      const index = action.payload;
      return [
        //Removes item "index" from id list.
        ...state.slice(0, index),
        ...state.slice(index + 1),
      ];
    })
    .addCase(receivePictureRequest, (state, action) => {
      const index = state.map((e) => e.id).indexOf(action.payload);

      if (index !== -1) {
        return [
          ...state.slice(0, index),
          {
            ...state[index],
            received: true,
            receivedTime: Date.now(),
          },
          ...state.slice(index + 1),
        ];
      }

      // If ID is not found, make no change
      return state;
    })
    .addCase(clearPictureRequestQueue, (state) => {
      return [];
    });
});

export const _activePictures = createReducer(
  initialActivePictures,
  (builder) => {
    builder
      .addCase(addActivePicture, (state, action) => {
        return [...state, action.payload];
      })
      .addCase(removeActivePicture, (state, action) => {
        const index = action.payload;
        return [
          //Removes item "index" from list.
          ...state.slice(0, index),
          ...state.slice(index + 1),
        ];
      })
      .addCase(clearActivePictures, (state) => {
        var newState = [];
        return newState;
      });
  }
);

export const _mapBounds = createReducer(null, (builder) => {
  builder
    .addCase(setMapBounds, (state, action) => {
      return action.payload;
    })
    .addCase(clearMapBounds, (state, action) => {
      return null;
    });
});

export const _mode = createReducer("AUTO", (builder) => {
  builder.addCase(setMode, (state, action) => {
    const newMode = action.payload;
    return newMode;
  });
});

export const _layerType = createReducer("RGB", (builder) => {
  builder.addCase(setLayerType, (state, action) => {
    const newMode = action.payload;
    return newMode;
  });
});

export const _messages = createReducer([], (builder) => {
  builder
    .addCase(addMessage, (state, action) => {
      const newMessage = action.payload;
      return [...state, newMessage];
    })
    .addCase(removeMessage, (state, action) => {
      const index = action.payload;
      return [...state.slice(0, index), ...state.slice(index + 1)];
    })
    .addCase(clearMessages, (state, action) => {
      return [];
    });
});

export const _mapState = createReducer("Main", (builder) => {
  builder.addCase(setMapState, (state, action) => {
    const newState = action.payload;
    return newState;
  });
});

export const _showWarning = createReducer(false, (builder) => {
  builder.addCase(setShowWarning, (state, action) => {
    const show = action.payload;
    return show;
  });
});

/**
 * ====================================================================================================
 *                                      State mapping functions
 * ====================================================================================================
 */
/**
 * These map the state variable to props of a React components.
 */

export function areaWaypoints(state) {
  return {
    areaWaypoints: state.areaWaypoints,
  };
}

export function clientID(state) {
  return {
    clientID: state.clientID,
  };
}

export function userPriority(state) {
  return {
    userPriority: state.userPriority,
  };
}

export function config(state) {
  return {
    config: state.config,
  };
}

export function zoomLevel(state) {
  return {
    zoomLevel: state.zoomLevel,
  };
}

export function mapPosition(state) {
  return {
    mapPosition: state.mapPosition,
  };
}

export function pictureRequestQueue(state) {
  return {
    pictureRequestQueue: state.pictureRequestQueue,
  };
}

export function activePictures(state) {
  return {
    activePictures: state.activePictures,
  };
}

export function mapBounds(state) {
  return {
    mapBounds: state.mapBounds,
  };
}

export function mode(state) {
  return {
    mode: state.mode,
  };
}

export function layerType(state) {
  return {
    layerType: state.layerType,
  };
}

export function messages(state) {
  return {
    messages: state.messages,
  };
}

export function mapState(state) {
  return {
    mapState: state.mapState,
  };
}

export function showWarning(state) {
  return {
    showWarning: state.showWarning,
  };
}
const states = {
  areaWaypoints,
  clientID,
  config,
  userPriority,
  zoomLevel,
  mapPosition,
  pictureRequestQueue,
  activePictures,
  mapBounds,
  mode,
  layerType,
  messages,
  mapState,
  showWarning,
};

/**
 * Combine multiple functions into a single.
 *
 * @param {Array | Object} funcs Functions to combine.
 */
export function combineStateMappings(funcs) {
  if (Axis.isObject(funcs)) funcs = Object.values(funcs);

  return (state) => {
    let obj;
    for (let func of funcs) {
      obj = { ...obj, ...func(state) };
    }
    return obj;
  };
}

/**
 * ====================================================================================================
 *                                         Dispatch mapping
 * ====================================================================================================
 */
/**
 * These map the action dispatches to React component props.
 */

export const areaWaypointActions = {
  addAreaWaypoint,
  removeAreaWaypoint,
  clearAreaWaypoints,
};

export const clientIDActions = { setClientID };

export const userPriorityActions = { setUserPriority };

export const configActions = { setConfigValue };

export const zoomLevelActions = { setZoomLevel };

export const mapPositionActions = { setMapPosition };

export const pictureRequestQueueActions = {
  addPictureRequest,
  removePictureRequest,
  receivePictureRequest,
  clearPictureRequestQueue,
};

export const activePicturesActions = {
  addActivePicture,
  removeActivePicture,
  clearActivePictures,
};

export const mapBoundsActions = { setMapBounds, clearMapBounds };

export const modeActions = { setMode };

export const layerTypeActions = { setLayerType };

export const messagesActions = { addMessage, removeMessage, clearMessages };

export const mapStateActions = { setMapState };

export const showWarningActions = { setShowWarning };

const actions = {
  areaWaypointActions,
  clientIDActions,
  configActions,
  userPriorityActions,
  zoomLevelActions,
  mapPositionActions,
  pictureRequestQueueActions,
  activePicturesActions,
  mapBoundsActions,
  modeActions,
  layerTypeActions,
  messagesActions,
  mapStateActions,
  showWarningActions,
};

/**
 * Storage
 */

/**
 * Props merging function. This function describes how props of "connected" React components are shaped.
 */
function mergeProps(stateProps, dispatchProps, ownProps) {
  return {
    store: {
      ...stateProps,
      ...dispatchProps,
    },
    ...ownProps,
  };
}

export const store = configureStore({
  reducer: {
    areaWaypoints: _areaWaypoints,
    clientID: _clientID,
    userPriority: _userPriority,
    config: _config,
    zoomLevel: _zoomLevel,
    mapPosition: _mapPosition,
    pictureRequestQueue: _pictureRequestQueue,
    activePictures: _activePictures,
    mapBounds: _mapBounds,
    mode: _mode,
    layerType: _layerType,
    messages: _messages,
    mapState: _mapState,
    showWarning: _showWarning,
  },
});

/**
 * Pre bound connect function for easy "connecting" React components.
 * @example
 * export default connect({ areaWaypoints, connectionToken }, { ...areaWaypointActions, ...connectionTokenActions })(MyReactComponent)
 */
export const connect = (mapStateToProps, mapDispatchToProps) => {
  if (!Axis.isFunction(mapStateToProps))
    mapStateToProps = combineStateMappings(mapStateToProps);

  return unboundConnect(mapStateToProps, mapDispatchToProps, mergeProps);
};

const storageExports = { store, connect, ...states, ...actions };

export default storageExports;
