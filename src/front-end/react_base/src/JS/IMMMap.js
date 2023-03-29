/**
 * Class file for map component.
 */

import React from 'react';
import { MapContainer , TileLayer, Marker, Polygon, ImageOverlay, useMapEvents } from 'react-leaflet';
import "../CSS/Map.scss";
import { connect, areaWaypoints, zoomLevel, mapPosition, mapState, mapBounds, activePictures } from './Storage.js'
import { mapPositionActions, zoomLevelActions, areaWaypointActions, mapStateActions } from './Storage.js'
import { viewify } from './Helpers/maphelper.js'

import Leaflet from 'leaflet';

// Room Icon pre-rendered + sizing style
const markedIcon = '<svg style="font-size: 2.25rem; width: 36px; height: 36px;" class="MuiSvgIcon-root" focusable="false" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"></path></svg>';

// Leaflet icon of pre-rendered Material Design icon
const marker = Leaflet.divIcon({className: "marker", iconAnchor: Leaflet.point(18, 34), html:markedIcon});

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
     * @param {*} e the click event cotaining click location
     */
    addAreaWaypoint(e) {
        if (this.props.allowDefine) {
            this.props.store.addAreaWaypoint({lat: e.latlng.lat, lng: e.latlng.lng})
        }
    }

    /**
     * Restructures the waypoint list so that the clicked markers waypoint is the first in the list and the waypoint that is added next is its neighbor.
     * @param {Integer} i 
     */
    markerClick(i) {
        if (i !== this.props.store.areaWaypoints.length - 1) {
            // Restructure waypoints.
            var waypoints = this.props.store.areaWaypoints;
            var newWP = [...waypoints.slice(i + 1, waypoints.length), ...waypoints.slice(0, i + 1)];

            // Remove all waypoints
            this.props.store.clearAreaWaypoints();
            // Timeout could be replaced by other synchronization for better experience
            setTimeout(() => {
                // Add restructured waypoints
                newWP.forEach(wp => this.props.store.addAreaWaypoint(wp, true));
            }, 1);
        }
        else {
            // Marked node was clicked, remove it
            this.props.store.removeAreaWaypoint(i);
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

export default connect({ areaWaypoints, zoomLevel, mapPosition, mapState, mapBounds, activePictures }, {...areaWaypointActions, ...mapPositionActions, ...zoomLevelActions, ...mapStateActions }) (IMMMap);
