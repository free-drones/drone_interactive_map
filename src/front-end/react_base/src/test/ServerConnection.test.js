import ServerConnection from '../JS/Connection/ServerConnection.js';
const Server = require('socket.io');

// Localhost
const testNamespace = '/ServerConnectionTest';
const SERVER_IP = "127.0.0.1";
const PORT = 4570;

// Set up local respons server.
var server = new Server(PORT);
var io = server.of(testNamespace);
var downstreamSocket;

beforeAll((done) => {
    try {
        io.once("connection", (socket) => {
            downstreamSocket = socket;
            done();
        });
    }
    catch (error) {
        done(error);
    }
});

afterAll((done) => {
    try {
        ServerConnection.disconnect();
        downstreamSocket.disconnect(true);
        server.close();
        done();
    }
    catch (error) {
        done(error);
    }
});

ServerConnection.initialize(SERVER_IP, PORT, testNamespace, { forceNew : true });

test('recives reply to downstream', (done) => {
    downstreamSocket.once("message", () => {
        downstreamSocket.emit("response", {message: "reply from mockup"});
    });

    ServerConnection.sendDownstream("message", {test: "test"}, (reply) => {
        try {
            expect(reply.message).toBe('reply from mockup')
            done();
        } catch (error) {
            done(error);
        }
    });
});

test('sends request to downstream', (done) => {
    downstreamSocket.once("message", (request) => {
        downstreamSocket.emit("response", '{}');

        try {
            expect(request.message).toBe('request from mockup');
            done();
        } catch (error) {
            done(error);
        }
    })

    ServerConnection.sendDownstream("message", {message: "request from mockup"});
});