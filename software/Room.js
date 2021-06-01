/*
  Room.js
  Logic for each abstracted room which contains a variety of modules. 
*/

const fetch = require("node-fetch");

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

  // Given an action Id, request a module to report action state to web
  // server. NOTE: Currently not used. 
  requestGetStateGet(actionId){
    if(actionId in this.actionsDict){
      var moduleId = this.actionsDict[actionId];
      if(moduleId in this.modulesDict){
        var module = this.modulesDict[moduleId];

        return module.requestGetStateGet(actionId);
      }
      else 
        console.log("[ERROR] requestGetStateGet failed! actionId " + actionId + " WAS found, but the saved moduleId "+ moduleId +" does not exist in room " + this.roomId + ".");
    }
    else 
      console.log("[ERROR] requestGetStateGet failed! actionId " + actionId + " does not exist in room " + this.roomId + ".");
    return false;
  }

  //Requests all modules to report action states to web server.
  requestAllActionStates(){
    for(var moduleId in this.modulesDict){
      var module = this.modulesDict[moduleId];
      var moduleActions = module.actions;
      for(var i = 0; i <  moduleActions.length; i++){
        module.requestGetStateGet(moduleActions[i]);
      }
    }
  }

  // Given the actionid and the state, update a module's state. We 
  // expect this whenever a module has completed an operation or
  // has restarted. Either way, accept what they're saying as truth. 
  moduleStateUpdate(actionId, toState){
    if(actionId in this.actionsDict){
      var moduleId = this.actionsDict[actionId];
      if(moduleId in this.modulesDict){
        var module = this.modulesDict[moduleId];

        return module.moduleStateUpdate(actionId, toState);
      }
      else 
        console.log("[ERROR] moduleStateUpdate failed! actionId " + actionId + " WAS found, but the saved moduleId "+ moduleId +" does not exist in room " + this.roomId + ".");
    }
    else 
      console.log("[ERROR] moduleStateUpdate failed! actionId " + actionId + " does not exist in room " + this.roomId + ".");
    return false;
  }
  
  // Return states of all ACTIONS in the room.
  actionStates(){
    var response = {};
    for(var module in this.modulesDict){
      var moduleStatesDict = this.modulesDict[module].statesDict;
      // Shed the moduleId from the information - the clients don't
      // need to know of these. 
      for(var key in moduleStatesDict){
        response[key] = moduleStatesDict[key];
      }
    }
    return response;
  }
}

module.exports = Room;