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
import { boundsToView, createRedLines } from "./Helpers/maphelper.js";
import { getDrones } from "./Connection/Downstream.js";
import { markedIcon, userPosIcon, pictureIndicatorIcon } from "./SvgIcons.js";

import Leaflet from "leaflet";
import PriorityPictureRequestInfo from "./Menu/PriorityPictureRequestInfo";

let hasLocationPanned = false;
let lastBoundUpdate = Date.now();

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
   * Clears timer when component is unmounted
   */
  componentWillUnmount() {
    // To avoid duplicate instances of getDronesTimer
    clearInterval(this.state.getDronesTimer);
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
    if (!map || !map._mapPane || Date.now() - lastBoundUpdate < 100) {
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
    if (this.props.allowDefine) {
      // Add new waypoint and check for crossing lines
      this.props.store.addAreaWaypoint(waypoint);
      this.updateCrossingLines(null, waypoint);
    } else {
      // Shows warning if placing waypoint would result in crossing lines
      this.props.store.setShowWarning(true);
    }
  }

  /**
   * Calculates and updates crossing lines. Shows warning message if lines cross.
   *
   * @param {integer} i Index of waypoint to be removed
   * @param {*} waypoint Waypoint to be added
   */
  updateCrossingLines(i = null, waypoint = null) {
    const newCrossingLines = createRedLines(
      this.props.store.areaWaypoints,
      waypoint,
      i
    );
    this.props.store.setCrossingLines(newCrossingLines);

    // Show error message if there are any crossing lines
    this.props.store.setShowWarning(newCrossingLines.length !== 0);
    return;
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
      // Remove waypoint and check for crossing lines
      this.props.store.removeAreaWaypoint(i);
      this.updateCrossingLines(i, null);
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
