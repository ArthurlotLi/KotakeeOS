/*
    server.js
    Primary file for node.js express project KotakeeOS.
*/

const express = require("express");
const path = require("path");
const fetch = require("node-fetch");

const Home = require("./Home.js");
const Room = require("./Room.js");
const Module = require("./Module.js");

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

const listeningPort = 8080;

// Open Weather Map stuff. Use the boolean to provide canned data
// if you're just testing stuff. (If you're restarting the app
// over and over again, you'll want this boolean set to true.)
const doNotQueryOpenWeatherMap = true;
const openweathermapApiKey = "47ad011b1eb24c37b31f2805da701cc4";
const updateWeatherWait = 900000; // Once every 15 minutes

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
const homeZipCode = "95051"
const home = new Home(homeRooms, homeZipCode, {}); // Start with no weather data. 

/*
  Initial Application Logic (executed once)
*/

// Create the app
const app = express();

// Create a timer for the open weather map API calls. 
home.updateWeather(openweathermapApiKey, doNotQueryOpenWeatherMap);
var updateWeatherInterval = setInterval(function() { home.updateWeather(openWeathermapApiKey, doNotQueryOpenWeatherMap); }, updateWeatherWait);
console.log("[DEBUG] Update Weather Interval set with interval " + updateWeatherWait + ".");

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
// Ex) http://192.168.0.197/moduleToggle/1/50/1
app.get('/moduleToggle/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleToggle GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.roomId != null && req.params.roomId != "null" && req.params.actionId != null && req.params.actionId != "null" && req.params.toState != null && req.params.toState != "null"){
    var roomId = parseInt(req.params.roomId);
    var actionId = parseInt(req.params.actionId);
    var toState = parseInt(req.params.toState);
    if(roomId != null && actionId != null && toState != null){
      home.actionToggle(roomId, actionId, toState);
      // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
      return res.status(200).send();
    }
  }
  return res.status(400).send();
});

// Handle requests from modules to update states when they have
// successfully been modified, or when they restart. 
// Ex) http://192.168.0.197/moduleStateUpdate/1/50/0
app.get('/moduleStateUpdate/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleStateUpdate GET request received. Arguments: " + JSON.stringify(req.params));
  // Update the module status.
  home.moduleStateUpdate(parseInt(req.params.roomId), parseInt(req.params.actionId), parseInt(req.params.toState));
  return res.status(200).send();
});

// Handle requests from clients to fetch module States. This
// should be called frequently (every few seconds).
// Ex) http://192.168.0.197/actionStates
app.get('/actionStates', (req, res) => {
  //console.log("[DEBUG] /actionStates GET request received.");
  return res.status(200).send(home.actionStates());
});

// Handle requests from clients to fetch general update. This
// should be called frequently (every 10 seconds or so).
// Ex) http://192.168.0.197/homeStatus
app.get('/homeStatus', (req, res) => {
  //console.log("[DEBUG] /homeStatus GET request received.");
  return res.status(200).send(home.homeStatus());
});

// Start the server to listen on this port.
app.listen(listeningPort, () => {
  console.log("Project KotakeeOS is online at port: " +listeningPort);
});

