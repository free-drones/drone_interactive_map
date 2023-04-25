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
  Popup,
} from "react-leaflet";
import "../CSS/Map.scss";
import {
  connect,
  pictureRequestQueue,
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
import { boundsToView } from "./Helpers/maphelper.js";
import { getDrones } from "./Connection/Downstream.js";
import { markedIcon, userPosIcon, pictureIndicatorIcon } from "./SvgIcons.js";

import Leaflet from "leaflet";
import PriorityPictureRequestInfo from "./Menu/PriorityPictureRequestInfo";

let hasLocationPanned = false;
let lastBoundUpdate = Date.now();

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
    crossing =
      crossing ||
      hasIntersectingVectors(c, d, a, b, p, q, r, s) ||
      hasIntersectingVectors(e, f, a, b, p, q, r, s);
  }

  return crossing;
}

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

  if (waypoints.length - 1 < 3) {
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
      crossing = crossing || vectorHelper(a, b, c, d, waypoints, i);
    }
  } else if (index === waypoints.length - 1) {
    a = waypoints[0].lat;
    b = waypoints[0].lng;

    c = waypoints[index - 1].lat;
    d = waypoints[index - 1].lng;

    // Do the check for every line on the map.
    for (let i = 0; i < waypoints.length - 2; i++) {
      crossing = crossing || vectorHelper(a, b, c, d, waypoints, i);
    }
  } else {
    a = waypoints[index + 1].lat;
    b = waypoints[index + 1].lng;

    c = waypoints[index - 1].lat;
    d = waypoints[index - 1].lng;

    // Do the check for every line on the map.
    for (let i = 0; i <= waypoints.length; i++) {
      if (i === index || i + 1 === index) {
        // skip this vector
      }
      if (i === waypoints.length) {
        const p = waypoints[i].lat;
        const q = waypoints[i].lng;

        const r = waypoints[0].lat;
        const s = waypoints[0].lng;
        crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
      } else {
        crossing = crossing || vectorHelper(a, b, c, d, waypoints, i);
      }
    }
  }

  return crossing;
}

/**
 * Configures points  (p, q) and (r, s) to be used in hasIntersectingVectors.
 *
 * a, b, c, d are integers making up points (a, b) and (c, d).
 *
 * @param {*} waypoints
 * @param {*} i index of what part of waypoint should be used
 */

function vectorHelper(a, b, c, d, waypoints, i) {
  const p = waypoints[i].lat;
  const q = waypoints[i].lng;

  const r = waypoints[i + 1].lat;
  const s = waypoints[i + 1].lng;
  return hasIntersectingVectors(a, b, c, d, p, q, r, s);
}

/**
 * If vector (a,b) -> (c,d) intersects with vector (p,q) -> (r,s) then return true.
 * a, b, c, d, p, q, r, s are integers
 */
function hasIntersectingVectors(a, b, c, d, p, q, r, s) {
  // det = determinant
  let det, length_1, length_2;
  det = (c - a) * (s - q) - (r - p) * (d - b);
  if (det === 0) {
    return false;
  }

  // length_2 & length_2 = lengths to intersecting point of vectors
  length_1 = ((s - q) * (r - a) + (p - r) * (s - b)) / det;
  length_2 = ((b - d) * (r - a) + (c - a) * (s - b)) / det;

  // if intersecting point is farther away than original vectors' length, then lengths will not be between 0 and 1.
  return 0 < length_1 && length_1 < 1 && 0 < length_2 && length_2 < 1;
}

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
      drones: null,
      oldDrones: null,
      getDronesTimer: null,
    };
  }

  /**
   * Pans and zooms to the selected area when it has been confirmed
   * @param {*} map
   */
  fitBounds(map) {
    if (this.props.store.mapState === "Main") {
      const bounds = Leaflet.latLngBounds(this.props.store.areaWaypoints);

      // Check that bounds has are valid value
      if (bounds && bounds.isValid()) {
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
    // Prevent the bounds from updating too frequently which can cause a crash
    if (Date.now() - lastBoundUpdate < 100) {
      return;
    }
    lastBoundUpdate = Date.now();
    const bounds = map.getBounds();
    const zoom = map.getZoom();
    this.props.store.setZoomLevel(zoom);
    this.props.store.setMapPosition(boundsToView(bounds));
  }

  /**
   * Adds an area waypoint to the map
   * @param {*} e the click event containing click location
   */
  addAreaWaypoint(e) {
    const waypoint = { lat: e.latlng.lat, lng: e.latlng.lng };

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
   * Drone position update, componentDidMount runs once on startup.
   */
  componentDidMount() {
    const updateDronesTimer = 1000;
    this.setState({
      getDronesTimer: setInterval(() => {
        getDrones((response) => {
          this.setState({ oldDrones: this.state.drones });
          this.setState({ drones: response.arg.drones });
        });
      }, updateDronesTimer),
    });
  }

  /**
   * Remove double timer from componentDidMount
   */
  componentWillUnmount() {
    clearInterval(this.state.getDronesTimer);
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
      // Marked node was clicked, remove it
      if (!removedWaypointLinesCrossing(i, this.props.store.areaWaypoints)) {
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
   * Places indicators where pictures have been requested.
   */
  pictureRequestIndicatorFactory() {
    const markers = this.props.store.pictureRequestQueue.map((data, i) => (
      <Marker
        position={[data.view.center.lat, data.view.center.lng]}
        key={`pictureRequestIndicator${i}`}
        icon={Leaflet.divIcon({
          className: data.isUrgent ? "urgent-picture" : "normal-picture",
          iconAnchor: Leaflet.point(13, 13),
          html: pictureIndicatorIcon,
        })}
      >
        <Popup>
          <PriorityPictureRequestInfo data={data} />
        </Popup>
      </Marker>
    ));

    return markers;
  }

  /**
   * Set Drone icon color based on current status
   *
   * @param {*} drone
   */
  droneColor(drone) {
    let status = drone.status;
    switch (status) {
      case "Auto":
        return "#000000"; // BLACK
      case "Manual":
        return "#FF0000"; // RED
      case "Photo":
        return "#0000FF"; // BLUE
      default:
        return "#A200FF"; // PURPLE
    }
  }

  /**
   * Calculates drone angle using linear trajectory based on two points
   *
   * @param {*} oldPoint
   * @param {*} newPoint
   */
  droneAngle(oldPoint, newPoint) {
    // Estimate latitude scale factor for each drone given its current position
    let latitudeScaleFactor = 1 / Math.cos((newPoint.lat * Math.PI) / 180);

    // Calculate angle in degrees
    const p1 = {
      x: oldPoint.lat * latitudeScaleFactor,
      y: oldPoint.lng,
    };

    const p2 = {
      x: newPoint.lat * latitudeScaleFactor,
      y: newPoint.lng,
    };

    const angleDeg = (Math.atan2(p2.y - p1.y, p2.x - p1.x) * 180) / Math.PI;
    return angleDeg;
  }

  /**
   * Places all drone icons on the map
   */
  droneFactory() {
    if (!this.state.oldDrones) {
      return [];
    }

    const drones = Object.entries(this.state.drones).map(([key, drone], i) => (
      <Marker
        position={[drone.location.lat, drone.location.lng]}
        key={`drone${i}`}
        icon={Leaflet.divIcon({
          className: "tmp",
          iconAnchor: Leaflet.point(
            this.props.store.config.droneIconPixelSize / 2,
            this.props.store.config.droneIconPixelSize / 2
          ),
          html: `<svg fill=${this.droneColor(drone)}
                    height="${this.props.store.config.droneIconPixelSize}px" 
                    width="${this.props.store.config.droneIconPixelSize}px" 
                    version="1.1" id="Layer_1" 
                    transform="rotate(${this.droneAngle(
                      this.state.oldDrones[key].location,
                      drone.location
                    )})"
                    xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
	                  viewBox="0 0 1792 1792" xml:space="preserve">
                    <path d="M187.8,1659L896,132.9L1604.2,1659L896,1285.5L187.8,1659z"/>
                    </svg> `,
        })}
      />
    ));
    return drones;
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
        move: () => {
          this.updateBounds(map);
        },
        moveend: () => {
          // This makes sure the bounds remain accurate, even with the 100ms rate limit for updating
          setTimeout(() => {
            this.updateBounds(map);
          }, 100);
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

        {/* Draws markers */}
        {this.props.allowDefine ? this.markerFactory() : ""}

        {/* Draws requested picture indicators */}
        {this.pictureRequestIndicatorFactory()}

        {/* Draws drone icons. */}
        {this.props.store.config.showDroneIcons && this.state.drones
          ? this.droneFactory()
          : ""}

        {
          /* Draws user position. */
          this.state.userPosition !== null ? (
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
          )
        }
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
    pictureRequestQueue,
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
