/*
  KotakeeOS Module

  Uses WifiNina Simple Web Server Wifi example as a baseline. 

  Universal code base for all KotakeeOS arduino nodes with logic for all 
  nodes included. TODO: Add more info and flush out design.
*/
#include <SPI.h>
#include <WiFiNINA.h>
#include <Servo.h>
#include <DHT.h> // Thermometers
#include <FastLED.h> // LEDStrips

#include "arduino_secrets.h" 

#define DHTTYPE DHT22  // We're using a Chinese knock-off of a DHT22. 
#define LED_TYPE    WS2811
#define COLOR_ORDER GRB
#define BRIGHTNESS          96
#define FRAMES_PER_SECOND  120

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
const int door1 = 5150;
const int door5 = 5154;
const int temp1 = 5250;
const int temp5 = 5254;
const int knob1 = 450;
const int knob5 = 454;
const int ledStrip1 = 1000;
const int ledStrip10 = 1009;

const int servoNeutral = 170; // 180 is out of motion and will cause buzzing.
const int servoActive = 110;
const int servoActionWait = 600; // time to move arm between neutral and active.

// Declare an alternate set of servo variables to use when 
// controlling stuff like the AC knob. 
const int servoAltNeutral = 8; // Item off
const int servoAltActive = 170; // Item on
const int servoAltActionWait = 700;

const int temperatureReadingInterval = 10000; // Minimum amount of time between temp reads. 

const int maxLEDs = 100; // What to initialize our arrays of CRGBs to at the start. 
// These are all the LED modes that we've implemented. 
const int ledModeRainbow = 101;
const int ledModeRainbowWithGlitter = 102;
const int ledModeConfetti = 103;
const int ledModeSinelon = 104;
const int ledModeJuggle = 105;
const int ledModeBpm = 106;

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
int info[actionsAndPinsMax]; // Area for misc information depending on the action. (Ex) LEDS need to know size of LED strip.)
int states[actionsAndPinsMax];
// Used to detect and shut down a pin that isn't connected so we don't
// unintentinally DDOS our own web server. 
unsigned long millisInput[actionsAndPinsMax];

int roomId = -1;

// We only support a certain number of servos per action.
Servo servo;
Servo servo1;
Servo servo2;
// We only support a certain number of total temp sensors. 
// Just put garbage for the initialization. We'll assign it
// properly if we actually do implement one according to the 
// server. 
DHT dht(-1, DHTTYPE);

// We support up to 10 LED light strips. 
CRGB leds1[maxLEDs];
CRGB leds2[maxLEDs];
CRGB leds3[maxLEDs];
CRGB leds4[maxLEDs];
CRGB leds5[maxLEDs];
CRGB leds6[maxLEDs];
CRGB leds7[maxLEDs];
CRGB leds8[maxLEDs];
CRGB leds9[maxLEDs];
CRGB leds10[maxLEDs];
uint8_t gHue = 0; // rotating "base color" used by many LED patterns.

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
    info[i] = -1;
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
  updateLEDs();
  WiFiClient client = server.available();   // listen for incoming clients

  if (client) {                             // if you get a client,
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected()) {            // loop while the client's connected
      // Read inputs if we need to for each client connected loop as well,
      // just in case so as to not block or lose any input. 
      readInputs(); 
      updateLEDs();

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

      // TODO: With this sensor value, depending on the action
      // value, do something with it. 

      // Handle Motion data.
      if(actions[i] <= motion5 && actions[i] >= motion1){
        int sensorValue = digitalRead(pins[i]);
        if(sensorValue == 1){
          // Indicate motion sensor information.
          inputDetected = true;
          states[i] = 1;
        }

        if(states[i] == 1 && millis() - millisInput[i] >= inputMillisReport){
          // Time to send a report to the server. 
          moduleInput(actions[i], "");
          Serial.print("[DEBUG] For actionId ");
          Serial.print(actions[i]);
          Serial.print(" at pin ");
          Serial.print(pins[i]);
          Serial.print(", read sensorValue of: ");
          Serial.println(sensorValue);

          states[i] = 0; // Reset the state back to zero between now and the next report. 
        }
      }
      // Handle Door data
      else if(actions[i] <= door5 && actions[i] >= door1){
        int sensorValue = digitalRead(pins[i]);
        if(sensorValue == 1 && states[i] == 0){
          // Door was open and now it is closed!
          inputDetected = true;
          states[i] = 1;
          // Time to send a report to the server. 
          moduleInput(actions[i], "");
        }
        else if (sensorValue == 0 && states[i] == 1){
          // Door was closed and now it is open!
          inputDetected = true;
          states[i] = 0;
          // Time to send a report to the server. 
          moduleInput(actions[i], "");
        }
        // Otherwise, no change, do nothing. 
      }
      else if(actions[i] <= temp5 && actions[i] >= temp1){
        // Do not read temp data unless we've waited the appropriate
        // amount of time since the last temp transmission.
        if((millis() - millisInput[i]) >= temperatureReadingInterval){
          float hum = dht.readHumidity();
          float temp= dht.readTemperature();
          //Print temp and humidity values to serial monitor
          Serial.print("[INFO] Read DHT22 Sensor Info. Humidity: ");
          Serial.print(hum);
          Serial.print(" %, Temp: ");
          Serial.print(temp);
          Serial.println(" Celsius");
          // We don't use states for these, instead we just
          // directly plug a string to the server. 
          String tempReport = String(temp) + "_" + String(hum);
          moduleInput(actions[i], tempReport);
        }
      }
      // Else the action is not implemented. Don't do anything. 
    }
  }

  if(inputDetected){
    digitalWrite(LED_BUILTIN, HIGH); 
  }
  else{
    digitalWrite(LED_BUILTIN, LOW); 
  }
}

// Called regularily with each loop. Implements all of the 
// LEDstrip functions that we support. 
void updateLEDs(){
  // Don't update every time. 
  EVERY_N_MILLISECONDS( 20 ) { gHue++; }
  EVERY_N_MILLISECONDS( 1000/FRAMES_PER_SECOND ) {  
    for(int i = 0; i < actionsAndPinsMax; i++){
      if(actions[i] != -1 && actions[i] <= ledStrip10 && actions[i] >= ledStrip1){
        // We have an action that is an LED strip!

        if(states[i] > 100){
          // Don't do anything if the state is shut down. 
          // Get the correct array to use.
          CRGB* leds = obtainCRGBArray(actions[i]);
          int numLeds = info[i];

          switch(states[i]){
            case ledModeRainbow: 
              rainbow(leds,numLeds);
              break;
            case ledModeRainbowWithGlitter:
              rainbowWithGlitter(leds, numLeds);
              break;
            case ledModeConfetti:
              confetti(leds, numLeds);
              break;
            case ledModeSinelon:
              sinelon(leds, numLeds);
              break;
            case ledModeJuggle:
              juggle(leds, numLeds);
              break;
            case ledModeBpm:
              bpm(leds, numLeds);
              break;
          }
          // Update all LED strips attached to this module. 
          FastLED.show();  
        }
      }
    }
  }
}

/*
  LED modes from FastLED's examples.
*/
void rainbow(CRGB* leds, int numLeds) 
{
  // FastLED's built-in rainbow generator
  fill_rainbow( leds, numLeds, gHue, 7);
}

void rainbowWithGlitter(CRGB* leds, int numLeds) 
{
  // built-in FastLED rainbow, plus some random sparkly glitter
  rainbow(leds, numLeds);
  addGlitter(leds, numLeds, 80);
}

void addGlitter( CRGB* leds, int numLeds, fract8 chanceOfGlitter) 
{
  if( random8() < chanceOfGlitter) {
    leds[ random16(numLeds) ] += CRGB::White;
  }
}

void confetti(CRGB* leds, int numLeds) 
{
  // random colored speckles that blink in and fade smoothlyled
  fadeToBlackBy( leds, numLeds, 10);
  int pos = random16(numLeds);
  leds[pos] += CHSV( gHue + random8(64), 200, 255);
}

void sinelon(CRGB* leds, int numLeds)
{
  // a colored dot sweeping back and forth, with fading trails
  fadeToBlackBy( leds, numLeds, 20);
  int pos = beatsin16( 13, 0, numLeds-1 );
  leds[pos] += CHSV( gHue, 255, 192);
}

void bpm(CRGB* leds, int numLeds)
{
  // colored stripes pulsing at a defined Beats-Per-Minute (BPM)
  uint8_t BeatsPerMinute = 62;
  CRGBPalette16 palette = PartyColors_p;
  uint8_t beat = beatsin8( BeatsPerMinute, 64, 255);
  for( int i = 0; i < numLeds; i++) { //9948
    leds[i] = ColorFromPalette(palette, gHue+(i*2), beat-gHue+(i*10));
  }
}

void juggle(CRGB* leds, int numLeds) {
  // eight colored dots, weaving in and out of sync with each other
  fadeToBlackBy( leds, numLeds, 20);
  byte dothue = 0;
  for( int i = 0; i < 8; i++) {
    leds[beatsin16( i+7, 0, numLeds-1 )] |= CHSV(dothue, 200, 255);
    dothue += 32;
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
      else if(actions[actionIndex] <= knob5 && actions[actionIndex] >= knob1){
        Serial.println("[DEBUG] Activating Servo Knob...");
        if(toStateInt == 32 || toStateInt == 30){
          servoTurnKnob(actionIndex, toStateInt, virtualCommand);
        }
        else{
          Serial.println("[WARNING] Illegal action was requested! Ignoring...");
        }
      }
      else if(actions[actionIndex] <= ledStrip10 && actions[actionIndex] >= ledStrip1){
        Serial.println("[DEBUG] Activating LED Strip...");
        if(toStateInt >= 100){
          activateLEDStripMode(actionIndex, toStateInt, virtualCommand);
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
        else if(actions[(i-1)/2] <= knob5 && actions[(i-1)/2] >= knob1){
          // Servo usage.
          pins[(i-1)/2] = atoi(str);
          initializeKnobServo((i-1)/2);
        }
        else if(actions[(i-1)/2] <= ledStrip10 && actions[(i-1)/2] >= ledStrip1){
          // Initialize for LED strip usage. 
          // We expect a 5 digit string, with the latter number being
          // the info field i.e. NUM_LEDs. Ex) "01.060"
          char pin1Str[3];
          memcpy( pin1Str, &str[0], 2 );
          pin1Str[2] = '\0'; // Null terminate the substring. Yay C++...
          char infoStr[3];
          memcpy( infoStr, &str[2], 3 );
          infoStr[2] = '\0'; // Null terminate the substring. Yay C++...
          pins[(i-1)/2] = atoi(pin1Str);
          info[(i-1)/2] = atoi(infoStr);
          initializeLEDStrip((i-1)/2);
        }
        else if(actions[(i-1)/2] >= inputActionThreshold){
          // Special input case, need to initalize sensor object. 
          if(actions[(i-1)/2] <= temp5 && actions[(i-1)/2] >= temp1){
            pins[(i-1)/2] = atoi(str);
            initializeDHT((i-1)/2);
          }
          else{
            // Initialize the pin as input rather than output. 
            pins[(i-1)/2] = atoi(str);
            initializePinInput((i-1)/2);
          }
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
        else if(actions[i/2] <= knob5 && actions[i/2] >= knob1){
          states[i/2] = 30; // 30 is off, 31 is active, 32 is on. 
        }
        else if(actions[i/2] <= ledStrip10 && actions[i/2] >= ledStrip1){
          // Our state represents the types of LED modes we've implemented. 
          // 100 is off. 
          states[i/2] = 100;
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
  Serial.print("[DEBUG] Info: ");
  for(int i = 0; i < actionsAndPinsMax; i++)
  {
    int infoVal = info[i];
    if(infoVal != -1){
      Serial.print(infoVal);
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

// Upon startup, make sure all servos are at the neutral position.
void initializeKnobServo(int actionIndex){
  // Activate the servo. We expect to be in neutral.
  servo.attach(pins[actionIndex]);
  servo.write(servoAltNeutral);
  delay(servoActionWait);
  servo.detach();

  Serial.print("[DEBUG] Initialized pin ");
  Serial.print(pins[actionIndex]);
  Serial.print(" with a knob Servo object for actionId ");
  Serial.println(actions[actionIndex]);
}

// Upon startup, initialize the FastLED object. Note that we
// expect the pin and the info array to be filled out here,
// the latter being the number of LEDs in the strip. 
void initializeLEDStrip(int actionIndex){
  int pin = pins[actionIndex];
  int numLEDs = info[actionIndex];
  // Get the correct array to use.
  CRGB* leds = obtainCRGBArray(actions[actionIndex]);

  // Well, FastLED works on the assembly level and generates
  // code for each pin that we use. this means that I HAVE
  // to specify a constant for compilation. Given my system's
  // run-time defined pin, we can use a workaround. This WILL 
  // take up excessive memory (More than a thousand bytes per
  // pin), but I think that's okay. That's how the cookie
  // crumbles when you try to do more specific things with 
  // a general light hobbyist microcontroller library. 
  switch (pin) {
    case 1:FastLED.addLeds<LED_TYPE,1,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 2:FastLED.addLeds<LED_TYPE,2,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 3:FastLED.addLeds<LED_TYPE,3,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 4:FastLED.addLeds<LED_TYPE,4,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 5:FastLED.addLeds<LED_TYPE,5,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 6:FastLED.addLeds<LED_TYPE,6,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 7:FastLED.addLeds<LED_TYPE,7,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 8:FastLED.addLeds<LED_TYPE,8,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 9:FastLED.addLeds<LED_TYPE,9,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 10:FastLED.addLeds<LED_TYPE,10,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 11:FastLED.addLeds<LED_TYPE,11,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 12:FastLED.addLeds<LED_TYPE,12,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 13:FastLED.addLeds<LED_TYPE,13,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 14:FastLED.addLeds<LED_TYPE,14,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 15:FastLED.addLeds<LED_TYPE,15,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 16:FastLED.addLeds<LED_TYPE,16,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 17:FastLED.addLeds<LED_TYPE,17,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 18:FastLED.addLeds<LED_TYPE,18,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 19:FastLED.addLeds<LED_TYPE,19,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 20:FastLED.addLeds<LED_TYPE,20,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;
    case 21:FastLED.addLeds<LED_TYPE,21,COLOR_ORDER>(leds, numLEDs).setCorrection(TypicalLEDStrip); break;   
    default:
      Serial.print("[ERROR] Failed to initalize pin ");
      Serial.print(pin);
      Serial.print(" with FastLED for actionId ");
      Serial.println(actions[actionIndex]);
      return;
  }

  // Clear the strip in case it had something on it. 
  for(int whiteLed = 0; whiteLed < numLEDs; whiteLed = whiteLed + 1) {
    leds[whiteLed] = CRGB::Black;
  }
  FastLED.show();
  delay(100);

  Serial.print("[DEBUG] Initialized pin ");
  Serial.print(pin);
  Serial.print(" with a FastLED object for actionId ");
  Serial.println(actions[actionIndex]);
}

// Upon startup, initialize the DHT sensor. TODO: currently only
// supports a single senor per module. 
void initializeDHT(int actionIndex){
  dht = DHT(pins[actionIndex], DHTTYPE);
  dht.begin(); // Start it up!

  Serial.print("[DEBUG] Initialized pin ");
  Serial.print(pins[actionIndex]);
  Serial.print(" with a DHT22 object for actionId ");
  Serial.println(actions[actionIndex]);
}

// Helper function - given the actionId for LEDStrips,
// return the CRGB array that matches that actionId. 
// I know, not the greatest but I think it's the best
// I can do for now. 
CRGB * obtainCRGBArray(int actionId){
  switch(actionId){
    case(ledStrip1):
      return leds1;
    case(ledStrip1+1):
      return leds2;
    case(ledStrip1+2):
      return leds3;
    case(ledStrip1+3):
      return leds4;
    case(ledStrip1+4):
      return leds5;
    case(ledStrip1+5):
      return leds6;
    case(ledStrip1+6):
      return leds7;
    case(ledStrip1+7):
      return leds8;
    case(ledStrip1+8):
      return leds9;
    default:
      return leds10;
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

// Unlike servoPressButton, we do not return to the
// neutral state after activating one state or another. 
// uses ALT constant variables for servos.
void servoTurnKnob(int actionIndex, int toStateInt, bool virtualCommand){
  // Sanity Check:
  if(toStateInt == 32 || toStateInt == 30){
    if(!virtualCommand){
      int pin = pins[actionIndex];
      // Notify the server of our new state. 
      states[actionIndex] = 31; // 31 = active.
      moduleStateUpdate(actions[actionIndex]);

      int servoToWrite;
      if(toStateInt == 32){
        // Turn on
        servoToWrite = servoAltActive;
      }
      else{
        // Turn off
        servoToWrite = servoAltNeutral;
      }
      servo.attach(pin);
      servo.write(servoToWrite);
      delay(servoAltActionWait);
      servo.detach();
    }

    // Notify the server of our new state. 
    states[actionIndex] = toStateInt;
    moduleStateUpdate(actions[actionIndex]);
  }
}

// Depending on the given state, do something with our LED.
// state 100 representes off.  
void activateLEDStripMode(int actionIndex, int toStateInt, bool virtualCommand){
  // Sanity Check:
  if(toStateInt >= 100){
    switch(toStateInt){
      case ledModeRainbow: 
      case ledModeRainbowWithGlitter:
      case ledModeConfetti:
      case ledModeSinelon:
      case ledModeJuggle:
      case ledModeBpm:
        // In the case that we got a mode we know, don't turn off. 
        // We'll handle the actual execution during the main loop. 
        states[actionIndex] = toStateInt; // 11 = active.
        moduleStateUpdate(actions[actionIndex]);
        break;
      default:
        // Get the correct array to use.
        CRGB* leds = obtainCRGBArray(actions[actionIndex]);
        int numLeds = info[actionIndex];
        // Turn the LED off. 
        for(int whiteLed = 0; whiteLed < numLeds; whiteLed = whiteLed + 1) {
          leds[whiteLed] = CRGB::Black;
        }
        FastLED.show();
        break;
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
//
// If this function is provided a second argument, it will
// ignore whatever state is present in the action and will
// explicitly send the string provided. 
// To not send explicit input, provide with an empty string.
void moduleInput(int actionId, String explicitInput) {
  WiFiClient webServer;
  String endpoint = "moduleInput";
  String explicitInputEndpoint = "moduleInputString";

  int i = findActionId(actionId);
  if(i < 0){
    Serial.print("[ERROR] moduleInput was unable to find actionId ");
    Serial.println(actionId);
  }

  String toState;
  if (explicitInput == ""){
    toState = String(states[i]);
  }
  else{
    toState = explicitInput;
    endpoint = explicitInputEndpoint;
  }
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
    webServer.println("GET /"+endpoint+"/"+roomIdStr+"/"+actionIdStr+"/" + toState);
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
