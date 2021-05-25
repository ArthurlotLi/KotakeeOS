/*
    server.js
    Primary file for node.js express project Silver.
*/

const express = require("express");
const path = require("path");

// Global constants
const listeningPort = 8080;

// Create the app
const app = express();

// Whenever the request path has "static" inside of it
// (i.e. "localhost:8080/static/js/index.js"), simply
// serve the static directory as you'd expect. 
app.use("/static", express.static(path.resolve(__dirname, "frontend", "static")));

// For all requests, we go back to the root with a get
// request. Meaning that it doesn't matter if user
// attempts to use post, we just use get.
app.get('/*',(req,res) => {
    res.sendFile(path.resolve(__dirname, "frontend", "index.html"));
});

// Start the server to listen on this port.
app.listen(process.env.PORT || listeningPort, () => console.log("Project SILVER is online..."));