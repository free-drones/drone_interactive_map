/**
 * API wrapping file for upstream communication.
 */

import ServerConnection from "./ServerConnection.js";
import {
  store,
  receivePictureRequest,
  setDrones,
  setOldDrones,
} from "../Storage.js";

/**
 * Handle new image notification.
 *
 * @param {Boolean} prioritized If the image was prioritized or not.
 * @param {Int} imageID ID of the new image.
 */
export function newImage(prioritized, imageID) {
  if (prioritized) {
    store.dispatch(receivePictureRequest(imageID));
  }

  let data = {
    fcn: "ack",
    fcn_name: "new_pic",
  };

  ServerConnection.sendUpstream(data);
}

/**
 * Handle updated drones notification.
 *
 * @param {Any} updatedDrones Updated list of all information for every drone.
 */
export function newDrones(updatedDrones) {
  // Update old drones
  if (store.getState().drones && store.getState().drones !== updatedDrones) {
    store.dispatch(setOldDrones(store.getState().drones));
  }

  // Update all drones
  if (updatedDrones) {
    store.dispatch(setDrones(updatedDrones));
  }

  let data = {
    fcn: "ack",
    fcn_name: "new_drones",
  };

  ServerConnection.sendUpstream(data);
}

const upstreamExports = { newImage, newDrones };

export default upstreamExports;
