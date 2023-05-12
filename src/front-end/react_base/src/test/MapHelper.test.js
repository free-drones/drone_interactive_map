import {
  boundsToView,
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

test("Tests lines that cross", () => {
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

test("Tests lines that don't cross", () => {
  let crossingLines = createRedLines(waypoints, point2, null);
  expect(crossingLines).toEqual([]);
});

test("Tests point that is not inside area", () => {
  let pointInside = isPointInsidePolygon(point2, waypoints);
  expect(pointInside).toEqual(false);
});

test("Tests point that is inside area", () => {
  let pointInside = isPointInsidePolygon(point3, waypoints);
  expect(pointInside).toEqual(true);
});