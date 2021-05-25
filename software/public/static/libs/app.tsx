/*
  app.tsx
  Primary script for serving front-facing dashboard functionality. 
  Typescript, so should be transpiled into Javascript before being
  executed. 
*/

var React = require('react');
var ReactDOM = require('react-dom');

export class App extends React.Component {
  render() {
    return(<h1>Hello!</h1>);
  }
}

ReactDOM.render(<App />, document.getElementById('app'));