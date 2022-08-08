/*
    server.js
    Primary file for node.js express project KotakeeOS.
*/

const express = require("express");
const path = require("path");
const fetch = require("node-fetch");
const findPort = require('find-open-port');

const Home = require("./Home.js");
const Room = require("./Room.js");
const Module = require("./Module.js");

// OSX only (might break elsewhere). Used for shell commands via 
// moduleInput handling. 
const { exec } = require('child_process');

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
  KNOB1: 450,
  KNOB2: 451,
  KNOB3: 452,
  KNOB4: 453,
  KNOB5: 454,
  // These get handled rather differently from other actions.
  // (toState represents different pre-programmed modes.)
  LEDSTRIP1: 1000,
  LEDSTRIP2: 1001,
  LEDSTRIP3: 1002,
  LEDSTRIP4: 1003,
  LEDSTRIP5: 1004,
  LEDSTRIP6: 1005,
  LEDSTRIP7: 1006,
  LEDSTRIP8: 1007,
  LEDSTRIP9: 1008,
  LEDSTRIP10: 1009,
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
  ADMIN1: 5350, // Not meant to be connected to anything physical. For interactions between clients and webserver.
  ADMIN2: 5351,
  ADMIN3: 5352,
  ADMIN4: 5353,
  ADMIN5: 5354,
}

// Bedroom IDs - Should be kept constant betweeen this and client
// application logic. 
const rooms = {
  BEDROOM: 1,
  LIVINGROOM: 2,
  BATHROOM: 3,
}

// End enums

/*
  Configurable Constants + app creation
*/

const listeningPort = 8080;

var pianoPort = null;

// Open Weather Map stuff. Use the boolean to provide canned data
// if you're just testing stuff. (If you're restarting the app
// over and over again, you'll want this boolean set to true.)
var doNotQueryOpenWeatherMap = false;

// Get arguments (currently only for query map.)
const args = process.argv.slice(2);
if(args.length > 0){
  // If we have ANYTHING, don't query the API. That's good enough for now. 
  doNotQueryOpenWeatherMap = true; 
}

const openweathermapApiKey = "47ad011b1eb24c37b31f2805da701cc4";
const updateWeatherWait = 120000; // Once every 2 minutes (1 min = 60000 ms)

// Used to kick off the piano subprocess (requres arguments to be added
// during runtime.)
const subprocessUsbPianoPlayerCommand = "python3 ./subprocesses/usb_piano_player/usb_piano_player.py"

// Create the app
const app = express();

// Satellite Servers
// TODO: we could really flush this out and add more than one server. These
// could (should) be an abstracted class. 
const satellite1 = "192.168.0.114:8080"

// When adding modules, create module object and add to room's
// array of Modules. 

// Arduino 1 Bedroom 
const module1BRId = 1; // Internal server use only. 
const module1BRRoomId = rooms.BEDROOM; 
const module1BRActions = [actions.LIGHTING1, actions.TEMP1, actions.LEDSTRIP1];
const module1BRPins = [12, 16, "14.060"];
const module1BRIpAddress = "192.168.0.186";
const module1BR = new Module(module1BRId, module1BRRoomId, module1BRActions, module1BRPins, module1BRIpAddress);

// Arduino 2 Living Room
const module2LRId = 2; // Internal server use only. 
const module2LRRoomId = rooms.LIVINGROOM; 
const module2LRActions = [actions.LIGHTING1, actions.DOOR1];
const module2LRPins = [12, 2];
const module2LRIpAddress = "192.168.0.160";
const module2LR = new Module(module2LRId, module2LRRoomId, module2LRActions, module2LRPins, module2LRIpAddress);

// Arduino 3 Living Room
const module3LRId = 3; // Internal server use only. 
const module3LRRoomId = rooms.LIVINGROOM; 
const module3LRActions = [actions.REMOTE1, actions.ADMIN1, actions.ADMIN2, actions.LIGHTING2, actions.TEMP1, actions.LIGHTING3, actions.ADMIN3]; // Admin action that is inert for this module. 
const module3LRPins = [12, 0, 0, 2, 16, 3, 0];
const module3LRIpAddress = "192.168.0.100";
const module3LR = new Module(module3LRId, module3LRRoomId, module3LRActions, module3LRPins, module3LRIpAddress);

// Arduino 4 Living Room
const module4LRId = 4; // Internal server use only. 
const module4LRRoomId = rooms.LIVINGROOM; 
const module4LRActions = [actions.REMOTE2, actions.SWITCH1, actions.MOTION1, actions.LEDSTRIP1, actions.TEMP2];
const module4LRPins = [12, "10.11", 8, "14.060", 15];
const module4LRIpAddress = "192.168.0.144";
const module4LR = new Module(module4LRId, module4LRRoomId, module4LRActions, module4LRPins, module4LRIpAddress);

// Arduino 5 Bathroom
const module5BAId = 5; // Internal server use only. 
const module5BARoomId = rooms.BATHROOM; 
const module5BAActions = [actions.SWITCH1, actions.SWITCH2, actions.MOTION1, actions.LIGHTING1, actions.DOOR1, actions.TEMP1];
const module5BAPins = ["10.11", 6.9, 8, 14, 2, 16];
const module5BAIpAddress = "192.168.0.101";
const module5BA = new Module(module5BAId, module5BARoomId, module5BAActions, module5BAPins, module5BAIpAddress);

// Arduino 6 LR
const module6LRId = 6; // Internal server use only. 
const module6LRRoomId = rooms.LIVINGROOM; 
const module6LRActions = [actions.KNOB1];
const module6LRPins = [12];
const module6LRIpAddress = "192.168.0.198";
const module6LR = new Module(module6LRId, module6LRRoomId, module6LRActions, module6LRPins, module6LRIpAddress);

const module7LRId = 7; // Internal server use only. 
const module7LRRoomId = rooms.LIVINGROOM; 
//const module7LRActions = [actions.KNOB1];
//const module7LRPins = [12];
const module7LRActions = [actions.REMOTE3];
const module7LRPins = [12];
const module7LRIpAddress = "192.168.0.146";
const module7LR = new Module(module7LRId, module7LRRoomId, module7LRActions, module7LRPins, module7LRIpAddress);

// Rooms (add objects here)
const bedroomModules = [module1BR];
const bedroomInputActions = {};
const bedroom = new Room(rooms.BEDROOM,bedroomModules, bedroomInputActions);

const livingRoomModules = [module2LR, module3LR, module4LR, module7LR, module6LR];
const livingRoomInputActionsTimeBounds = {
  // MinHr, MinMin, MaxHr, MaxMin
  350: [3, 05, 17, 50], // These arrays must be multiples of 4. 
}
const airConditioningOn = 81; // How hot it must be to turn on the air conditioner. 
const airConditioningOff = 79; // How hot it must be to turn off the air conditioner. 
const livingRoomInputActions = {
  5251: { // Temperature input
    "function":"temperatureOnOff",
    "onHeat":airConditioningOn,
    "offHeat": airConditioningOff,
    "onActions": {
      450: 32,
    },
    "offActions":{
      450: 30,
    }
  },
  5050: {
    "function" : "timeout",
    1: {
      "start":{
        350: {
          "toState": 22,
          "timeBounds": livingRoomInputActionsTimeBounds[350],
        },
      },
      "timeout": {
        350: { 
          "duration" : 60000,
          "toState": 20,
          "timeBounds": livingRoomInputActionsTimeBounds[350],
        },
      },
    },
  },
  5150:{
    "function":"command",
    1: { // When the door is closed. 
      "command" : "afplay ./assets/testJingle.mp3"
    }
  },
  5350:{
    "function":"command",
    1: { // Admin command of 1 from clients. 
      "command" : "python3 ../speechServer/hotwordTriggerWord.py 13112",
      // Don't start the server if the light is on, signaling that the server is already on.
      // Not the greatest solution (leaves gaps and isn't explicit) but it works for now.
      // Note this is all experimental. 
      "block": {
        51: 1,
      }
    }
  },
  5351:{
    "function":"command",
    1: { // Admin command of 1 from clients. 
      "command" : "python3 ../speechServer/hotwordNone.py",
      // Don't start the server if the light is on, signaling that the server is already on.
      // Not the greatest solution (leaves gaps and isn't explicit) but it works for now.
      // Note this is all experimental. 
      "block": {
        51: 1,
      }
    }
  },
  5352:{
    "function":"command",
    1: { // When the speech server is triggered. 
      "command" : "afplay ./assets/testChime.wav"
    }
  },
}
const livingRoom = new Room(rooms.LIVINGROOM,livingRoomModules, livingRoomInputActions);

const bathroomModules = [module5BA];
const bathroomInputActionsTimeBounds = {
  // MinHr, MinMin, MaxHr, MaxMin
  350: [3, 05, 17, 50], // These arrays must be multiples of 4. 
  50: [17, 51, 23, 59, 0, 0, 3, 04],
}
const fanOnHumidity = 85;
const fanOffHumidity = 84; // Not used. 
const bathroomInputActions = {
  // If the humidity is too high, turn on the fan automatically. 
  5250: { // Temperature input
    "function":"humidityOnOff",
    "onHum":fanOnHumidity,
    "offHum": fanOffHumidity,
    "onActions": {
      351: 22,
    },
    "offActions":{}
  },
  // Motion sensor (Turn on bathroom light)
  // Turn lights on on motion. Turn off after timeout. Do not turn 
  // off lights if door is closed. 
  5050: {
    "function" : "timeout",
    1: {
      "start":{
        350: {
          "toState": 22,
          "timeBounds": bathroomInputActionsTimeBounds[350]
        },
        50: {
          "toState": 1,
          "timeBounds": bathroomInputActionsTimeBounds[50]
        },
      },
      "timeout": {
        350: { 
          "duration" : 150000,
          "toState": 20,
          "timeBounds": bathroomInputActionsTimeBounds[350]
        },
        50: {
          "duration" : 20000,
          "toState": 0,
          "timeBounds": bathroomInputActionsTimeBounds[50]
        },
      },
      "block": {
        350: {
          5150: 1,
        },
        50: {
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
          "duration" : 150000,
          "toState": 20,
          "timeBounds": bathroomInputActionsTimeBounds[350]
        },
        50: {
          "duration" : 20000,
          "toState": 0,
          "timeBounds": bathroomInputActionsTimeBounds[50]
        },
        // Vent fan
        351: { 
          "duration" : 80000,
          "toState": 20
        },
      },
      "block": {
        350: {
          5050: 1,
        },
        351: { // Block if you yourself have been turned back on (door closed again)
          5150: 1,
        },
      },
    },
    1:{
      "start": {
        350: { // Turn on the light 
          "toState": 22,
          "timeBounds": bathroomInputActionsTimeBounds[350]
        },
        // Red light First half of night
        50: {
          "toState": 1,
          "timeBounds": bathroomInputActionsTimeBounds[50]
        },
        351: { // Turn on the vent
          "toState": 22,
        },
      },
    }
  }
};
const bathroom = new Room(rooms.BATHROOM,bathroomModules, bathroomInputActions);

// Home
const homeRooms = [bedroom, livingRoom, bathroom];
const homeZipCode = "95051"
const home = new Home(homeRooms, homeZipCode, {}); // Start with no weather data. 

/*
  Initial Application Logic (executed once)
*/

// Create a timer for the open weather map API calls. 
home.updateWeather(openweathermapApiKey, doNotQueryOpenWeatherMap);
var updateWeatherInterval = setInterval(function() { 
  home.updateWeather(openweathermapApiKey, doNotQueryOpenWeatherMap); 
  }, updateWeatherWait);
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

// To support parsing of JSON objects in both body and url. 
app.use(express.json({limit: '150mb', extended: true}));
app.use(express.urlencoded({
  extended: true
}));

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
      // things we do with the input. Note strings are also valid here. 
      home.moduleStateUpdate(roomId, actionId, toState);
      home.moduleInput(roomId, actionId, toState)
      // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
      return res.status(200).send();
    }
  }
  return res.status(400).send();
});

// Handle requests from modules to report input (actions > 5000)
// that is not a state update. This is useful for stuff like
// temp readouts (Ex) toState = "27.50_41.10")
// Ex) http://192.168.0.197/moduleInputString/1/5250/27.50_41.10
app.get('/moduleInputString/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleInputString GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.roomId != null && req.params.roomId != "null" && req.params.actionId != null && req.params.actionId != "null" && req.params.toState != null && req.params.toState != "null"){
    var roomId = parseInt(req.params.roomId);
    var actionId = parseInt(req.params.actionId);
    var toState = req.params.toState; // We expect this to be a string.
    if(roomId != null && actionId != null && toState != null){
      // We always update the state in memory regardless of what additional
      // things we do with the input. Note strings are also valid here. 
      home.moduleStateUpdate(roomId, actionId, toState);
      // Handle this input with explicit true flag for stringInput.
      home.moduleInput(roomId, actionId, toState, true)
      // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
      return res.status(200).send();
    }
  }
  return res.status(400).send();
});

// Handle requests from clients to modify the moduleInput dicts of
// specific rooms. For example, changing a "thermostat" by modifiying
// the value of onHeat for a specific temp module. 
app.post('/moduleInputModify', (req, res) => {
  console.log("[DEBUG] /moduleInputModify POST request received. Body: " + JSON.stringify(req.body));
  if(req.body.roomId != null && req.body.roomId != "null" 
  && req.body.newModuleInput != null && req.body.newModuleInput != "null"){
    var roomId = parseInt(req.body.roomId);
    var newModuleInput = req.body.newModuleInput;
    if(roomId != null && newModuleInput != null){
      home.moduleInputModify(roomId, newModuleInput);
      return res.status(200).send();
    }
    return res.status(400).send();
  }
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

app.get('/serverDisabled/:bool', (req, res) => {
  console.log("[DEBUG] /serverDisabled GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.bool != null && req.params.bool != "null"){
    home.setServerDisabled(req.params.bool);
    return res.status(200).send();
  }
});

app.get('/moduleInputDisabled/:bool', (req, res) => {
  console.log("[DEBUG] /moduleInputDisabled GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.bool != null && req.params.bool != "null"){
    home.setModuleInputDisabled(req.params.bool);
    return res.status(200).send();
  }
});

// Handle requests to either turn everything off or on. 
// 1 or 0 is synonymous with what you'd expect.
// Ex) http://192.168.0.197/moduleToggleAll/1
app.get('/moduleToggleAll/:toState', (req, res) => {
  console.log("[DEBUG] /moduleToggleAll GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.toState != null && req.params.toState != "null"){
    var toState = parseInt(req.params.toState);
    if(toState != null){
      home.actionToggleAll(toState);
      // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
      return res.status(200).send();
    }
  }
  return res.status(400).send();
});

// Handle requests from clients to switch modules without
// explicitly stating the desired final state. 
// Ex) http://192.168.0.197/moduleSwitch/1/50
app.get('/moduleSwitch/:roomId/:actionId', (req, res) => {
  console.log("[DEBUG] /moduleSwitch GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.roomId != null && req.params.roomId != "null" && req.params.actionId != null && req.params.actionId != "null"){
    var roomId = parseInt(req.params.roomId);
    var actionId = parseInt(req.params.actionId);
    if(roomId != null && actionId != null){
      home.actionSwitch(roomId, actionId);
      // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
      return res.status(200).send();
    }
  }
  return res.status(400).send();
});

app.post('/pianoPlayMidi', (req, res) => {
  console.log("[DEBUG] /pianoPlayMidi POST request received. Body: " + JSON.stringify(req.body));
  if(pianoPort== null){
    return res.status(400).send();
  }
  if(req.body.song_name != null && req.body.midi_contents != "null"){
    var song_name = req.body.song_name;
    var midi_contents = req.body.midi_contents;
    if(song_name != null && midi_contents != null){

      const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ "song_name": song_name, "midi_contents" : midi_contents })
      };
      fetch(`http://localhost:${pianoPort}/startSong`, requestOptions);
      
      return res.status(200).send();
    }
    return res.status(400).send();
  }
});

app.get('/pianoStopMidi', (req, res) => {
  console.log("[DEBUG] /pianoStopMidi GET request received.");
  if(pianoPort== null){
    return res.status(400).send();
  }
  fetch(`http://localhost:${pianoPort}/stopSong`);
  return res.status(200).send();
});

// TODO: Abstract this so that we could potentially have 
// multiple satellites. 
app.get('/toggleHotwordNoneSatellite', (req, res) => {
  console.log("[DEBUG] /toggleHotwordNoneSatellite GET request received.");
  fetch("http://" + satellite1 + "/toggleHotwordNone");
  return res.status(200).send();
});
app.get('/toggleSpeechServerSatellite', (req, res) => {
  console.log("[DEBUG] /toggleSpeechServerSatellite GET request received.");
  fetch("http://" + satellite1 + "/toggleSpeechServer");
  return res.status(200).send();
});

// Execute subprocess to play the piano song via USB. 
findPort().then(port => {
  pianoPort = port;
  let command = subprocessUsbPianoPlayerCommand + " " + port
  console.log("[DEBUG] Creating Usb Piano Player subprocess with command: " + command);
  exec(command)
});

// Start the server to listen on this port.
app.listen(listeningPort, () => {
  console.log("Project KotakeeOS is online at port: " +listeningPort);
});

