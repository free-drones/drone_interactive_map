/**
 * Setup for connection to server.
 */

import io from "socket.io-client";
import * as Upstream from "./Upstream.js";
import {
  store,
  setUserPriority,
  areaWaypointActions,
  setMapBounds,
  setMapState,
} from "../Storage.js";

/**
 * Logging flag. For controlling logging of calls behaviour.
 */
const LOGGING = true;

/**
 * Back-end IP address.
 */
// const SERVER_IP = "pum2020.linkoping-ri.se";
const SERVER_IP = "localhost";

/**
 * Back-end port.
 */
const PORT = 8080;

/**
 * Response time out time in ms.
 */
const TIME_OUT_MS = 10000;

var socket;

/**
 * Initialize the server connection.
 *
 * @param {String} serverIP Server IP address to connect to. Default SERVER_IP.
 * @param {Int} port Downstream request port to connect to. Default PORT.
 * @param {String} namespace Optional namespace to connect to. Default "/"
 * @param {Object} socketOptions Optional socket options.
 */
export function initialize(
  serverIP = SERVER_IP,
  port = PORT,
  namespace = "",
  socketOptions = {}
) {
  var connectionString = "http://" + serverIP + ":" + port + namespace;

  // Set up socket
  socket = io(connectionString, socketOptions);
  socket.connect();
  console.log("Stream bound to " + connectionString);
  socket.on("notify", upstreamRequestEventHandler);
  socket.on("set_priority", userPriorityEventHandler);
}

export function disconnect() {
  if (socket != null) socket.disconnect();
}

/**
 * Message queue. Contains all unsent messages.
 */
var messageQueue = [];

/**
 * Handle a request from backend.
 *
 * @param {String} message Received message
 */
function upstreamRequestEventHandler(message) {
  switch (message.fcn) {
    case "new_pic":
      Upstream.newImage(message.prioritized, message.imageID);
      break;
    default:
      throw new Error("Unknown function type '" + message.fcn + "'.");
  }
}

/**
 * Handle a SET_PRIORITY request from backend.
 *
 * @param {String} message Received message
 */
function userPriorityEventHandler(message) {
  // If this user is not a high priority user lower userPriority and set the correct area defined by other user
  if (message.high_priority_client !== store.getState().clientID) {
    store.dispatch(setUserPriority(5));
    // Clears any waypoints set by this user
    store.dispatch(areaWaypointActions.clearAreaWaypoints());
    // Adds all waypoints set by high priority user
    for (const waypoint of message.coordinates) {
      store.dispatch(
        areaWaypointActions.addAreaWaypoint({
          lat: waypoint.lat,
          lng: waypoint.long,
        })
      );
    }
    store.dispatch(setMapBounds(message.bounds));
    store.dispatch(setMapState("Main"));
  }
}

/**
 * Queue a message to be sent downstream. This will happen immediately if no other messages are in the queue.
 *
 * @param {String} event Event type to emit
 * @param {Object} data JSON object to be sent
 * @param {Function} callback Optional callback function
 */
export function sendDownstream(event, data, callback = null) {
  messageQueue.push([event, data, callback]);
  if (messageQueue.length === 1) handleNextMessage();
}

/**
 * Send a message upstream. NOTE that this function is only called as a reply to a notification from back-end.
 *
 * @param {Object} data JSON object to be sent
 */
export function sendUpstream(data) {
  socket.emit("notify", data);
}

/**
 * Sent a message downstream.
 *
 * @param {String} data JSON object to be sent
 * @param {Function} callback Optional callback function
 */
function _sendDownstream(event, data, callback = null) {
  var responseTimeout = setTimeout(() => {
    callback = null;
    throw new Error("Response to '" + event + "' event timed out.");
  }, TIME_OUT_MS);

  socket.once(`${event}_response`, (reply) => {
    clearTimeout(responseTimeout);

    if (callback !== null && callback !== undefined) callback(reply);

    handleNextMessage();
  });

  if (LOGGING) {
    console.log(new Date(Date.now()) + ": " + event);
    console.log(data);
  }

  socket.emit(event, data);
}

/**
 * Handle next message in the message queue
 */
function handleNextMessage() {
  var mesBack = messageQueue.shift();

  if (mesBack !== null && mesBack !== undefined) _sendDownstream(...mesBack);
}

const serverConnectionExports = {
  initialize,
  disconnect,
  sendUpstream,
  sendDownstream,
};

export default serverConnectionExports;
