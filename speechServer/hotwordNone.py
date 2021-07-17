#
# hotwordNone.py
#
# Simply runs commandParsing code as if a user has just said
# a hotword. Meant to run off a button press. 
#
# Usage: python3 hotwordNone
#

import argparse

from commandParsing import CommandParser
import time

commandParser = CommandParser()

def runApplicationServer(useAlt):
  print("Initializing kotakeeOS command parser standalone.")

  # Experimental - query the server to turn on the LED to signal
  # Speech server is online. 
  if useAlt:
    commandParser.querySpeechServerLED(1, 2, 52)
  else:
    commandParser.querySpeechServerLED(1, 2, 51)

  commandParser.listenForCommand()
  time.sleep(2) # Enough time to allow the speech prompt to complete. 

  # Experimental - query the server to turn on the LED to signal
  # Speech server is no longer online. 
  if useAlt:
    commandParser.querySpeechServerLED(0, 2, 52)
  else:
    commandParser.querySpeechServerLED(0, 2, 51)
  print("Shutting down. Goodnight.")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('-a', action='store_true', default=False) # TODO: maybe make this scalable to more than one server. 
  args = parser.parse_args()
  useAlt = args.a

  if(useAlt is True or useAlt is None):
    useAlt = True
  else:
    useAlt = False

  runApplicationServer(useAlt)