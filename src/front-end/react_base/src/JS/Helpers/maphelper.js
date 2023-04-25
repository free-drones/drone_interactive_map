/**
 * Utility functions for map.
 */

/**
 * Formats collection of bounds into a view object.
 */
export function boundsToView(bounds) {
  // latlng objects
  const nw = bounds.getNorthWest();
  const ne = bounds.getNorthEast();
  const sw = bounds.getSouthWest();
  const se = bounds.getSouthEast();
  const center = bounds.getCenter();

  // List of coordinate pairs to be stored by state.
  const view = {
    upLeft: {
      lat: nw.lat,
      lng: nw.lng,
    },
    upRight: {
      lat: ne.lat,
      lng: ne.lng,
    },
    downLeft: {
      lat: sw.lat,
      lng: sw.lng,
    },
    downRight: {
      lat: se.lat,
      lng: se.lng,
    },
    center: {
      lat: center.lat,
      lng: center.lng,
    },
  };

  return view;
}

/**
 * 
 * 
 * 
 *@param {any} waypoints Current list of waypoints
 *@param {any} newWaypoint  Waypoint to be added
 *@param {integer} removeWaypointIndex index of waypoint to be removed
 */
export function createRedLines(waypoints, newWaypoint = null, removeWaypointIndex = null) {
  let crossingLines = [];
  let newWaypoints = [];
  // Add new waypoint to list
  if (newWaypoint) {
    newWaypoints = [...waypoints, newWaypoint];
  }
  // Or remove it from old list
  else {
    newWaypoints = [...waypoints.slice(0, removeWaypointIndex), ...waypoints.slice(removeWaypointIndex + 1)];
  }

  // standard case
  for(let j = 0; j < newWaypoints.length - 1; j++){
    // Check if lines intersect
    const a = newWaypoints[j].lat;
    const b = newWaypoints[j].lng;
    const c = newWaypoints[j + 1].lat;
    const d = newWaypoints[j + 1].lng;

    for (let i = 0; i < newWaypoints.length - 1; i++) {
      const p = newWaypoints[i].lat;
      const q = newWaypoints[i].lng;

      const r = newWaypoints[i + 1].lat;
      const s = newWaypoints[i + 1].lng;

      if(hasIntersectingVectors(c, d, a, b, p, q, r, s) && (j != i)) {
        crossingLines.push([newWaypoints[i], newWaypoints[i + 1]]);
      }
    }
    // special case for when list loops around (line from last to first waypoint)
    const p = newWaypoints[newWaypoints.length - 1].lat;
    const q = newWaypoints[newWaypoints.length - 1].lng;
    const r = newWaypoints[0].lat;
    const s = newWaypoints[0].lng;

    if(hasIntersectingVectors(c, d, a, b, p, q, r, s)) {
      crossingLines.push([newWaypoints[newWaypoints.length - 1], newWaypoints[0]]);
    }
  }
  return crossingLines;
}

/**
 * Checks if adding a waypoint results in new crossing lines.
 *
 * @param {any} newWaypoint new waypoint that will be added.
 *
 * @returns true if the new waypoint lines have intersections, otherwise false.
 */
export function newWaypointLinesCrossing(newWaypoint, waypoints) {
  // vector 1: (c,d) -> (a,b) (neighbour 1, forward in list) intersects with (p,q) -> (r,s).
  // vector 2: (e,f) -> (a,b) (neighbour 2, backward in list) intersects with (p,q) -> (r,s).

  // No lines can cross if there are only 3 waypoints.
  if (waypoints.length < 3) {
    return false;
  }

  let crossing = false;

  const a = newWaypoint.lat;
  const b = newWaypoint.lng;

  const c = waypoints[0].lat;
  const d = waypoints[0].lng;

  const e = waypoints[waypoints.length - 1].lat;
  const f = waypoints[waypoints.length - 1].lng;

  // Check if new lines will intersect with old lines.
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
 * If vector (a,b) -> (c,d) intersects with vector (p,q) -> (r,s) then return true, otherwise false.
 *
 * a, b, c, d, p, q, r, s are integers
 */
function hasIntersectingVectors(a, b, c, d, p, q, r, s) {
  // det = determinant
  let det, length_1, length_2;
  det = (c - a) * (s - q) - (r - p) * (d - b);
  if (det === 0) {
    return false;
  }

  // length_1 & length_2 = lengths to intersecting point of vectors.
  length_1 = ((s - q) * (r - a) + (p - r) * (s - b)) / det;
  length_2 = ((b - d) * (r - a) + (c - a) * (s - b)) / det;

  // If intersecting point is farther away than original vectors' length, then lengths will not be between 0 and 1.
  return 0 < length_1 && length_1 < 1 && 0 < length_2 && length_2 < 1;
}



const mapHelperExports = {
  boundsToView,
  newWaypointLinesCrossing,
  createRedLines,
};

export default mapHelperExports;


