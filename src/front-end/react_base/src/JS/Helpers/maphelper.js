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
 * Checks all lines for intersections with each other.
 * Handles both new and removed waypoints based on input parameters.
 *
 *@param {any} waypoints Current list of waypoints
 *@param {any} newWaypoint  Waypoint to be added
 *@param {integer} removeWaypointIndex index of waypoint to be removed
 *
 *@returns List of all crossing lines
 */
export function createRedLines(
  waypoints,
  newWaypoint = null,
  removeWaypointIndex = null
) {
  let crossingLines = [];
  let newWaypoints = [];

  /* Creates a new waypoint list based on if a waypoint should be added or removed. */
  if (newWaypoint) {
    // Add new waypoint to list
    newWaypoints = [...waypoints, newWaypoint];
  } else if (removeWaypointIndex) {
    // Remove waypoint from old list
    newWaypoints = [
      ...waypoints.slice(0, removeWaypointIndex),
      ...waypoints.slice(removeWaypointIndex + 1),
    ];
  } else {
    // No parameters were passed when calling function
    return crossingLines;
  }

  // Standard case
  // Checks if vector (c,d) -> (a,b) intersects with vector (p,q) -> (r,s).
  for (let j = 0; j < newWaypoints.length - 1; j++) {
    // Creation of first line
    const a = newWaypoints[j].lat;
    const b = newWaypoints[j].lng;
    const c = newWaypoints[j + 1].lat;
    const d = newWaypoints[j + 1].lng;

    for (let i = 0; i < newWaypoints.length - 1; i++) {
      // Creation of second line
      const p = newWaypoints[i].lat;
      const q = newWaypoints[i].lng;

      const r = newWaypoints[i + 1].lat;
      const s = newWaypoints[i + 1].lng;

      // Check if lines intersect
      if (hasIntersectingVectors(c, d, a, b, p, q, r, s) && j !== i) {
        crossingLines.push([newWaypoints[i], newWaypoints[i + 1]]);
      }
    }
    // Special case when list loops around (line between last and first waypoint)
    const p = newWaypoints[newWaypoints.length - 1].lat;
    const q = newWaypoints[newWaypoints.length - 1].lng;
    const r = newWaypoints[0].lat;
    const s = newWaypoints[0].lng;

    // Check if lines intersect
    if (hasIntersectingVectors(c, d, a, b, p, q, r, s)) {
      crossingLines.push([newWaypoints[j], newWaypoints[j + 1]]);
      crossingLines.push([
        newWaypoints[newWaypoints.length - 1],
        newWaypoints[0],
      ]);
    }
  }

  return crossingLines;
}

/**
 * If vector 1: (a,b) -> (c,d) intersects with vector 2: (p,q) -> (r,s) then return true, otherwise false.
 *
 * a, b, c, d, p, q, r, s are integers
 */
function hasIntersectingVectors(a, b, c, d, p, q, r, s) {
  // det = determinant
  let det, length_1, length_2;
  det = (c - a) * (s - q) - (r - p) * (d - b);

  // Lines are parallel and will never intersect
  if (det === 0) {
    return false;
  }

  // Finds a point where the two vectors intersect.
  // Length_1 and length_2 are the distances to the intersecting point as a percentage of the vectors' original length.
  length_1 = ((s - q) * (r - a) + (p - r) * (s - b)) / det;
  length_2 = ((b - d) * (r - a) + (c - a) * (s - b)) / det;

  // A value between 1 and 0 means that the intersecting point is on the original vectors length.
  // If intersecting point is farther away than original vectors' length, then vectors do not cross.
  return 0 < length_1 && length_1 < 1 && 0 < length_2 && length_2 < 1;
}

export function isPointInsidePolygon(point, polygonMarkers) {
  let inside = false;
  const x = point.lat;
  const y = point.lng;
  // Uses ray casting algorithm which projects a ray from the point and if the ray crosses
  // the marker lines an odd amount of times, the point is inside the polygon
  // i iterates from 0 to the end
  // j starts from the last marker and then follows one step behind i
  // e.g. i => 0, 1, 2, 3 and j => 3, 0, 1, 2
  for (
    let i = 0, j = polygonMarkers.length - 1;
    i < polygonMarkers.length;
    j = i++
  ) {
    const xi = polygonMarkers[i].lat;
    const yi = polygonMarkers[i].lng;
    const xj = polygonMarkers[j].lat;
    const yj = polygonMarkers[j].lng;

    const intersect =
      ((yi > y && yj <= y) || (yi <= y && yj > y)) &&
      x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) {
      // inside is true if it has been flipped an odd amount of times
      inside = !inside;
    }
  }

  return inside;
}

const mapHelperExports = {
  boundsToView,
  createRedLines,
  isPointInsidePolygon,
};

export default mapHelperExports;
