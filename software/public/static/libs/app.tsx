/*
  app.tsx
  Primary script for serving front-facing dashboard functionality. 
  Typescript, so should be transpiled into Javascript before being
  executed. 
*/

var React = require('react');
var ReactDOM = require('react-dom');

export class App extends React.Component {
  constructor(){
    super();
    this.state = {};
    // This is where you'd put this.function = this.function.bind(this);
  }

  async componentDidMount(){
    // Add whatever you'd like here. 
  }

  render() {
    return(
      <div>
        <h1>Hello there!</h1>
      </div>
    );
  }
}

ReactDOM.render(<App />, document.getElementById('app'));