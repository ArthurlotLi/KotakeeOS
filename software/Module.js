/*
  Module.js
  Logic for each abstracted module and its lower level logic to
  interface with the arduino modules themselves. 
*/

const fetch = require("node-fetch");

// Each module contains an array of supported actions and an ipAddress.
class Module {
  constructor(moduleId, roomId, actions, pins, ipAddress){
    this.moduleId = moduleId;
    this.roomId = roomId;
    this.ipAddress = ipAddress;
    this.actions = actions;
    this.pins = pins; // like-indexed array accompanying actions array. 
    // Create a dictionary of states indexed by actionId. 
    var statesDict = {};
    for(var i = 0; i < actions.length; i++){
      statesDict[actions[i]] = -999; // uninitialized. 
    }
    this.statesDict = statesDict;
  }

  // Return ipAddress.
  getIpAddress(){
    return this.ipAddress;
  }

  // Given an actionId, return current state. Returns null if actionId
  // does not exist for this module (not implemented).
  getActionState(actionId){
    if(this.actions.includes(actionId)){
      if(actionId in this.statesDict){
        return this.statesDict[actionId]; 
      }
      else 
        console.log("[ERROR] getActionState failed! actionId " + actionId + " is implemented, but there is no statesDict entry for module" + this.ipAddress + ".");
    }
    else 
      console.log("[ERROR] getActionState failed! actionId " + actionId + " is not implemented for module " + this.ipAddress + ".");
    return false;
  }

  // Set the state of a specific action. Return true if no fatal
  // errors occur. 
  setActionState(actionId, toState){
    if(this.actions.includes(actionId)){
      if(actionId in this.statesDict){
        var currentState = this.statesDict[actionId];
        if(currentState != toState) {
          this.statesDict[actionId] = toState; 
          console.log("[DEBUG] setActionState overwriting state of " + currentState + " with " + toState + " for actionid " + actionId + " for module " + this.ipAddress + ".");
          return true;
        }
        else {
          console.log("[DEBUG] setActionState state " + currentState + " is equivalent to gotten state "+ toState + " for actionid " + actionId + " for module  " + this.ipAddress + ". Ignoring request.");
        }
      }
      else 
        console.log("[ERROR] setActionState failed! actionId " + actionId + " is implemented, but there is no statesDict entry for module" + this.ipAddress + ".");
    }
    else 
      console.log("[ERROR] setActionState failed! actionId " + actionId + " is not implemented for module " + this.ipAddress + ".");
    return false;
  }

  // Given actionId and toState, sends instruction to module to change 
  // the state (if it is a valid new state). Returns true if action was
  // successful, false if something went wrong (i.e. given state is
  // actually current)
  async actionToggle(actionId, toState, virtual = false){
    var stateRetVal = this.getActionState(actionId);
    if(stateRetVal != null && stateRetVal != toState){ 
      // Verified that the action is correct. Execute the action.
      return await this.requestGetStateToggle(actionId, toState, virtual);
    }
    else
      console.log("[WARNING] Provided toState \'" + toState + "\' for " + actionId + " conflicts with existing state \'"+stateRetVal+"\' for module " + this.ipAddress + ".");
    return false;
  }

  // Given actionId and toState, updates the state based on what
  // the module has told us. No strings attached. 
  moduleStateUpdate(actionId, toState){
    return this.setActionState(actionId, toState);
  }

  // Sends a request to the arduino to change to a new state. Returns
  // true if the action was succesfully received (200). Also accepts
  // virtual boolean to specify whether to not execute physical
  // action. 
  async requestGetStateToggle(actionId, toState, virtual = false){
    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      if(virtual){
        apiResponse = await fetch('http://' + this.ipAddress + '/stateVirtualToggle/' + actionId + '/' + toState); 
      }
      else{
        apiResponse = await fetch('http://' + this.ipAddress + '/stateToggle/' + actionId + '/' + toState); 
      }
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("[DEBUG] requestGetStateToggle (module " +this.ipAddress+ ") returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("[ERROR] requestGetStateToggle (module " +this.ipAddress+ ") failed! Error:\n" + error);
    }
    if(apiResponse.status == 200){
      // Executed successfully!
      return true;
    }
    console.log("[WARNING] requestGetStateToggle (module " +this.ipAddress+ ") returned with status " + apiResponse.status + ".");
    return false;
  }

  // Sends a request to the arduino to get state status. 
  // The arduino will then seperately reply with its standard
  // reply commands. 
  async requestGetStateGet(actionId){
    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      apiResponse = await fetch('http://' + this.ipAddress + '/stateGet/' + actionId); 
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("[DEBUG] requestGetStateGet (module " +this.ipAddress+ ") returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("[ERROR] requestGetStateGet (module " +this.ipAddress+ ") failed! Error:\n" + error);
    }
    if(apiResponse.status == 200){
      // Executed successfully!
      return true;
    }
    console.log("[WARNING] requestGetStateGet (module " +this.ipAddress+ ") returned with status " + apiResponse.status + ".");
    return false;
  }

  // Sends a request to the arduino telling it all of the
  // implemented actions and corresponding pin numbers 
  // of this module object. (Yay for object oriented!)
  async moduleUpdate(){
    var actionsAndPins = []; // An array of pairs actions + pins. 
    for(var i = 0; i < this.actions.length; i++){
      var actionStr = this.actions[i].toString();
      var pinStr = this.pins[i].toString();
      if(pinStr.contains(".")){
        var pinSplitStr = pinStr.split(".");
        var pin1 = parseInt(pinSplitStr[0]);
        var pin2 = parseInt(pinSplitStr[1]);
        var pin1String;
        var pin2String;
        if(pin1 < 10){
          // Single digit.
          pin1String = "0" + pin1.toString();
        }
        else{
          pin1String = pin1.toString();
        }
        if(pin2 < 10){
          // Single digit.
          pin2String = "0" + pin2.toString();
        }
        else{
          pin2String = pin2.toString();
        }
        pinStr = pin1String + pin2String;
      }
      actionsAndPins.push(actionStr);
      actionsAndPins.push(pinStr);
    }

    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      apiResponse = await fetch('http://' + this.ipAddress + '/moduleUpdate/' + this.roomId + "/"+ actionsAndPins.join('/')); 
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("[DEBUG] moduleUpdate (module " +this.ipAddress+ ") returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("[ERROR] moduleUpdate (module " +this.ipAddress+ ") failed! Error:\n" + error);
    }
    if(apiResponse.status == 200){
      // Executed successfully!
      return true;
    }
    console.log("[WARNING] moduleUpdate (module " +this.ipAddress+ ") returned with status " + apiResponse.status + ".");
    return false;
  }
}

module.exports = Module;