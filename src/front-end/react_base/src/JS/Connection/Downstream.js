/**
 * API wrapping file for downstream communication.
 */

import ServerConnection from "./ServerConnection.js";
import Storage from "../Storage.js";

/**
 * Image mode constant.
 */
export const MODE = {
  automatic: "AUTO",
  manual: "MAN",
};


/**
 * Request mode. Either "auto" or "man"
 * @typedef {String} Mode
 */

/**
 * A map coordinate.
 * @typedef {Object} Coordinate
 *
 * @property {number} lat Latitude of coordinate
 * @property {number} lng Longitude of coordinate
 */

/**
 * A view of a map.
 * @typedef {Object} View
 *
 * @property {Coordinate} upLeft Upper left coordinate
 * @property {Coordinate} upRight Upper right coordinate
 * @property {Coordinate} downLeft Bottom left coordinate
 * @property {Coordinate} downRight Bottom right coordinate
 * @property {Coordinate} center Center coordinate
 */

/**
 * Callback function from API calls.
 *
 * @callback APICallback
 * @param {Object} JSON object of response
 */

/**
 * Make a connect call downstream.
 *
 * @param {APICallback} callback Optional callback function
 */
export function connect(callback = null) {
  ServerConnection.sendDownstream("init_connection", {}, callback);
}

/**
 * Make a check alive call downstream.
 *
 * @param {APICallback} callback Optional callback function
 */
export function checkAlive(callback = null) {
  ServerConnection.sendDownstream("check_alive", {}, callback);
}

/**
 * Make a disconnect call downstream.
 *
 * @param {APICallback} callback Optional callback function
 */
export function disconnect(callback = null) {
  ServerConnection.sendDownstream("quit", {}, callback);
}

/**
 * Make a define area call downstream.
 *
 * @param {Number} clientID Client ID for the connected client
 * @param {Coordinate[]} waypointsList Ordered array of waypoints.
 * @param {Coordinate[]} bounds List of top left and bottom right coordinates
 * @param {APICallback} callback Optional callback function
 */
export function setArea(clientID, waypointsList, bounds, callback = null) {
  let message = {
    fcn: "set_area",
    arg: {
      client_id: clientID,
      bounds: bounds,
      coordinates: waypointsList.map((coordinate) =>
        translateCoordinate(coordinate)
      ),
    },
  };

  ServerConnection.sendDownstream("set_area", message, callback);
}

/**
 * Make a request view call downstream.
 *
 * @param {View} view Current view
 * @param {APICallback} callback Optional callback function
 */
export function requestView(clientID, view, callback = null) {
  let message = {
    fcn: "request_view",
    arg: {
      client_id: clientID,
      coordinates: translateView(view),
    },
  };

  ServerConnection.sendDownstream("request_view", message, callback);
}

/**
 * Make a prioritized image request downstream.
 *
 * @param {View} view Current view
 * @param {APICallback} callback Optional callback function
 */
export function requestPriorityView(clientID, view, isUrgent, callback = null) {
  let message = {
    fcn: "request_priority_view",
    arg: {
      client_id: clientID,
      coordinates: translateView(view),
      isUrgent: isUrgent,
    },
  };

  ServerConnection.sendDownstream("request_priority_view", message, callback);
}

/**
 * Make a clear image queue request downstream.
 *
 * @param {APICallback} callback Optional callback function
 */
export function clearImageQueue(callback = null) {
  ServerConnection.sendDownstream("clear_que", {}, callback);
}

/**
 * Set image request mode.
 *
 * @param {Mode} mode New mode
 * @param {APICallback} callback Optional callback function
 */
export function setMode(mode, view = null, callback = null) {
  if (mode === MODE.automatic && !isValidView(view))
    throw new Error(
      "Invalid view. When requesting automatic mode a valid view must be given."
    );

  let message = {
    fcn: "set_mode",
    arg: {
      mode: mode,
    },
  };

  if (view !== null) {
    message = {
      ...message,
      arg: {
        ...message.arg,
        zoom: translateView(view),
      },
    };
  }

  ServerConnection.sendDownstream("set_mode", message, callback);
}

/**
 * Get information about drones.
 *
 * @param {APICallback} callback Optional callback function
 */
export function getInfo(callback = null) {
  ServerConnection.sendDownstream("get_info", {}, callback);
}

/**
 * Get information of queue ETA (seconds).
 *
 * @param {APICallback} callback Optional callback function
 */
export function getQueueETA(callback = null) {
  ServerConnection.sendDownstream("que_ETA", {}, callback);
}

/**
 * Check that the view is valid and translate the view to back-end API object format.
 *
 * @param {View} view View to be translated
 */
export function translateView(view) {
  if (!isValidView(view))
    throw new Error(
      'Invalid view. View must contain properties "upLeft", "upRight", "downReft", "downRight" and "center", each with a "lat" and "lng" property.'
    );

  return {
    up_left: translateCoordinate(view.upLeft),
    up_right: translateCoordinate(view.upRight),
    down_left: translateCoordinate(view.downLeft),
    down_right: translateCoordinate(view.downRight),
    center: translateCoordinate(view.center),
  };
}

/**
 * Check if the given coordinate is valid and translate the coordinate to back-end API object format.
 *
 * @param {Coordinate} coordinate Coordinate to be translated
 */
export function translateCoordinate(coordinate) {
  if (!isValidCoordinate(coordinate))
    throw new Error(
      'Invalid coordinate. Coordinate must contain properties "lat" and "lng".'
    );

  return {
    lat: coordinate.lat,
    long: coordinate.lng,
  };
}

/**
 * Check if given view is valid.
 *
 * @param {View} view View to be checked
 */
export function isValidView(view) {
  return (
    view.upLeft !== undefined &&
    view.upRight !== undefined &&
    view.downLeft !== undefined &&
    view.downRight !== undefined &&
    view.center !== undefined &&
    isValidCoordinate(view.upLeft) &&
    isValidCoordinate(view.upRight) &&
    isValidCoordinate(view.downLeft) &&
    isValidCoordinate(view.downRight)
  );
}

/**
 * Check if a given coordinate is valid.
 *
 * @param {Coordinate} coordinate Coordinate to be checked
 */
export function isValidCoordinate(coordinate) {
  return coordinate.lat !== undefined && coordinate.lng !== undefined;
}

/**
 * Second order function to wrap a callback function with boilerplate functionality for handling error and unknown responses. Callbacks wrapped with this function will only be called if call was successful (ack).
 *
 * @example
 * Downstream.connect(Downstream.callbackWrapper((reply) => {
 *     props.store.connectionToken(reply.arg.client_id);
 * }));
 *
 * @param {APICallback} callback Optional callback function to be wrapped
 */
export function callbackWrapper(callback = null) {
  return (reply) => {
    switch (reply.fcn) {
      case "ack":
        if (callback !== null && callback !== undefined) callback(reply);
        break;
      case "error":
        Storage.store.dispatch(
          Storage.messagesActions.addMessage(
            "error",
            "Error " + reply.fcn_name,
            reply.error_report
          )
        );
        break;
      default:
        throw new Error(
          "Received unexpected function '" + reply.fcn + "' in reply."
        );
    }
  };
}

const downstreamExports = {
  MODE,
  connect,
  checkAlive,
  disconnect,
  setArea,
  requestView,
  requestPriorityView,
  clearImageQueue,
  setMode,
  getInfo,
  getQueueETA,
  callbackWrapper,
};

export default downstreamExports;
