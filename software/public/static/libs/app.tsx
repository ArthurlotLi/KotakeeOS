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
const updateActionStatesWait = 500; // 0.5 seconds. 

// Get webserver address to make API requests to it. apiURL should
// therefore contain http://192.168.0.197 (regardless of subpage).
const currentURL = window.location.href;
const splitURL = currentURL.split("/");
const apiURL = splitURL[0] + "//" + splitURL[2]; 

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
}

// Bedroom IDs - Should be kept constant betweeen this and client
// application logic. 
const rooms = {
  BEDROOM: 1,
  LIVINGROOM: 2,
}

// End enums

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
    };

    // Binding functions to "this"
    this.updateTime = this.updateTime.bind(this);
    this.updateHomeStatus = this.updateHomeStatus.bind(this);
    this.updateActionStates = this.updateActionStates.bind(this);
  }

  // BIG TODO: migrate both updateWeather to webserver, so all 
  // applications have a centralized weather and time. This 
  // allows for more calls to the weather API. Should be retrieved 
  // via the single status web call.

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
    if(data == null) {
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
      var currentWeatherFeelsLike = "Feels Like: " + parseInt(mainFeels_like).toFixed(0) + " F";
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
    if(data == null) {
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
    }
    if (data != null){
      console.log("DEBUG: Parsing updateActionStates data:");
      console.log(data);
      var currentLastUpdate = data.lastUpdate.toString();
      // Shove it right into the states. We know it'll be structured
      // with roomId first, then actionId. 
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
    if(actionId <= actions.LIGHTING5 && actionId >= actions.LIGHTING1){
      console.log("Test.");
      if(currentState == 0){
        toState = 1;
      }
      else {
        toState = 0;
      }
    }
    // TODO: handle additional actionIds. We will make this a 
    // whitelist, not a blacklist. 

    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      apiResponse = await fetch(apiURL + "/moduleToggle/" +roomId + "/"  + actionId + "/" + toState);
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
  }

  render() {
    return(
      <div>
        <div id="app-location">
          Santa Clara, CA
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
        </div>

        <div id="app-modules">
          <button onClick={() => { this.moduleToggle(rooms.BEDROOM, actions.LIGHTING1) }}>Bedroom Light<br></br>{this.state.actionStates ? this.state.actionStates[rooms.BEDROOM][actions.LIGHTING1] : -1}</button>
          <button onClick={() => { this.moduleToggle(rooms.BEDROOM, actions.CURTAINS1) }}>Bedroom Curtains<br></br>{this.state.actionStates ? this.state.actionStates[rooms.BEDROOM][actions.CURTAINS1]: -1}</button>
          <button onClick={() => { this.moduleToggle(rooms.LIVINGROOM, actions.LIGHTING1) }}>Living Room Light<br></br>{this.state.actionStates ? this.state.actionStates[rooms.LIVINGROOM][actions.LIGHTING1] : -1}</button>
        </div>

        <div id="app-home-status">
          <div id="app-home-status-modules">Modules: {this.state.currentModulesCount}</div>
        </div>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.getElementById('app'));