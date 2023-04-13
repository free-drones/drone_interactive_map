/**
 * Redux storage test file.
 */

import Storage, {
  addAreaWaypoint,
  removeAreaWaypoint,
  clearAreaWaypoints,
  setClientID,
  setMapPosition,
  setZoomLevel,
  addRequest,
  removeRequest,
  receiveRequest,
  clearRequestQueue,
  addActivePicture,
  removeActivePicture,
  setSensor,
  setMode,
  setMapBounds,
} from "../JS/Storage.js";

test("adds waypoint to list", () => {
  Storage.store.dispatch(addAreaWaypoint({ lat: 1, lng: 2 }));
  expect(Storage.store.getState().areaWaypoints).toEqual([{ lat: 1, lng: 2 }]);

  // Reset for future tests
  Storage.store.dispatch(removeAreaWaypoint(0));
});

test("adds bad waypoint to list", () => {
  try {
    Storage.store.dispatch(addAreaWaypoint({ lat: "1", lng: "2" }));
  } catch (e) {
    expect(e.message).toBe("Invalid waypoint!");
  }

  // Reset for future tests
  Storage.store.dispatch(removeAreaWaypoint(0));
});

test("adds listed waypoint to list", () => {
  try {
    Storage.store.dispatch(addAreaWaypoint([2, 1]));
  } catch (e) {
    expect(e.message).toBe("Invalid waypoint!");
  }

  // Reset for future tests
  Storage.store.dispatch(removeAreaWaypoint(0));
});

test("removes waypoint from list", () => {
  Storage.store.dispatch(addAreaWaypoint({ lat: 1, lng: 2 }));
  Storage.store.dispatch(addAreaWaypoint({ lat: 3, lng: 4 }));
  Storage.store.dispatch(removeAreaWaypoint(0));

  expect(Storage.store.getState().areaWaypoints).toEqual([{ lat: 3, lng: 4 }]);

  // Reset for future tests
  Storage.store.dispatch(removeAreaWaypoint(0));
});

test("clears waypoint list", () => {
  Storage.store.dispatch(addAreaWaypoint({ lat: 1, lng: 2 }));
  Storage.store.dispatch(addAreaWaypoint({ lat: 3, lng: 4 }));
  Storage.store.dispatch(clearAreaWaypoints());

  expect(Storage.store.getState().areaWaypoints).toEqual([]);
});

test("sets client ID", () => {
  Storage.store.dispatch(setClientID(1337));

  expect(Storage.store.getState().clientID).toEqual(1337);
});

test("sets bad connection token", () => {
  try {
    Storage.store.dispatch(setClientID("KATT"));
  } catch (e) {
    expect(e.message).toBe("Client ID must be a number.");
  }
});

test("sets map position", () => {
  Storage.store.dispatch(
    setMapPosition({
      upLeft: {
        lat: 58.409049,
        lng: 15.609948,
      },
      upRight: {
        lat: 58.409049,
        lng: 15.609948,
      },
      downLeft: {
        lat: 58.409049,
        lng: 15.609948,
      },
      downRight: {
        lat: 58.409049,
        lng: 15.609948,
      },
      center: {
        lat: 58.409049,
        lng: 15.609948,
      },
    })
  );

  expect(Storage.store.getState().mapPosition).toEqual({
    upLeft: {
      lat: 58.409049,
      lng: 15.609948,
    },
    upRight: {
      lat: 58.409049,
      lng: 15.609948,
    },
    downLeft: {
      lat: 58.409049,
      lng: 15.609948,
    },
    downRight: {
      lat: 58.409049,
      lng: 15.609948,
    },
    center: {
      lat: 58.409049,
      lng: 15.609948,
    },
  });
});

test("sets map position", () => {
  try {
    Storage.store.dispatch(
      setMapPosition({
        upLeft: {
          lat: "katt",
          lng: 15.609948,
        },
        upRight: {
          lat: 58.409049,
          lng: 15.609948,
        },
        downLeft: {
          lat: 58.409049,
          lng: 15.609948,
        },
        downRight: {
          lat: 58.409049,
          lng: 15.609948,
        },
        center: {
          lat: 58.409049,
          lng: 15.609948,
        },
      })
    );
  } catch (e) {
    expect(e.message).toBe("Invalid view!");
  }
});

test("sets bad map position", () => {
  try {
    Storage.store.dispatch(setMapPosition({ lat: "2", lng: "l" }));
  } catch (e) {
    expect(e.message).toBe("Invalid view!");
  }
});

test("sets zoom level", () => {
  Storage.store.dispatch(setZoomLevel(5));

  expect(Storage.store.getState().zoomLevel).toEqual(5);
});

test("sets high zoom level", () => {
  Storage.store.dispatch(setZoomLevel(25));
  expect(Storage.store.getState().zoomLevel).toEqual(22);
});

test("sets low zoom level", () => {
  Storage.store.dispatch(setZoomLevel(-50));
  expect(Storage.store.getState().zoomLevel).toEqual(0);
});

test("adds a picture request", () => {
  Storage.store.dispatch(addRequest(1));

  expect(Storage.store.getState().requestQueue.size).toEqual(1);
  expect(Storage.store.getState().requestQueue.items.length).toEqual(1);
  expect(Storage.store.getState().requestQueue.items[0]).toHaveProperty(
    "id",
    1
  );
  expect(Storage.store.getState().requestQueue.items[0]).toHaveProperty(
    "received",
    false
  );
  expect(Storage.store.getState().requestQueue.items[0]).toHaveProperty(
    "receiveTime",
    null
  );
  expect(Storage.store.getState().requestQueue.items[0]).toHaveProperty(
    "requestTime"
  );

  Storage.store.dispatch(removeRequest(0));
});

test("adds a bad picture request", () => {
  try {
    Storage.store.dispatch(addRequest("Katt"));
  } catch (e) {
    expect(e.message).toBe("Invalid request ID!");
  }
});

test("removes a picture request", () => {
  Storage.store.dispatch(addRequest(2));
  Storage.store.dispatch(removeRequest(0));

  expect(Storage.store.getState().requestQueue).toEqual({ size: 0, items: [] });
});

test("receives a picture request", () => {
  Storage.store.dispatch(addRequest(1));
  Storage.store.dispatch(addRequest(4));
  Storage.store.dispatch(addRequest(7));

  Storage.store.dispatch(receiveRequest(4));

  const index = Storage.store
    .getState()
    .requestQueue.items.map((e) => e.id)
    .indexOf(4);

  expect(Storage.store.getState().requestQueue.size).toEqual(3);
  expect(Storage.store.getState().requestQueue.items.length).toEqual(3);
  expect(Storage.store.getState().requestQueue.items[index]).toHaveProperty(
    "id",
    4
  );
  expect(Storage.store.getState().requestQueue.items[index]).toHaveProperty(
    "received",
    true
  );
  expect(Storage.store.getState().requestQueue.items[index]).toHaveProperty(
    "receiveTime"
  );
  expect(Storage.store.getState().requestQueue.items[index]).toHaveProperty(
    "requestTime"
  );

  Storage.store.dispatch(removeRequest(0));
  Storage.store.dispatch(removeRequest(0));
  Storage.store.dispatch(removeRequest(0));
});

test("clears the request queue", () => {
  Storage.store.dispatch(addRequest(1));
  Storage.store.dispatch(addRequest(2));
  Storage.store.dispatch(clearRequestQueue());

  expect(Storage.store.getState().requestQueue).toEqual({ size: 0, items: [] });
});

test("adds an active picture", () => {
  Storage.store.dispatch(
    addActivePicture({
      type: "RGB",
      prioritized: true,
      imageID: 1,
      url: "URL",
      timeTaken: 8,
      coordinates: {
        upLeft: {
          lat: 58.123456,
          lng: 16.123456,
        },
        upRight: {
          lat: 59.123456,
          lng: 17.123456,
        },
        downLeft: {
          lat: 60.123456,
          lng: 18.123456,
        },
        downRight: {
          lat: 61.123456,
          lng: 19.123456,
        },
        center: {
          lat: 61.123456,
          lng: 19.123456,
        },
      },
    })
  );

  expect(Storage.store.getState().activePictures).toEqual([
    {
      type: "RGB",
      prioritized: true,
      imageID: 1,
      url: "URL",
      timeTaken: 8,
      coordinates: {
        upLeft: {
          lat: 58.123456,
          lng: 16.123456,
        },
        upRight: {
          lat: 59.123456,
          lng: 17.123456,
        },
        downLeft: {
          lat: 60.123456,
          lng: 18.123456,
        },
        downRight: {
          lat: 61.123456,
          lng: 19.123456,
        },
        center: {
          lat: 61.123456,
          lng: 19.123456,
        },
      },
    },
  ]);

  Storage.store.dispatch(removeActivePicture(0));
});
/*
test('removes an active picture', () => {
    Storage.store.dispatch(addActivePicture("E pic!"));
    Storage.store.dispatch(removeActivePicture(0));

    expect(Storage.store.getState().activePictures).toEqual([]);
});*/

test("set mode", () => {
  Storage.store.dispatch(setMode("MAN"));

  expect(Storage.store.getState().mode).toEqual("MAN");
});

test("set mode auto", () => {
  Storage.store.dispatch(setMode("AUTO"));

  expect(Storage.store.getState().mode).toEqual("AUTO");
});

test("set bad mode", () => {
  try {
    Storage.store.dispatch(setMode("KATT"));
  } catch (e) {
    expect(e.message).toBe("Mode must be either MAN or AUTO.");
  }
});

test("set bounds", () => {
  Storage.store.dispatch(
    setMapBounds([
      [1, 2],
      [2, 1],
    ])
  );
  expect(Storage.store.getState().mapBounds).toEqual([
    [1, 2],
    [2, 1],
  ]);
});

test("sets sensor", () => {
  Storage.store.dispatch(setSensor("RGB"));
  Storage.store.dispatch(setSensor("Map"));
  Storage.store.dispatch(setSensor("IR"));

  expect(Storage.store.getState().sensor).toEqual("IR");
});

test("set bad bounds", () => {
  try {
    Storage.store.dispatch(setMapBounds({ lat: [1, 2], lng: [2, 1] }));
  } catch (e) {
    expect(e.message).toBe(
      "Bounds should be a pair of coordinates. Ex: [[1,2], [2,1]]"
    );
  }
});
