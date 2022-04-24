/*
  database.js
  Self-contained utilities for accessing the home database server from the
  KotakeeOS web server. 
*/

const pg = require('pg');

const dataUsername = "postgres"; 
const dataPassword = "password"; // Please ignore the bad practice.
const dataIpAddress = "localhost";
const dataPort = 5432;
const dataConnString = "postgres://" + dataUsername + ":" + dataPassword + "@" + dataIpAddress +":" + dataPort;

const weatherDatabase = "weather_test";

class DatabaseBridge {
  constructor(databaseName){
    print("")
    this.client = new pg.Client(dataConnString + "/" + databaseName);
  }
}
