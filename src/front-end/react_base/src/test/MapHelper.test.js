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

const newCrossingWaypoint = {
  lat: 2,
  lng: 1,
};

test("Tests lines that cross", () => {
  let testing = createRedLines(waypoints, newCrossingWaypoint, null);
  expect(testing).toEqual([
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
