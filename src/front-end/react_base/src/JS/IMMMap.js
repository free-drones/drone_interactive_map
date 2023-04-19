/**
 * Class file for map component.
 */

import React from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Polygon,
  ImageOverlay,
  useMapEvents,
  ScaleControl,
  Polyline,
} from "react-leaflet";
import "../CSS/Map.scss";
import {
  connect,
  config,
  areaWaypoints,
  zoomLevel,
  mapPosition,
  mapState,
  mapBounds,
  activePictures,
} from "./Storage.js";
import {
  mapPositionActions,
  zoomLevelActions,
  areaWaypointActions,
  mapStateActions,
  showWarningActions,
} from "./Storage.js";
import { 
  boundsToView,
  newWaypointLinesCrossing, 
  removedWaypointLinesCrossing,
  checkRedLinesCrossing,
} from "./Helpers/maphelper.js";

import Leaflet from "leaflet";

// Room Icon pre-rendered + sizing style
const markedIcon =
  '<svg style="font-size: 2.25rem; width: 36px; height: 36px;" class="MuiSvgIcon-root" focusable="false" viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"></path></svg>';
const userPosIcon =
  '<svg class="svg-icon" style="width: 22px;height: 22px;vertical-align: middle;fill: currentColor;overflow: hidden;" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg"><path d="M512 512m-442.7 0a442.7 442.7 0 1 0 885.4 0 442.7 442.7 0 1 0-885.4 0Z" fill="#9BBFFF" /><path d="M512 512m-263 0a263 263 0 1 0 526 0 263 263 0 1 0-526 0Z" fill="#377FFC" /></svg>';

let hasLocationPanned = false;


/**
 * ====================================================================================================
 *                                       IMMMAP class
 * ====================================================================================================
 */

class IMMMap extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      userPosition: null,
      crossingLines: [],
     };
}

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
    this.props.store.setMapPosition(boundsToView(bounds));
  }

  /**
   * Adds an area waypoint to the map
   * @param {*} e the click event containing click location
   */
  addAreaWaypoint(e) {
    const waypoint = { lat: e.latlng.lat, lng: e.latlng.lng };
    this.setState({ paintRedLine: false});

    if (
      this.props.allowDefine &&
      !newWaypointLinesCrossing(waypoint, this.props.store.areaWaypoints)
    ) {
      this.props.store.setShowWarning(false);
      this.props.store.addAreaWaypoint(waypoint);
    } else {
      // Shows popup with crossing lines warning message
      this.props.store.setShowWarning(true);
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
      var newWP = [
        ...waypoints.slice(i + 1, waypoints.length),
        ...waypoints.slice(0, i + 1),
      ];

      // Remove all waypoints
      this.props.store.clearAreaWaypoints();
      // Add restructured waypoints
      newWP.forEach((wp) => this.props.store.addAreaWaypoint(wp));
    } else {
      // If removing node results in crossing lines, paint it red
      let newCrossingLines = removedWaypointLinesCrossing(i, this.props.store.areaWaypoints);
      let pointsToBeRemoved = [];


      // Adds new red line that is crossing lines
      newCrossingLines.map((wp) => {
        if (!(this.state.crossingLines.includes(wp))){
          this.state.crossingLines.push(wp);
        }
      })

      // Check if removed waypoint was one edge of a line. If so, remove the line. 
      this.state.crossingLines.map((redLine, index) => {
        if (redLine[0] == this.props.store.areaWaypoints[i] || redLine[1] == this.props.store.areaWaypoints[i] || (!checkRedLinesCrossing(redLine[0], redLine[1], this.props.store.areaWaypoints, i))) {
          pointsToBeRemoved.push(index);
        } 
      })


      console.log("PRINTING CROSSING LINE ", this.state.crossingLines);
      console.log("PRINTING NEW CROSSING LINE ", newCrossingLines);
      console.log("PRINTING INDEX LIST ", pointsToBeRemoved);
      // Remove red lines if the one of its waypoints gets removed
      for (const i of pointsToBeRemoved.reverse()) { 
        console.log(" removed point: ", i)
        this.state.crossingLines.splice(i, 1); 
      }   

      /**
       * TODO :
       * for each crossing line, check if it still crosses any of the other lines. if not -> remove it from crossing line list.
       * 
       * (crossingLines.map --> test all wp with almost the same function as removedWaypointLinesCrossing. 
       *  Check both vector wp[0] -> wp[1] if it crosses another line, if no then remove wp from crossingLines.)
       * */ 

      

      /**
       * 
       * TODO: 
       * FIX THIS TO ANOTHER WARNING MESSAGE::
       * 
       * this.props.store.setShowWarning(true);
       * */ 
      
      // Marked node was clicked, remove it
      this.props.store.removeAreaWaypoint(i);

      this.state.crossingLines.map((redLine, index) => {
        if (!checkRedLinesCrossing(redLine[0], redLine[1], this.props.store.areaWaypoints)) {
          pointsToBeRemoved.push(index);
        } 
      })
      
      }
    }

  /**
   * Places all waypoints as markers on the map.
   */
  markerFactory() {
    const markers = this.props.store.areaWaypoints.map((pos, i) => (
      <Marker
        position={pos}
        key={`marker${i}`}
        icon={Leaflet.divIcon({
          className:
            (i === this.props.store.areaWaypoints.length - 1
              ? "last-marker" // If it is the last marker add special styling
              : i === 0
              ? "first-marker" // If it is the first marker add special styling
              : "") + " marker", // Always use the base marker styling
          iconAnchor: Leaflet.point(18, 34),
          html: markedIcon,
        })}
        eventHandlers={{ click: () => this.markerClick(i) }}
      />
    ));

    return markers;
  }

  /**
   * Renders the map and markers.
   */
  render() {
    const tile_server_url =
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

    const worldPolygon = [
      [90, -180],
      [90, 180],
      [-90, 180],
      [-90, -180],
    ];

    const MapEventHandler = () => {
      const map = useMapEvents({
        click: (e) => {
          this.addAreaWaypoint(e);
        },
        zoomlevelschange: () => {
          // Gets called on load, so use it as a replacement for load
          this.fitBounds(map);
          map.locate();
        },
        zoom: () => {
          this.updateBounds(map);
        },
        moveend: () => {
          this.updateBounds(map);
        },
        locationfound: (location) => {
          // Called when user's gps location has been found
          if (!hasLocationPanned) {
            // Makes sure only to pan to the user's location once
            hasLocationPanned = true;
            map.panTo(location.latlng);
            // Keeps the user's location up to date
            setInterval(() => {
              map.locate();
            }, 10000);
          }
          this.setState({ userPosition: location.latlng });
          // Shows the button for centering on the user and makes clicking it center on the user
          if (this.props.centerButton) {
            this.props.centerButton.current.addEventListener("click", () =>
              map.flyTo(this.state.userPosition)
            );
            this.props.centerButton.current.style.visibility = "visible";
          }
        },
      });
      return null;
    };

    return (
      <MapContainer
        className="map"
        center={this.props.center}
        zoom={this.props.zoom}
        zoomControl={false}
        maxBounds={this.props.maxBounds}
        maxBoundsViscosity={0.5}
        minZoom={10}
        attributionControl={this.props.store.mapState === "Main"} // Only shows the attribution in Main, since it is covered in StartUp
      >
        <MapEventHandler />
        <ScaleControl imperial={false} position="bottomright" />
        <TileLayer
          maxNativeZoom={18}
          maxZoom={22}
          attribution='&amp;copy <a href="http://osm.org/copyright">OpenStreetMap</a>     contributors'
          url={tile_server_url}
        />

        {/*Draws the polygon of the defined area.*/}
        {this.props.allowDefine ? (
          <Polygon
            fill={false}
            positions={[
              this.props.store.areaWaypoints.map((coord) => [
                coord.lat,
                coord.lng,
              ]),
            ]}
          />
        ) : (
          ""
        )}

        {/* Paint crossing lines red.*/}
        {(this.props.allowDefine && 
        this.props.store.areaWaypoints.length != 0 &&
        this.state.crossingLines
        ) ? (
          <Polyline
            pathOptions = {{color: 'red'}}
            positions={[
              this.state.crossingLines.map((waypointPair) => [
                [waypointPair[0].lat, waypointPair[0].lng],
                [waypointPair[1].lat, waypointPair[1].lng]
              ]),
            ]}
          />
        ) : (
          ""
        )}

        {/*Draws an overlay for the whole world except for defined area.*/}
        {!this.props.allowDefine &&
        Object.keys(this.props.store.areaWaypoints).length > 0 ? (
          <Polygon
            positions={[
              worldPolygon,
              this.props.store.areaWaypoints.map((coord) => [
                coord.lat,
                coord.lng,
              ]),
            ]}
          />
        ) : (
          ""
        )}

        {/*Draws markers*/}
        {this.props.allowDefine ? this.markerFactory() : ""}

        {/* This marker is only here to show the effects of the drone icon configs until the actual drone icons are added */}
        {this.props.store.config.showDroneIcons ? (
          <Marker
            position={[59.815636, 17.649551]}
            icon={Leaflet.divIcon({
              className: "tmp",
              iconAnchor: Leaflet.point(
                this.props.store.config.droneIconPixelSize / 2,
                this.props.store.config.droneIconPixelSize / 2
              ),
              html: `<svg fill="#000000" height="${this.props.store.config.droneIconPixelSize}px" width="${this.props.store.config.droneIconPixelSize}px" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1792 1792" xml:space="preserve"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M103,703.4L1683,125L1104.6,1705L867.9,940.1L103,703.4z"></path></g></svg>`,
            })}
          />
        ) : (
          ""
        )}
        {this.state.userPosition !== null ? (
          <Marker
            position={this.state.userPosition}
            icon={Leaflet.divIcon({
              className: "userIcon",
              iconAnchor: Leaflet.point(11, 11),
              html: userPosIcon,
            })}
          />
        ) : (
          ""
        )}
        {this.props.store.activePictures.map((img) => (
          <ImageOverlay
            url={img.url}
            bounds={[
              [img.coordinates.upLeft.lat, img.coordinates.upLeft.lng],
              [img.coordinates.downRight.lat, img.coordinates.downRight.lng],
            ]}
            zIndex={img.prioritized ? 450 : 400}
            key={img.imageID}
          />
        ))}
      </MapContainer>
    );
  }
}

export default connect(
  {
    config,
    areaWaypoints,
    zoomLevel,
    mapPosition,
    mapState,
    mapBounds,
    activePictures,
  },
  {
    ...areaWaypointActions,
    ...mapPositionActions,
    ...zoomLevelActions,
    ...mapStateActions,
    ...showWarningActions,
  }
)(IMMMap);
