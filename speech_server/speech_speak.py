#
# speech_speak.py
#
# Implements verbal output to the user utilizing pyttsx3 module for 
# speech synthesis. A single static class should be utilized for all 
# speech_server interactions.

import pyttsx3
#import threading
import wave
import pyaudio

class SpeechSpeak:
  engine = None

  chime_location = None
  startup_location = None
  shutdown_location = None
  timer_location = None

  def __init__(self, chime_location, startup_location, shutdown_location, timer_location):
    self.engine = pyttsx3.init()

    self.chime_location = chime_location
    self.startup_location = startup_location
    self.shutdown_location = shutdown_location
    self.timer_location = timer_location

  # Disable multithreading for speech - it's one or the other, it
  # seems. 
  """
  # Non-blocking text to speech. Do be warned this might interefere 
  # with the speech recognition and may cut off if the calling class
  # is disposed off. 
  def execute_text_thread(self, output_text):
    print("[DEBUG] Starting thread for text output: '"+output_text+"'")
    text_thread = threading.Thread(target=self.speak_text_threaded, args=(output_text,), daemon=True).start()

  # Convert text to speech using pyttsx3 engine, designed to support
  # threading. 
  def speak_text_threaded(self, output_text):
    print("[DEBUG] Executing output text: '"+output_text+"'")
    if self.engine._inLoop:
      self.engine.endLoop()
    self.engine.say(output_text)
    self.engine.runAndWait()
  """

  # Convert text to speech using pyttsx3 engine. Note calling this by 
  # itself causes a block on the main thread. 
  def speak_text(self, output_text):
    if(output_text is not None and output_text != ""):
      print("[DEBUG] Executing output text: '"+output_text+"'")
      self.engine.say(output_text)
      self.engine.runAndWait()
  
  def execute_startup(self):
    self.execute_sound(self.startup_location)

  def execute_shutdown(self):
    self.execute_sound(self.shutdown_location)

  def execute_chime(self):
    self.execute_sound(self.chime_location)

  def execute_timer(self):
    self.execute_sound(self.timer_location)

  # Let out a chime to indicate that you're listening. Source:
  # stack overflow
  def execute_sound(self, location):
    chunk = 1024
    f = wave.open(location, "rb")
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