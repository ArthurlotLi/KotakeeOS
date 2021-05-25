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
    this.state = {
      currentHoursMinutes: null,
      currentSeconds: null,
      currentDayMonthYear: null,
    };
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
    var seconds = splitTime[2];
    if(hours.charAt(0) == '0'){
      // Strip leading zero from hours if present.
      hours = hours.charAt(1);
    }
    var currentHoursMinutes =  hours + ":" + minutes;
    var currentSeconds = seconds;

    var currentDay = date.getDate().toString();
    var currentMonth = date.toLocaleString('default', {month: 'long'});
    var curentYear = date.getFullYear().toString();
    var currentDayMonthYear = currentDay + " " + currentMonth + " " + curentYear;

    this.setState({
      currentHoursMinutes: currentHoursMinutes,
      currentSeconds: currentSeconds,
      currentDayMonthYear: currentDayMonthYear,
    });
  }

  // Executed only once upon startup.
  async componentDidMount(){
    // Start the clock and the interval to update it. 
    this.updateTime();
    setInterval(this.updateTime, 1000);
  }

  render() {
    return(
      <div>
        <div id="App-clock">
          <h1>{this.state.currentHoursMinutes}<span> {this.state.currentSeconds}</span></h1>
          <h3>{this.state.currentDayMonthYear}</h3>
        </div>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.getElementById('app'));