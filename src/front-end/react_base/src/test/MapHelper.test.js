import {
  createRedLines,
  isPointInsidePolygon,
} from "../JS/Helpers/maphelper";

const waypoints = [
  {
    lat: 1,
    lng: 1,
  },
  {
    lat: 2,
    lng: 2,
  },
  {
    lat: 1,
    lng: 2,
  },
];

const point1 = {
  lat: 2,
  lng: 1,
};

const point2 = {
  lat: 0,
  lng: 0,
};

const point3 = {
  lat: 1.3,
  lng: 1.9,
};

/**
 * -------------------- CROSSING LINES TESTS --------------------
 */


test("Tests lines that cross when adding waypoint", () => {
  let crossingLines = createRedLines(waypoints, point1, null);
  expect(crossingLines).toEqual([
    [
      { lat: 1, lng: 2 },
      { lat: 2, lng: 1 },
    ],
    [
      { lat: 1, lng: 1 },
      { lat: 2, lng: 2 },
    ],
  ]);
});

test("Tests lines that don't cross when adding waypoint", () => {
  let crossingLines = createRedLines(waypoints, point2, null);
  expect(crossingLines).toEqual([]);
});

test("Tests lines that cross when adding and removing waypoint", () => {
  let crossingLines = createRedLines(waypoints, point1, 1);
  expect(crossingLines).toEqual([
    [
      { lat: 1, lng: 2 },
      { lat: 2, lng: 1 },
    ],
    [
      { lat: 1, lng: 1 },
      { lat: 2, lng: 2 },
    ],
  ]);
});

test("Tests lines that don't cross when adding and removing waypoint", () => {
  let crossingLines = createRedLines(waypoints, point2, 1);
  expect(crossingLines).toEqual([]);
});

test("Tests lines that don't cross when removing waypoint", () => {
  let crossingLines = createRedLines(waypoints, null, 1);
  expect(crossingLines).toEqual([]);
});

const crossingPolygon = [
  {
    lat: 1,
    lng: 1,
  },
  {
    lat: 2,
    lng: 2,
  },
  {
    lat: 2.1,
    lng: 2.1,
  },
  {
    lat: 1,
    lng: 2,
  },
  {
    lat: 2,
    lng: 1,
  },
  {
    lat: 0,
    lng: 1.5,
  },
];

test("Tests lines that cross when removing waypoint", () => {
  let crossingLines = createRedLines(crossingPolygon, null, 5);
  expect(crossingLines).toEqual([
    [
      { lat: 1, lng: 2 },
      { lat: 2, lng: 1 },
    ],
    [
      { lat: 1, lng: 1 },
      { lat: 2, lng: 2 },
    ],
  ]);
});

test("Tests lines that cross when removing waypoint", () => {
  let crossingLines = createRedLines(crossingPolygon, null, 2);
  expect(crossingLines).toEqual([
    [
      { lat: 1, lng: 2 },
      { lat: 2, lng: 1 },
    ],
    [
      { lat: 2, lng: 1 },
      { lat: 0, lng: 1.5 },
    ],
    [
      { lat: 1, lng: 1 },
      { lat: 2, lng: 2 },
    ],
    [
      { lat: 1, lng: 1 },
      { lat: 2, lng: 2 },
    ],
  ]);
});


/**
 * -------------------- POINT IN POLYGON TESTS --------------------
 */

test("Tests point that is not inside area", () => {
  let pointInside = isPointInsidePolygon(point2, waypoints);
  expect(pointInside).toEqual(false);
});

test("Tests point that is inside area", () => {
  let pointInside = isPointInsidePolygon(point3, waypoints);
  expect(pointInside).toEqual(true);
});