#
# hotwordPocketSphinx.py
#
# Root program for speech recognition application server designed
# to interface with the kotakeeOS Web Server. This sends requests
# to activate-deactivate modules just like any other regular 
# web application. 
#
# Utilize pocketsphinx as a sort of "brute force" way of implementing
# Hotword detection. 
#
# Initial code based off of:
# https://www.geeksforgeeks.org/python-convert-speech-to-text-and-text-to-speech/
#
# Usage: python3 hotwordPocketSphinx.py
#

import speech_recognition as sr
import pyttsx3
import requests
import time
import threading
import json

from commandParsing import CommandParser

pause_threshold = 0.5 # Small. We're only listening for a word.
#hotWord = "iris"
#hotWord = "california" # Triggers activation of google query. 
hotWords = ["california"]
audio_timeout = 5.0
phrase_time_limit = 5.0

# Initialize the hotword recognizer
r = sr.Recognizer()
r.pause_threshold = pause_threshold 
commandParser = CommandParser()

def runApplicationServer():
  print("Initializing kotakeeOS speech application server with PocketSphinx hotword detection.")

  # Experimental - query the server to turn on the LED to signal
  # Speech server is online. 
  commandParser.querySpeechServerLED(1)
  commandParser.startupProcedure()
  
  while commandParser.stopServer is not True:
    listenForHotWord()

  # Experimental - query the server to turn on the LED to signal
  # Speech server is no longer online. 
  commandParser.querySpeechServerLED(0)
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
      print("[DEBUG] Now Listening for Hotword(s): "+str(hotWords)+" ...")
      start = time.time()
      # Listen for input
      #r.dynamic_energy_threshold = False
      audio2 = r.listen(source2, timeout = audio_timeout, phrase_time_limit=phrase_time_limit)

      # Use offline CMU Sphinx recognizer
      recognizedText = r.recognize_sphinx(audio2)
      # String cleanup
      recognizedText = recognizedText.lower()
      end = time.time()
      print("[DEBUG] Recognized hotword audio: '" + recognizedText + "' in " + str(end-start) + " ")
      # Parse recognized text
      if commandParser.stopServer is not True and any(x in recognizedText for x in hotWords):
        print("[DEBUG] Hotword recognized!")
        commandParser.listenForCommand()
      # Disabled, because a bot randomly saying "You're welcome"
      # behind my back is freaking me out. 
      #elif stopServer is not True and "thank you" in recognizedText or "thanks" in recognizedText:
        # For fun. 
        #executeTextThread("You're welcome.")

  except sr.RequestError as e:
    print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
  except sr.UnknownValueError:
    pass
  except sr.WaitTimeoutError:
    pass

if __name__ == "__main__":
  runApplicationServer()