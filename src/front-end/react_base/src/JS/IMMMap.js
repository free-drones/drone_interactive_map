/**
 * Class file for map component.
 */

import React, {useState} from 'react';
import { MapContainer , TileLayer, Marker, Polygon, ImageOverlay, useMapEvents } from 'react-leaflet';
import "../CSS/Map.scss";
import { connect, areaWaypoints, zoomLevel, mapPosition, mapState, mapBounds, activePictures } from './Storage.js'
import { mapPositionActions, zoomLevelActions, areaWaypointActions, mapStateActions, showWarningActions } from './Storage.js'
import { viewify } from './Helpers/maphelper.js'

import Leaflet from 'leaflet';

// Room Icon pre-rendered + sizing style
const markedIcon = '<svg style="font-size: 2.25rem; width: 36px; height: 36px;" class="MuiSvgIcon-root" focusable="false" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"></path></svg>';

// Leaflet icon of pre-rendered Material Design icon
const marker = Leaflet.divIcon({className: "marker", iconAnchor: Leaflet.point(18, 34), html:markedIcon});


/**
 * ====================================================================================================
 *                                         Help functions
 * ====================================================================================================
 */

/**
 * Checks if there are waypoints having crossing connections when a new waypoint is added.
 * 
 * @param {any} waypoint that will be added and have it connections checked.
 * 
 * Returns true if waypoint lines cross
 */
function newWaypointLinesCrossing(waypoint, waypoints) {
    // vectors to be checked lat=y long=x
    // vector 1: (c,d) -> (a,b) (neighbour 1, forward in list) intersects with (p,q) -> (r,s)
    // vector 2: (e,f) -> (a,b) (neighbour 2, backward in list) intersects with (p,q) -> (r,s)

    if (waypoints.length < 3) {
        return false;
    }

    let crossing = false;

    const a = waypoint.lat;
    const b = waypoint.lng;

    const c = waypoints[0].lat; 
    const d = waypoints[0].lng;

    const e = waypoints[waypoints.length - 1].lat;
    const f = waypoints[waypoints.length - 1].lng;

    // Do the check for every line on the map.
    for (let i = 0; i < waypoints.length - 1; i++) {
        const p = waypoints[i].lat; 
        const q = waypoints[i].lng;

        const r = waypoints[i + 1].lat; 
        const s = waypoints[i + 1].lng;
        crossing = crossing || hasIntersectingVectors(c, d, a, b, p, q, r, s) || hasIntersectingVectors(e, f, a, b, p, q, r, s);
    };

    return crossing;
};

/**
 * Checks if any waypoints have crossing connections when waypoint of index is removed.
 * 
 * @param {Integer} index of waypoint that will be removed.
 * 
 * Returns true if waypoint lines cross
 */
function removedWaypointLinesCrossing(index, waypoints) {
    // vectors to be checked lat=y long=x
    // vector 1: (a,b) -> (c,d) intersects with (p,q) -> (r,s)

    if ((waypoints.length - 1) < 3) {
        return false;
    }

    let crossing, a, b, c, d;

    // Removing waypoints should only happen when (index == waypoints.length - 1) but this is more secure.
    if (index === 0) {
        a = waypoints[1].lat; 
        b = waypoints[1].lng;

        c = waypoints[waypoints.length - 1].lat; 
        d = waypoints[waypoints.length - 1].lng;

        // Do the check for every line on the map.
        for (let i = 1; i < waypoints.length - 1; i++) {
            const p = waypoints[i].lat; 
            const q = waypoints[i].lng;

            const r = waypoints[i + 1].lat; 
            const s = waypoints[i + 1].lng;
            crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
        };

    } else if (index === waypoints.length - 1) {
        a = waypoints[0].lat; 
        b = waypoints[0].lng;

        c = waypoints[index - 1].lat; 
        d = waypoints[index - 1].lng;

        // Do the check for every line on the map.
        for (let i = 0; i < waypoints.length - 2; i++) {
            const p = waypoints[i].lat; 
            const q = waypoints[i].lng;

            const r = waypoints[i + 1].lat; 
            const s = waypoints[i + 1].lng;
            crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
        };
        
    } else {
        a = waypoints[index + 1].lat; 
        b = waypoints[index + 1].lng;

        c = waypoints[index - 1].lat; 
        d = waypoints[index - 1].lng;

        // Do the check for every line on the map.
        for (let i = 0; i <= waypoints.length; i++) {
            if ((i === index) || (i + 1 === index)) {
                // skip this vector
            }
            if (i === waypoints.length) {
                const p = waypoints[i].lat; 
                const q = waypoints[i].lng;

                const r = waypoints[0].lat; 
                const s = waypoints[0].lng;
                crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
            } else {
                const p = waypoints[i].lat; 
                const q = waypoints[i].lng;

                const r = waypoints[i + 1].lat; 
                const s = waypoints[i + 1].lng;
                crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
            }
        };
    }

    return crossing;
};

/**
 * If vector (a,b) -> (c,d) intersects with vector (p,q) -> (r,s), return true. 
 */
function hasIntersectingVectors(a, b, c, d, p, q, r, s) {
    // det = determenant
    let det, gamma, lambda;
    det = (c - a) * (s - q) - (r - p) * (d - b);
    if (det === 0) {
        console.log("Det = 0");
        return false;
    }

    //gamma & lambda = lengths to intesecting point
    lambda = ((s - q) * (r - a) + (p - r) * (s - b)) / det;
    gamma = ((b - d) * (r - a) + (c - a) * (s - b)) / det;
    return (0 < lambda && lambda < 1) && (0 < gamma && gamma < 1);
};


/**
 * ====================================================================================================
 *                                       IMMMAP class
 * ====================================================================================================
 */


class IMMMap extends React.Component {

    /**
     * Pans and zooms to the selected area when it has been confirmed
     * @param {*} map 
     */
    fitBounds(map) {
        if (this.props.store.mapState === "Main") {
            let bounds = this.props.store.mapBounds;

            // Check that bounds has a value
            if (bounds) {
                map.fitBounds(bounds);
            }
        }
    }

    /**
     * Update the state with current viewport on every zoom and move.
     * @param {Object} parentProps reference to props of IMMMap component
     * @param {MapConstructor} map Reference to the MapContainer element
     */
    updateBounds(map) {
        const bounds = map.getBounds();
        const zoom = map.getZoom();
        // Make sure zoom level is not already set, ignore update if already set.
        if (this.props.store.zoomLevel === zoom) {
            return;
        }

        this.props.store.setZoomLevel(zoom);
        this.props.store.setMapPosition(viewify(bounds));
    }

    /**
     * Adds an area waypoint to the map
     * @param {*} e the click event containing click location
     */
    addAreaWaypoint(e) {
        const waypoint = {lat: e.latlng.lat, lng: e.latlng.lng};

        if (this.props.allowDefine && !newWaypointLinesCrossing(waypoint, this.props.store.areaWaypoints)) {
            this.props.store.setShowWarning(false);
            this.props.store.addAreaWaypoint(waypoint);
            console.log("false lel")
        } else{
            // Shows popup with crossing lines warning message
            this.props.store.setShowWarning(true);
            console.log("true sadge");
            console.log("allowDefine: ", this.props.allowDefine);
            console.log("lines crossing: ", waypoint);

        }
    }

    /**
     * Restructures the waypoint list so that the clicked markers waypoint is the first in the list and the waypoint that is added next is its neighbor.
     * @param {Integer} i 
     */
    markerClick(i) {
        this.props.store.setShowWarning(false);
        if (i !== this.props.store.areaWaypoints.length - 1) {
            // Restructure waypoints.
            var waypoints = this.props.store.areaWaypoints;
            var newWP = [...waypoints.slice(i + 1, waypoints.length), ...waypoints.slice(0, i + 1)];

            // Remove all waypoints
            this.props.store.clearAreaWaypoints();
            // Timeout could be replaced by other synchronization for better experience
            setTimeout(() => {
                // Add restructured waypoints
                newWP.forEach(wp => this.props.store.addAreaWaypoint(wp));
            }, 1);
        }
        else {
            // Marked node was clicked, remove it
            if(!removedWaypointLinesCrossing(i, this.props.store.areaWaypoints)) {
                this.props.store.removeAreaWaypoint(i);
            } else {
                // Shows popup with crossing lines warning message
                this.props.store.setShowWarning(true);
            }
        }
    }

    /**
     * Places all waypoints as markers on the map.
     */
    markerFactory() {
        const markers = this.props.store.areaWaypoints.map((pos, i) => 
            <Marker 
                position={pos}
                key={JSON.stringify(pos)}
                icon={marker}
                eventHandlers={{ click: () => this.markerClick(i) }}
            />
        );

        return(markers);
    }

    /**
     * Renders the map and markers.
     */
    render() {
        const tile_server_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

        const worldPolygon = [[90, -180], [90, 180], [-90, 180], [-90, -180]];

        function MapEventHandler(props) {
            const parent = props.parent; // parent is what is referred to as "this" outside of this function
            const map = useMapEvents({
              click: (e) => {
                parent.addAreaWaypoint(e)
                // map.locate()  // This finds the users current position via gps
              },
              layeradd: () => {
                parent.fitBounds(map)
              },
              zoom: () => {
                parent.updateBounds(map)
              },
              moveend: () => {
                parent.updateBounds(map)
              },

            //   locationfound: (location) => { // Called when user's gps location has been found
            //     console.log('location found:', location)
            //   },
              
            })
            return null
          }

        return(
            <MapContainer
                className="map"
                center={this.props.center}
                zoom={this.props.zoom}
                zoomControl={false}
                maxBounds={this.props.maxBounds}
                maxBoundsViscosity={0.5}
                minZoom={10}
            >
                <MapEventHandler parent={this} />
                <TileLayer maxNativeZoom={18} maxZoom={22}
                    attribution='&amp;copy <a href="http://osm.org/copyright">OpenStreetMap</a>     contributors'
                    url={tile_server_url}
                />

                {/*Draws the polygon of the defined area.*/}
                {this.props.allowDefine
                    ? <Polygon fill={false} positions={[this.props.store.areaWaypoints.map((coord) => [coord.lat, coord.lng])]} />
                    : ""
                }

                {/*Draws an overlay for the whole world except for defined area.*/}
                {!this.props.allowDefine && Object.keys(this.props.store.areaWaypoints).length > 0
                    ? <Polygon positions={[worldPolygon, this.props.store.areaWaypoints.map((coord) => [coord.lat, coord.lng])]} />
                    : ""
                }

                {/*Draws markers*/}
                {this.props.allowDefine
                    ? this.markerFactory()
                    : ""
                }

                {this.props.store.activePictures.map((img) => 
                    <ImageOverlay
                        url={img.url}
                        bounds={[[img.coordinates.upLeft.lat, img.coordinates.upLeft.lng], [img.coordinates.downRight.lat, img.coordinates.downRight.lng]]}
                        zIndex={img.prioritized ? 450 : 400}
                        key={img.imageID}
                    />
                )}         

            </MapContainer>
        );
    }
}

export default connect({ areaWaypoints, zoomLevel, mapPosition, mapState, mapBounds, activePictures }, {...areaWaypointActions, ...mapPositionActions, ...zoomLevelActions, ...mapStateActions, ...showWarningActions }) (IMMMap);
