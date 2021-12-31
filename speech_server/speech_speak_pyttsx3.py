#
# speech_speak_pyttsx3.py
#
# Subprocess companion for speech_speak. Unfortunately working with
# pyttsx3 and threads means that it's very difficult (impossible?) 
# to detect when a speech execution has completed. So we're using
# multiprocessing. 

#import sys
import pyttsx3

class SpeechSpeakPyttsx3:
  engine = None

  def __init__(self): 
    self.engine = pyttsx3.init()
  
  def execute_text(self, input_text):
    self.engine.say(input_text)
    self.engine.runAndWait() # Blocks the thread until it completes.

speech_speak_pyttsx3 = SpeechSpeakPyttsx3()

# Obsolete: Calling the process directly with an argument. 
# Inefficient, as it requires initializing the engine every
# time. Better to interact with the subprocess as it runs
# continously in the background.

#speech_speak_pyttsx3.execute_text(str(sys.argv[1])) 