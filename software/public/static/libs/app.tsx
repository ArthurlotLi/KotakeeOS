/*
  app.tsx

  Primary script for serving front-facing dashboard functionality. 
  Typescript, so it should be transpiled into Javascript before being
  executed. 
*/

var React = require('react');
var ReactDOM = require('react-dom');

const updateTimeWait = 1000; // Every second
const updateHomeStatusWait = 10000; // 10 seconds. 
const updateActionStatesWait = 250; // 0.25 seconds. 

// Get webserver address to make API requests to it. apiURL should
// therefore contain http://192.168.0.197 (regardless of subpage).
const currentURL = window.location.href;
const splitURL = currentURL.split("/");
const apiURL = splitURL[0] + "//" + splitURL[2]; 

const defaultBackgroundColor = "#303030";
const virtualBackgroundColor = "#c77e00";

/*
  Enums to keep constant with server logic. 
*/

// Actions enum - Should be kept constant between this and server 
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
  TEMP1: 5250,
  TEMP2: 5251,
  TEMP3: 5252,
  TEMP4: 5253,
  TEMP5: 5254,
}

// Bedroom IDs - Should be kept constant betweeen this and client
// application logic. 
const rooms = {
  BEDROOM: 1,
  LIVINGROOM: 2,
  BATHROOM: 3,
}

// End enums

// Frontend enum only (for display purposes to translate roomIds 
// and actionIDs onto buttons.)
const implementedButtons = {
  "1.50": "Bedroom Lamp",
  "2.50": "Living Room Lamp",
  "2.250": "Soundbar Power",
  "2.251": "Ceiling Fan Lamp",
  "2.252": "Printer Power",
  "2.350": "Kitchen Light",
  "3.50": "Bathroom LED",
  "3.350": "Bathroom Light",
  "3.351": "Bathroom Fan",
  "2.450": "A/C Unit"
}

// When we need to use state data in other ways, enumerated
// by specific strings to tell the app what to do. 
const implementedFeatures ={
  "2.5250": "temperature",
  "1.5250": "temperature",
}

const dayOfWeek = [
  'Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'
];

export class App extends React.Component {
  constructor(){
    super();

    // Interval handles to clean up.
    this.updateTimeInverval = null;
    this.updateHomeStatusInterval = null;
    this.updateActionStatesInterval = null;

    // Various functions to ensure cleanliness.
    this.updateHomeStatusWorking = false;
    this.updateActionStatesWorking = false;
    
    // State
    this.state = {
      currentHoursMinutes: null,
      currentSeconds: null,
      currentAmPm: null,
      currentDayMonthYear: null,
      currentWeatherMain: null,
      currentWeatherMinMax: null,
      currentWeatherFeelsLike: null,
      currentModulesCount: null,
      actionStates: null,
      lastUpdateActionStates: null,
      lastUpdateHomeStatus: null,
      virtualMode: false,
    };

    // Binding functions to "this"
    this.updateTime = this.updateTime.bind(this);
    this.updateHomeStatus = this.updateHomeStatus.bind(this);
    this.updateActionStates = this.updateActionStates.bind(this);
    this.toggleVirtualMode = this.toggleVirtualMode.bind(this);
    this.featureAllLights = this.featureAllLights.bind(this);
    this.featureSpeechServer = this.featureSpeechServer.bind(this);
  }

  // Modify date state variables whenever called (timer-linked.)
  updateTime(){
    var date = new Date();
    var time = date.toLocaleTimeString(navigator.language, {
      hour: '2-digit',
      minute:'2-digit',
      second:'2-digit',
    });
    var splitTime = time.split(":");
    var hours = splitTime[0];
    var minutes = splitTime[1];
    if(hours.charAt(0) == '0'){
      // Strip leading zero from hours if present.
      hours = hours.charAt(1);
    }
    var splitEnd = splitTime[2].split(" ");
    var seconds = splitEnd[0];

    var currentAmPm = " " + splitEnd[1];
    var currentHoursMinutes =  hours + ":" + minutes;
    var currentSeconds = ":" + seconds;

    var currentDay = date.getDate().toString();
    var currentMonth = date.toLocaleString('default', {month: 'long'});
    var curentYear = date.getFullYear().toString();
    var currentWeekDay = dayOfWeek[date.getDay()];
    var currentDayMonthYear = currentWeekDay + " - " + currentDay + " " + currentMonth + " " + curentYear;

    this.setState({
      currentHoursMinutes: currentHoursMinutes,
      currentSeconds: currentSeconds,
      currentAmPm: currentAmPm,
      currentDayMonthYear: currentDayMonthYear,
    });
  }

  // Query the web server if no data is provied. If data is provided,
  // we'll use that instead. 
  async updateHomeStatus(data = null){
    if(data == null && !this.updateHomeStatusWorking) {
      // Stop browsers from bombarding web server if they hang on something.
      this.updateHomeStatusWorking = true;
      var apiResponse = null;
      var startTime, endTime; // We report in debug the api time.
      try{
        var lastUpdate = this.state.lastUpdateHomeStatus;
        if(lastUpdate == null){
          lastUpdate = 0;
        }
        startTime = new Date();
        apiResponse = await fetch(apiURL + "/homeStatus/" + lastUpdate);
        endTime = new Date();
      }
      catch(error){
        console.log("ERROR: homeStatus call failed!");
      }
      if(apiResponse.status == 200){
        var timeDiff = endTime - startTime;
        console.log("DEBUG: homeStatus call returned in " + timeDiff/1000 + " seconds.");
        data = await apiResponse.json();
      }
      else if(apiResponse.status == 204){
        // Heartbeat, do nothing. 
      }
      else{
        console.log("WARNING: homeStatus call returned with status " + apiResponse.status + ".");
      }
      this.updateHomeStatusWorking = false;
    }
    if(data != null){
      console.log("DEBUG: Parsing homeStatus data:");
      console.log(data);

      var currentLastUpdate = data.lastUpdate.toString();

      var currentModulesCount = data.modulesCount;

      var weatherData = data.weatherData;

      // Given open weather map JSON data, parse it. See example: 
      // https://openweathermap.org/current#zip
      var weatherMain = weatherData.weather[0].main; // "Clear"
      var weatherDesc = weatherData.weather[0].description; // "clear sky"
      var mainTemp = weatherData.main.temp;
      var mainFeels_like = weatherData.main.feels_like; 
      var mainTemp_min = weatherData.main.temp_min;
      var mainTemp_max = weatherData.main.temp_max; 
      var mainPressure = weatherData.main.pressure; // "1023"
      var mainHumidity = weatherData.main.humidity; // "100"
      var visibility = weatherData.visibility; // "16093"
      var windSpeed = weatherData.wind.speed; // "1.5"
      var windDeg = weatherData.wind.deg; // "350"
      var dt = weatherData.dt; // "1560350645"
      var sysSunrise = weatherData.sys.sunrise; // "1560343627"
      var sysSunset = weatherData.sys.sunset; // "1560396563"

      var currentWeatherMain = parseInt(mainTemp).toFixed(0) + " F - " + weatherMain;
      var currentWeatherMinMax = parseInt(mainTemp_min).toFixed(0) + " F | " + parseInt(mainTemp_max).toFixed(0) + " F";
      var currentWeatherFeelsLike = "Feels Like " + parseInt(mainFeels_like).toFixed(0) + " F" + " (" + parseInt(mainHumidity).toFixed(0) + " %)";
      await this.setState({
        currentWeatherMain: currentWeatherMain,
        currentWeatherMinMax: currentWeatherMinMax,
        currentWeatherFeelsLike: currentWeatherFeelsLike,
        currentModulesCount: currentModulesCount,
        lastUpdateHomeStatus: currentLastUpdate,
      });
    }
  }

  // Query the web server if no data is provied. If data is provided,
  // we'll use that instead. 
  async updateActionStates(data = null){
    if(data == null && !this.updateActionStatesWorking) {
      // Stop browsers from bombarding web server if they hang on something.
      this.updateActionStatesWorking = true;
      var apiResponse = null;
      var startTime, endTime; // We report in debug the api time.
      try{
        var lastUpdate = this.state.lastUpdateActionStates;
        if(lastUpdate == null){
          lastUpdate = 0;
        }
        startTime = new Date();
        apiResponse = await fetch(apiURL + "/actionStates/" + lastUpdate);
        endTime = new Date();
      }
      catch(error){
        console.log("ERROR: actionStates call failed!");
      }
      if(apiResponse.status == 200){
        var timeDiff = endTime - startTime;
        console.log("DEBUG: actionStates call returned in " + timeDiff/1000 + " seconds.");
        data = await apiResponse.json();
      }
      else if(apiResponse.status == 204){
        //Heartbeat, do nothing.
      }
      else{
        console.log("WARNING: actionStates call returned with status " + apiResponse.status + ".");
      }
      this.updateActionStatesWorking = false;
    }
    if (data != null){
      this.handleActionStates(data);
    }
  }

  // Abstraction because spaghetti is bad. 
  handleActionStates(data){
    if (data != null){
      console.log("DEBUG: Parsing handleActionStates data:");
      console.log(data);
      var currentLastUpdate = data.lastUpdate.toString();
      // We only get data if it's been updated thanks to the timestamp
      // processing, so now we need to update our information. 
      for(var key in data){
        // Ignore the lastUpdate variable. 
        if(key != "lastUpdate"){
          var roomId = key; // Just to make things clearer.
          var room = data[key];
          for(var actionId in room){
            // Check if we've implemented this action in the list of interface
            // actions. 
            var buttonText = implementedButtons[roomId + "." + actionId];
            if(buttonText == null || buttonText == ""){
              // This action is not applicable to buttons. Check to see
              // if we applied it to other elements. 
              var featureName = implementedFeatures[roomId + "." + actionId];
              if(featureName != null && featureName != ""){
                // We have a feature.
                switch(featureName){
                  case "temperature":
                    // Handle temperatures. Expects a state like "str_27.70_42.20".
                    var tempDivId = 'app-temps-' + roomId + '-' + actionId;
                    var tempDiv = document.getElementById(tempDivId);
                    var humDivId = 'app-hum-' + roomId + '-' + actionId;
                    var humDiv = document.getElementById(humDivId);
                    if(tempDiv != null && humDiv != null){
                      var actionStateString = String(room[actionId]);
                      var tempInfo = actionStateString.split("_");
                      if(tempInfo.length >= 2){
                        var temp = parseFloat(tempInfo[0]);
                        var hum = parseFloat(tempInfo[1]).toFixed(0);
                        // Convert temp to F from C
                        var tempStr =  ((temp * 1.8) +32).toFixed(0);
                        tempDiv.innerHTML = tempStr + " F";
                        humDiv.innerHTML = hum + " %";
                      }
                    }
                    else{
                      console.log("WARNING: handleActionStates attempted to find a temp div with id " + tempDivId + " and hum div with id "+humDivId+ " that did not exist!");
                    }
                    break;
                  default:
                    console.log("WARNING: handleActionStates attempted to handle a feature that did not exist!");
                }
              }
            }
            else{
              // Handle buttons. 
              var buttonId = 'app-modules-' + roomId + '-' + actionId;
              var button = document.getElementById(buttonId);
              if(button != null){
                button.innerHTML = buttonText;
                var actionState = room[actionId];
                if(actionState == "1"){
                  button.style.backgroundColor = '#03a100'; // Green
                }
                else if(actionState == "0"){
                  button.style.backgroundColor = '#a60000';  // Red
                }
                else if(actionState == "10"){
                  button.style.backgroundColor = '#a60000'; // Red
                }
                else if(actionState == "11"){
                  button.style.backgroundColor = '#d9a30f';  // Orange
                }
                else if(actionState == "12"){
                  button.style.backgroundColor = '#03a100';  // Green
                }
                else if(actionState == "20"){
                  button.style.backgroundColor = '#a60000'; // Red
                }
                else if(actionState == "21"){
                  button.style.backgroundColor = '#d9a30f';  // Orange
                }
                else if(actionState == "22"){
                  button.style.backgroundColor = '#03a100';  // Green
                }
                else {
                  button.style.backgroundColor = '#222222';  // Default null color.
                }
              }
              else{
                console.log("WARNING: handleActionStates attempted to find a button with id " + buttonId + " that did not exist!");
              }
            }
          }
        }
      }

      this.setState({
        actionStates: data,
        lastUpdateActionStates: currentLastUpdate,
      });
    }
  }

  // Query the web server to update an action to a different state
  // based on what we know.
  async moduleToggle(roomId, actionId){
    console.log("DEBUG: moduleToggle called with roomId " + roomId + " and actionId " + actionId + ".");
    var toState = null;
    var currentState = this.state.actionStates[roomId][actionId];
    if(currentState == null){
      console.log("ERROR: moduleToggle attempted to toggle room " + roomId + " action " +actionId+" that has no reported state!");
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
        console.log("WARNING: moduleToggle attempted to toggle action with current state of 11. Ignored.");
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
        console.log("WARNING: moduleToggle attempted to toggle action with current state of 21. Ignored.");
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
        console.log("WARNING: moduleToggle attempted to toggle action with current state of 31. Ignored.");
      }
    }
    else{
      // We default to a binary paradigm.
      if(currentState == 0){
        toState = 1;
      }
      else {
        toState = 0;
      }
    }

    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      if(this.state.virtualMode){
        apiResponse = await fetch(apiURL + "/moduleVirtualToggle/" +roomId + "/"  + actionId + "/" + toState);
      }
      else{
        apiResponse = await fetch(apiURL + "/moduleToggle/" +roomId + "/"  + actionId + "/" + toState);
      }
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("DEBUG: Module Lighting Bedroom call (bedroomModule1) returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("ERROR: Module Lighting Bedroom call (bedroomModule1) failed!");
    }
    if(apiResponse.status == 200){
      // TODO - do something to save the state in the web server...? 
    }
    else{
      console.log("WARNING: Module Lighting Bedroom call (bedroomModule1) call returned with status " + apiResponse.status + ".");
    }
  }

  // Enter and exit the debug mode, which allows users to manually
  // specify current states for 10 11 12 actions. 
  async toggleVirtualMode(){
    await this.setState({
      virtualMode: !this.state.virtualMode,
    });
    this.updateActionStates(); // requery server having reset our states. 
    var body = document.getElementById("body");
    // Change the color schemes accordingly. 
    if(this.state.virtualMode){
      body.style.backgroundColor = virtualBackgroundColor;
    }
    else{
      body.style.backgroundColor = defaultBackgroundColor;
    }
  }

  // Experimental - Have server turn all lights on or off. Note
  // this essentially harmonizes all light states. Converts 
  // the majority to the minority. If they are equal, always
  // turns everything on. 
  featureAllLights(){
    var data = this.state.actionStates;
    if (data != null){
      var onCount = 0;
      var offCount = 0;
      for(var key in data){
        // Ignore the lastUpdate variable. 
        if(key != "lastUpdate"){
          var roomId = key; // Just to make things clearer.
          var room = data[key];
          for(var actionId in room){
            // For every single room and action, check the state. 
            var actionState = parseInt(room[actionId]);
            if(actionState == 1 || actionState == 12 || actionState == 22 || actionState == 32){
              onCount++;
            }
            else{
              // We'll just count everything else as on (even if we're in 11 to go
              // to 10, for example.)
              offCount++;
            }
          }
        }
      }
      var turnAllOn = true;
      if(onCount > offCount){
        turnAllOn = false;
      }
      for(var key in data){
        // Ignore the lastUpdate variable. 
        if(key != "lastUpdate"){
          var roomId = key; // Just to make things clearer.
          var room = data[key];
          for(var actionId in room){
            var actionState = parseInt(room[actionId]);
            if(turnAllOn){
              if(actionState != 1 && actionState != 12 && actionState != 22 && actionState != 32){
                this.moduleToggle(roomId, actionId);
              }
            }
            else{
              if(actionState != 0 && actionState != 10 && actionState != 20 && actionState != 30){
                this.moduleToggle(roomId, actionId);
              }
            }
          }
        }
      }
    }
  }

  // Experimental - turn the server's speech server on. 
  async featureSpeechServer(){
    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      apiResponse = await fetch(apiURL + "/moduleInput/2/5350/1");
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("DEBUG: featureSpeechServer call returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("ERROR: featureSpeechServer call failed!");
    }
    if(apiResponse.status == 200){
      // TODO - do something to save the state in the web server...? 
    }
    else{
      console.log("WARNING: Module Lighting Bedroom call (bedroomModule1) call returned with status " + apiResponse.status + ".");
    }
  }

  // Executed only once upon startup.
  componentDidMount(){
    // Start the clock and the interval to update it every second.
    this.updateTime();
    this.updateTimeInverval = setInterval(this.updateTime, updateTimeWait);

    // Query the weather and start the interval to update it.
    this.updateHomeStatus();
    this.updateHomeStatusInterval = setInterval(this.updateHomeStatus, updateHomeStatusWait);

    // Query the Server for action updates and start the interval to update it.
    this.updateActionStates();
    this.updateActionStatesInterval = setInterval(this.updateActionStates, updateActionStatesWait);
  }

  // Executed upon close.
  componentWillUnmount(){
    clearInterval(this.updateTimeInterval);
    clearInterval(this.updateHomeStatusInterval);
    clearInterval(this.updateActionStatesInterval);
  }

  render() {
    return(
      <div>
        <div id="app-location">
          <div><button class="app-location-debug" onClick={this.toggleVirtualMode}>Virtual Mode</button></div>
          <div><button class="app-location-debug" onClick={this.featureAllLights}>All Modules</button></div>
          <div><button class="app-location-debug" onClick={this.featureSpeechServer}>Speech Server</button></div>
        </div>

        <div id="app-clock">
          <div id="app-clock-time">
            {this.state.currentHoursMinutes}
            <span id="app-clock-time-seconds">{this.state.currentSeconds}</span>
            <span id="app-clock-time-ampm">{this.state.currentAmPm}</span>
          </div>
          <div id="app-clock-date">{this.state.currentDayMonthYear}</div>
        </div>

        <div id="app-weather">
          <div id="app-weather-main">{this.state.currentWeatherMain}</div>
          <div id="app-weather-minMax">{this.state.currentWeatherMinMax}</div>
          <div id="app-weather-feelsLike">{this.state.currentWeatherFeelsLike}</div>
          <hr></hr>
          <div id="app-temps">
            <div class="app-temps-line">Living Room - <span id={"app-temps-"+rooms.LIVINGROOM+"-"+actions.TEMP1}>00 F</span> (<span id={"app-hum-"+rooms.LIVINGROOM+"-"+actions.TEMP1}>00 %</span>)</div>
            <div class="app-temps-line">Bedroom - <span id={"app-temps-"+rooms.BEDROOM+"-"+actions.TEMP1}>00 F</span> (<span id={"app-hum-"+rooms.BEDROOM+"-"+actions.TEMP1}>00 %</span>)</div>
          </div>
        </div>

        <div id="app-modules-row1">
          <button id={"app-modules-"+rooms.BEDROOM+"-"+actions.LIGHTING1} onClick={() => { this.moduleToggle(rooms.BEDROOM, actions.LIGHTING1) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.LIGHTING1} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.LIGHTING1) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.REMOTE2} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.REMOTE2) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.REMOTE10} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.REMOTE10) }}></button>
        </div>

        <div id="app-modules-row2">
          <button id={"app-modules-"+rooms.BATHROOM+"-"+actions.SWITCH1} onClick={() => { this.moduleToggle(rooms.BATHROOM, actions.SWITCH1) }}></button>
          <button id={"app-modules-"+rooms.BATHROOM+"-"+actions.SWITCH2} onClick={() => { this.moduleToggle(rooms.BATHROOM, actions.SWITCH2) }}></button>
          <button id={"app-modules-"+rooms.BATHROOM+"-"+actions.LIGHTING1} onClick={() => { this.moduleToggle(rooms.BATHROOM, actions.LIGHTING1) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.SWITCH1} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.SWITCH1) }}></button>
        </div>

        <div id="app-modules-row3">
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.REMOTE1} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.REMOTE1) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.REMOTE3} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.REMOTE3) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.KNOB1} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.KNOB1) }}></button>
          <button id={"app-modules-"+rooms.LIVINGROOM+"-"+actions.REMOTE10} onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.REMOTE10) }}></button>
        </div>

        <div id="app-home-status">
          <div id="app-home-status-modules">Modules: {this.state.currentModulesCount}</div>
        </div>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.getElementById('app'));