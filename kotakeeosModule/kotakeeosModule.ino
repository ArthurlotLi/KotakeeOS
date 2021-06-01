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
const int relayPin = 13; 
bool relayPinState = false;
// IP of the web server.
IPAddress webServerIpAddress(192,168,0,197);
const int webServerPort = 8080;

int status = WL_IDLE_STATUS;
WiFiServer server(80);

void setup() {
  Serial.begin(9600);      // initialize serial communication
  pinMode(relayPin, OUTPUT);      // set the LED pin mode

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
    Serial.println(ssid);                   // print the network name (SSID);

    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);
    // wait 10 seconds for connection:
    delay(10000);
  }
  server.begin();                           // start the web server on port 80
  printWifiStatus();                        // you're connected now, so print out the status

  // Send out initial state notification to web server since we just restarted. 
  moduleStateUpdate();
}


void loop() {
  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    //Serial.println("new client");           // print a message out the serial port
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
        if (currentLine.endsWith("GET /stateToggle/50/1")) {
          if (!relayPinState) { 
            Serial.println("[DEBUG] Instructed to turn on light when it was off. Executing...");
            // If it's off, turn it on. 
            digitalWrite(relayPin, HIGH);
            relayPinState = true;
            // Inform the web server.
            moduleStateUpdate();
          }
          else{
            Serial.println("[WARNING] Was instructed to turn on light when it was already on. Request ignored.");
          }
        }
        else if(currentLine.endsWith("GET /stateToggle/50/0")){
          if(relayPinState) {
            Serial.println("[DEBUG] Instructed to turn off light when it was on. Executing...");
            // if it's on, turn it off.  
            digitalWrite(relayPin, LOW);
            relayPinState = false;
            // Inform the web server.
            moduleStateUpdate();
          }
          else{
            Serial.println("[WARNING] Was instructed to turn off light when it was already off. Request ignored.");
          }
        }
        else if(currentLine.endsWith("GET /stateGet/50")){
          Serial.println("[DEBUG] stateGet request received. Replying...");
          moduleStateUpdate();
        }
      }
    }
    // close the connection:
    client.stop();
    //Serial.println("client disconnected");
  }
}

// Given current state, notify the web server!
void moduleStateUpdate(){
  WiFiClient webServer;

  String toState;
  if(relayPinState){
    toState = String(1);
  }
  else{
    toState = String(0);
  }

  // Make a basic HTTP request:
  if(webServer.connect(webServerIpAddress, webServerPort)){
    webServer.println("GET /moduleStateUpdate/1/50/" + toState);
    webServer.println("Connection: close");
    webServer.println();
    Serial.println("[DEBUG] Queried Web Server successfully with state " + toState + ".");
    webServer.stop();
  }
  else{
    Serial.println("[ERROR] querying Web Server with state " + toState + "...");
  }
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
