/*
    server.js
    Primary file for node.js express project KotakeeOS.
*/

const express = require("express");
const path = require("path");
const fetch = require("node-fetch");

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

// So we don't spam the server.
const cannedWeatherData = {
  "coord": {
    "lon": -121.9844,
    "lat": 37.3483
  },
  "weather": [
    {
      "id": 801,
      "main": "Clouds",
      "description": "few clouds",
      "icon": "02d"
    }
  ],
  "base": "stations",
  "main": {
    "temp": 86.68,
    "feels_like": 84.87,
    "temp_min": 59.16,
    "temp_max": 105.26,
    "pressure": 1011,
    "humidity": 33
  },
  "visibility": 10000,
  "wind": {
    "speed": 11.5,
    "deg": 330
  },
  "clouds": {
    "all": 20
  },
  "dt": 1622499910,
  "sys": {
    "type": 1,
    "id": 5845,
    "country": "US",
    "sunrise": 1622465358,
    "sunset": 1622517745
  },
  "timezone": -25200,
  "id": 0,
  "name": "Santa Clara",
  "cod": 200
};

/*
  Classes (TODO: export to another file)
*/

// Encompassing class for all rooms. Contains various attributes
// regarding the home at large. 
class Home {
  constructor(rooms, zipCode, weatherData){
    this.zipCode = zipCode;
    this.weatherData = weatherData;
    // Given array of rooms, create dictionary indexed by roomId. 
    var roomsDict = {};
    for(var i = 0; i < rooms.length; i++){
      var room = rooms[i];
      roomsDict[room.roomId] = room;
    }
    this.roomsDict = roomsDict
  }

  // Returns various general data.
  homeStatus(){
    var status = {
      modulesCount: null,
      weatherData: null,
    }

    // Get total modules. 
    var modulesCount = 0;
    for(var room in this.roomsDict){
      if(this.roomsDict.hasOwnProperty(room)){
        modulesCount = modulesCount + this.roomsDict[room].modulesCount;
      }
    }

    status.modulesCount = modulesCount;
    status.weatherData = this.weatherData;
    return status;
  }

  // Returns a room object given ID. 
  getRoom(roomId){
    if(roomId in this.roomsDict){
      return this.roomsDict[roomId];
    }
    return null;
  }

  // Given roomId, actionId, and toState, kick off the process. 
  actionToggle(roomId, actionId, toState){
    if(this.getRoom(roomId) != null){
      var room = this.getRoom(roomId);
      return room.actionToggle(actionId, toState);
    }
    else
      console.log("[ERROR] actionToggle failed! roomId " + roomId + " does not exist.");
    return null;
  }

  // Weather parsing. Called on a timer by the server. Data is
  // requested by apps whenever they want. Given the API Key that
  // is held by the server. Also given doNotQuery boolean which
  // is default to false. If given it to true, we just provide
  // bunk data to prevent spamming the server. 
  async updateWeather(openweathermapApiKey, doNotQuery = false){
    if(doNotQuery){
      this.weatherData = cannedWeatherData;
      console.log("[DEBUG] updateWeater was given doNotQuery command, so canned data was retreived.");
    }
    else {
      var apiResponse = null;
      var startTime, endTime; // We report in debug the api time.
      try{
        startTime = new Date();
        apiResponse = await fetch("http://api.openweathermap.org/data/2.5/weather?zip="+this.zipCode+"&units=imperial&appid="+openweathermapApiKey);
        endTime = new Date();
        var timeDiff = endTime - startTime;
        console.log("[DEBUG] Open Weather Map API call returned in " + timeDiff/1000 + " seconds.");
      }
      catch(error){
        console.log("[ERROR] Open Weather Map API call failed!");
      }
      if(apiResponse.status == 200){
        // Simply save the data in the home's variables. This is
        // so that we don't lose any data given to use by the API
        // and the apps can use it as they see fit (we're just paying
        // it forward). 
        var receivedData = await apiResponse.json();
        this.weatherData = receivedData;
      }
      else{
        console.log("[WARNING] Open Weather Map API call returned with status " + apiResponse.status + ".");
      }
    }
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
    var modulesCount = modules.length;
    for(var i = 0; i < modulesCount; i++){
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
    this.modulesCount = modulesCount;
    console.log("[DEBUG] Created room id " + roomId+ " with the following info:\nactionsDict " + JSON.stringify(actionsDict) + "\nmodulesDict " + JSON.stringify(modulesDict) + "\nmodulesCount " + modulesCount);
  }

  // Given action Id and toState, execute Module code if found in dict
  // AND if the state is not what is currently stored. Otherwise ignore.
  // Returns true or false depending on execution status. 
  actionToggle(actionId, toState){
    if(actionId in this.actionsDict){
      var moduleId = this.actionsDict[actionId];
      if(moduleId in this.modulesDict){
        var module = this.modulesDict[moduleId];

        return module.actionToggle(actionId, toState);
      }
      else 
        console.log("[ERROR] actionToggle failed! actionId " + actionId + " WAS found, but the saved moduleId "+ moduleId +" does not exist in room " + this.roomId + ".");
    }
    else 
      console.log("[ERROR] actionToggle failed! actionId " + actionId + " does not exist in room " + this.roomId + ".");
    return false;
  }
}

// Each module contains an array of supported actions and an ipAddress.
class Module {
  constructor(moduleId, actions, ipAddress){
    this.moduleId = moduleId;
    this.ipAddress = ipAddress;
    this.actions = actions;
    // Create a dictionary of states indexed by actionId. 
    var statesDict = {};
    for(var i = 0; i < actions.length; i++){
      statesDict[actions[i]] = 0;
    }
    this.statesDict = statesDict;
  }

  // Given an actionId, return current state. Returns null if actionId
  // does not exist for this module (not implemented).
  getActionState(actionId){
    if(this.actions.includes(actionId)){
      if(actionId in this.statesDict){
        return this.statesDict[actionId]; 
      }
      else 
        console.log("[ERROR] getActionState failed! actionId " + actionId + " is implemented, but there is no statesDict entry for module" + this.moduleId + ".");
    }
    else 
      console.log("[ERROR] getActionState failed! actionId " + actionId + " is not implemented for module " + this.moduleId + ".");
    return null;
  }

  // Given actionId and toState, sends instruction to module to change 
  // the state (if it is a valid new state). Returns true if action was
  // successful, false if something went wrong (i.e. given state is
  // actually current)
  async actionToggle(actionId, toState){
    var stateRetVal = this.getActionState(actionId);
    if(stateRetVal != null && stateRetVal != toState){ 
      // Verified that the action is correct. Execute the action.
      return await this.requestGetStateToggle(actionId, toState);
    }
    else
      console.log("[WARNING] Provided toState \'" + toState + "\' for " + actionId + " conflicts with existing state \'"+stateRetVal+"\' for module " + this.moduleId + ".");
    return false;
  }

  // Sends a request to the arduino to change to a new state. Returns
  // true if the action was succesfully received (200).
  async requestGetStateToggle(actionId, toState){
    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      //apiResponse = await fetch('http://' + this.ipAddress + '/stateToggle/' + actionId + '/' + toState); 
      apiResponse = await fetch('http://' + this.ipAddress + '/testRelay');  // TODO REMOVE ME! 
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("[DEBUG] requestGetStateToggle (module " +this.moduleId+ ") returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("[ERROR] requestGetStateToggle (module " +this.moduleId+ ") failed! Error:\n" + error);
    }
    if(apiResponse.status == 200){
      // Executed successfully!
      return true;
    }
    console.log("[WARNING] requestGetStateToggle (module " +this.moduleId+ ") returned with status " + apiResponse.status + ".");
    return false;
  }
}

/*
  Configurable Constants
*/

const listeningPort = 8080;

// Open Weather Map stuff. Use the boolean to provide canned data
// if you're just testing stuff. 
const doNotQueryOpenWeatherMap = false;
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
// Ex) http://192.168.0.197/moduleToggle?roomId=1&actionId=75&newState=1
app.get('/moduleToggle/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleToggle GET request received. Arguments: " + JSON.stringify(req.params));
  if(req.params.roomId != null && req.params.actionId != null && req.params.toState != null){
    home.actionToggle(parseInt(req.params.roomId), parseInt(req.params.actionId), parseInt(req.params.toState));
    // For now, we'll send 200 regardless of status. We won't block for actionToggle to execute. 
    return res.status(200).send();
  }
  else{
    return res.status(400).send();
  }
});

app.get('/moduleToggle', (req, res) => {
  console.log("[DEBUG] /moduleToggle GET request received. Arguments: " + JSON.stringify(req.params));
  return res.status(200).send();
});

// Handle requests from modules to update states when they have
// successfully been modified. 
// Ex) http://192.168.0.197/moduleStatusUpdate?roomId=1&actionId=75&newState=1
app.get('/moduleStateUpdate/:roomId/:actionId/:toState', (req, res) => {
  console.log("[DEBUG] /moduleStateUpdate GET request received. Arguments: " + JSON.stringify(req.params));
  return res.status(200).send();
});

// Handle requests from clients to fetch module States. This
// should be called frequently (every few seconds).
// Ex) http://192.168.0.197/moduleStates
app.get('/moduleStates', (req, res) => {
  console.log("[DEBUG] /moduleStates GET request received.");
  return res.status(200).send();
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

