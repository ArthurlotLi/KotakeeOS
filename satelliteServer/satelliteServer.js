/*
    satelliteServer.js
    Remote servers that interface with the primary server in
    various ways. For example, starting up speech server in
    different rooms. 
*/

const express = require("express");
const path = require("path");
const fetch = require("node-fetch");

// OSX only (might break elsewhere). Used for shell commands via 
// moduleInput handling. 
const { exec } = require('child_process');

/*
  Configurable Constants + app creation
*/

const listeningPort = 8080;
const apiURL = "http://192.168.0.197:8080";

const speechServerCommand = "python3 ../speechServer/hotwordPocketSphinx.py";
const hotwordNoneCommand =  "python3 ../speechServer/hotwordNone.py";
const block = {
  52: 1,
}
const blockRoom = 2;

// Create the app
const app = express();

var actionStates = null;

// Whenever the request path has "static" inside of it, simply serve 
// the static directory as you'd expect. 
app.use("/static", express.static(path.resolve(__dirname, "public", "static")));

// Handle requests from the server to turn on the speech server.  
app.get('/toggleSpeechServer', (req, res) => {
  console.log("[DEBUG] /toggleSpeechServer GET request received. Arguments: " + JSON.stringify(req.params));
  handleSpeechServerRequest();
  return res.status(200).send();
});

// Handle requests from the server to turn on the single line server.
app.get('/toggleHotwordNone', (req, res) => {
  console.log("[DEBUG] /toggleHotwordNone GET request received. Arguments: " + JSON.stringify(req.params));
  handleSpeechServerRequest(true);
  return res.status(200).send();
});

async function handleSpeechServerRequest(hotwordNone = false){
  // Execute the command, but only if the blocking status isn't there. 
  await updateActionStates();
  if(actionStates != null && actionStates[String(blockRoom)] != null){
    var roomActionStates = actionStates[String(blockRoom)];
    for (var actionId in block){
      var currentState = roomActionStates[actionId];
      if(currentState != null){
        if(currentState == block[actionId]){
          console.log("[WARN] Blocking toggleSpeechServer request due to blocking action state.")
          return res.status(200).send();
        }
      }
    }
    // If we're still here, we weren't blocked. 
    if(hotwordNone){
      console.log("[DEBUG] Executing command: " + hotwordNoneCommand);
      exec(hotwordNoneCommand, null)
    }
    else{
      console.log("[DEBUG] Executing command: " + speechServerCommand);
      exec(speechServerCommand, null)
    }
  }
}

// Query the web server if no data is provied. If data is provided,
// we'll use that instead. 
async function updateActionStates(){
  var apiResponse = null;
  var startTime, endTime; // We report in debug the api time.
  //try{
    startTime = new Date();
    console.log("DEBUG: updateActionStates submitting query: " + apiURL + "/actionStates/" + 0);
    apiResponse = await fetch(apiURL + "/actionStates/" + String(0)); // We always query the server eveyr time. 
    endTime = new Date();
  //}
  /*catch(error){
    console.log("ERROR: actionStates call failed!");
  }*/
  if(apiResponse.status == 200){
    var timeDiff = endTime - startTime;
    console.log("DEBUG: actionStates call returned in " + timeDiff/1000 + " seconds.");
    actionStates = await apiResponse.json();
    return;
  }
  else if(apiResponse.status == 204){
    //Heartbeat, do nothing.
  }
  else{
    console.log("WARNING: actionStates call returned with status " + apiResponse.status + ".");
  }
}

// Start the server to listen on this port.
app.listen(listeningPort, () => {
  console.log("Project KotakeeOS is online at port: " +listeningPort);
});

