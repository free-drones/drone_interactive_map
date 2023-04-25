import ServerConnection from "../JS/Connection/ServerConnection.js";
import Downstream, {
  isValidView,
  translateView,
  isValidCoordinate,
  translateCoordinate,
} from "../JS/Connection/Downstream.js";
import "core-js";
const { Server } = require("socket.io");

// Localhost
const testNamespace = "/DownstreamTest";
const SERVER_IP = "127.0.0.1";
const PORT = 4571;

// Set up local response server.
var server = new Server(PORT);
var io = server.of(testNamespace);
var downstreamSocket;

beforeAll((done) => {
  try {
    io.once("connection", (socket) => {
      downstreamSocket = socket;
      done();
    });
  } catch (error) {
    done(error);
  }
});

afterAll((done) => {
  try {
    ServerConnection.disconnect();
    downstreamSocket.disconnect(true);
    server.close();
    done();
  } catch (error) {
    done(error);
  }
});

ServerConnection.initialize(SERVER_IP, PORT, testNamespace, { forceNew: true });

var validCoordinateSend = {
  lat: 53.123456,
  lng: 16.123456,
};

var validCoordinateReceived = {
  lat: validCoordinateSend.lat,
  long: validCoordinateSend.lng,
};

const validBounds = [
  [53.123456, 16.123456],
  [53.123456, 16.123456],
];

var invalidCoordinate = {
  lant: 5,
  long: 17,
};

var validViewSend = {
  upLeft: {
    lat: 53.123456,
    lng: 16.123456,
  },
  upRight: {
    lat: 53.123456,
    lng: 16.123456,
  },
  downLeft: {
    lat: 53.123456,
    lng: 16.123456,
  },
  downRight: {
    lat: 53.123456,
    lng: 16.123456,
  },
  center: {
    lat: 53.123456,
    lng: 16.123456,
  },
};

var validViewReceived = {
  up_left: {
    lat: validViewSend.upLeft.lat,
    long: validViewSend.upLeft.lng,
  },
  up_right: {
    lat: validViewSend.upRight.lat,
    long: validViewSend.upRight.lng,
  },
  down_left: {
    lat: validViewSend.downLeft.lat,
    long: validViewSend.downLeft.lng,
  },
  down_right: {
    lat: validViewSend.downRight.lat,
    long: validViewSend.downRight.lng,
  },
  center: {
    lat: validViewSend.center.lat,
    long: validViewSend.center.lng,
  },
};

var invalidView = {
  uLeft: {
    lat: "53.123456",
    lng: "16.123456",
  },
  upright: {
    lat: "53.123456",
    lng: "16.123456",
  },
  down_left: {
    lat: "53.123456",
    lng: "16.123456",
  },
  downRight: {
    lat: "53.123456",
    long: "16.123456",
  },
};

test("valid coordinate", () => {
  expect(isValidCoordinate(validCoordinateSend)).toBe(true);
});

test("invalid coordinate", () => {
  expect(isValidCoordinate(invalidCoordinate)).toBe(false);
});

test("valid view", () => {
  expect(isValidView(validViewSend)).toBe(true);
});

test("invalid view", () => {
  expect(isValidView(invalidView)).toBe(false);
});

test("translates coordinate", () => {
  expect(translateCoordinate(validCoordinateSend)).toEqual(
    validCoordinateReceived
  );
});

test("translates view", () => {
  expect(translateView(validViewSend)).toEqual(validViewReceived);
});

test("send connect", (done) => {
  downstreamSocket.once("init_connection", (request) => {
    try {
      // Save request data to be validated in callback
      expect(request).toEqual({});

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "init_connection",
        arg: {
          client_id: 1,
        },
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.connect(() => {
    done();
  });
});

test("send disconnect", (done) => {
  downstreamSocket.once("quit", (request) => {
    try {
      // Validate request
      expect(request).toEqual({});

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "quit",
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.disconnect(() => {
    done();
  });
});

test("send set_area", (done) => {
  downstreamSocket.once("set_area", (request) => {
    try {
      // Validate request
      expect(request).toEqual({
        fcn: "set_area",
        arg: {
          client_id: 1,
          coordinates: [validCoordinateReceived],
          bounds: validBounds,
        },
      });

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "set_area",
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.setArea(1, [validCoordinateSend], validBounds, () => {
    done();
  });
});

test("send request_view", (done) => {
  downstreamSocket.once("request_view", (request) => {
    try {
      // Validate request
      expect(request).toEqual({
        fcn: "request_view",
        arg: { client_id: 1, coordinates: validViewReceived },
      });

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "request_view",
        arg: {
          image_data: [],
        },
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.requestView(1, validViewSend, () => {
    done();
  });
});

test("send request_priority_picture", (done) => {
  downstreamSocket.once("request_priority_picture", (request) => {
    try {
      // Validate request
      expect(request).toEqual({
        fcn: "request_priority_picture",
        arg: { client_id: 1, coordinates: validViewReceived, isUrgent: false },
      });

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "request_priority_picture",
        arg: {
          force_que_id: 1,
        },
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.requestPriorityPicture(1, validViewSend, false, () => {
    done();
  });
});

test("send clear_queue", (done) => {
  downstreamSocket.once("clear_queue", (request) => {
    try {
      // Validate request
      expect(request).toEqual({});

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "clear_queue",
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.clearImageQueue(() => {
    done();
  });
});

test("send set_mode (manual)", (done) => {
  downstreamSocket.once("set_mode", (request) => {
    try {
      // Validate request
      expect(request).toEqual({ fcn: "set_mode", arg: { mode: "MAN" } });

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "set_mode",
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.setMode(Downstream.MODE.manual, null, () => {
    done();
  });
});

test("send set_mode (automatic)", (done) => {
  downstreamSocket.once("set_mode", (request) => {
    try {
      // Validate request
      expect(request).toEqual({
        fcn: "set_mode",
        arg: { mode: "AUTO", zoom: validViewReceived },
      });

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "set_mode",
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.setMode(Downstream.MODE.automatic, validViewSend, () => {
    done();
  });
});

test("send set_mode (automatic, fail)", () => {
  expect(() => {
    Downstream.setMode(Downstream.MODE.automatic);
  }).toThrow();
});

test("send get_info", (done) => {
  downstreamSocket.once("get_info", (request) => {
    try {
      // Validate request
      expect(request).toEqual({});

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "get_info",
        arg: [
          {
            "drone-id": "one",
            time2bingo: 15,
          },
        ],
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.getInfo(() => {
    done();
  });
});

test("send que_ETA", (done) => {
  downstreamSocket.once("que_ETA", (request) => {
    try {
      // Validate request
      expect(request).toEqual({});

      // Emulate server response
      let response = {
        fcn: "ack",
        fcn_name: "que_ETA",
        arg: {
          ETA: "53",
        },
      };
      downstreamSocket.emit("response", response);
    } catch (error) {
      done(error);
    }
  });

  Downstream.getQueueETA(() => {
    done();
  });
});
