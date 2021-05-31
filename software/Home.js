/*
  Room.js
  Logic for each abstracted home (for now we just expect a single home).
*/

const fetch = require("node-fetch");

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

  // Given roomId, actionId, and toState, update the state of 
  // a module. 
  moduleStateUpdate(roomId, actionId, toState){
    if(this.getRoom(roomId) != null){
      var room = this.getRoom(roomId);
      return room.moduleStateUpdate(actionId, toState);
    }
    else
      console.log("[ERROR] moduleStateUpdate failed! roomId " + roomId + " does not exist.");
    return null;
  }

  // Return states of all modules in system, identifying each
  // action by actionId, seperated by roomId. This is expected
  // to be a frequently called function on timers by all clients.
  // The end JSON object should have three layers. 
  actionStates(){
    var response = {}
    for(var room in this.roomsDict){
      if(this.roomsDict.hasOwnProperty(room)){
        // For each room, request actionStates.
        response[room] = this.roomsDict[room].actionStates();
      }
    }
    return response;
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

module.exports = Home;