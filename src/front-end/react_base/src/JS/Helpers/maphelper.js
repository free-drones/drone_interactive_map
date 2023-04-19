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
 * Checks if adding a waypoint results in new crossing lines
 *
 * @param {any} waypoint that will be added
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
 * Checks if removing a waypoint results in new crossing lines
 *
 * @param {Integer} index of waypoint that will be removed.
 * 
 * Returns crossing line
 */
export function removedWaypointLinesCrossing(index, waypoints) {
  // vectors to be checked lat=x long=y
  // vector (a,b) -> (c,d) intersects with (p,q) -> (r,s)

  let crossing, tempCrossing, a, b, c, d;
  let newCrossingLine = [];

  if (waypoints.length - 1 < 3) {
    return newCrossingLine;
  }

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

      if (tempCrossing && (newCrossingLine.length === 0)) {
        newCrossingLine.push([waypoints[1], waypoints[waypoints.length - 1]])
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
      if (tempCrossing && (newCrossingLine.length === 0)) {
        newCrossingLine.push([waypoints[0], waypoints[index - 1]])
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
        // skip since this waypoint is about to be removed, and so will the connecting lines.
        continue;
      }
      if (i === waypoints.length) {
        const p = waypoints[i].lat;
        const q = waypoints[i].lng;

        const r = waypoints[0].lat;
        const s = waypoints[0].lng;

        tempCrossing = hasIntersectingVectors(a, b, c, d, p, q, r, s);
        crossing = crossing || tempCrossing;
        if (tempCrossing && (newCrossingLine.length === 0)) {
          newCrossingLine.push([waypoints[index + 1], waypoints[index - 1]])
        }

      } else {
        tempCrossing = vectorHelper(a, b, c, d, waypoints, i);
        crossing = crossing || tempCrossing;
        if (tempCrossing && (newCrossingLine.length === 0)) {
          newCrossingLine.push([waypoints[index + 1], waypoints[index - 1]])
        }
      }
    }
  }
  return newCrossingLine;
}

/**
 * Checks if red lines are still crossing. If not -> remove them.
 */

export function checkRedLinesCrossing(point1, point2, waypoints, index) {
  // vectors to be checked lat=x long=y
  // vector (a,b) -> (c,d) intersects with (p,q) -> (r,s)

  let crossing;
  let a = point1.lat;
  let b = point1.lng;
  let c = point2.lat;
  let d = point2.lng;

  for (let i = 0; i < waypoints.length - 1; i++) {
    // Don't check if red line overlaps with itself or lines that will be removed when waypoint at index is removed
    if ((point1 == waypoints[i] && point2 == waypoints[i + 1]) || (point1 == waypoints[i + 1] && point2 == waypoints[i]) 
    || (index == i) || (index == i + 1)) { 
      //console.log("Line overlapping with it self at index: ", i);
      continue;
    }
    crossing = crossing || vectorHelper(a, b, c, d, waypoints, i);
  }

  if ((point1 == waypoints[0] && point2 == waypoints[waypoints.length - 1]) ||
      (point1 == waypoints[waypoints.length - 1] && point2 == waypoints[0]) || 
      (index == 0) || (index == waypoints.length - 1)) {
        //console.log("INSIDE RETURN HAHAHAHAH");
         return crossing
  }
  
  let p = waypoints[waypoints.length - 1].lat;
  let q = waypoints[waypoints.length - 1].lng;
  let r = waypoints[0].lat;
  let s = waypoints[0].lng;

  console.log(" Waypoint 1: ", a, b, '\n',"Waypoint 2: ", c, d, '\n',"Waypoint 3: ", p, q, '\n', "Waypoint 4: ", r, s);
  console.log("======================================================================");
  
  crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
  return crossing
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
  checkRedLinesCrossing,
};


export default mapHelperExports;
