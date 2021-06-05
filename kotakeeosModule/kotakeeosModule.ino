/*
  KotakeeOS Module

  Uses WifiNina Simple Web Server Wifi example as a baseline. 

  Universal code base for all KotakeeOS arduino nodes with logic for all 
  nodes included. TODO: Add more info and flush out design.

  Seriously, this is a terrible web server, write a better one! 
*/
#include <SPI.h>
#include <WiFiNINA.h>

#include "arduino_secrets.h" 

char ssid[] = SECRET_SSID;  
char pass[] = SECRET_PASS;   
int keyIndex = 0;     

// Hard coded array since we can only handle up to 25 actions
// (arduinos only have up so many I/O pins. )
const int actionsAndPinsMax = 25;
int actions[actionsAndPinsMax];
int pins[actionsAndPinsMax];
int states[actionsAndPinsMax];

int moduleId = -1;

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
    states[i] = -1;
  }

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
  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
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
          String actionId;
          int actionIdInt;
          String toState;
          int toStateInt;

          // Get the rest of the first line. 
          String actionIdAndToState = currentLine;
          actionIdAndToState.replace("GET /stateToggle/", ""); // Shed the first part. 
          Serial.print("[DEBUG] Received stateToggle command from server. actionIdAndToState is: ");
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
              if(toStateInt == 1){
                // If it's off, turn it on. 
                digitalWrite(pins[actionIndex], HIGH);
                states[actionIndex] = 1;
              }
              else{
                // If it's on, turn it off
                digitalWrite(pins[actionIndex], LOW);
                states[actionIndex] = 0;
              }
              // Inform the web server.
              moduleStateUpdate(actionIdInt);
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
        // Expect Ex) stateGet/50
        else if(currentLine.startsWith("GET /stateGet/") && currentLine.endsWith(" ")){
          String actionIdStr = currentLine;
          actionIdStr.replace("GET /stateGet/", ""); // Shed the first part. 
          int actionId = actionIdStr.toInt();
          Serial.print("[DEBUG] stateGet request received. actionId is: ");
          Serial.println(actionId);
          moduleStateUpdate(actionId);
        }
        else if(currentLine.startsWith("GET /moduleUpdate/") && currentLine.endsWith(" ")){
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
              moduleId = atoi(str);
            }
            else{
              if(i%2 == 0){
                // Even. (i.e. 2, 4, 6...)
                pins[(i-1)/2] = atoi(str);
              }
              else{
                // Odd. (1, 3, 5...)
                actions[i/2] = atoi(str);
                states[i/2] = 0; // Initialize all states. 
                // TODO: For states that aren't binary, initialize them
                // here given the actionId. 
              }
            }
            i++;
          }
          Serial.print("[DEBUG] ModuleId: ");
          Serial.println(moduleId);
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
          }
          Serial.println("");
          // We've now populated our actions and pins array and
          // are ready to go. 

          // Initialize all pins.
          initializePins();

          // Send our initial state notification to web server.
          initialStateUpdate();
        }
      }
    }
    // close the connection:
    client.stop();
  }
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
void initializePins(){
  for(int i = 0; i < actionsAndPinsMax; i++){
    int pin = pins[i];
    if(pin > 0){
      pinMode(pin, OUTPUT);
      Serial.print("[DEBUG] initialized pin ");
      Serial.print(pin);
      Serial.println(" with OUTPUT for actionId " + actions[i]);
    }
  }
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
  String moduleIdStr = String(moduleId);

  // Make a basic HTTP request:
  if(webServer.connect(webServerIpAddress, webServerPort)){
    webServer.println("GET /moduleStateUpdate/"+moduleIdStr+"/"+actionIdStr+"/" + toState);
    webServer.println("Connection: close");
    webServer.println();
    Serial.println("[DEBUG] Queried Web Server successfully with moduleId "+ moduleIdStr+ " and actionId "+actionIdStr+" and state " + toState + ".");
    webServer.stop();
  }
  else{
    Serial.println("[ERROR] querying Web Server with moduleId "+ moduleIdStr+ " and actionId "+actionIdStr+" and state " + toState + "...");
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
