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
  addPictureRequest,
  removePictureRequest,
  receivePictureRequest,
  clearPictureRequestQueue,
  addActivePicture,
  removeActivePicture,
  setLayerType,
  setMode,
  setMapBounds,
  setUserPriority,
  setConfigValue,
  setShowWarning,
  setCrossingLines,
  clearCrossingLines,
} from "../JS/Storage.js";

import defaultConfigValues from "../frontendConfig.json";

const exampleView = {
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
};

/**
 * -------------------- WAYPOINT LIST TESTS --------------------
 */

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

/**
 * -------------------- CLIENT ID TESTS --------------------
 */

test("sets client ID", () => {
  Storage.store.dispatch(setClientID(1337));

  expect(Storage.store.getState().clientID).toEqual(1337);
});

test("sets bad Client ID", () => {
  try {
    Storage.store.dispatch(setClientID("CAT"));
  } catch (e) {
    expect(e.message).toBe("Client ID must be a number.");
  }
});

/**
 * -------------------- MAP POSITION TESTS --------------------
 */

test("sets map position", () => {
  Storage.store.dispatch(setMapPosition(exampleView));

  expect(Storage.store.getState().mapPosition).toEqual(exampleView);
});

test("sets map position", () => {
  try {
    Storage.store.dispatch(
      setMapPosition({
        upLeft: {
          lat: "cat",
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

/**
 * -------------------- ZOOM LEVEL TESTS --------------------
 */

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

/**
 * -------------------- PICTURE REQUEST TESTS --------------------
 */

test("adds a picture request", () => {
  Storage.store.dispatch(addPictureRequest(1, exampleView));

  expect(Storage.store.getState().pictureRequestQueue.length).toEqual(1);
  expect(Storage.store.getState().pictureRequestQueue[0]).toHaveProperty(
    "id",
    1
  );
  expect(Storage.store.getState().pictureRequestQueue[0]).toHaveProperty(
    "received",
    false
  );
  expect(Storage.store.getState().pictureRequestQueue[0]).toHaveProperty(
    "receiveTime",
    null
  );
  expect(Storage.store.getState().pictureRequestQueue[0]).toHaveProperty(
    "requestTime"
  );

  Storage.store.dispatch(removePictureRequest(0));
});

test("adds a bad picture request", () => {
  try {
    Storage.store.dispatch(addPictureRequest("cat", exampleView));
  } catch (e) {
    expect(e.message).toBe("Invalid request ID!");
  }
});

test("removes a picture request", () => {
  Storage.store.dispatch(addPictureRequest(2, exampleView));
  Storage.store.dispatch(removePictureRequest(0));

  expect(Storage.store.getState().pictureRequestQueue).toEqual([]);
});

test("receives a picture request", () => {
  Storage.store.dispatch(addPictureRequest(1, exampleView));
  Storage.store.dispatch(addPictureRequest(4, exampleView));
  Storage.store.dispatch(addPictureRequest(7, exampleView));

  Storage.store.dispatch(receivePictureRequest(4));

  const index = Storage.store
    .getState()
    .pictureRequestQueue.map((e) => e.id)
    .indexOf(4);

  expect(Storage.store.getState().pictureRequestQueue.length).toEqual(3);
  expect(Storage.store.getState().pictureRequestQueue[index]).toHaveProperty(
    "id",
    4
  );
  expect(Storage.store.getState().pictureRequestQueue[index]).toHaveProperty(
    "received",
    true
  );
  expect(Storage.store.getState().pictureRequestQueue[index]).toHaveProperty(
    "receiveTime"
  );
  expect(Storage.store.getState().pictureRequestQueue[index]).toHaveProperty(
    "requestTime"
  );

  Storage.store.dispatch(removePictureRequest(0));
  Storage.store.dispatch(removePictureRequest(0));
  Storage.store.dispatch(removePictureRequest(0));
});

test("clears the request queue", () => {
  Storage.store.dispatch(addPictureRequest(1, exampleView));
  Storage.store.dispatch(addPictureRequest(2, exampleView));
  Storage.store.dispatch(clearPictureRequestQueue());

  expect(Storage.store.getState().pictureRequestQueue).toEqual([]);
});

/**
 * -------------------- ACTIVE PICTURE TESTS --------------------
 */

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

/**
 * -------------------- MODE TESTS --------------------
 */

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
    Storage.store.dispatch(setMode("CAT"));
  } catch (e) {
    expect(e.message).toBe("Mode must be either MAN or AUTO.");
  }
});

/**
 * -------------------- BOUNDS TESTS --------------------
 */

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

test("set bad bounds", () => {
  try {
    Storage.store.dispatch(setMapBounds({ lat: [1, 2], lng: [2, 1] }));
  } catch (e) {
    expect(e.message).toBe(
      "Bounds should be a pair of coordinates. Ex: [[1,2], [2,1]]"
    );
  }
});

/**
 * -------------------- LAYER TYPE TESTS --------------------
 */

test("sets layerType", () => {
  Storage.store.dispatch(setLayerType("RGB"));
  Storage.store.dispatch(setLayerType("Map"));
  Storage.store.dispatch(setLayerType("IR"));

  expect(Storage.store.getState().layerType).toEqual("IR");
});

test("sets bad layerType", () => {
  try {
    Storage.store.dispatch(setLayerType("CAT"));
  } catch (e) {
    expect(e.message).toBe("LayerType must be either RGB, IR or Map.");
  }
});

/**
 * -------------------- USER PRIORITY TESTS --------------------
 */

test("sets User Priority", () => {
  Storage.store.dispatch(setUserPriority(5));

  expect(Storage.store.getState().userPriority).toEqual(5);
});

test("sets bad User Priority", () => {
  try {
    Storage.store.dispatch(setUserPriority("CAT"));
  } catch (e) {
    expect(e.message).toBe("User Priority must be a number.");
  }
});

/**
 * -------------------- CONFIG TESTS --------------------
 */

test("checks if default config looks correct", () => {
  expect(Storage.store.getState().config).toEqual(defaultConfigValues);
});

test("sets droneIconPixelSize", () => {
  Storage.store.dispatch(setConfigValue("droneIconPixelSize", 5));

  expect(Storage.store.getState().config).toHaveProperty(
    "droneIconPixelSize",
    5
  );
  expect(JSON.parse(sessionStorage.getItem("config"))).toHaveProperty(
    "droneIconPixelSize",
    5
  );
  // Make sure it only changes the value it is supposed to change
  expect(Storage.store.getState().config).toHaveProperty(
    "showDroneIcons",
    true
  );
});

test("sets random value", () => {
  Storage.store.dispatch(setConfigValue("CAT", "FELINE"));

  expect(Storage.store.getState().config).toHaveProperty("CAT", "FELINE");
  // Make sure it only changes the value it is supposed to change
  expect(Storage.store.getState().config).toHaveProperty(
    "showDroneIcons",
    true
  );
});

/**
 * -------------------- SHOW WARNING TESTS --------------------
 */

test("sets show warning", () => {
  Storage.store.dispatch(setShowWarning(true));

  expect(Storage.store.getState().showWarning).toEqual(true);
});

/**
 * -------------------- CROSSING LINES TESTS --------------------
 */
test("sets crossing lines to list of one line", () => {
  Storage.store.dispatch(
    setCrossingLines([
      [
        { lat: 1, lng: 2 },
        { lat: 2, lng: 3 },
      ],
    ])
  );
  expect(Storage.store.getState().crossingLines).toEqual([
    [
      { lat: 1, lng: 2 },
      { lat: 2, lng: 3 },
    ],
  ]);
});

test("clears waypoint list", () => {
  Storage.store.dispatch(
    setCrossingLines([
      [
        { lat: 1, lng: 2 },
        { lat: 2, lng: 3 },
      ],
    ])
  );
  Storage.store.dispatch(clearCrossingLines());

  expect(Storage.store.getState().crossingLines).toEqual([]);
});
