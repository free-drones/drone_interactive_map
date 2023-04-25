


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
  //props.store.setCrossingLines(crossingLines);
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
* 
* Removes red lines that disappear when placing a new waypoint. 
*
* @returns list of removed lines
*/
export function removeRedLinesOnNewWaypoint() {
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
  for (const i of redLinesToBeRemoved) {
    this.props.store.removeCrossingLine(i);
  }
  return redLinesToBeRemoved;
}

/**
 * Checks if removing a waypoint results in new crossing lines.
 *
 * @param {Integer} index of waypoint that will be removed.
 * @param {list} waypoints list of current waypoints on the map.
 * @returns waypoints for crossing line if there is one, otherwise null.
 */
export function removedWaypointLinesCrossing(index, waypoints) {
  // vector (a,b) -> (c,d) intersects with (p,q) -> (r,s).

  let a, b, c, d;
  let newCrossingLine = null;

  // No lines can cross if there are only 3 waypoints.
  if (waypoints.length <= 3) {
    return newCrossingLine;
  }

  /*
   Removing waypoints should only happen when (index === waypoints.length - 1) but this is more secure.

   There are 3 cases: index is the first element of the waypoint list, 
   index is the last element of the waypoint list or index is in the middle of the waypoint list.
  */

  // Case 1: index is first element in waypoints.
  if (index === 0) {
    a = waypoints[1].lat;
    b = waypoints[1].lng;

    c = waypoints[waypoints.length - 1].lat;
    d = waypoints[waypoints.length - 1].lng;

    // Do the check for every line on the map.
    for (let i = 1; i < waypoints.length - 1; i++) {
      // If we find a crossing line, return it.
      if (vectorHelper(a, b, c, d, waypoints, i)) {
        newCrossingLine = [waypoints[1], waypoints[waypoints.length - 1]];
        return newCrossingLine;
      }
    }

    // Case 2: index is last element in waypoints.
  } else if (index === waypoints.length - 1) {
    a = waypoints[0].lat;
    b = waypoints[0].lng;

    c = waypoints[index - 1].lat;
    d = waypoints[index - 1].lng;

    // Do the check for every line on the map.
    for (let i = 0; i < waypoints.length - 2; i++) {
      if (vectorHelper(a, b, c, d, waypoints, i)) {
        newCrossingLine = [waypoints[0], waypoints[index - 1]];
        return newCrossingLine;
      }
    }

    // Case 3: index is a middle element in waypoints.
  } else {
    a = waypoints[index + 1].lat;
    b = waypoints[index + 1].lng;

    c = waypoints[index - 1].lat;
    d = waypoints[index - 1].lng;

    // Do the check for every line on the map.
    for (let i = 0; i <= waypoints.length; i++) {
      if (i === index || i + 1 === index) {
        // Skip since this waypoint is about to be removed, and so will the connecting lines.
        continue;
      }

      // Special case for when the line between first and last node will be checked.
      if (i === waypoints.length) {
        const p = waypoints[i].lat;
        const q = waypoints[i].lng;

        const r = waypoints[0].lat;
        const s = waypoints[0].lng;

        // Call hasIntersectingVectors directly to handle special case.
        if (hasIntersectingVectors(a, b, c, d, p, q, r, s)) {
          newCrossingLine = [waypoints[index + 1], waypoints[index - 1]];
          return newCrossingLine;
        }

        // Default case.
      } else {
        if (vectorHelper(a, b, c, d, waypoints, i)) {
          newCrossingLine = [waypoints[index + 1], waypoints[index - 1]];
          return newCrossingLine;
        }
      }
    }
  }
  return newCrossingLine;
}

/**
 * Checks if red line (point1 -> point2) are still crossing after removing a waypoint.
 *
 * @param {*} point1 starting point of red line.
 * @param {*} point2 end point of red line.
 * @param {array} waypoints list of all waypoints on the map.
 * @param {integer} index of waypoint about to be removed.
 * @returns true if red line intersects with other lines, otherwise false.
 */
export function checkRedLinesCrossing(point1, point2, waypoints, index) {
  // point1 = (a,b), point2 = (c,d).
  // vector (a,b) -> (c,d) intersects with (p,q) -> (r,s).

  let crossing;
  let a = point1.lat;
  let b = point1.lng;
  let c = point2.lat;
  let d = point2.lng;

  // Check if red line crosses (most) other lines except for special cases.
  for (let i = 0; i < waypoints.length - 1; i++) {
    // If the red line overlaps with itself or with lines that are about to be removed, skip.
    if (
      (point1 === waypoints[i] && point2 === waypoints[i + 1]) ||
      (point1 === waypoints[i + 1] && point2 === waypoints[i]) ||
      index === i ||
      index === i + 1
    ) {
      continue;
    }
    crossing = crossing || vectorHelper(a, b, c, d, waypoints, i);
  }

  /*
    Below is a special case where the red line is checked for 
    intersections with the line from first to last waypoint.
  */

  // If the red line overlaps with itself or with lines that are about to be removed, skip.
  if (
    (point1 === waypoints[0] && point2 === waypoints[waypoints.length - 1]) ||
    (point1 === waypoints[waypoints.length - 1] && point2 === waypoints[0]) ||
    index === 0 ||
    index === waypoints.length - 1
  ) {
    return crossing;
  }

  // Check if the line from first to last waypoint intersects with the given red line.
  let p = waypoints[waypoints.length - 1].lat;
  let q = waypoints[waypoints.length - 1].lng;
  let r = waypoints[0].lat;
  let s = waypoints[0].lng;

  crossing = crossing || hasIntersectingVectors(a, b, c, d, p, q, r, s);
  return crossing;
}

/**
 * Configures points  (p, q) and (r, s) to be used in hasIntersectingVectors.
 *
 * a, b, c, d are integers making up points (a, b) and (c, d).
 *
 * @param {*} waypoints
 * @param {*} i index of what part of waypoint should be used.
 * @returns true if there are intersecting vectors, otherwise false.
 */

function vectorHelper(a, b, c, d, waypoints, i) {
  const p = waypoints[i].lat;
  const q = waypoints[i].lng;

  const r = waypoints[i + 1].lat;
  const s = waypoints[i + 1].lng;
  return hasIntersectingVectors(a, b, c, d, p, q, r, s);
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
  removedWaypointLinesCrossing,
  checkRedLinesCrossing,
  removeRedLinesOnNewWaypoint,
  createRedLines,
};

export default mapHelperExports;


