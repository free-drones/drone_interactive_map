/**
 * Mockup of backend.
 * Run this when testing frontend without backend running.
 */

const MockupConstants = require("./MockupConstants.js");
const { Server } = require("socket.io");

// Set up local response server.
var server = new Server(MockupConstants.PORT, { cors: { origin: "*" } });
var io = server.of(MockupConstants.NAMESPACE);

let client_id_counter = 1;

const priorityAndArea = {
  high_priority_client: null,
  bounds: [],
  coordinates: [],
};

io.on("connect", (socket) => {
  console.log("\n   === Got connection ===   ");

  // "fake" drone data for testing GUI
  const simulatedDrones = {
    drone1: {
      drone_id: 1,
      location: {
        lat: 58.39463,
        long: 15.575143,
      },
      mode: "AUTO",
    },

    drone2: {
      drone_id: 2,
      location: {
        lat: 58.39463,
        long: 15.577143,
      },
      mode: "MAN",
    },

    drone3: {
      drone_id: 3,
      location: {
        lat: 58.39463,
        long: 15.579143,
      },
      mode: "PHOTO",
    },

    drone4: {
      drone_id: 4,
      location: {
        lat: 58.39463,
        long: 15.581143,
      },
      mode: "AUTO",
    },
  };

  // Testing updating drone data
  setInterval(() => {
    simulatedDrones.drone1.location.lat -= 0.0006;
    simulatedDrones.drone2.location.lat -= 0.0003;
    simulatedDrones.drone3.location.lat += 0.0003;
    simulatedDrones.drone4.location.lat += 0.0003;

    simulatedDrones.drone1.location.long -= 0.0006;
    simulatedDrones.drone2.location.long += 0.0003;
    simulatedDrones.drone3.location.long -= 0.0003;
    simulatedDrones.drone4.location.long += 0.0003;

    let reply = {
      fcn: "new_drones",
      arg: {
        drones: simulatedDrones,
      },
    };
    socket.emit("notify", reply);
  }, 1000);

  // Connect
  socket.on("init_connection", (request) => {
    console.log("init_connection call");

    let reply = {
      fcn: "ack",
      fcn_name: "init_connection",
      arg: {
        client_id: client_id_counter++,
      },
    };

    socket.emit("init_connection_response", reply);
  });

  // CheckAlive
  socket.on("check_alive", (request) => {
    console.log("check_alive call");

    let reply = {
      fcn: "ack",
      fcn_name: "check_alive",
    };

    socket.emit("check_alive_response", reply);
  });

  // Disconnect
  socket.on("quit", (request) => {
    console.log("quit call");

    let reply = {
      fcn: "ack",
      fcn_name: "quit",
    };
    //TODO: Check if user had high priority and set new high priority 

    socket.emit("quit_response", reply);
  });

  // SetArea
  socket.on("set_area", (request) => {
    console.log("set_area call");

    let reply = {
      fcn: "ack",
      fcn_name: "set_area",
    };

    socket.emit("set_area_response", reply);
    priorityAndArea.high_priority_client = request.arg.client_id;
    priorityAndArea.bounds = request.arg.bounds;
    priorityAndArea.coordinates = request.arg.coordinates;
    io.emit("set_priority", priorityAndArea);
  });

  // RequestView
  socket.on("request_view", (request) => {
    console.log("request_view call");

    let reply = {
      fcn: "ack",
      fcn_name: "request_view",
      arg: {
        image_data: [],
      },
    };

    socket.emit("request_view_response", reply);
  });

  // RequestPriorityPicture
  socket.on("request_priority_picture", (request) => {
    console.log("request_priority_picture call");

    let reply = {
      fcn: "ack",
      fcn_name: "request_priority_picture",
      arg: {
        force_queue_id: 1,
      },
    };

    socket.emit("request_priority_picture_response", reply);
  });

  // ClearImageQueue
  socket.on("clear_queue", (request) => {
    console.log("clear_queue call");

    let reply = {
      fcn: "ack",
      fcn_name: "clear_queue",
    };

    socket.emit("clear_queue_response", reply);
  });

  // SetMode
  socket.on("set_mode", (request) => {
    console.log("set_mode call");

    let reply = {
      fcn: "ack",
      fcn_name: "set_mode",
    };

    socket.emit("set_mode_response", reply);
  });

  // GetQueueETA
  socket.on("queue_ETA", (request) => {
    console.log("queue_ETA call");

    let reply = {
      fcn: "ack",
      fcn_name: "queue_ETA",
      arg: {
        ETA: 9999999,
      },
    };
    socket.emit("queue_ETA_response", reply);
  });
});
