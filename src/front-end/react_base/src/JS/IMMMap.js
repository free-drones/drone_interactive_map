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
  crossingLines,
} from "./Storage.js";
import {
  mapPositionActions,
  zoomLevelActions,
  areaWaypointActions,
  mapStateActions,
  showWarningActions,
  crossingLineActions,
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
    this.setState({ paintRedLine: false });

    if (
      this.props.allowDefine &&
      !newWaypointLinesCrossing(waypoint, this.props.store.areaWaypoints)
    ) {
      // Add new waypoint and remove old red lines
      this.props.store.addAreaWaypoint(waypoint);
      const removedLines = this.removeRedLinesOnNewWaypoint();

      // Show error message if there are any crossing lines
      this.props.store.setShowWarning(
        this.props.store.crossingLines.length > removedLines.length
      );
    } else {
      // Shows popup with crossing lines warning
      this.props.store.setShowWarning(true);
    }
  }

  /**
   * Removes red lines that disappear when placing a new waypoint.
   *
   * @returns list of removed lines
   */
  removeRedLinesOnNewWaypoint() {
    let redLinesToBeRemoved = [];
    const firstWaypoint = this.props.store.areaWaypoints[0];
    const lastWaypoint =
      this.props.store.areaWaypoints[this.props.store.areaWaypoints.length - 1];

    // Two cases of lines that will be removed when adding new waypoint, used to compare with red lines
    const tempRemovedLine1 = [firstWaypoint, lastWaypoint];
    const tempRemovedLine2 = [lastWaypoint, firstWaypoint];

    // If removed line was part of crossing lines list, remove it.
    this.props.store.crossingLines.forEach((line, index) => {
      if (
        !(line === tempRemovedLine1 || line === tempRemovedLine2) &&
        (line[0] === firstWaypoint || line[1] === lastWaypoint) &&
        (line[0] === lastWaypoint || [line[1] === firstWaypoint])
      ) {
        redLinesToBeRemoved.push(index);
      }
    });

    // Remove red lines if placing a new waypoint removes intersection
    for (const i of redLinesToBeRemoved.reverse()) {
      this.props.store.removeCrossingLine(i);
    }
    return redLinesToBeRemoved;
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

      // Remove all waypoints.
      this.props.store.clearAreaWaypoints();

      // Add restructured waypoints.
      newWP.forEach((wp) => this.props.store.addAreaWaypoint(wp));
    } else {
      // Add new red lines from removing waypoint.
      const addedLine = this.addRedLines(i);
      // Remove red lines from removing waypoint.
      const removedLines = this.removeRedLines(i);
      // Show warning if there are any red lines left
      this.props.store.setShowWarning(
        this.props.store.crossingLines.length > removedLines.length || addedLine
      );
      // Marked node was clicked, remove it.
      this.props.store.removeAreaWaypoint(i);
    }
  }

  /**
   * Removing red lines that disappear when removing a waypoint.
   * @param {integer} i index of waypoint about to be removed.
   * @returns list of removed lines
   */
  removeRedLines(i) {
    let redLinesToBeRemoved = [];
    // Check if removed waypoint was one edge of a red line. If so, remove the red line.
    this.props.store.crossingLines.forEach((redLine, index) => {
      if (
        redLine[0] === this.props.store.areaWaypoints[i] ||
        redLine[1] === this.props.store.areaWaypoints[i] ||
        !checkRedLinesCrossing(
          redLine[0],
          redLine[1],
          this.props.store.areaWaypoints,
          i
        )
      ) {
        redLinesToBeRemoved.push(index);
      }
    });

    // Remove red lines if the one of its waypoints gets removed.
    for (const i of redLinesToBeRemoved.reverse()) {
      this.props.store.removeCrossingLine(i);
    }
    return redLinesToBeRemoved;
  }

  /**
   * Add new red lines that appear when removing a waypoint.
   *
   * @param {integer} i index of waypoint about to be removed.
   * @returns true if a line has been removed
   */
  addRedLines(i) {
    // If removing waypoint results in crossing lines, paint it red.
    let newCrossingLine = removedWaypointLinesCrossing(
      i,
      this.props.store.areaWaypoints
    );
    let lineAdded = false;
    // Adds red line that is crossing lines.
    if (
      newCrossingLine &&
      !this.props.store.crossingLines.includes(newCrossingLine)
    ) {
      this.props.store.addCrossingLine(newCrossingLine);
      lineAdded = true;
    }
    return lineAdded;
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
        {this.props.allowDefine &&
        this.props.store.areaWaypoints.length !== 0 &&
        this.props.store.crossingLines ? (
          <Polyline
            pathOptions={{ color: "red" }}
            positions={[
              this.props.store.crossingLines.map((waypointPair) => [
                [waypointPair[0].lat, waypointPair[0].lng],
                [waypointPair[1].lat, waypointPair[1].lng],
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
    crossingLines,
  },
  {
    ...areaWaypointActions,
    ...mapPositionActions,
    ...zoomLevelActions,
    ...mapStateActions,
    ...showWarningActions,
    ...crossingLineActions,
  }
)(IMMMap);
