/*
    server.js
    Primary file for node.js express project KotakeeOS.
*/

const express = require("express");
const path = require("path");
const redis = require('redis');

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
  REMOTE1: 250,
  REMOTE2: 251,
  REMOTE3: 252,
  REMOTE4: 253,
  REMOTE5: 254,
  REMOTE6: 255,
  REMOTE7: 256,
  REMOTE8: 257,
  REMOTE9: 258,
  REMOTE10: 259,
  REMOTE11: 260,
  REMOTE12: 261,
  REMOTE13: 262,
  REMOTE14: 263,
  REMOTE15: 264,
  REMOTE16: 265,
  REMOTE17: 266,
  REMOTE18: 267,
  REMOTE19: 268,
  REMOTE20: 269,
  SWITCH1: 350,
  SWITCH2: 351,
  SWITCH3: 352,
  SWITCH4: 353,
  SWITCH5: 354,
  // Input enums. Are considered "actions" but are treated entirely differently. 
  // Seperated from actions by 5000. Do not need to be known by client.
  MOTION1: 5050,
  MOTION2: 5051,
  MOTION3: 5052,
  MOTION4: 5053,
  MOTION5: 5054,
  DOOR1: 5150,
  DOOR2: 5151,
  DOOR3: 5152,
  DOOR4: 5153,
  DOOR5: 5154,
  TEMP1: 5250,
  TEMP2: 5251,
  TEMP3: 5252,
  TEMP4: 5253,
  TEMP5: 5254,
}

// Bedroom IDs - Should be kept constant betweeen this and client
// application logic. 
const rooms = {
  BEDROOM: 1,
  LIVINGROOM: 2,
  BATHROOM: 3,
}

// pubsub topic names
const HOME_STATUS = 'homeStatus';
const ACTION_STATES = 'actionStates';

// End enums

/*
  Configurable Constants + app creation
*/

const listeningPort = 8080;

// Open Weather Map stuff. Use the boolean to provide canned data
// if you're just testing stuff. (If you're restarting the app
// over and over again, you'll want this boolean set to true.)
var doNotQueryOpenWeatherMap = false;
const useRedis = false;

// Get arguments (currently only for query map.)
const args = process.argv.slice(2);
if(args.length > 0){
  // If we have ANYTHING, don't query the API. That's good enough for now. 
  doNotQueryOpenWeatherMap = true; 
}

const openweathermapApiKey = "47ad011b1eb24c37b31f2805da701cc4";
const updateWeatherWait = 120000; // Once every 2 minutes (1 min = 60000 ms)

// For pubsub architecture
var publisher;
if(useRedis){
  console.log("[DEBUG] redis has been enabled. Ensure redis-server has been run otherwise an exception is imminent.");
  publisher = redis.createClient();
}
else{
  console.log("[DEBUG] redis is NOT enabled.");
  publisher = null;
}

// Create the app
const app = express();

// When adding modules, create module object and add to room's
// array of Modules. 

// Arduino 1 Bedroom 
const module1BRId = 1; // Internal server use only. 
const module1BRRoomId = rooms.BEDROOM; 
const module1BRActions = [actions.LIGHTING1];
const module1BRPins = [12];
const module1BRIpAddress = "192.168.0.198";
const module1BR = new Module(module1BRId, module1BRRoomId, module1BRActions, module1BRPins, module1BRIpAddress);

// Arduino 2 Living Room
const module2LRId = 2; // Internal server use only. 
const module2LRRoomId = rooms.LIVINGROOM; 
const module2LRActions = [actions.LIGHTING1];
const module2LRPins = [12];
const module2LRIpAddress = "192.168.0.160";
const module2LR = new Module(module2LRId, module2LRRoomId, module2LRActions, module2LRPins, module2LRIpAddress);

// Arduino 3 Living Room
const module3LRId = 3; // Internal server use only. 
const module3LRRoomId = rooms.LIVINGROOM; 
const module3LRActions = [actions.REMOTE1];
const module3LRPins = [12];
const module3LRIpAddress = "192.168.0.100";
const module3LR = new Module(module3LRId, module3LRRoomId, module3LRActions, module3LRPins, module3LRIpAddress);

// Arduino 4 Living Room
const module4LRId = 4; // Internal server use only. 
const module4LRRoomId = rooms.LIVINGROOM; 
const module4LRActions = [actions.REMOTE2, actions.SWITCH1, actions.REMOTE3, actions.MOTION1];
const module4LRPins = [12, 10.11, 9, 8];
const module4LRIpAddress = "192.168.0.144";
const module4LR = new Module(module4LRId, module4LRRoomId, module4LRActions, module4LRPins, module4LRIpAddress);

// Arduino 5 Bathroom
const module5BAId = 5; // Internal server use only. 
const module5BARoomId = rooms.BATHROOM; 
const module5BAActions = [actions.SWITCH1, actions.SWITCH2, actions.MOTION1, actions.LIGHTING1, actions.DOOR1];
const module5BAPins = [10.11, 6.9, 8, 14, 2];
const module5BAIpAddress = "192.168.0.101";
const module5BA = new Module(module5BAId, module5BARoomId, module5BAActions, module5BAPins, module5BAIpAddress);

// Arduino 6 LR
const module6LRId = 6; // Internal server use only. 
const module6LRRoomId = rooms.LIVINGROOM; 
const module6LRActions = [actions.DOOR1];
const module6LRPins = [2];
const module6LRIpAddress = "192.168.0.186";
const module6LR = new Module(module6LRId, module6LRRoomId, module6LRActions, module6LRPins, module6LRIpAddress);

// Rooms (add objects here)
const bedroomModules = [module1BR];
const bedroomInputActions = {};
const bedroom = new Room(rooms.BEDROOM,bedroomModules, bedroomInputActions);

const livingRoomModules = [module2LR, module3LR, module4LR, module6LR];
const livingRoomInputActions = {
  5050: {
    "function" : "timeout",
    1: {
      "duration" : 20000,
      "start":{
        350: 22,
      },
      "timeout": {
        350: 20,
      },
    },
  },
};
const livingRoom = new Room(rooms.LIVINGROOM,livingRoomModules, livingRoomInputActions);

const bathroomModules = [module5BA];
// Input logic. Kinda hard to follow, but allows for super ganular
// functionality given an input. Here's an example. 5050 is the
// input action to handle. The function is timeout, so we're looking
// for predetermined values here and there. When the input is 1, 
// we set the following actions to the given state, in this case,
// we turn 350 on at state 22. We ignore all other inputs, as 1
// is the only one we specify. In handling 1, we look for "timeout"
// and "block", the latter of which is optional. For "timeout" specifies
// what to do when the specified time runs out, in this case, we turn
// 350 off at state 20. "block" specifies what action states, if any,
// prevent the timeout. Oh, and we also specify a custom duration here. 
const bathroomInputActions = {
  // Motion sensor (Turn on bathroom light)
  // Turn lights on on motion. Turn off after timeout. Do not turn 
  // off lights if door is closed. 
  5050: {
    "function" : "timeout",
    1: {
      //"timeOfDayMin": 6,
      //"timeOfDayMax": 20,
      "start":{
        350: 22,
      },
      "timeout": {
        350: { 
          "duration" : 16000,
          "toState": 20
        },
      },
      "block": {
        350: {
          5150: 1,
        },
      }
    },
  },
  // Door (Timeout after it is opened.)
  // Turn lights and vent on if closed, without timeout. When door is
  // opened, do nothing, but start timeout counter to shut down lights.
  // Do not shut down lights if motion is being detected inside. 
  5150: {
    "function" : "timeout",
    0: { // Door was opened after being closed. 
      "timeout": {
        350: { 
          "duration" : 16000,
          "toState": 20
        },
        351: { 
          "duration" : 8000,
          "toState": 20
        },
      },
      "block": {
        350: {
          5050: 1,
        },
      },
    },
    1:{
      "start": {
        350: 22,
        351: 22,
      },
    }
  }
};
const bathroom = new Room(rooms.BATHROOM,bathroomModules, bathroomInputActions);

// Home
const homeRooms = [bedroom, livingRoom, bathroom];
const homeZipCode = "95051"
const home = new Home(homeRooms, homeZipCode, {}, HOME_STATUS, ACTION_STATES, publisher); // Start with no weather data. 

/*
  Initial Application Logic (executed once)
*/

// Create a timer for the open weather map API calls. 
home.updateWeather(openweathermapApiKey, doNotQueryOpenWeatherMap);
var updateWeatherInterval = setInterval(function() { home.updateWeather(openweathermapApiKey, doNotQueryOpenWeatherMap); }, updateWeatherWait);
console.log("[DEBUG] Update Weather Interval set with interval " + updateWeatherWait + ".");

// On startup, request all modules to report action states. 
// (in case of web server crash, for example)
home.requestAllActionStates();

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

// Handle requests from clients to activate modules, without having
// them know what modules are which. Does not actually toggle the
// physical action. Used to resolve desynchronization issues. 
// Ex) http://192.168.0.197/moduleVirtualToggle/1/50/1
app.get('/moduleVirtualToggle/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleVirtualToggle GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.roomId != null && req.params.roomId != "null" && req.params.actionId != null && req.params.actionId != "null" && req.params.toState != null && req.params.toState != "null"){
    var roomId = parseInt(req.params.roomId);
    var actionId = parseInt(req.params.actionId);
    var toState = parseInt(req.params.toState);
    if(roomId != null && actionId != null && toState != null){
      home.actionToggle(roomId, actionId, toState, true);
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

// Handle requests from modules to report input (actions > 5000).
// Motion detection, temperature reports, door open/close, etc.
// This is basically where all the fun (and more complicated)
// stuff happens. 
// Ex) http://192.168.0.197/moduleInput/1/5050/0
app.get('/moduleInput/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleInput GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.roomId != null && req.params.roomId != "null" && req.params.actionId != null && req.params.actionId != "null" && req.params.toState != null && req.params.toState != "null"){
    var roomId = parseInt(req.params.roomId);
    var actionId = parseInt(req.params.actionId);
    var toState = parseInt(req.params.toState);
    if(roomId != null && actionId != null && toState != null){
      // We always update the state in memory regardless of what additional
      // things we do with the input. 
      home.moduleStateUpdate(roomId, actionId, toState);
      home.moduleInput(roomId, actionId, toState)
      // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
      return res.status(200).send();
    }
  }
  return res.status(400).send();
});

// Handle requests from clients to fetch module States. This
// should be called frequently (every few seconds).
// Ex) http://192.168.0.197/actionStates
app.get('/actionStates/:lastUpdate', (req, res) => {
  //console.log("[DEBUG] /actionStates GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.lastUpdate != null && req.params.lastUpdate != "null"){
    lastUpdate = parseInt(req.params.lastUpdate)
    var response = home.actionStates(lastUpdate);
    if (response == null){
      // No change since last update. 
      return res.status(204).send();
    }
    else {
      console.log("[DEBUG] /actionStates GET request with earlier lastUpdate of " +lastUpdate +" received. Responding.");
      return res.status(200).send(response);
    }
  }
});

// Handle requests from clients to fetch general update. This
// should be called frequently (every 10 seconds or so).
// Ex) http://192.168.0.197/homeStatus
app.get('/homeStatus/:lastUpdate', (req, res) => {
  //console.log("[DEBUG] /homeStatus GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.lastUpdate != null && req.params.lastUpdate != "null"){
    lastUpdate = parseInt(req.params.lastUpdate)
    var response = home.homeStatus(lastUpdate);
    if(response == null){
      // No change since last update. 
      return res.status(204).send();
    }
    else{
      console.log("[DEBUG] /homeStatus GET request with earlier lastUpdate of " +lastUpdate +" received. Responding.");
      return res.status(200).send(response);
    }
  }
});

// Handle requests from modules upon startup, who don't know
// who they are and what they can do, and respond with
// their capabilities based on their passed in ip address. 
// Note that we expect their ips to correspond to the MAC
// of the arduino pernamently (DCHP reservation).
app.get('/moduleStartup/:ipAddress', (req, res) => {
  console.log("[DEBUG] /moduleStartup GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.ipAddress != null && req.params.ipAddress != "null"){
    var response = home.moduleUpdate(req.params.ipAddress);
    if(response){
      return res.status(200).send();
    }
    else{
      // Something went wrong - unknown IP address, perhaps? 
      return res.status(400).send();
    }
  }
});

// Start the server to listen on this port.
app.listen(listeningPort, () => {
  console.log("Project KotakeeOS is online at port: " +listeningPort);
});

