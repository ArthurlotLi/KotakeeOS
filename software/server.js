/*
    server.js
    Primary file for node.js express project KotakeeOS.
*/

const express = require("express");
const path = require("path");

/*
  Enums to keep constant with client logic. 
*/

// Actions enum - Should be kept constant between this and client 
// application logic. Each arduino will contain an array of 
// implemented actions, and within a room, no duplicate actions
// will be present (allowing deliniation between multiple lighting
// modules, for example)
const actions = {
  LIGHTING1: 50,
  LIGHTING2: 51,
  LIGHTING3: 52,
  LIGHTING4: 53,
  LIGHTING5: 54,
  CURTAINS1: 150,
  CURTAINS2: 151,
  CURTAINS3: 152,
  CURTAINS4: 153,
  CURTAINS5: 154,
}

// Bedroom IDs - Should be kept constant betweeen this and client
// application logic. 
const rooms = {
  BEDROOM: 1,
  LIVINGROOM: 2,
}

/*
  Configurable Constants
*/

// Modify these when adding/removing modules.
const bedroomModule1Address = "192.168.0.198";
const listeningPort = 8080;

// Create the app
const app = express();

/*
  Classes (TODO: export to another file)
*/

// Encompassing class for all rooms. Contains various attributes
// regarding the home at large. 
class Home {
  constructor(rooms){
    this.rooms = rooms;
  }
}

// Each room contains room enum as well as an array of modules. 
class Room {
  constructor(roomId, modules){
    this.roomId = roomId;
    this.modules = modules;
  }
}

// Each module contains an array of supported actions and an ipAddress.
class Module {
  constructor(actions, states, ipAddress){
    this.actions = actions;
    this.states = states;
    this.ipAddress = ipAddress;
  }
}

/*
  Web Application logic
*/

// Whenever the request path has "static" inside of it, simply serve 
// the static directory as you'd expect. 
app.use("/static", express.static(path.resolve(__dirname, "public", "static")));

// For the main (and only) page, serve the web application to the client. 
app.get('/',(req,res) => {
    res.sendFile(path.resolve(__dirname, "public", "index.html"));
});

/*
  Web Server logic
*/

// Handle requests from clients to activate modules, without having
// them know what modules are which. 
// Ex) http://192.168.0.197/moduleToggle?roomId=1&actionId=75&newState=1
app.get('moduleToggle', (req, res) => {
})

// Handle requests from modules to update states when they have
// successfully been modified. 
// Ex) http://192.168.0.197/moduleStatusUpdate?roomId=1&actionId=75&newState=1
app.get('moduleStateUpdate', (req, res) => {
})

// Handle requests from clients to fetch module States. This
// should be called frequently (every few seconds).
// Ex) http://192.168.0.197/moduleStates
app.get('moduleStates', (req, res) => {
})

// Handle requests from clients to fetch general update. This
// should be called frequently (every 10 seconds or so).
// Ex) http://192.168.0.197/homeStatus
app.get('homeStatus', (req, res) => {
})

// Start the server to listen on this port.
app.listen(listeningPort, () => {
  console.log("Project KotakeeOS is online at port: " +listeningPort);
});

