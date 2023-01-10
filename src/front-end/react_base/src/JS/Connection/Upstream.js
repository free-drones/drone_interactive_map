/**
 * API wrapping file for upstream communication.
 */

import ServerConnection from './ServerConnection.js';
import {store, recieveRequest} from '../Storage.js';

/**
 * Request type. Either "RGB" or "IR"
 * @typedef {String} Type
 */

/**
 * Handle new image notification.
 * 
 * @param {Type} type Image type.
 * @param {Boolean} prioritized If the image was proiritized or not.
 * @param {Int} imageID ID of the new image.
 */
export function newImage(type, prioritized, imageID) {
    if (prioritized) {
        store.dispatch(recieveRequest(imageID))
    }

    let data = {
        fcn : "ack",
        fcn_name : "new_pic"
    }

    ServerConnection.sendUpstream(data);
}

export default { newImage };