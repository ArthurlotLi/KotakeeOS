#
# speech_speak.py
#
# Implements verbal output to the user utilizing pyttsx3 module for 
# speech synthesis. A single static class should be utilized for all 
# speech_server interactions.

import pyttsx3
import threading

class SpeechSpeak:
  engine = None

  def __init__(self):
    self.engine = pyttsx3.init()

  # Non-blocking text to speech. Do be warned this might interefere 
  # with the speech recognition and may cut off if the calling class
  # is disposed off. 
  def execute_text_thread(self, output_text):
    print("[DEBUG] Starting thread for text output: '"+output_text+"'")
    text_thread = threading.Thread(target=self.speak_text_thread_function, args=(output_text,), daemon=True).start()

  # Specifically designed function to override any existing usage
  # of the engine to say something. 
  def speak_text_thread_function(self, output_text):
    print("[DEBUG] Attempting to output text: '"+output_text+"'")
    if self.engine._inLoop:
      self.engine.endLoop()
    self.engine.say(output_text)
    self.engine.runAndWait()

  # Convert text to speech using pyttsx3 engine. Note calling this by 
  # itself causes a block on the main thread. 
  def speak_text(self, output_text):
    print("[DEBUG] Executing text output: '"+output_text+"'")
    self.engine.say(output_text)
    self.engine.runAndWait()