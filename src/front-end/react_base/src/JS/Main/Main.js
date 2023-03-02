/*
*  Main file.
*  Loads all components through Main().
*/

import React from 'react';
import IMMMap from "../IMMMap.js"
import CameraButton from './CameraButton.js';
import { Navigate } from "react-router-dom";

import { connect, clientID, mapPosition, mapPositionActions, requestQueue, requestQueueActions, areaWaypoints, areaWaypointActions, mapBounds, zoomLevel, mapState, mapStateActions, sensor, mode, activePictures, activePicturesActions } from "../Storage.js";

import SettingsDrawer from '../Menu/SettingsDrawer.js';
import StatusDrawer from '../Menu/StatusDrawer.js';

import { requestView, requestPriorityView, callbackWrapper } from '../Connection/Downstream.js';

/**
 * View request timer interval in ms.
 */
const REQUEST_VIEW_TIMER = 2000;

class Main extends React.Component {
    constructor(props) {
        super(props)
        this.cameraClickHandler = this.cameraClickHandler.bind(this);
    }

    /**
     * On click event for camera button.
     */
    cameraClickHandler() {
        requestPriorityView(this.props.store.clientID, this.props.store.mapPosition, this.props.store.sensor, callbackWrapper((response) => {
            this.props.store.addRequest(response.arg.force_que_id);
        }));
    }

    /**
     * Function run on mount, handles setup.
     */
    componentDidMount() {
        this.requestViewInterval = setInterval(() => {
            requestView(this.props.store.clientID, this.props.store.mapPosition, this.props.store.sensor, callbackWrapper((response) => {
                // Get IDs of currently active pictures.
                const currentImageIDs = this.props.store.activePictures.map((item) => item.imageID);

                for (let image of response.arg.image_data) {

                    // If the image is not already in active pictures, add it.
                    if (!currentImageIDs.includes(image.image_id)) {

                        // Translate between back-end and front-end notation.
                        // Add to storage.
                        this.props.store.addActivePicture({
                            type: image.type,
                            prioritized: image.prioritized,
                            imageID: image.image_id,
                            url: image.url,
                            timeTaken: image.time_taken,
                            coordinates: {
                                upLeft: {
                                    lat: image.coordinates.up_left.lat,
                                    lng: image.coordinates.up_left.long
                                },
                                upRight: {
                                    lat: image.coordinates.up_right.lat,
                                    lng: image.coordinates.up_right.long
                                },
                                downLeft: {
                                    lat: image.coordinates.down_left.lat,
                                    lng: image.coordinates.down_left.long
                                },
                                downRight: {
                                    lat: image.coordinates.down_right.lat,
                                    lng: image.coordinates.down_right.long
                                },
                                center: {
                                    lat: image.coordinates.center.lat,
                                    lng: image.coordinates.center.long
                                }
                            }
                        });
                    }
                }

                // Get IDs of the new active images 
                const newImageIDs = response.arg.image_data.map((item) => item.image_id)

                // Get IDs of the images that will be removed form the current active images.
                const removedImageIDs = currentImageIDs.filter((item) => !newImageIDs.includes(item))

                // Get the indices of the images that will be removed from the current active images.
                const removedIndices = this.props.store.activePictures.map((item, index) => [index, item.imageID]).reduce((acc, item) => removedImageIDs.includes(item[1]) ? [...acc, item[0]] : acc, [])

                // Remove images that are no longer active.
                // Reverse indices list to prevent skipping of images when removing a lower index first.
                for (let index of removedIndices.reverse()) {
                    this.props.store.removeActivePicture(index);
                }
            }));
        }, REQUEST_VIEW_TIMER);
    }

    componentWillUnmount() {
        clearInterval(this.requestViewInterval);
    }

    /**
     * Checks if area of interest is properly defined.
     */
    areaIsInvalid() {
        var invalid = false;

        if (this.props.store.areaWaypoints.length < 3) {
            invalid = true;
        }

        if (this.props.store.mapBounds == null) {
            invalid = true;
        }

        //Prepare for reroute to StartUp if defined area is properly defined.
        if (invalid === true) {
            this.props.store.setMapState("StartUp");
        }

        return invalid;
    }

    render() {
        return (
            <div>
                {this.areaIsInvalid() ? <Navigate to="/StartUp" replace={true} /> : <div />}

                <SettingsDrawer />
                <StatusDrawer />
                <IMMMap key={this.props.store.mapBounds} center={this.props.store.mapPosition.center} zoom={this.props.store.zoomLevel} maxBounds={this.props.store.mapBounds} allowDefine={false} />
                <CameraButton clickHandler={this.cameraClickHandler} />
            </div>
        );
    }
}


export default connect({ clientID, mapPosition, requestQueue, areaWaypoints, mapBounds, zoomLevel, mapState, mode, sensor, activePictures }, { ...mapPositionActions, ...requestQueueActions, ...areaWaypointActions, ...mapStateActions, ...activePicturesActions })(Main)
