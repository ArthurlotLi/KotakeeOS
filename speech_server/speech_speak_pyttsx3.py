#
# speech_speak_pyttsx3.py
#
# Subprocess companion for speech_speak. Unfortunately working with
# pyttsx3 and threads means that it's very difficult (impossible?) 
# to detect when a speech execution has completed. So we're using
# multiprocessing. 

import sys
import pyttsx3

class SpeechSpeakPyttsx3:
  engine = None

  def __init__(self): 
    self.engine = pyttsx3.init()
  
  def execute_text(self, input_text):
    self.engine.say(input_text)
    self.engine.runAndWait() # Blocks the thread until it completes.

speech_speak_pyttsx3 = SpeechSpeakPyttsx3()
speech_speak_pyttsx3.say(str(sys.argv[1]))