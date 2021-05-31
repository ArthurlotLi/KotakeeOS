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
}

module.exports = Room;