#
# hotwordNone.py
#
# Simply runs commandParsing code as if a user has just said
# a hotword. Meant to run off a button press. 
#
# Usage: python3 hotwordNone
#

from commandParsing import CommandParser
import time

commandParser = CommandParser()

def runApplicationServer():
  print("Initializing kotakeeOS command parser standalone.")

  # Experimental - query the server to turn on the LED to signal
  # Speech server is online. 
  commandParser.querySpeechServerLED(1)

  commandParser.listenForCommand()
  time.sleep(2) # Enough time to allow the speech prompt to complete. 

  # Experimental - query the server to turn on the LED to signal
  # Speech server is no longer online. 
  commandParser.querySpeechServerLED(0)
  print("Shutting down. Goodnight.")

if __name__ == "__main__":
  runApplicationServer()