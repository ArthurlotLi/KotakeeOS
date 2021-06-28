/*
  KotakeeOS Module

  Uses WifiNina Simple Web Server Wifi example as a baseline. 

  Universal code base for all KotakeeOS arduino nodes with logic for all 
  nodes included. TODO: Add more info and flush out design.
*/
#include <SPI.h>
#include <WiFiNINA.h>
#include <Servo.h>

#include "arduino_secrets.h" 

char ssid[] = SECRET_SSID;  
char pass[] = SECRET_PASS;   
int keyIndex = 0;     

// Constants to keep up to date with server and app logic. 
// Actionst that do not fall within these bounds are 
// considered binary 0 1 states. 
const int remote1 = 250;
const int remote20 = 269;
const int switch1 = 350;
const int switch5 = 354;
const int inputActionThreshold = 5000; // ActionIds greater than this number are treated as inputs. 
const int motion1 = 5050;
const int motion5 = 5054;

const int servoNeutral = 170; // 180 is out of motion and will cause buzzing.
const int servoActive = 110;
const int servoActionWait = 600; // time to move arm between neutral and active.

// Sanity mechanism. if we request to send an input status to the server 
// within this elapsed time frame, we will declare that specific pin
// unplugged and forcefully delete that action/pin/state etc from our
// memory. 
const unsigned long fatalInputPinMillis = 200; 

// Time between reports (Buckets of time after which, if we see motion 
// detected, we'll send a query to the server.)
const unsigned long inputMillisReport = 500;

// Hard coded array since we can only handle up to 25 actions
// (arduinos only have up so many I/O pins. )
const int actionsAndPinsMax = 25;
int actions[actionsAndPinsMax];
int pins[actionsAndPinsMax];
int pins2[actionsAndPinsMax]; // Subsequent pin arrays for actions that use more than one. 
int states[actionsAndPinsMax];
// Used to detect and shut down a pin that isn't connected so we don't
// unintentinally DDOS our own web server. 
unsigned long millisInput[actionsAndPinsMax];

int roomId = -1;

// TODO: facilitate more than just one servo in use at any given point
// in time. 
Servo servo;
Servo servo1;
Servo servo2;

// IP of the web server.
IPAddress webServerIpAddress(192,168,0,197);
const int webServerPort = 8080;

int status = WL_IDLE_STATUS;
WiFiServer server(80);

void setup() {
  // Variable housekeeping.
  // Zero all values.
  for(int i = 0; i < actionsAndPinsMax; i++){
    actions[i] = -1;
    pins[i] = -1;
    pins2[i] = -1;
    states[i] = -1;
    millisInput[i] = 0;
  }

  // Debug pin for indiciating stuff. 
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(9600);      // initialize serial communication
  Serial.println("[DEBUG] KotakeeOS Arduino Module booting...");

  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("[ERROR] Communication with WiFi module failed! Giving up...");
    // don't continue
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("[ERROR] Please upgrade the firmware");
  }

  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("[DEBUG] Attempting to connect to Network named: ");
    Serial.println(ssid);

    status = WiFi.begin(ssid, pass);
    // wait 10 seconds for connection:
    delay(10000);
  }
  server.begin();
  printWifiStatus();

  // Now that we're online, let's ask the server what
  // actions/pins we should have. 
  moduleStartupRequest();
}


void loop() {
  readInputs(); // Read inputs if we need to. 
  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      // Read inputs if we need to for each client connected loop as well,
      // just in case so as to not block or lose any input. 
      readInputs(); 

      if (client.available()) {             // if there's bytes to read from the client,
        char c = client.read();             // read a byte, then
        //Serial.write(c);                    // print it out the serial monitor
        if (c == '\n') {                    // if the byte is a newline character
          // End of HTTP Request - client is connecting directly to the index. 
          // Send a response:
          if (currentLine.length() == 0) {
            // HTTP headers always start with a response code (e.g. HTTP/1.1 200 OK)
            // and a content-type so the client knows what's coming, then a blank line:
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println();

            // the content of the HTTP response follows the header:
            client.print("<h1>KotakeeOS Arduino Module</h1>");
            client.print("<p>Please note that this interface is meant for debugging only.<p>");
            client.print("Click <a href=\"/testRelay\">here</a> to toggle the installed relay.<br>");

            // The HTTP response ends with another blank line:
            client.println();
            // break out of the while loop:
            break;
          } else {    // if you got a newline, then clear currentLine:
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }

        // Check to see if the client request is servable. 
        // Note that here even if we get multiple requests to 
        // do something (like turn actionId 50 to on), if 
        // it's already on we don't do anything. 
        // TODO: HTTP response codes... 

        // Expect Ex) GET /stateToggle/50/1 (actionId/toState)
        if (currentLine.startsWith("GET /stateToggle/") && currentLine.endsWith(" ")) {
          handleStateToggle(currentLine, false);
        }
        // Expect Ex) GET /stateVirtualToggle/50/1 (actionId/toState)
        if (currentLine.startsWith("GET /stateVirtualToggle/") && currentLine.endsWith(" ")) {
          handleStateToggle(currentLine, true);
        }
        // Expect Ex) stateGet/50
        else if(currentLine.startsWith("GET /stateGet/") && currentLine.endsWith(" ")){
          handleStateGet(currentLine);
        }
        else if(currentLine.startsWith("GET /moduleUpdate/") && currentLine.endsWith(" ")){
          handleModuleUpdate(currentLine);
        }
      }
    }
    // close the connection:
    client.stop();
  }
}

// Called regularily with each loop - both the main loop and
// the client.connected loop to ensure no input is blocked or
// delayed. 
void readInputs(){
  bool inputDetected = false;
  // Go through all currently implemented actions. If any
  // are > 5000, they have a pin that must be read for input.
  for(int i = 0; i < actionsAndPinsMax; i++){
    if(actions[i] != -1 && actions[i] > inputActionThreshold){
      // We have an action that is an input!
      int sensorValue = digitalRead(pins[i]);

      // TODO: With this sensor value, depending on the action
      // value, do something with it. 

      // Handle Motion data.
      if(actions[i] <= motion5 && actions[i] >= motion1){
        if(sensorValue == 1){
          // Indicate motion sensor information.
          inputDetected = true;
          states[i] = 1;
        }

        if(states[i] == 1 && millis() - millisInput[i] >= inputMillisReport){
          // Time to send a report to the server. 
          moduleInput(actions[i]);
          Serial.print("[DEBUG] For actionId ");
          Serial.print(actions[i]);
          Serial.print(" at pin ");
          Serial.print(pins[i]);
          Serial.print(", read sensorValue of: ");
          Serial.println(sensorValue);

          states[i] = 0; // Reset the state back to zero between now and the next report. 
        }
      }
    }
  }

  if(inputDetected){
    digitalWrite(LED_BUILTIN, HIGH); 
  }
  else{
    digitalWrite(LED_BUILTIN, LOW); 
  }
}

void handleStateToggle(String currentLine, bool virtualCommand){
  String actionId;
  int actionIdInt;
  String toState;
  int toStateInt;

  // Get the rest of the first line. 
  String actionIdAndToState = currentLine;
  if(virtualCommand){
    actionIdAndToState.replace("GET /stateVirtualToggle/", ""); // Shed the first part. 
    Serial.print("[DEBUG] Received stateVirtualToggle command from server. actionIdAndToState is: ");
  }
  else{
    actionIdAndToState.replace("GET /stateToggle/", ""); // Shed the first part. 
    Serial.print("[DEBUG] Received stateToggle command from server. actionIdAndToState is: ");
  }
  Serial.println(actionIdAndToState);

  // Convert from String to string
  char buf[actionIdAndToState.length()];
  actionIdAndToState.toCharArray(buf, sizeof(buf));
  char *p = buf;
  char *str;
  int i = 0;
  while (((str = strtok_r(p, "/", &p)) != NULL) && i < 2){ // delimiter is /
    if(i == 0){
      actionId = str;
      actionIdInt = actionId.toInt();
    }
    else if(i == 1){
      toState = str;
      toStateInt = toState.toInt();
    }
    i++;
  }

  // Get the id of the action.
  int actionIndex = findActionId(actionIdInt);

  if(actionIndex >= 0){
    if (states[actionIndex] != toStateInt) { 
      Serial.print("[DEBUG] Instructed to toggle action " + actionId + " from state ");
      Serial.print(states[actionIndex]);
      Serial.print(" to " + toState + ". Executing on pin ");
      Serial.print(pins[actionIndex]);
      Serial.println("...");

      if(actions[actionIndex] <= remote20 && actions[actionIndex] >= remote1){
        Serial.println("[DEBUG] Activating Servo...");
        // 10 off, 11 active, 12 on. 
        if(toStateInt == 12 || toStateInt == 10){
          // If we're ready, let's become active. 
          servoPressButton(actionIndex, toStateInt, virtualCommand);
        }
        else{
          Serial.println("[WARNING] Illegal action was requested! Ignoring...");
        }
      }
      else if(actions[actionIndex] <= switch5 && actions[actionIndex] >= switch1){
        Serial.println("[DEBUG] Activating Servos...");
        // 20 off, 21 active, 22 on. 
        if(toStateInt == 22 || toStateInt == 20){
          // If we're ready, let's become active. 
          servoPressSwitch(actionIndex, toStateInt, virtualCommand);
        }
        else{
          Serial.println("[WARNING] Illegal action was requested! Ignoring...");
        }
      }
      else{
        // Default binary 0, 1. 
        if(toStateInt == 1){
          Serial.println("[DEBUG] Turning on...");
          // If it's off, turn it on. 
          if(!virtualCommand)
            digitalWrite(pins[actionIndex], HIGH);
          states[actionIndex] = 1;
        }
        else{
          Serial.println("[DEBUG] Turning off...");
          // If it's on, turn it off
          if(!virtualCommand)
            digitalWrite(pins[actionIndex], LOW);
          states[actionIndex] = 0;
        }
        // Inform the web server.
        moduleStateUpdate(actionIdInt);
      }
    }
    else{
      Serial.print("[WARNING] Instructed to toggle action " + actionId + " from state ");
      Serial.print(states[actionIndex]);
      Serial.println(" to " + toState + ". Request Ignored.");
    }
  }
  else{
    Serial.print("[WARNING] Instructed to toggle action " + actionId + ", but actionId does is not Implemented!");
  }
}

void handleStateGet(String currentLine){
  String actionIdStr = currentLine;
  actionIdStr.replace("GET /stateGet/", ""); // Shed the first part. 
  int actionId = actionIdStr.toInt();
  Serial.print("[DEBUG] stateGet request received. actionId is: ");
  Serial.println(actionId);
  moduleStateUpdate(actionId);
}

void handleModuleUpdate(String currentLine){
  // Get the rest of the first line. 
  String actionsAndPins = currentLine;
  actionsAndPins.replace("GET /moduleUpdate/", ""); // Shed the first part. 
  Serial.print("[DEBUG] Given action and pin information from server. actionsAndPins is: ");
  Serial.println(actionsAndPins);

  // Convert from String to string
  char buf[actionsAndPins.length()];
  actionsAndPins.toCharArray(buf, sizeof(buf));
  char *p = buf;
  char *str;
  int i = 0;
  while ((str = strtok_r(p, "/", &p)) != NULL){ // delimiter is /
    if(i == 0){
      // First item is always the id. 
      roomId = atoi(str);
    }
    else{
      if(i%2 == 0){
        // Even. (i.e. 2, 4, 6...)
        // Since this is always the second of the pair, 
        // we know the aciton already exists. check it and
        // initialize the pin accordingly. 
        if(actions[(i-1)/2] <= remote20 && actions[(i-1)/2] >= remote1){
          // Servo usage.
          pins[(i-1)/2] = atoi(str);
          initializeServos((i-1)/2);
        }
        else if(actions[(i-1)/2] <= switch5 && actions[(i-1)/2] >= switch1){
          // We expect, in the case of two pins, a 4 digit
          // string regardless. 
          char pin1Str[3];
          memcpy( pin1Str, &str[0], 2 );
          pin1Str[2] = '\0'; // Null terminate the substring. Yay C++...
          char pin2Str[3];
          memcpy( pin2Str, &str[2], 2 );
          pin2Str[2] = '\0'; // Null terminate the substring. Yay C++...
          pins[(i-1)/2] = atoi(pin1Str);
          pins2[(i-1)/2] = atoi(pin2Str);
          initializeServos((i-1)/2);
        }
        else if(actions[(i-1)/2] >= inputActionThreshold){
          // Initialize the pin as input rather than output. 
          pins[(i-1)/2] = atoi(str);
          initializePinInput((i-1)/2);
        }
        else {
          pins[(i-1)/2] = atoi(str);
          initializePin((i-1)/2);
        }
      }
      else{
        // Odd. (1, 3, 5...)
        actions[i/2] = atoi(str);
        // Initialize the state. This initial state depends on the 
        // action type. 
        if(actions[i/2] <= remote20 && actions[i/2] >= remote1){
          states[i/2] = 10; // 10 is off, 11 is active, 12 is on. 
        }
        else if(actions[i/2] <= switch5 && actions[i/2] >= switch1){
          states[i/2] = 20; // 20 is off, 21 is active, 22 is on. 
        }
        else if(actions[i/2] >= inputActionThreshold){
          // For input actions, we're still using 0 as our default state.
          states[i/2] = 0;
        }
        else{
          states[i/2] = 0; // Default as binary.
        }
      }
    }
    i++;
  }
  Serial.print("[DEBUG] roomId: ");
  Serial.println(roomId);
  Serial.print("[DEBUG] Actions: ");
  for(int i = 0; i < actionsAndPinsMax; i++)
  {
    int actionId = actions[i];
    if(actionId != -1){
      Serial.print(actionId);
      Serial.print(" ");
    }
  }
  Serial.println("");
  Serial.print("[DEBUG] Pins: ");
  for(int i = 0; i < actionsAndPinsMax; i++)
  {
    int pin = pins[i];
    if(pin != -1){
      Serial.print(pin);
      Serial.print(" ");
    }
    int pin2 = pins2[i];
    if(pin2 != -1){
      Serial.print("and ");
      Serial.print(pin2);
      Serial.print(" ");
    }
  }
  Serial.println("");
  Serial.print("[DEBUG] States: ");
  for(int i = 0; i < actionsAndPinsMax; i++)
  {
    int state = states[i];
    if(state != -1){
      Serial.print(state);
      Serial.print(" ");
    }
  }
  Serial.println("");
  // We've now populated our actions and pins array and
  // are ready to go. 

  // Send our initial state notification to web server.
  initialStateUpdate();
}

// Helper function. Given an actionId, get the index of
// both the action and the pin. If not found, return
// -1. 
int findActionId(int actionId){
  for(int i = 0; i < actionsAndPinsMax; i++)
  {
    if(actionId == actions[i]){
      return i;
    }
  }
  return -1;
}

// For all pins in the pins array, initialize them. 
// TODO: Obsolete.
void initializePins(){
  for(int i = 0; i < actionsAndPinsMax; i++){
    int pin = pins[i];
    if(pin > 0){
      initializePin(i);
    }
  }
}

// Takes in given actionIndex The latter is only for
// Serial debugging. 
void initializePin(int actionIndex){
  pinMode(pins[actionIndex], OUTPUT);
  Serial.print("[DEBUG] Initialized pin ");
  Serial.print(pins[actionIndex]);
  Serial.print(" with OUTPUT for actionId ");
  Serial.println(actions[actionIndex]);
}

// Takes in actionindex to initialize a Pin for input,
// rather than output. 
void initializePinInput(int actionIndex){
  pinMode(pins[actionIndex], INPUT);
  Serial.print("[DEBUG] Initialized pin ");
  Serial.print(pins[actionIndex]);
  Serial.print(" with INPUT for actionId ");
  Serial.println(actions[actionIndex]);
}

// Upon startup, make sure all servos are at the neutral position.
void initializeServos(int actionIndex){
  // Activate the servo. We expect to be in neutral.
  servo.attach(pins[actionIndex]);
  servo.write(servoNeutral);
  delay(servoActionWait);
  servo.detach();

  Serial.print("[DEBUG] Initialized pin ");
  Serial.print(pins[actionIndex]);

  if(pins2[actionIndex] != -1){
    servo.attach(pins2[actionIndex]);
    servo.write(servoNeutral);
    delay(servoActionWait);
    servo.detach();
    Serial.print(" and pin ");
    Serial.print(pins2[actionIndex]);
  }
  Serial.print(" with a Servo object for actionId ");
  Serial.println(actions[actionIndex]);
}

// Call moduleStateUpdate for all implemented actions.
void initialStateUpdate(){
  for(int i = 0; i < actionsAndPinsMax; i++){
    int actionId = actions[i];
    if(actionId > 0){
      moduleStateUpdate(actionId);
    }
  }
}

// Given an action index that is presumably for a remote action,
// Set ourselves as state active, notify the server, perform 
// the action, return to neutral state, and notify the server
// again. Also takes in a toStateInt to know what to tell
// the server at the end of the procedure. 
void servoPressButton(int actionIndex, int toStateInt, bool virtualCommand){
  // Sanity Check:
  if(toStateInt == 12 || toStateInt == 10){
    if(!virtualCommand){
      int pin = pins[actionIndex];
      // Notify the server of our new state. 
      states[actionIndex] = 11; // 11 = active.
      moduleStateUpdate(actions[actionIndex]);

      // Activate the servo. We expect to be in neutral.
      servo.attach(pin);
      servo.write(servoActive);
      delay(servoActionWait);
      servo.write(servoNeutral);
      delay(servoActionWait);
      servo.detach();
    }

    // Notify the server of our new state. 
    states[actionIndex] = toStateInt;
    moduleStateUpdate(actions[actionIndex]);
  }
}

// Given an action index that is presumably for a switch action,
// Set ourselves as state active, notify the server, perform 
// the action, return to neutral state, and notify the server
// again. Also takes in a toStateInt to know what to tell
// the server at the end of the procedure. 
void servoPressSwitch(int actionIndex, int toStateInt, bool virtualCommand){
  // Sanity Check:
  if(toStateInt == 22 || toStateInt == 20){
    if(!virtualCommand){
      int pin;
      if(toStateInt == 22){
        // Pin2 is to turn on. 
        pin = pins2[actionIndex];
      }
      else{
        // Pin1 is to turn off. 
        pin = pins[actionIndex];
      }
      // Notify the server of our new state. 
      states[actionIndex] = 21; // 21 = active.
      moduleStateUpdate(actions[actionIndex]);

      // Activate the servo. We expect to be in neutral.
      servo.attach(pin);
      servo.write(servoActive);
      delay(servoActionWait);
      servo.write(servoNeutral);
      delay(servoActionWait);
      servo.detach();
    }

    // Notify the server of our new state. 
    states[actionIndex] = toStateInt;
    moduleStateUpdate(actions[actionIndex]);
  }
}

// Given current state of given actionId, notify the web server!
void moduleStateUpdate(int actionId){
  WiFiClient webServer;

  int i = findActionId(actionId);
  if(i < 0){
    Serial.print("[ERROR] moduleStateUpdate was unable to find actionId ");
    Serial.println(actionId);
  }

  String toState = String(states[i]);
  String actionIdStr = String(actionId);
  String roomIdStr = String(roomId);

  // Make a basic HTTP request:
  if(webServer.connect(webServerIpAddress, webServerPort)){
    webServer.println("GET /moduleStateUpdate/"+roomIdStr+"/"+actionIdStr+"/" + toState);
    webServer.println("Connection: close");
    webServer.println();
    Serial.println("[DEBUG] Queried Web Server successfully with roomId "+ roomIdStr+ " and actionId "+actionIdStr+" and state " + toState + ".");
    webServer.stop();
  }
  else{
    Serial.println("[ERROR] querying Web Server with roomId "+ roomIdStr+ " and actionId "+actionIdStr+" and state " + toState + "...");
  }
}

// Given a need to report input to the web server, do so!
// Takes in actionId (int) and sends the "state," aka the 
// sensorValue. Is also in charge of shutting down a pin
// that is spamming requests.  
void moduleInput(int actionId) {
  WiFiClient webServer;

  int i = findActionId(actionId);
  if(i < 0){
    Serial.print("[ERROR] moduleInput was unable to find actionId ");
    Serial.println(actionId);
  }

  String toState = String(states[i]);
  String actionIdStr = String(actionId);
  String roomIdStr = String(roomId);

  if(millis() - millisInput[i] < fatalInputPinMillis){
    // Sanity check. If we're attempting to query the server for a second
    // time within the fatalInputPinMillis timespan for this particular
    // pin, shut the entire action down. 
    Serial.println("[ERROR] moduleInput was queried too many times at once! Eliminating "+ roomIdStr+ " and actionId "+actionIdStr+".");
    actions[i] = -1;
    pins[i] = -1;
    pins2[i] = -1;
    states[i] = -1;
    millisInput[i] = -1;
    return;
  }
  // Otherwise we're good.
  millisInput[i] = millis();

  // Make a basic HTTP request:
  if(webServer.connect(webServerIpAddress, webServerPort)){
    webServer.println("GET /moduleInput/"+roomIdStr+"/"+actionIdStr+"/" + toState);
    webServer.println("Connection: close");
    webServer.println();
    Serial.println("[DEBUG] moduleInput Queried Web Server successfully with roomId "+ roomIdStr+ " and actionId "+actionIdStr+" and state " + toState + ".");
    webServer.stop();
  }
  else{
    Serial.println("[ERROR] moduleInput failed querying Web Server with roomId "+ roomIdStr+ " and actionId "+actionIdStr+" and state " + toState + "...");
  }
}

// Upon startup, request the server to send our information! 
void moduleStartupRequest(){
  WiFiClient webServer;
  String ip = IpAddress2String(WiFi.localIP());

  // Make a basic HTTP request:
  if(webServer.connect(webServerIpAddress, webServerPort)){
    webServer.println("GET /moduleStartup/" + ip);
    webServer.println("Connection: close");
    webServer.println();
    Serial.println("[DEBUG] Queried Web Server successfully with moduleStartup with ipAddress " + ip + ".");
    webServer.stop();
  }
  else{
    Serial.println("[ERROR] querying Web Server with moduleStartup with ipAddress " + ip + "...");
  }
}

// author apicquot from https://forum.arduino.cc/index.php?topic=228884.0
String IpAddress2String(const IPAddress& ipAddress)
{
  return String(ipAddress[0]) + String(".") +
          String(ipAddress[1]) + String(".") +
          String(ipAddress[2]) + String(".") +
          String(ipAddress[3]);
}

void printWifiStatus() {
  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("[DEBUG] Arduino Local IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("[DEBUG] Arduino signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
