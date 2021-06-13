#
# sever.py
#
# Root program for speech recognition application server designed
# to interface with the kotakeeOS Web Server. This sends requests
# to activate-deactivate modules just like any other regular 
# web application. 
#
# Initial code based off of:
# https://www.geeksforgeeks.org/python-convert-speech-to-text-and-text-to-speech/
#
# Usage: python3 server.py
#

import speech_recognition as sr
import pyttsx3

import requests
import time

import threading

# Application constants.
webServerIpAddress = "http://192.168.0.197:8080"

#hotWord = "iris"
hotWord = "california" # Triggers activation of google query. 

cancelWords = ["stop", "cancel", "go away", "quit", "no thanks"] # stops google query.
hotWordReceiptPrompt = "Yes?"
successfulCommandPrompt = "Understood."
cancellationPrompt = "Going back to sleep."
failedCommandPrompt = "Sorry, I didn't understand that."
stopServerPrompt = "Understood. Good night."

# Initialize the recognizer
r = sr.Recognizer()
r2 = sr.Recognizer()
engine = pyttsx3.init()

# Kill swith
stopServer = False

def runApplicationServer():
  print("Initializing kotakeeOS speech application server...")

  r.pause_threshold = 0.5 # Small. We're only listening for a word.
  r2.pause_threshold = 1.0 # Give it a larger pause threshold
  
  while stopServer is not True:
    listenForHotWord()
  
  print("Shutting down. Goodnight.")

# When run, listens for a single command and executes
# acceptable ones accordingly. 
def listenForHotWord():
  try:
    # Specify the microphone as the input source.
    with sr.Microphone() as source2:
      # Wait a moment to allow the recognizer to adjust
      # the energy threshold based on surrounding noise
      # level...
      r.adjust_for_ambient_noise(source2)
      print("[DEBUG] Now Listening for Hotword '"+hotWord+"' ...")
      start = time.time()

      # Listen for input
      #r.dynamic_energy_threshold = False
      audio2 = r.listen(source2, timeout = 5.0, phrase_time_limit=5.0)

      # Use offline CMU Sphinx recognizer
      recognizedText = r.recognize_sphinx(audio2)

      # String cleanup
      recognizedText = recognizedText.lower()
      end = time.time()

      print("[DEBUG] Recognized hotword audio: '" + recognizedText + "' in " + str(end-start) + " ")

      # Parse recognized text
      if stopServer is not True and hotWord in recognizedText:
        print("[DEBUG] Hotword recognized!")
        listenForCommand()

  except sr.RequestError as e:
    print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
  except sr.UnknownValueError:
    pass
  except sr.WaitTimeoutError:
    pass

# Uses far more intelligent google API to parse a command. 
def listenForCommand():
  successfulCommand = False
  # Try three times, or until user cancels, or command was
  # executed.
  for i in range(3): 
    try:
      # Specify the microphone as the input source.
      with sr.Microphone() as source2:
        # Wait a moment to allow the recognizer to adjust
        # the energy threshold based on surrounding noise
        # level...
        r2.adjust_for_ambient_noise(source2)
        executeTextThread(hotWordReceiptPrompt)
        print("[DEBUG] Now Listening for Command...")
        start = time.time()

        # Listen for input
        audio2 = r2.listen(source2)

        # Use Google's API to recognize the audio.
        recognizedText = r2.recognize_google(audio2)

        # String cleanup
        recognizedText = recognizedText.lower()
        end = time.time()

        print("[DEBUG] Recognized command audio: '" + recognizedText + "' in " + str(end-start) + " ")

        # Parse recognized text
        if any(x in recognizedText for x in cancelWords):
          print("[DEBUG] User requested cancellation. Stopping command parsing...")
          break
        else:
          if parseAndExecuteCommand(recognizedText):
            successfulCommand = True
            break

    except sr.RequestError as e:
      print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
    except sr.UnknownValueError:
      print("[Warning] Last sentence was not understood.")
  
  # Stopping. Let user know big brother google is no longer
  # listening. 
  if successfulCommand is False:
    executeTextThread(cancellationPrompt)

# Non-blocking text to speech. Do be warned this
# might interefere with the speech recognition. 
def executeTextThread(command):
  textThread = threading.Thread(target=speakText, args=(command,), daemon=True).start()
  
# Convert text to speech using pyttsx3 engine.
# Note calling this by itself causes a block
# on the main thread. 
def speakText(command):
  if engine._inLoop:
    engine.endLoop()
  engine.say(command)
  engine.runAndWait()

# Given a queried command from the google text recognition
# API, parse and execute accordingly.
def parseAndExecuteCommand(command):
  global stopServer
  # Ex) http://192.168.0.197:8080/moduleToggle/1/50/1
  queries = []

  # The silly command
  if ("good night" in command or "freeze all motor functions" in command or "goodnight" in command):
    executeTextThread(stopServerPrompt)
    time.sleep(5) # Enough time to allow the speech prompt to complete. 
    stopServer = True
    return True
  elif("everything" in command):
    if("off" in command):
      queries.append(webServerIpAddress + "/moduleToggle/1/50/0")
      queries.append(webServerIpAddress + "/moduleToggle/2/50/0")
      queries.append(webServerIpAddress + "/moduleToggle/2/250/10")
      queries.append(webServerIpAddress + "/moduleToggle/2/251/10")
      queries.append(webServerIpAddress + "/moduleToggle/2/350/20")
    elif("on" in command):
      queries.append(webServerIpAddress + "/moduleToggle/1/50/1")
      queries.append(webServerIpAddress + "/moduleToggle/2/50/1")
      queries.append(webServerIpAddress + "/moduleToggle/2/250/12")
      queries.append(webServerIpAddress + "/moduleToggle/2/251/12")
      queries.append(webServerIpAddress + "/moduleToggle/2/350/22")
  else:
    if("bedroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/1/50/0") # query off first, because on is in one. 
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/1/50/1")

    if("living" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/50/0")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/50/1")
    
    if("speaker" in command or "soundbar" in command or ("sound" in command and "bar" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/250/10")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/250/12")
    
    if("ceiling" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/251/10")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/251/12")

    if("kitchen" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/350/20")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/350/22")

  if len(queries) > 0:
    # We have received a valid command. Query the server. 
    for query in queries:
      print("[DEBUG] Sending query: " + query)
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] Request received successfully.")
      else:
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
    executeTextThread(successfulCommandPrompt)
    return True
  else:
    executeTextThread(failedCommandPrompt)
    print("[DEBUG] No valid command was received.")
    return False

if __name__ == "__main__":
  runApplicationServer()