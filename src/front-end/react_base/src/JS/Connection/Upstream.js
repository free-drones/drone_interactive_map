/**
 * API wrapping file for upstream communication.
 */

import ServerConnection from "./ServerConnection.js";
import { store, receivePictureRequest } from "../Storage.js";

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

const upstreamExports = { newImage };

export default upstreamExports;
