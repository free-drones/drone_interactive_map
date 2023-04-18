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
 * Checks if there are waypoints having crossing connections when a new waypoint is added.
 *
 * @param {any} waypoint that will be added and have it connections checked.
 *
 * Returns true if waypoint lines cross
 */
export function newWaypointLinesCrossing(waypoint, waypoints) {
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
 * Returns list of all crossing lines
 */
export function removedWaypointLinesCrossing(index, waypoints) {
  // vectors to be checked lat=y long=x
  // vector 1: (a,b) -> (c,d) intersects with (p,q) -> (r,s)

  
  if (waypoints.length - 1 < 3) {
    return false;
  }

  let crossing, tempCrossing, a, b, c, d;
  let crossingWaypointList = [];

  // Removing waypoints should only happen when (index == waypoints.length - 1) but this is more secure.
  if (index === 0) {
    a = waypoints[1].lat;
    b = waypoints[1].lng;

    c = waypoints[waypoints.length - 1].lat;
    d = waypoints[waypoints.length - 1].lng;

    // Do the check for every line on the map.
    for (let i = 1; i < waypoints.length - 1; i++) {
      tempCrossing = vectorHelper(a, b, c, d, waypoints, i);
      crossing = crossing || tempCrossing;

      if (tempCrossing) {
        crossingWaypointList.push([waypoints[1], waypoints[waypoints.length - 1]])
      }
    }
  } else if (index === waypoints.length - 1) {
    a = waypoints[0].lat;
    b = waypoints[0].lng;

    c = waypoints[index - 1].lat;
    d = waypoints[index - 1].lng;

    // Do the check for every line on the map.
    for (let i = 0; i < waypoints.length - 2; i++) {
      tempCrossing = vectorHelper(a, b, c, d, waypoints, i);
      crossing = crossing || tempCrossing;
      if (tempCrossing) {
        crossingWaypointList.push([waypoints[0], waypoints[index - 1]])
      }
  
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

        tempCrossing = hasIntersectingVectors(a, b, c, d, p, q, r, s);
        crossing = crossing || tempCrossing;
        if (tempCrossing) {
          crossingWaypointList.push([waypoints[index + 1], waypoints[index - 1]])
        }

      } else {
        tempCrossing = vectorHelper(a, b, c, d, waypoints, i);
        crossing = crossing || tempCrossing;
        if (tempCrossing) {
          crossingWaypointList.push([waypoints[index + 1], waypoints[index - 1]])
        }
      }
    }
  }
  return crossingWaypointList;
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



const mapHelperExports = {
  boundsToView, 
  newWaypointLinesCrossing, 
  removedWaypointLinesCrossing,
};


export default mapHelperExports;
