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

const prioAndArea = {
  high_priority_client: null,
  bounds: [],
  coordinates: [],
};

io.on("connect", (socket) => {
  console.log("\n   === Got connection ===   ");

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

    socket.emit("response", reply);
  });

  // CheckAlive
  socket.on("check_alive", (request) => {
    console.log("check_alive call");

    let reply = {
      fcn: "ack",
      fcn_name: "check_alive",
    };

    socket.emit("response", reply);
  });

  // Disconnect
  socket.on("quit", (request) => {
    console.log("quit call");

    let reply = {
      fcn: "ack",
      fcn_name: "quit",
    };
    //TODO: Check if user had high prio and set new high prio

    socket.emit("response", reply);
  });

  // SetArea
  socket.on("set_area", (request) => {
    console.log("set_area call");

    let reply = {
      fcn: "ack",
      fcn_name: "set_area",
    };

    socket.emit("response", reply);
    prioAndArea.high_priority_client = request.arg.client_id;
    prioAndArea.bounds = request.arg.bounds;
    prioAndArea.coordinates = request.arg.coordinates;
    io.emit("set_prio", prioAndArea);
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

    socket.emit("response", reply);
  });

  // RequestPriorityView
  socket.on("request_priority_view", (request) => {
    console.log("request_priority_view call");

    let reply = {
      fcn: "ack",
      fcn_name: "request_priority_view",
      arg: {
        force_que_id: 1,
      },
    };

    socket.emit("response", reply);
  });

  // ClearImageQueue
  socket.on("clear_que", (request) => {
    console.log("clear_que call");

    let reply = {
      fcn: "ack",
      fcn_name: "clear_que",
    };

    socket.emit("response", reply);
  });

  // SetMode
  socket.on("set_mode", (request) => {
    console.log("set_mode call");

    let reply = {
      fcn: "ack",
      fcn_name: "set_mode",
    };

    socket.emit("response", reply);
  });

  // GetInfo
  socket.on("get_info", (request) => {
    console.log("get_info call");

    let reply = {
      fcn: "ack",
      fcn_name: "get_info",
      arg: [
        {
          "drone-id": "test",
          time2bingo: 9999999,
        },
      ],
    };

    socket.emit("response", reply);
  });

  // "fake" drone starting position, replace with real drone data later

  let simulatedDronePosition = [
    [58.39463, 15.575143],
    [58.39463, 15.577143],
  ];
  //let simulatedDronePosition = [[58.3947753, 15.5789432]]

  // GetPosition
  socket.on("get_drones", (request) => {
    console.log("get_drones call");

    simulatedDronePosition[0][0] = simulatedDronePosition[0][0] + 0.00006;
    simulatedDronePosition[1][0] = simulatedDronePosition[1][0] - 0.00004;
    simulatedDronePosition[0][1] = simulatedDronePosition[0][1] - 0.0006;
    simulatedDronePosition[1][1] = simulatedDronePosition[1][1] + 0.0007;
    let reply = {
      fcn: "ack",
      fcn_name: "get_drones",
      arg: {
        position: simulatedDronePosition,
      },
    };
    socket.emit("response", reply);
  });

  // GetQueueETA
  socket.on("que_ETA", (request) => {
    console.log("que_ETA call");

    let reply = {
      fcn: "ack",
      fcn_name: "que_ETA",
      arg: {
        ETA: 9999999,
      },
    };
    socket.emit("response", reply);
  });
});
