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
  Classes (TODO: export to another file)
*/

// Encompassing class for all rooms. Contains various attributes
// regarding the home at large. 
class Home {
  constructor(rooms, weatherData){
    // Given array of rooms, create dictionary indexed by roomId. 
    var roomsDict = {};
    for(var i = 0; i < rooms.length; i++){
      var room = rooms[i];
      roomsDict[room.roomId] = room;
    }
    this.rooms = roomsDict
    this.weatherData = weatherData;
  }
}

// Each room contains room enum as well as an array of modules. 
class Room {
  constructor(roomId, modules){
    this.roomId = roomId;
    // Create two dictionaries - one indexed by actionId, the other
    // by moduleId. 
    var actionsDict = {};
    var modulesDict = {};
    for(var i = 0; i < modules.length; i++){
      // Iterate through all modules in room and save all seen actions.
      // Link each action to the module object itself for easy access.
      var module = modules[i];
      modulesDict[module.moduleId] = module;
      for(var j = 0; j < module.actions.length; j++){
        // Iterate through all actions for this module and add them. 
        actionsDict[module.actions[j]] = module.moduleId;
      }
    }
    this.actionsDict = actionsDict;
    this.modulesDict = modulesDict;
    console.log("[DEBUG] Created module with actionsDict: " + JSON.stringify(actionsDict) + " and modulesDict: " + JSON.stringify(modulesDict));
  }
}

// Each module contains an array of supported actions and an ipAddress.
class Module {
  constructor(moduleId, actions, ipAddress){
    this.moduleId = moduleId;
    this.actions = actions;
    var newStates = [];
    for(var i = 0; i < actions.length; i++){
      newStates.push(0);
    }
    this.states = newStates;
    this.ipAddress = ipAddress;
  }
}

/*
  Configurable Constants
*/

const listeningPort = 8080;

// When adding modules, create module object and add to room's
// array of Modules. 

// Arduino 1 Bedroom 
const module1BRId = 1;
const module1BRActions = [actions.LIGHTING1];
const module1BRIpAddress = "192.168.0.198";
const moduleBR1 = new Module(module1BRId, module1BRActions, module1BRIpAddress);

// Rooms (add objects here)
const bedroomModules = [moduleBR1];
const bedroom = new Room(rooms.BEDROOM,bedroomModules);
const livingRoomModules = [];
const livingRoom = new Room(rooms.LIVINGROOM,livingRoomModules);

// Home
const homeRooms = [bedroom, livingRoom];
const home = new Home(homeRooms, {}); // TODO add weather data. 

// Create the app
const app = express();

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
app.get('/moduleToggle/:roomId/:actionId/:newState', (req, res) => {
  console.log("[DEBUG] /moduleToggle GET request received. Arguments: " + JSON.stringify(req.params));
  res.status(200).send();
})

app.get('/moduleToggle', (req, res) => {
  console.log("[DEBUG] /moduleToggle GET request received. Arguments: " + JSON.stringify(req.params));
  res.status(200).send();
})

// Handle requests from modules to update states when they have
// successfully been modified. 
// Ex) http://192.168.0.197/moduleStatusUpdate?roomId=1&actionId=75&newState=1
app.get('/moduleStateUpdate/:roomId/:actionId/:newState', (req, res) => {
  console.log("[DEBUG] /moduleStateUpdate GET request received. Arguments: " + JSON.stringify(req.params));
  res.status(200).send();
})

// Handle requests from clients to fetch module States. This
// should be called frequently (every few seconds).
// Ex) http://192.168.0.197/moduleStates
app.get('/moduleStates', (req, res) => {
  console.log("[DEBUG] /moduleStates GET request received.");
  res.status(200).send();
})

// Handle requests from clients to fetch general update. This
// should be called frequently (every 10 seconds or so).
// Ex) http://192.168.0.197/homeStatus
app.get('/homeStatus', (req, res) => {
  console.log("[DEBUG] /homeStatus GET request received.");
  res.status(200).send();
})

// Start the server to listen on this port.
app.listen(listeningPort, () => {
  console.log("Project KotakeeOS is online at port: " +listeningPort);
});

