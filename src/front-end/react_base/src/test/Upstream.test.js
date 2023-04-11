import ServerConnection from "../JS/Connection/ServerConnection.js";
import "core-js";
const { Server } = require("socket.io");

// Localhost
const testNamespace = "/UpstreamTest";
const SERVER_IP = "127.0.0.1";
const PORT = 4572;

// Set up local respons server.
var server = new Server(PORT);
var io = server.of(testNamespace);
var upstreamSocket;

beforeAll((done) => {
  try {
    io.once("connection", (socket) => {
      upstreamSocket = socket;
      done();
    });
  } catch (error) {
    done(error);
  }
});

afterAll((done) => {
  try {
    ServerConnection.disconnect();
    upstreamSocket.disconnect(true);
    server.close();
    done();
  } catch (error) {
    done(error);
  }
});

ServerConnection.initialize(
  SERVER_IP,
  PORT,
  testNamespace,
  { forceNew: true },
  { forceNew: true }
);

test("recieve new_pic", (done) => {
  try {
    upstreamSocket.once("notify", (reply) => {
      // Assert that reply was a valid ack
      expect(reply).toEqual({ fcn: "ack", fcn_name: "new_pic" });
      done();
    });

    let data = {
      fcn: "new_pic",
      arg: {
        type: "IR",
        prioritized: true,
        image_id: 721,
      },
    };

    upstreamSocket.emit("notify", data);
  } catch (error) {
    done(error);
  }
});
