/*
  app.tsx

  Primary script for serving front-facing dashboard functionality. 
  Typescript, so it should be transpiled into Javascript before being
  executed. 
*/

var React = require('react');
var ReactDOM = require('react-dom');

const openweathermapZipCode = "95051"
const openweathermapApiKey = "47ad011b1eb24c37b31f2805da701cc4";
const updateTimeWait = 1000; // Every second
const updateWeatherWait = 900000; // Once every 15 minutes

export class App extends React.Component {
  constructor(){
    super();

    // Interval handles to clean up.
    this.updateTimeInverval = null;
    this.updateWeatherInterval = null;
    
    // State
    this.state = {
      currentHoursMinutes: null,
      currentSeconds: null,
      currentAmPm: null,
      currentDayMonthYear: null,
      currentWeatherMain: null,
      currentWeatherMinMax: null,
      currentWeatherFeelsLike: null,
    };

    // Binding functions to "this"
    this.updateTime = this.updateTime.bind(this);
    this.updateWeather = this.updateWeather.bind(this);
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
    var currentDayMonthYear = currentDay + " " + currentMonth + " " + curentYear;

    this.setState({
      currentHoursMinutes: currentHoursMinutes,
      currentSeconds: currentSeconds,
      currentAmPm: currentAmPm,
      currentDayMonthYear: currentDayMonthYear,
    });
  }

  // Modify weather state variables whenever called (timer-linked)
  async updateWeather(){
    var apiResponse = null;
    var startTime, endTime; // We report in debug the api time.
    try{
      startTime = new Date();
      apiResponse = await fetch("http://api.openweathermap.org/data/2.5/weather?zip="+openweathermapZipCode+"&units=imperial&appid=" + openweathermapApiKey);
      endTime = new Date();
      var timeDiff = endTime - startTime;
      console.log("DEBUG: Open Weather Map API call returned in " + timeDiff/1000 + " seconds.");
    }
    catch(error){
      console.log("ERROR: Open Weather Map API call failed!");
    }
    if(apiResponse.status == 200){
      var receivedData = await apiResponse.json();
  
      console.log("DEBUG: Received Open Weather Map API data:");
      console.log(receivedData);

      // Given open weather map JSON data, parse it. See example: 
      // https://openweathermap.org/current#zip
      var weatherMain = receivedData.weather[0].main; // "Clear"
      var weatherDesc = receivedData.weather[0].description; // "clear sky"
      var mainTemp = receivedData.main.temp;
      var mainFeels_like = receivedData.main.feels_like; 
      var mainTemp_min = receivedData.main.temp_min;
      var mainTemp_max = receivedData.main.temp_max; 
      var mainPressure = receivedData.main.pressure; // "1023"
      var mainHumidity = receivedData.main.humidity; // "100"
      var visibility = receivedData.visibility; // "16093"
      var windSpeed = receivedData.wind.speed; // "1.5"
      var windDeg = receivedData.wind.deg; // "350"
      var dt = receivedData.dt; // "1560350645"
      var sysSunrise = receivedData.sys.sunrise; // "1560343627"
      var sysSunset = receivedData.sys.sunset; // "1560396563"

      var currentWeatherMain = parseInt(mainTemp).toFixed(0) + " F - " + weatherMain;
      var currentWeatherMinMax = parseInt(mainTemp_min).toFixed(0) + " F | " + parseInt(mainTemp_max).toFixed(0) + " F";
      var currentWeatherFeelsLike = "Feels Like: " + parseInt(mainFeels_like).toFixed(0) + " F";
      this.setState({
        currentWeatherMain: currentWeatherMain,
        currentWeatherMinMax: currentWeatherMinMax,
        currentWeatherFeelsLike: currentWeatherFeelsLike,
      });
    }
    else{
      console.log("WARNING: Open Weather Map API call returned with status " + apiResponse.status + ".");
    }
  }

  moduleLightingBedroom(){
    console.log("TODO: Bedroom lighting module activated.");
  }

  moduleCurtainsBedroom(){
    console.log("TODO: Bedroom curtains module activated.");
  }

  moduleLightingLivingRoom(){
    console.log("TODO: Living Room lighting module activated.");
  }

  // Executed only once upon startup.
  componentDidMount(){
    // Start the clock and the interval to update it every second.
    this.updateTime();
    this.updateTimeInverval = setInterval(this.updateTime, updateTimeWait);

    // Query the weather and start the interval to update it (every 60 minutes).
    this.updateWeather();
    this.updateWeatherInterval = setInterval(this.updateWeather, updateWeatherWait);
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
          <button onClick={this.moduleLightingBedroom}>Bedroom Light</button>
          <button onClick={this.moduleCurtainsBedroom}>Bedroom Curtains</button>
          <button onClick={this.moduleLightingLivingRoom}>Living Room Light</button>
        </div>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.getElementById('app'));