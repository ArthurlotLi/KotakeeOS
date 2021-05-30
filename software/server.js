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

  // Returns various general data.
  homeStatus(){
    var status = {
      modulesCount = null,
      weatherData = null,
    }

    // Get total modules. 
    var modulesCount = 0;
    for(var room in this.rooms){
      if(rooms.hasOwnProperty(room)){
        modulesCount = modulesCount + room.modulesCount;
      }
    }

    status.modulesCount = modulesCount;
    status.weatherData = this.weatherData;
    console.log("[DEBUG] Retreived weather data: " + JSON.stringify(status));
    return status;
  }

  // Returns a room object given ID. 
  getRoom(roomId){
    if(roomId in this.roomsDict){
      return this.roomsDict[roomId];
    }
    return null;
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
    console.log("[DEBUG] Created room id " + roomId+ " with the following info:\nactionsDict " + JSON.stringify(actionsDict) + "\nmodulesDict " + JSON.stringify(modulesDict));
  }

  // Given action Id and toState, execute Module code if found in dict
  // AND if the state is not what is currently stored. Otherwise ignore.
  // Returns true or false depending on execution status. 
  actionToggle(actionId, toState){
    if(actionId in this.actionsDict){
      var moduleId = this.actionsDict[actionId];
      if(moduleId in this.modulesDict){
        var module = this.modulesDict[moduleId];

        return module.actionToggle(actionid, toState);
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
      statesDict[action[i]] = 0;
    }
    this.statesDict = statesDict;
  }

  // Given an actionId, return current state. Returns null if actionId
  // does not exist for this module (not implemented).
  getActionState(actionId){
    if(this.actions.includes(actionId)){
      if(actionId in this.statesDict){
        return this.statesDict.actionId; 
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
  actionToggle(actionId, toState){
    var stateRetVal = this.getActionState(actionId);
    if(stateRetVal){
      if(stateRetVal != toState){ 
        // Verified that the action is correct. Execute the action.
        return await requestGetStateToggle(actionId, toState);
      }
      else
        console.log("[WARNING] Provided toState \'" + toState + "\' for " + actionId + " conflicts with existing state \'"+stateRetVal+"\' for module " + this.moduleId + ".");
    }
    return false;
  }

  // Sends a request to the arduino to change to a new state. Returns
  // true if the action was succesfully received (200).
  async requestGetStateToggle(actionId, toState){
    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      apiResponse = await fetch('http://' + this.ipAddress + '/stateToggle/' + actionId + '/' + toState); 
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("[DEBUG] requestGetStateToggle (module " +this.moduleId+ ") returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("[ERROR] requestGetStateToggle (module " +this.moduleId+ ") failed!");
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

console.log("Testing bedroom actionToggle(50). " + bedroom.actionToggle(50));

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

