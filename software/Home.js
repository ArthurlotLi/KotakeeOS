/*
  Room.js
  Logic for each abstracted home (for now we just expect a single home).
*/

const fetch = require("node-fetch");

// OSX only (might break elsewhere). Used for shell commands via 
// moduleInput handling. 
const { exec } = require('child_process');

// So we don't spam the server. Used only when the argument has been
// provided on startup. 
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
  Enums to keep constant with client logic. 
*/

// TODO: Utilize the constants.js file properly instead of copy and pasting
// this all over. 
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
    this.lastUpdateHomeStatus = null;
    this.lastUpdateActionStates = null;

    // Because it's a callback! 
    this.inputTimeoutCallback = this.inputTimeoutCallback.bind(this);

    // Kill switch, essentially. So my AC doesn't run for 3 hours
    // when I don't want it to. All this does is prevent 
    // moduleToggle and moduleInput handling. 
    this.serverDisabled = false; 
    // Stop all moduleInput functionality, including timeouts
    // currently active and stuff like that. Can be enabled
    // when serverDisabled is false, but will be reset if
    // serverDisabled is set back to false. 
    this.moduleInputDisabled = false; 
  }

  // Returns various general data.
  homeStatus(lastUpdate){
    if(this.lastUpdateHomeStatus != null && lastUpdate < this.lastUpdateHomeStatus){
      var status = {
        modulesCount: null,
        weatherData: null,
        lastUpdate: this.lastUpdateHomeStatus,
        serverDisabled: this.serverDisabled, 
        moduleInputDisabled: this.moduleInputDisabled,
        moduleInput: {},
      }

      // Get total modules. 
      var modulesCount = 0;
      for(var roomId in this.roomsDict){
        if(this.roomsDict.hasOwnProperty(roomId)){
          var roomItem = this.roomsDict[roomId]; // I know, this is kinda confusing. 
          modulesCount = modulesCount + roomItem.modulesCount;
          // Append the inputActions dict to the homeStatus,
          // indexed by roomId.
          status.moduleInput[roomId] = roomItem.inputActions;
        }
      }

      status.modulesCount = modulesCount;
      status.weatherData = this.weatherData;
      return status;
    }
    else{
      return null;
    }
  }

  // Returns a room object given ID. 
  getRoom(roomId){
    if(roomId in this.roomsDict){
      return this.roomsDict[roomId];
    }
    return null;
  }

  // Returns either null or the action state of a room's 
  // action. 
  getActionState(roomId, actionId){
    var room = this.getRoom(roomId);
    if(room != null){
      return room.getActionState(actionId);
    }
    else
      console.log("[ERROR] getActionState failed! roomId " + roomId + " does not exist.");
    return null;
  }

  // Disables actionToggle and moduleInput.
  setServerDisabled(bool){
    // Sanity check
    if(bool == "1" || bool == true || bool == "true"){
      if(this.serverDisabled != true){
        this.serverDisabled = true;
        this.lastUpdateHomeStatus = new Date().getTime();
      }
    }
    else{
      if(this.serverDisabled != false){
        this.serverDisabled = false;
        this.moduleInputDisabled = false; // Reset this as well - enable the entire server. 
        this.lastUpdateHomeStatus = new Date().getTime();
      }
    }
  }

  // Disables moduleInput functionality, including active
  // timeouts. 
  setModuleInputDisabled(bool){
    // Sanity check
    if(bool == "1" || bool == true || bool == "true"){
      if(this.moduleInputDisabled != true){
        this.moduleInputDisabled = true;
        this.lastUpdateHomeStatus = new Date().getTime();
      }
    }
    else{
      if(this.moduleInputDisabled != false){
        this.moduleInputDisabled = false;
        this.lastUpdateHomeStatus = new Date().getTime();
      }
    }
  }

  // Given roomId, actionId, and toState, kick off the process. 
  // Accepts virtual boolean to specify not to execute physical
  // action to resolve desynchronization issues. 
  actionToggle(roomId, actionId, toState, virtual = false){
    var room = this.getRoom(roomId);
    if(room != null){
      if(this.serverDisabled){
        console.log("[WARN] actionToggle rejected because the server has been disabled.");
        return false;
      }
      return room.actionToggle(actionId, toState, virtual);
    }
    else
      console.log("[ERROR] actionToggle failed! roomId " + roomId + " does not exist.");
    return false;
  }

  // For the entire home, execute actions corresponding to the
  // provided state. 
  // 0 = everything turns off
  // 1 = everything turns on (party mode)
  actionToggleAll(toState){
    for(var roomId in this.roomsDict){
      if(this.roomsDict.hasOwnProperty(roomId)){
        var roomItem = this.roomsDict[roomId]; // I know, this is kinda confusing. 
        for(var actionId in roomItem.actionsDict)
        {
          var actionState = this.getActionState(roomId, actionId)
          if(parseInt(toState) == 1){
            // Turn everything that isn't on, on
            if(actionState != 1 && actionState != 12 && actionState != 22 && actionState != 32 && actionState != 107){
              this.actionSwitch(roomId, actionId, actionState);
            }
          }
          else{
            // Turn everything that isn't off, off. 
            if(actionState != 0 && actionState != 10 && actionState != 20 && actionState != 30 && actionState != 100){
              this.actionSwitch(roomId, actionId, actionState);
            }
          }        
        }
      }
    }
  }

  // In comparison to actionToggle, this function only takes
  // in the roomId + actionId and automatically changes the
  // state of something to the opposite state, given that 
  // it is a binary function. 
  //
  // A special case to note is that of LED strips - we only
  // go between off and 107 for those via this. 
  //
  // This function was migrated from clients to simplify the
  // calls necessary, reducing the need to examine the action
  // states unecessarily. 
  actionSwitch(roomId, actionId, currentState = null, ledMode = null)
  {
    // Figure out what toState is. 
    var toState = null;
    if (currentState ==  null)
      currentState = this.getActionState(roomId, actionId)
    if(currentState == null){
      console.log("[ERROR] actionSwitch attempted to switch room " + roomId + " action " +actionId+" that has no reported state!");
      return;
    }
    // Highest Lighting and Lowest Lighting are expected to be
    // numerical bounds for general category. 
    if(parseInt(actionId) <= actions.REMOTE19 && parseInt(actionId) >= actions.REMOTE1){
      if(currentState == 10) {
        toState = 12;
      }
      else if (currentState == 12){
        toState = 10;
      }
      else{
        // current state is 11 or something else. Ignore. 
        console.log("[WARNING] actionSwitch attempted to toggle action with current state of 11. Ignored.");
      }
    }
    else if(parseInt(actionId) <= actions.SWITCH5 && parseInt(actionId) >= actions.SWITCH1){
      if(currentState == 20) {
        toState = 22;
      }
      else if (currentState == 22){
        toState = 20;
      }
      else{
        // current state is 21 or something else. Ignore. 
        console.log("[WARNING] actionSwitch attempted to toggle action with current state of 21. Ignored.");
      }
    }
    else if(parseInt(actionId) <= actions.KNOB5 && parseInt(actionId) >= actions.KNOB1){
      if(currentState == 30) {
        toState = 32;
      }
      else if (currentState == 32){
        toState = 30;
      }
      else{
        // current state is 31 or something else. Ignore. 
        console.log("[WARNING] actionSwitch attempted to toggle action with current state of 31. Ignored.");
      }
    }
    else if(parseInt(actionId) <= actions.LEDSTRIP10 && parseInt(actionId) >= actions.LEDSTRIP1){
      // TODO: Right now this is hard coded. We should be able to 
      // store state numbers per combination (i.e. "2.1000: 107")
      if(ledMode == null){
        ledMode = 107;
      }
      if(currentState == 100) {
        toState = ledMode;
      }
      else if (currentState != 100){
        toState = 100;
      }
      else{
        // current state is 31 or something else. Ignore. 
        console.log("[WARNING] actionSwitch attempted to toggle action with current state of 31. Ignored.");
      }
    }
    else if (parseInt(actionId) <= actions.LIGHTING5 && parseInt(actionId) >= actions.LIGHTING1){
      if(currentState == 0){
        toState = 1;
      }
      else {
        toState = 0;
      }
    }
    // If the action is not within the list of states, ignore it. 
    else {
      console.log("[WARNING] actionSwitch attempted to toggle actionId " + String(actionId) + ", which is invalid. Ignored.");
      return;
    }

    console.log("[DEBUG] actionSwitch Attempting to toggle actionId " + actionId + " for roomId " + roomId + " to state " + toState + "." );

    // We now have the correct state. Switch it. 
    this.actionToggle(roomId, actionId, toState)
  }

  // Given roomId, actionId, and toState, use stored room 
  // variables to execute some sort of function upon input. 
  // Allows for the specification of stringInput, in which
  // case we'll use a different pool of functions. 
  moduleInput(roomId, actionId, toState, stringInput = false){
    if(this.serverDisabled){
      console.log("[WARN] moduleInput rejected because the server has been disabled.");
      return false;
    }

    // SANITY CHECKS. SO MANY SANTIY CHECKS.  
    var room = this.getRoom(roomId);
    if(room == null){
      console.log("[ERROR] moduleInput failed! roomId " + roomId + " does not exist.");
      return false;
    }
    var inputActions = room.getInputActions();
    if(inputActions == null || Object.keys(inputActions).length <= 0){
      console.log("[WARNING] moduleInput failed! roomId " + roomId + " has an empty inputActions array!");
      return false;
    }
    var actionInputActions = inputActions[actionId]; // A funny name, I know. 
    if(actionInputActions == null){
      console.log("[WARNING] moduleInput failed! roomId " + roomId + " does not have an inputActions entry for actionId " +actionId+"!");
      return false;
    }
    var inputFunction = actionInputActions["function"]
    if(inputFunction == null){
      console.log("[WARNING] moduleInput failed! roomId " + roomId + " inputActions entry for actionId " +actionId+" does not have a function definition!");
      return false;
    }

    // Note we only stop here in the case of disabled module
    // input because we want to let commands through. 
    if(this.moduleInputDisabled && inputFunction != "command"){
      console.log("[WARN] moduleInput rejected because module input has been disabled.");
      return false;
    }

    // Now we handle things differently based on what state
    // info type we got. 
    if(stringInput){
      // Handle string input. 
      switch(inputFunction){
        case "temperatureOnOff":
          return this.moduleInputTemperatureOnOff(roomId, actionId, toState, actionInputActions, room);
        case "humidityOnOff":
          return this.moduleInputHumidityOnOff(roomId, actionId, toState, actionInputActions, room);
        default:
          console.log("[ERROR] moduleInput failed! roomId " + roomId + " inputActions entry for actionId " +actionId+" specifies a function that does not exist!");
          return false;
      }
    }
    else{
      // Handle state input. 
      var stateInputActions = actionInputActions[toState]
      if(stateInputActions == null){
        console.log("[WARNING] moduleInput failed! roomId " + roomId + " inputActions entry for actionId " +actionId+" does not have a state "+toState+" definition!");
        return false;
      }

      // If we survived the great filter, let's act depending 
      // on the function given.
      switch(inputFunction){
        case "timeout":
          return this.moduleInputTimeout(roomId, actionId, toState, stateInputActions, room);
        case "command":
          return this.moduleExecuteCommand(roomId, actionId, toState, stateInputActions);
        default:
          console.log("[ERROR] moduleInput failed! roomId " + roomId + " inputActions entry for actionId " +actionId+" specifies a function that does not exist!");
          return false;
      }
    }
  }

  // A fun thing. Plays a sound.
  moduleExecuteCommand(roomId, actionId, toState, stateInputActions){
    if(this.moduleInputDisabled){
      console.log("[WARN] moduleExecuteCommand rejected because module input has been disabled.");
      return false;
    }

    var block = stateInputActions["block"];
    var command = stateInputActions["command"];
    // Works only in OSX.
    if(block != null){
      for(var blockActionId in block){
        var blockActionIdState = block[blockActionId];
        var actionState = this.getActionState(roomId, blockActionId);
        if(actionState == blockActionIdState){
          // Execute command blocked successfully. 
          console.log("[DEBUG] moduleExecuteCommand actionState of blockActionId " + blockActionId + " is EQUAL to blockActionIdState " + blockActionIdState + ". Not executing command " + command + ".");
          return;
        }
      }
    }
    console.log("[DEBUG] Executing command: " + command);
    exec(command, null)
  }

  // Given a toState string that presents temp and humidity
  // (Ex) 27.70_42.00), turn something on/off Note that we 
  // convert from celsius here. 
  moduleInputTemperatureOnOff(roomId, actionId, toState, actionInputActions, room){
    if(this.moduleInputDisabled){
      console.log("[WARN] moduleInputTemperatureOnOff rejected because module input has been disabled.");
      return false;
    }

    // Expect mandatory fields "onHeat", "offHeat", "onActions", "offActions".
    // The latter two may be blank, but still must be here. 
    var actionStateString = String(toState);
    var tempInfo = actionStateString.split("_");
    if(tempInfo.length < 2){
      console.log("[ERROR] moduleInputTemperatureOnOff Received an invalid toState! roomId " + roomId + " inputActions entry for actionId " +actionId+".");
      return false;
    }
    // Convert temp to F from C
    var currentTemp = parseFloat(tempInfo[0]);
    currentTemp = parseInt(((currentTemp * 1.8) +32).toFixed(0));

    // Parse mandatory fields 
    var onHeat = actionInputActions["onHeat"];
    var offHeat = actionInputActions["offHeat"];
    var onActions = actionInputActions["onActions"];
    var offActions = actionInputActions["offActions"];
    if(onHeat == null || offHeat == null || onActions == null || offActions == null){
      console.log("[ERROR] moduleInputTemperatureOnOff parsed invalid instructions! roomId " + roomId + " inputActions entry for actionId " +actionId+".");
      return false;
    }

    // Sanity checked. 
    if(currentTemp >= onHeat){
      // Execute onActions. 
      for (var actionId in onActions){
        this.actionToggle(roomId, actionId, onActions[actionId]);
      }
    }
    else if(currentTemp <= offHeat){
      // Execute onActions. 
      for (var actionId in offActions){
        this.actionToggle(roomId, actionId, offActions[actionId]);
      }
    }
    // Otherwise we're within the grey area (if it exists). Do nothing. 
  }

  moduleInputHumidityOnOff(roomId, actionId, toState, actionInputActions, room){
    if(this.moduleInputDisabled){
      console.log("[WARN] moduleInputHumidityOnOff rejected because module input has been disabled.");
      return false;
    }

    // Expect mandatory fields "onHum", "offHum", "onActions", "offActions".
    // The latter two may be blank, but still must be here. 
    var actionStateString = String(toState);
    var tempInfo = actionStateString.split("_");
    if(tempInfo.length < 2){
      console.log("[ERROR] moduleInputHumidityOnOff Received an invalid toState! roomId " + roomId + " inputActions entry for actionId " +actionId+".");
      return false;
    }
    var currentHum = parseFloat(tempInfo[1]);
    currentHum = parseInt(currentHum.toFixed(0));

    // Parse mandatory fields 
    var onHum = actionInputActions["onHum"];
    var offHum = actionInputActions["offHum"];
    var onActions = actionInputActions["onActions"];
    var offActions = actionInputActions["offActions"];
    if(onHum == null || offHum == null || onActions == null || offActions == null){
      console.log("[ERROR] moduleInputHumidityOnOff parsed invalid instructions! roomId " + roomId + " inputActions entry for actionId " +actionId+".");
      return false;
    }

    // Sanity checked. 
    if(currentHum >= onHum){
      // Execute onActions. 
      for (var actionId in onActions){
        this.actionToggle(roomId, actionId, onActions[actionId]);
      }
    }
    else if(currentHum <= offHum){
      // Execute onActions. 
      for (var actionId in offActions){
        this.actionToggle(roomId, actionId, offActions[actionId]);
      }
    }
    // Otherwise we're within the grey area (if it exists). Do nothing. 
  }

  // Handle timeout input request. We expect to be completely
  // sane at this point, having gone through the moduleInput
  // funnel. We handle inputs with a number of keywords, some 
  // optional some not, listed here. 
  //
  // Handle timeouts - execute certain actions at the start
  // and "timeout". A "timeout" is defined as there having 
  // been no further reports from the specified actionId
  // and roomId between the time of start and time after 
  // timeout duration. If there was, the timeout expires 
  // with no action taken.
  //
  // Additionally, there is the option to block a timeout action
  // even if a valid timeout event is detected - a sort of 
  // override. 
  //
  // Expects usual trio from get request plus stateInputActions
  // from the room actionInput object. 
  moduleInputTimeout(roomId, actionId, toState, stateInputActions, room){
    if(this.moduleInputDisabled){
      console.log("[WARN] moduleInputTimeout rejected because module input has been disabled.");
      return false;
    }

    // Given the stateInputActions value, kick off the timeout
    // functionality depending on what attributes are present.

    // Optional attributes
    // Start - actions to do immediately upon timeout start. 
    var startDict = stateInputActions["start"];
    if(startDict != null){
      for(var startActionId in startDict){
        var startActionIdDict = startDict[startActionId];
        // Verify time requirements if they are present. 
        if(startActionIdDict["timeBounds"] == null || this.checkTimeRequirements(startActionIdDict["timeBounds"])){
          this.actionToggle(roomId, startActionId, startActionIdDict["toState"]);
        }
      }
    }

    // Block - optional. Gets thrown into inputTimeoutCallback. 
    var blockDict = stateInputActions["block"];

    // Timeout - actions to do once the timeout expires start. 
    var timeoutDict = stateInputActions["timeout"];
    if(timeoutDict != null){
      for(var timeoutActionId in timeoutDict){
        var timeoutActionIdDict = timeoutDict[timeoutActionId];
        // Verify time requirements if they are present. 
        if(timeoutActionIdDict["timeBounds"] == null || this.checkTimeRequirements(timeoutActionIdDict["timeBounds"])){
          var timeoutActionIdToState = timeoutActionIdDict['toState'];

          // Mandatory attributes
          var duration = timeoutActionIdDict["duration"];
          if(duration == null){
            console.log("[ERROR] moduleInputTimeout failed! roomId " + roomId + " inputActions entry for actionId " +actionId+" and timeoutActionId " +timeoutActionIdDict+ " does not have a duration for state " +toState +"!");
            return false;
          }

          var currentTime = new Date();
          // Save it in the room object. 
          room.insertIntoInputActionsTimeoutTimes(actionId, currentTime);
          // Create timeout callback with read duration plus arguments. 
          setTimeout(this.inputTimeoutCallback, duration, currentTime, actionId, roomId, timeoutActionId, timeoutActionIdToState, room, blockDict);
        }
      }
    }
  }

  // Helper function, given an array that is a multiple a of 4
  // structured as follows: [minHr, minMin,maxHr, maxMin (repeated)],
  // will return true or false if the current time lands within
  // an acceptable time. 
  checkTimeRequirements(timeBounds){
    var date = new Date();
    var currentHrs = date.getHours(); // 0 - 23
    var currentMins = date.getMinutes(); // 0 - 59

    if(timeBounds.length%4 != 0){
      console.log("[ERROR] checkTimeRequirements failed - given timeBounds array was not a multiple of 4!");
      return null;
    }

    var numBounds = timeBounds.length/4;
    for(var i = 0; i < numBounds; i++){
      var timeMinHr = parseInt(timeBounds[i*4]);
      var timeMinMin = parseInt(timeBounds[i*4+1]);
      var timeMaxHr = parseInt(timeBounds[i*4+2]);
      var timeMaxMin = parseInt(timeBounds[i*4+3]);

      //console.log("[DEBUG] Checking time requirements " + timeMaxHr + ", " + timeMaxMin + ", " + timeMinHr + ", " + timeMinMin + " with current hours " + currentHrs + " and minutes " + currentMins + ".");

      if((currentHrs < timeMaxHr && currentHrs > timeMinHr) || 
      (currentHrs == timeMaxHr && currentMins <= timeMaxMin) ||
      (currentHrs == timeMinHr && currentMins >= timeMinMin)){
        //console.log("[DEBUG] ...Passed!");
        return true;
      }
    }
    return false;
  }

  // Function called on at timeout. Expects the current time at time 
  // of timeout call, actionId and roomId, 
  inputTimeoutCallback(timeOfTimeoutMotion, actionId, roomId, actionIdToTrigger, actionToggleState, room, blockDict){
    if(this.moduleInputDisabled){
      console.log("[WARN] inputTimeoutCallback rejected because module input has been disabled.");
      return false;
    }

    var timeOfLastActionMotion = room.getInputActionsTimeoutTimes()[actionId];
    // Check if we've received no more inputs for this action since 
    // timeOfTimeoutMotion. 
    if(timeOfLastActionMotion == null || timeOfLastActionMotion == timeOfTimeoutMotion){

      // Check the blockDict before we execute the timeout action. 
      if(blockDict != null){
        //console.log("[DEBUG] inputTimeoutCallback parsing blockDict " + JSON.stringify(blockDict))
        for(var subjectActionId in blockDict){
          var subjectDict = blockDict[subjectActionId];
          if(parseInt(subjectActionId) == parseInt(actionIdToTrigger))
          {
            for(var blockActionId in subjectDict){
              var blockActionIdState = subjectDict[blockActionId];
              // Get the state of that particular module action. 
              var actionState = this.getActionState(roomId, blockActionId);
              //console.log("inputTimeoutCallback testing: actionState is " + actionState + ", blockActonIdState is " + blockActionIdState + ", subjectActionId is " + subjectActionId + ", and actionIdToTrigger is " + actionIdToTrigger);
              if(actionState != null && parseInt(actionState) == parseInt(blockActionIdState) ){
                console.log("[DEBUG] inputTimeoutCallback actionState of blockActionId " + blockActionId + " is EQUAL to blockActionIdState " + blockActionIdState + ". Not executing valid timeout.");
                return;
              }
            }
          }
        }
      }
      console.log("[DEBUG] inputTimeoutCallback timeOfTimeoutMotion is null or equal to timeOfLastMotion for room " + roomId + " action " + actionId);
      // If we haven't seen any more movement between the time the timout
      // was started and now.
      this.actionToggle(roomId, actionIdToTrigger, actionToggleState);
      // We'll reset the action state of the input state to 0 upon 
      // successful timeout. 
      this.moduleStateUpdate(roomId, actionId, 0);
    }
  }

  // Given a roomId and a new JSON object, replace the room's
  // inputActions. 
  async moduleInputModify(roomId, newModuleInput){
    var room = this.getRoom(roomId);
    if(room != null){
      if(newModuleInput != null){
        room.setInputActions(newModuleInput);
        // This will change homeStatus, so let's update our clients. 
        this.lastUpdateHomeStatus = new Date().getTime();
      }
      else{
        console.log("[ERROR] moduleInputModify failed! newModuleInput is null.");
      }
    }
    else
      console.log("[ERROR] moduleInputModify failed! roomId " + roomId + " does not exist.");
    return null;
  }

  // Given roomId, actionId, and toState, update the state of 
  // a module. 
  async moduleStateUpdate(roomId, actionId, toState){
    if(this.getRoom(roomId) != null){
      var room = this.getRoom(roomId);
      var updateStatus = await room.moduleStateUpdate(actionId, toState);
      if(updateStatus){
        this.lastUpdateActionStates = new Date().getTime();
        console.log("[DEBUG] moduleStateUpdate succeeded. New lastUpdateActionStates is: " + this.lastUpdateActionStates + ".");
      }
    }
    else
      console.log("[ERROR] moduleStateUpdate failed! roomId " + roomId + " does not exist.");
    return false;
  }
  // Return states of all modules in system, identifying each
  // action by actionId, seperated by roomId. This is expected
  // to be a frequently called function on timers by all clients.
  // The end JSON object should have three layers. 
  actionStates(lastUpdate){
    if(this.lastUpdateActionStates != null && lastUpdate < this.lastUpdateActionStates){
      var response = {
        lastUpdate: this.lastUpdateActionStates,
      }
      for(var room in this.roomsDict){
        if(this.roomsDict.hasOwnProperty(room)){
          // For each room, request actionStates.
          response[room] = this.roomsDict[room].actionStates();
        }
      }
      return response;
    }
    else{
      return null;
    }
  }

  //Requests all modules to report action states to web server.
  requestAllActionStates(){
    for(var room in this.roomsDict){
      if(this.roomsDict.hasOwnProperty(room)){
        // For each room, requestAllActionStates.
        this.roomsDict[room].requestAllActionStates();
      }
    }
  }

  // Given the ipAddress of a module, find that module and 
  // tell it its expected capabilities + pin numbers. 
  async moduleUpdate(ipAddress){
    for(var room in this.roomsDict){
      if(this.roomsDict.hasOwnProperty(room)){
        // For each room, feed them the ip address until one
        // room replies with true. 
        var foundModule = this.roomsDict[room].getModule(ipAddress);
        if(foundModule != null ){
          // Then, request that the room request the module be
          // informed of its capabiltiies. 
          return foundModule.moduleUpdate();
        }
      }
    }
    console.log("[ERROR] moduleUpdate failed! A module with " + ipAddress + " does not exist.");
    return false;
  }

  // Weather parsing. Called on a timer by the server. Data is
  // requested by apps whenever they want. Given the API Key that
  // is held by the server. Also given doNotQuery boolean which
  // is default to false. If given it to true, we just provide
  // bunk data to prevent spamming the server. 
  async updateWeather(openweathermapApiKey, doNotQuery = false){
    if(doNotQuery){
      this.weatherData = cannedWeatherData;
      this.lastUpdateHomeStatus = new Date().getTime();
      console.log("[DEBUG] updateWeater was given doNotQuery command, so canned data was retreived. New lastUpdateHomeStatus is: " + this.lastUpdateHomeStatus + ".");
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
        this.lastUpdateHomeStatus = new Date().getTime();
        console.log("[DEBUG] updateWeather succeeded. New lastUpdateHomeStatus is: " + this.lastUpdateHomeStatus + ".");
      }
      else{
        console.log("[WARNING] Open Weather Map API call returned with status " + apiResponse.status + ".");
      }
    }
  }
}

module.exports = Home;