/*
  Module.js
  Logic for each abstracted module and its lower level logic to
  interface with the arduino modules themselves. 
*/

const fetch = require("node-fetch");

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

module.exports = Module;