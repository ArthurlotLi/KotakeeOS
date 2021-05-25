/*
  app.tsx

  Primary script for serving front-facing dashboard functionality. 
  Typescript, so it should be transpiled into Javascript before being
  executed. 
*/

var React = require('react');
var ReactDOM = require('react-dom');

export class App extends React.Component {
  constructor(){
    super();

    // Interval handles to clean up.
    this.updateTimeInverval = null;
    
    // State
    this.state = {
      currentHoursMinutes: null,
      currentSeconds: null,
      currentAmPm: null,
      currentDayMonthYear: null,
    };

    // Binding functions to "this"
    this.updateTime = this.updateTime.bind(this);
  }

  // Modify date state variables whenever called (timer-linked. )
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
    // Start the clock and the interval to update it. 
    this.updateTime();
    this.updateTimeInverval = setInterval(this.updateTime, 1000);
  }

  // Executed upon close.
  componentWillUnmount(){
    clearInterval(this.updateTimeInterval);
  }

  render() {
    return(
      <div>
        <div id="app-location">
          Location. 
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
          Weather. 
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