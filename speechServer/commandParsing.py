#
# commandParsing.py
#
# Contains command parsing software used by all variants
# of the kotakeeOS speechServer. Uses google speech recognition
# to parse complex commands accurately. Must be called by a 
# calling program that provides hotword detection to initialize. 

import speech_recognition as sr
import pyttsx3
import requests
import time
from datetime import date
import threading
import json

import wave
import pyaudio

# Utilize ML/AI NLP project QuestAI.
from quest_ai_parsing import QuestAiParsing

class CommandParser:
  # Constants that may be configured.
  webServerIpAddress = "http://192.168.0.197:8080"
  cancelWords = ["stop", "cancel", "go away", "quit", "no thanks", "sleep"] # stops google query.
  stopServerCommands = ["goodnight", "good night", "freeze all motor functions", "turn yourself off", "shutdown", "deactivate"]
  command_split_keywords = ["break", "brake"]
  hotWordReceiptPrompt = "Yes?"
  successfulCommandPrompt = "" # By default, don't say anything and just activate something. 
  cancellationPrompt = "Going back to sleep."
  stopServerPrompt = "Understood. Shutting down."
  startupPrompt = "Good morning, Speech Server initialized. Now listening for hotwords."
  pauseThreshold = 1.0
  maxCommandAttempts = 1

  chime_location = "./assets/testChime.wav"

  quest_ai_parser = None

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

  # A custom startup so we can announce the type of hotword
  # parser. 
  def startupProcedureCustom(self, prompt):
    self.executeTextThread(prompt)

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

      # Indicate that you are currently active. 
      self.querySpeechServerLED(1, 2, 51)

      # Try three times, or until user cancels, or command was
      # executed.
      for i in range(self.maxCommandAttempts): 
        try:
            self.executeChime()

            print("[DEBUG] Now Listening for Command...")
            start = time.time()

            # Listen for input
            audio2 = self.r2.listen(source2, timeout=5,phrase_time_limit=5)

            # However, if we do not have access to the internet,
            # utilize pocketsphinx instead (even though it's
            # kinda trash, becuase it's better than nothing). 
            recognizedText = None
            if self.actionStates is not None:
              # Use Google's API to recognize the audio.
              recognizedText = self.r2.recognize_google(audio2)
            else:
              # Use offline CMU Sphinx recognizer
              recognizedText = self.r2.recognize_sphinx(audio2)

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
        except sr.WaitTimeoutError:
          print("[Warning] Timeout occured.")
    
    # Indicate that you are no longer active. 
    self.querySpeechServerLED(0, 2, 51)

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
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        self.actionStates = json.loads(response.text)
        self.actionStatesLastUpdate = self.actionStates['lastUpdate']
        print("[DEBUG] Action States request received successfully. actionStatesLastUpdate is now: " + str(self.actionStatesLastUpdate))
        #print(str(actionStates))
      elif(response.status_code != 204):
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] queryActionStates unable to connect to server.")

  # Queries server for misc non-module information
  def queryHomeStatus(self):
    query = self.webServerIpAddress + "/homeStatus/" + str(self.homeStatusLastUpdate)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        self.homeStatus = json.loads(response.text)
        self.homeStatusLastUpdate = self.homeStatus['lastUpdate']
        print("[DEBUG] Home Status request received successfully. homeStatusLastUpdate is now: " + str(self.homeStatusLastUpdate))
        #print(str(homeStatus))
      elif(response.status_code != 204):
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] queryHomeStatus unable to connect to server.")

  # Experimental - queries server to turn speech server signal light on/off. 
  def querySpeechServerLED(self, toState, roomId, actionId):
    query = self.webServerIpAddress + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] querySpeechServerLED request received successfully.")
      elif(response.status_code != 204):
        print("[WARNING] Server rejected querySpeechServerLED request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] querySpeechServerLED unable to connect to server.")

  # Experimental - queries server providing input. 
  def querySpeechServerInput(self, toState, roomId, actionId):
    query = self.webServerIpAddress + "/moduleInput/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] querySpeechServerInput request received successfully.")
      elif(response.status_code != 204):
        print("[WARNING] Server rejected querySpeechServerInput request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] querySpeechServerInput unable to connect to server.")

  # Let out a chime to indicate that you're listening. This code
  # is not mine, but it works like a charm!
  def executeChime(self):
    chunk = 1024
    f = wave.open(self.chime_location, "rb")
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                channels = f.getnchannels(),  
                rate = f.getframerate(),  
                output = True) 
    data = f.readframes(chunk)
    while data:  
      stream.write(data)  
      data = f.readframes(chunk)
    stream.stop_stream()  
    stream.close()  

    #close PyAudio  
    p.terminate()

  # Given a queried command from the google text recognition
  # API, parse and execute accordingly. Executes rudimentary
  # language processing by finding keywords and acting accordingly. 
  def parseAndExecuteCommand(self, full_command):
    # Ex) http://192.168.0.197:8080/moduleToggle/1/50/1
    queries = []
    confirmationPrompt = self.successfulCommandPrompt
    valid_command = False

    if any(x in full_command for x in self.stopServerCommands):
      self.executeTextThread(self.stopServerPrompt)
      time.sleep(2) # Enough time to allow the speech prompt to complete. 
      self.stopServer = True
      return True

    # Multi-command parsing. Break the command phrase in two
    # given the array of keywords.
    commands = [full_command]
    for keyword in self.command_split_keywords:
      new_commands = []
      for i in range(0, len(commands)):
        split_commands = commands[i].split(keyword)
        for group in split_commands:
          new_commands.append(group)
      commands = new_commands

    # Parse command chronologically.
    for command in commands:
      if("weather" in command or "like outside" in command or "how hot" in command or "how cold" in command):
        if(self.homeStatus is not None):
          weatherString = "It is currently " + str(int(self.homeStatus["weatherData"]["main"]["temp"])) + " degrees Fahrenheit, " +str(self.homeStatus["weatherData"]["weather"][0]["description"]) + ", with a maximum of " + str(int(self.homeStatus["weatherData"]["main"]["temp_max"])) + " and a minimum of " + str(int(self.homeStatus["weatherData"]["main"]["temp_min"])) + ". Humidity is " +  str(self.homeStatus["weatherData"]["main"]["humidity"]) + " percent."
          self.executeTextThread(weatherString)
          time.sleep(9) # Enough time to allow the speech prompt to complete. 
          valid_command = True
      elif("everything" in command or "all modules" in command):
        if(self.actionStates is not None):
          if("off" in command or "on" in command):
            # Manage prompt. 
            promptOnOff = "on"
            toState = 1
            if("off" in command):
              promptOnOff = "off"
              toState = 0
            confirmationPrompt = "Turning everything " + promptOnOff + "."
            queries.append(self.webServerIpAddress + "/moduleToggleAll/" + str(toState))
      elif("thermostat" in command):
        if(self.homeStatus is not None and self.homeStatus["moduleInput"] is not None and self.homeStatus["moduleInput"]['2'] is not None):
          if(self.homeStatus["moduleInput"]['2']['5251'] is not None and self.homeStatus["moduleInput"]['2']['5251']["offHeat"] is not None and self.homeStatus["moduleInput"]['2']['5251']["onHeat"] is not None):
            onHeat = self.homeStatus["moduleInput"]['2']['5251']["onHeat"]
            offHeat = self.homeStatus["moduleInput"]['2']['5251']["offHeat"]
            newTemp = self.text2int(command)
            print("[DEBUG] Parsed number " + str(newTemp) + " from thermostat request.")
            if(newTemp > 30 and newTemp < 100):
              onHeat = newTemp+1
              offHeat = onHeat-2
              newHomeStatus = self.homeStatus["moduleInput"]['2']
              newHomeStatus['5251']["onHeat"] = onHeat
              newHomeStatus['5251']["offHeat"] = offHeat
              dataToSend = {
                "roomId": 2,
                "newModuleInput": newHomeStatus
              }
              # Send a post message from here. 
              query = self.webServerIpAddress + "/moduleInputModify"
              print("[DEBUG] Sending query: " + query + " with body:")
              print(dataToSend)
              response = requests.post(query, data=json.dumps(dataToSend, indent = 4), headers = {'Content-Type': 'application/json'}, timeout=5)
              if(response.status_code == 200):
                print("[DEBUG] Request received successfully.")
              else:
                print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
              self.executeTextThread("Setting thermostat to " + str(newTemp) + ".")
              valid_command = True
      elif("temperature" in command):
        # Handle temperatures. Expects a state like "27.70_42.20".
        lr_2_state = self.actionStates["2"]["5251"].split("_")
        br_state = self.actionStates["1"]["5250"].split("_")
        # Convert to Farenheit. 
        lr_2_temp = str(round(((float(lr_2_state[0]) * 9) / 5) + 32))
        br_temp = str(round(((float(br_state[0]) * 9) / 5) + 32))

        # Operational server status
        statusString = "The Living Room is currently " + lr_2_temp + " degrees. The Bedroom is currently " + br_temp + " degrees."
        self.executeTextThread(statusString)
        time.sleep(4) # Enough time to allow the speech prompt to complete. 
        valid_command = True
      elif(("auto" in command or "input" in command or "automatic" in command) and ("off" in command or "on" in command or "enable" in command or "disable" in command)):
        if(self.homeStatus is not None and self.homeStatus["moduleInputDisabled"] is not None):
          currentAutoStatus = self.homeStatus["moduleInputDisabled"]
          newState = "true"
          if("activate" in command or "turn on" in command or "enable" in command):
            newState = "false"
          queries.append(self.webServerIpAddress + "/moduleInputDisabled/" + newState)
          # Manage prompt. 
          if(newState == "false"):
            confirmationPrompt = "Enabling automatic server actions."
          else:
            confirmationPrompt = "Disabling automatic server actions."
      elif("server" in command and ("off" in command or "on" in command or "enable" in command or "disable" in command)):
        if(self.homeStatus is not None and self.homeStatus["serverDisabled"] is not None):
          currentAutoStatus = self.homeStatus["serverDisabled"]
          newState = "true"
          if("activate" in command or "turn on" in command or "enable" in command):
            newState = "false"
          queries.append(self.webServerIpAddress + "/serverDisabled/" + newState)
          # Manage prompt. 
          if(newState == "false"):
            confirmationPrompt = "Enabling central server operations."
          else:
            confirmationPrompt = "Disabling central server operations."
      elif("status" in command and ("home" in command or "system" in command or "server" in command)):
        if(self.homeStatus is not None and self.actionStates is not None):
          # Report all information. 
          serverDisabled = "enabled"
          if(self.homeStatus["serverDisabled"] == "true" or self.homeStatus['serverDisabled'] == True):
            serverDisabled = "disabled"
          moduleInputDisabled = "enabled"
          if(self.homeStatus["moduleInputDisabled"] == "true" or self.homeStatus['moduleInputDisabled'] == True):
            moduleInputDisabled = "disabled"
          onHeat = int(self.homeStatus["moduleInput"]['2']['5251']["onHeat"])

          # Handle temperatures. Expects a state like "27.70_42.20".
          lr_2_state = self.actionStates["2"]["5251"].split("_")
          br_state = self.actionStates["1"]["5250"].split("_")
          # Convert to Farenheit. 
          lr_2_temp = str(round(((float(lr_2_state[0]) * 9) / 5) + 32))
          br_temp = str(round(((float(br_state[0]) * 9) / 5) + 32))

          # Operational server status
          statusString = "KotakeeOS is currently " + serverDisabled + " with automatic actions " + moduleInputDisabled + ". There are " + str(self.homeStatus["modulesCount"]) + " connected modules. The thermostat is currently set to " + str(onHeat - 1) + " degrees."
          # Action states status
          statusString = statusString + " The Living Room is currently " + lr_2_temp + " degrees. The Bedroom is currently " + br_temp + " degrees."
          self.executeTextThread(statusString)
          time.sleep(12) # Enough time to allow the speech prompt to complete. 
          valid_command = True
      elif("time" in command or "clock" in command):
        currentTime = time.strftime("%H%M", time.localtime())
        timeString = "It is currently " + currentTime + "."
        self.executeTextThread(timeString)
        time.sleep(2) # Enough time to allow the speech prompt to complete. 
        valid_command = True
      elif("date" in command or "day" in command or "month" in command or "today" in command):
        dateToday = date.today()
        dateString = "Today is "+ time.strftime("%A", time.localtime()) + ", " + time.strftime("%B", time.localtime()) + " " + str(dateToday.day) + ", " + str(dateToday.year)
        self.executeTextThread(dateString)
        time.sleep(3) # Enough time to allow the speech prompt to complete. 
        valid_command = True
      elif("question" in command):
        # If we asked for advanced output or "8 ball", our output should be
        # different.
        output_type = 0
        if("advanced" in command or "detailed" in command): output_type = 1
        elif("eight ball" in command or "8-ball" in command or "8 ball" in command): output_type = 2
        # Initialize if it's not running. Only do this once and keep it up
        # afterwards because the quest_ai_parser takes a while to get running. 
        if(self.quest_ai_parser is None):
          self.executeTextThread("Initializing Quest AI... please wait.")
          self.quest_ai_parser = QuestAiParsing(recognizer = self.r2, engine = self.engine, pause_threshold = self.pauseThreshold)
        self.quest_ai_parser.standard_query(output_type = output_type, online_functionality=self.actionStates is not None)
        valid_command = True
      elif("calculator" in command or "calculate" in command):
        # Get the first number and then the second number in the query. Ignore
        # all others if there are any. Fail if there are not enough numbers.
        # Fail if there is not a specifying operator. 
        first_term = None
        second_term = None
        operator = None # Term used in final message as well. 
        negative_term = False
        for word in command.split():
          # Test as an operator.
          if operator is None:
            if word == "add" or word == "plus" or word == "+":
              operator = "plus"
              continue
            elif word == "subtract" or word == "minus" or word == "-":
              operator = "minus"
              continue
            elif word == "multiply" or word == "times" or word == "*" or word == "x":
              operator = "times"
              continue
            elif word == "divide" or word == "divided" or word == "/":
              operator = "divided by"
              continue
          # Test as a number or a "negative" term.
          if first_term is None or second_term is None:
            if word == "negative":
              negative_term = True
            else:
              # Parse as a number. 
              possible_term = self.text2int(word)
              if possible_term != 0:
                if negative_term is True:
                  possible_term = -possible_term
                  negative_term = False
                if first_term is None:
                  first_term = possible_term
                else:
                  second_term = possible_term
                
        # We've now theoretically gotten everything.
        if first_term is not None and second_term is not None and operator is not None:
          solution = None
          if operator == "plus":
            solution = first_term + second_term
          elif operator == "minus":
            solution = first_term - second_term
          elif operator == "times":
            solution = first_term * second_term
          else:
            solution = first_term / second_term
          self.executeTextThread(str(first_term) + " " + operator + " " + str(second_term) + " equals " + str(solution) + ".")
          time.sleep(3) # Enough time to allow the speech prompt to complete. 
          valid_command = True
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
        if("bathroom" in command and ("led" in command or "night" in command)):
          queries.append(self.generateQuery(command, 3, 50, 1, 0))
        if("printer" in command):
          queries.append(self.generateQuery(command, 2, 252, 12, 10))
        if("bedroom" in command and ("night" in command or "red led" in command or "red leds" in command)):
          queries.append(self.generateQuery(command, 1, 1000, 108, 100))
        if("living" in command and ("night" in command or "red led" in command or "red leds" in command)):
          queries.append(self.generateQuery(command, 2, 1000, 108, 100))
        if("bedroom" in command and ("led" in command or "party" in command or "rgb" in command)):
          queries.append(self.generateQuery(command, 1, 1000, 107, 100))
        if("living" in command and ("led" in command or "party" in command or "rgb" in command)):
          queries.append(self.generateQuery(command, 2, 1000, 107, 100))

    if len(queries) > 0:
      # We have received a valid command. Query the server. 
      for query in queries:
        print("[DEBUG] Sending query: " + query)
        response = requests.get(query)
        if(response.status_code == 200):
          print("[DEBUG] Request received successfully.")
        else:
          print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
      if(confirmationPrompt is not None and confirmationPrompt != ""):
        self.executeTextThread(confirmationPrompt)
      valid_command = True

    if valid_command != True:
      print("[DEBUG] No valid command was received.")
    
    return valid_command

  # Given the possible command string, roomId, actionId, and 
  # a binary set of states, return a query. 
  # 
  # If the command contains the keyword "virtual", a virtual 
  # module toggle will be created instead of physical. 
  def generateQuery(self, command, roomId, actionId, onState, offState):
    endpoint = "/moduleToggle/"
    if "virtual" in command:
      endpoint = "/moduleVirtualToggle/"
    if("off" in command or "deactivate" in command):
      return self.webServerIpAddress + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(offState)
    elif("on" in command or "activate" in command or "initialize" in command):
      return self.webServerIpAddress + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(onState)
    else:
      #No on or off specified. Check queried information. 
      if(self.actionStates is not None):
        if(self.actionStates[str(roomId)][str(actionId)] == int(onState)):
          return self.webServerIpAddress + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(offState)
        else:
          return self.webServerIpAddress + endpoint+str(roomId)+"/"+str(actionId)+"/" + str(onState)

  # Helper function I got off stack overflow - really sweet code!
  # Slightly modified to allow non-number characters. 
  # https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers
  def text2int(self, textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          print("[DEBUG] text2int parsing invalid word: " + str(word))
          if self.intTryParse(word) is True:
            return int(word)
          continue
          #raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current
    
  # Dunno why this isn't standard. 
  def intTryParse(self, value):
    try:
      int(value)
      return True
    except ValueError:
      return False