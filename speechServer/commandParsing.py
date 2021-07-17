#
# commandParsing.py
# (Yes I know my camelCase vs _ styling is all over the place)
#
# Contains command parsing software used by all variants
# of the kotakeeOS speechServer. Uses google speech recognition
# to parse complex commands accurately. Must be called by a 
# calling program that provides hotword detection to initialize. 

import speech_recognition as sr
import pyttsx3
import requests
import time
import threading
import json

class CommandParser:
  # Constants that may be configured.
  webServerIpAddress = "http://192.168.0.197:8080"
  cancelWords = ["stop", "cancel", "go away", "quit", "no thanks"] # stops google query.
  stopServerCommands = ["goodnight", "good night", "freeze all motor functions", "turn yourself off", "shutdown", "deactivate"]
  hotWordReceiptPrompt = "Yes?"
  successfulCommandPrompt = "Understood."
  cancellationPrompt = "Going back to sleep."
  stopServerPrompt = "Understood. Good night."
  startupPrompt = "Good morning, Speech Server initialized. Now listening for hotwords."
  pauseThreshold = 1.0
  maxCommandAttempts = 2

  # Ah, I'm so happy this matches perfectly with the client code. 
  # Thanks, python. 
  implementedButtons = {
    "1.50": "Bedroom Lamp",
    "2.50": "Living Room Lamp",
    "2.250": "Soundbar Power",
    "2.251": "Ceiling Fan Lamp",
    "2.252": "Printer Power",
    "2.350": "Kitchen Light",
    "3.50": "Bathroom LED",
    "3.350": "Bathroom Light",
    "3.351": "Bathroom Fan",
    "2.450": "Air Conditioner",
    "2.1000": "TV",
    "1.1000": "Bed",
  }

  # Also needs to be kept constant with clients. . 
  actions = {
    "LIGHTING1": 50,
    "LIGHTING2": 51,
    "LIGHTING3": 52,
    "LIGHTING4": 53,
    "LIGHTING5": 54,
    "CURTAINS1": 150,
    "CURTAINS2": 151,
    "CURTAINS3": 152,
    "CURTAINS4": 153,
    "CURTAINS5": 154,
    "REMOTE1": 250,
    "REMOTE2": 251,
    "REMOTE3": 252,
    "REMOTE4": 253,
    "REMOTE5": 254,
    "REMOTE6": 255,
    "REMOTE7": 256,
    "REMOTE8": 257,
    "REMOTE9": 258,
    "REMOTE10": 259,
    "REMOTE11": 260,
    "REMOTE12": 261,
    "REMOTE13": 262,
    "REMOTE14": 263,
    "REMOTE15": 264,
    "REMOTE16": 265,
    "REMOTE17": 266,
    "REMOTE18": 267,
    "REMOTE19": 268,
    "REMOTE20": 269,
    "SWITCH1": 350,
    "SWITCH2": 351,
    "SWITCH3": 352,
    "SWITCH4": 353,
    "SWITCH5": 354,
    "KNOB1": 450,
    "KNOB2": 451,
    "KNOB3": 452,
    "KNOB4": 453,
    "KNOB5": 454,
    "LEDSTRIP1": 1000,
    "LEDSTRIP2": 1001,
    "LEDSTRIP3": 1002,
    "LEDSTRIP4": 1003,
    "LEDSTRIP5": 1004,
    "LEDSTRIP6": 1005,
    "LEDSTRIP7": 1006,
    "LEDSTRIP8": 1007,
    "LEDSTRIP9": 1008,
    "LEDSTRIP10": 1009,
    "TEMP1": 5250,
    "TEMP2": 5251,
    "TEMP3": 5252,
    "TEMP4": 5253,
    "TEMP5": 5254,
  }

  # Local variables.
  r2 = None
  engine = None
  stopServer = False
  actionStates = None
  homeStatus = None
  actionStatesLastUpdate = 0
  homeStatusLastUpdate = 0

  # Initialize the stuff we need to do at startup. 
  def __init__(self):
    self.r2 = sr.Recognizer()
    self.engine = pyttsx3.init()
    self.r2.pause_threshold = self.pauseThreshold

  # Called at the very start before hotword parsing starts
  # (if desired) to announce that the application is now
  # listening + other bits like the weather. 
  def startupProcedure(self):
    self.queryHomeStatus()
    if(self.homeStatus is not None):
      weatherString = " It is currently " + str(int(self.homeStatus["weatherData"]["main"]["temp"])) + " degrees Fahrenheit, " +str(self.homeStatus["weatherData"]["weather"][0]["description"]) + ", with a maximum of " + str(int(self.homeStatus["weatherData"]["main"]["temp_max"])) + " and a minimum of " + str(int(self.homeStatus["weatherData"]["main"]["temp_min"])) + ". Humidity is " +  str(self.homeStatus["weatherData"]["main"]["humidity"]) + " percent."
      self.executeTextThread(self.startupPrompt + weatherString)
    
  # Only executes a lone text thread in case the user doesn't
  # want the whole spiel.
  def startupProcedureFast(self):
    self.executeTextThread(self.startupPrompt)

  # Uses far more intelligent google API to parse a command. 
  # The main function that will be kicked off by the hotword
  # application. 
  def listenForCommand(self):
    successfulCommand = False

    # When the hotword has been said, kick off a thread
    # to query the server for the latest homeStatus and
    # states. This should be fast enough so that it's always
    # done by the time the user says the command. 
    self.executeQueryServerThread()
    
    with sr.Microphone() as source2:
      # Wait a moment to allow the recognizer to adjust
      # the energy threshold based on surrounding noise
      # level...
      self.r2.adjust_for_ambient_noise(source2, duration=0.7)

      # Try three times, or until user cancels, or command was
      # executed.
      for i in range(self.maxCommandAttempts): 
        try:
          # Specify the microphone as the input source.
            self.executeTextThread(self.hotWordReceiptPrompt)
            time.sleep(0.7) # Try not to detet the prompt. 
            print("[DEBUG] Now Listening for Command...")
            start = time.time()

            # Listen for input
            audio2 = self.r2.listen(source2, timeout=5,phrase_time_limit=5)

            # Use Google's API to recognize the audio.
            recognizedText = self.r2.recognize_google(audio2)

            # String cleanup
            recognizedText = recognizedText.lower()
            end = time.time()

            print("[DEBUG] Recognized command audio: '" + recognizedText + "' in " + str(end-start) + " ")

            # Parse recognized text
            if any(x in recognizedText for x in self.cancelWords):
              print("[DEBUG] User requested cancellation. Stopping command parsing...")
              break
            else:
              if self.parseAndExecuteCommand(recognizedText):
                successfulCommand = True
                break

        except sr.RequestError as e:
          print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
        except sr.UnknownValueError:
          print("[Warning] Last sentence was not understood.")
    
    # Stopping. Let user know big brother google is no longer
    # listening. 
    if successfulCommand is False:
      self.executeTextThread(self.cancellationPrompt)

  # Non-blocking text to speech. Do be warned this
  # might interefere with the speech recognition. 
  def executeTextThread(self, command):
    print("[DEBUG] Starting thread for text output: '"+command+"'")
    textThread = threading.Thread(target=self.speakText, args=(command,), daemon=True).start()
    
  # Convert text to speech using pyttsx3 engine.
  # Note calling this by itself causes a block
  # on the main thread. 
  def speakText(self, command):
    if self.engine._inLoop:
      self.engine.endLoop()
    self.engine.say(command)
    self.engine.runAndWait()

  # Non-blocking query to fill status objects.
  def executeQueryServerThread(self):
    queryActionStatesThread = threading.Thread(target=self.queryActionStates, daemon=True).start()
    queryHomeStatusThread = threading.Thread(target=self.queryHomeStatus, daemon=True).start()

  # Queries server for states of all modules. 
  def queryActionStates(self):
    query = self.webServerIpAddress + "/actionStates/" + str(self.actionStatesLastUpdate)
    print("[DEBUG] Querying server: " + query)
    response = requests.get(query)
    if(response.status_code == 200):
      self.actionStates = json.loads(response.text)
      self.actionStatesLastUpdate = self.actionStates['lastUpdate']
      print("[DEBUG] Action States request received successfully. actionStatesLastUpdate is now: " + str(self.actionStatesLastUpdate))
      #print(str(actionStates))
    elif(response.status_code != 204):
      print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

  # Queries server for misc non-module information
  def queryHomeStatus(self):
    query = self.webServerIpAddress + "/homeStatus/" + str(self.homeStatusLastUpdate)
    print("[DEBUG] Querying server: " + query)
    response = requests.get(query)
    if(response.status_code == 200):
      self.homeStatus = json.loads(response.text)
      self.homeStatusLastUpdate = self.homeStatus['lastUpdate']
      print("[DEBUG] Home Status request received successfully. homeStatusLastUpdate is now: " + str(self.homeStatusLastUpdate))
      #print(str(homeStatus))
    elif(response.status_code != 204):
      print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

  # Experimental - queries server to turn speech server signal light on/off. 
  def querySpeechServerLED(self, toState, roomId, actionId):
    query = self.webServerIpAddress + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    print("[DEBUG] Querying server: " + query)
    response = requests.get(query)
    if(response.status_code == 200):
      print("[DEBUG] querySpeechServerLED request received successfully.")
    elif(response.status_code != 204):
      print("[WARNING] Server rejected querySpeechServerLED request with status code " + str(response.status_code) + ".")

  # Given a queried command from the google text recognition
  # API, parse and execute accordingly.
  def parseAndExecuteCommand(self, command):
    # Ex) http://192.168.0.197:8080/moduleToggle/1/50/1
    queries = []

    if any(x in command for x in self.stopServerCommands):
      self.executeTextThread(self.stopServerPrompt)
      time.sleep(2) # Enough time to allow the speech prompt to complete. 
      self.stopServer = True
      return True
    elif("weather" in command or "like outside" in command or "how hot" in command or "how cold" in command):
      if(self.homeStatus is not None):
        weatherString = "It is currently " + str(int(self.homeStatus["weatherData"]["main"]["temp"])) + " degrees Fahrenheit, " +str(self.homeStatus["weatherData"]["weather"][0]["description"]) + ", with a maximum of " + str(int(self.homeStatus["weatherData"]["main"]["temp_max"])) + " and a minimum of " + str(int(self.homeStatus["weatherData"]["main"]["temp_min"])) + ". Humidity is " +  str(self.homeStatus["weatherData"]["main"]["humidity"]) + " percent."
        self.executeTextThread(weatherString)
        time.sleep(8) # Enough time to allow the speech prompt to complete. 
        return True
    elif("everything" in command or "all modules" in command):
      if(self.actionStates is not None):
        if("off" in command or "on" in command):
          # Go through each room in actionStates.
          for roomId in self.actionStates:
            actionStatesDict = self.actionStates[roomId]
            if isinstance(actionStatesDict, dict): # for actionStates elements that aren't dict, i.e. lastUpdate. 
              for actionId in self.actionStates[roomId]:
                if(str(roomId) + "." + str(actionId) in self.implementedButtons):
                  # We have a valid action that we've implemented. 
                  onState = 1
                  offState = 0
                  if(int(actionId) <= self.actions["REMOTE20"] and int(actionId) >= self.actions["REMOTE1"]):
                    onState = 12
                    offState = 10
                  elif(int(actionId) <= self.actions["SWITCH5"] and int(actionId) >= self.actions["SWITCH1"]):
                    onState = 22
                    offState = 20
                  elif(int(actionId) <= self.actions["KNOB5"] and int(actionId) >= self.actions["KNOB1"]):
                    onState = 32
                    offState = 30
                  elif(int(actionId) <= self.actions["LEDSTRIP10"] and int(actionId) >= self.actions["LEDSTRIP1"]):
                    onState = 107 # PARTY MODE ONLY!
                    offState = 100
                  queries.append(self.generateQuery(command, roomId, actionId, onState, offState))
    else:
      if("bedroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.generateQuery(command, 1, 50, 1, 0))
      if("living" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.generateQuery(command, 2, 50, 1, 0))
      if("speaker" in command or "soundbar" in command or ("sound" in command and "bar" in command)):
        queries.append(self.generateQuery(command, 2, 250, 12, 10))
      if("ceiling" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.generateQuery(command, 2, 251, 12, 10))
      if("kitchen" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.generateQuery(command, 2, 350, 22, 20))
      if("bathroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
        queries.append(self.generateQuery(command, 3, 350, 22, 20))
      if("bathroom" in command and ("fan" in command or "vent")):
        queries.append(self.generateQuery(command, 3, 351, 22, 20))
      if("printer" in command):
        queries.append(self.generateQuery(command, 2, 252, 12, 10))

    if len(queries) > 0:
      # We have received a valid command. Query the server. 
      for query in queries:
        print("[DEBUG] Sending query: " + query)
        response = requests.get(query)
        if(response.status_code == 200):
          print("[DEBUG] Request received successfully.")
        else:
          print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
      self.executeTextThread(self.successfulCommandPrompt)
      return True
    else:
      print("[DEBUG] No valid command was received.")
      return False

  # Given the possible command string, roomId, actionId, and 
  # a binary set of states, return a query. 
  def generateQuery(self, command, roomId, actionId, onState, offState):
    if("off" in command or "deactivate" in command):
      return self.webServerIpAddress + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(offState)
    elif("on" in command or "activate" in command or "initialize" in command):
      return self.webServerIpAddress + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(onState)
    else:
      #No on or off specified. Check queried information. 
      if(self.actionStates is not None):
        if(self.actionStates[str(roomId)][str(actionId)] == int(onState)):
          return self.webServerIpAddress + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(offState)
        else:
          return self.webServerIpAddress + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(onState)
    