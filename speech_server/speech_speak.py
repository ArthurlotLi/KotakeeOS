#
# speech_speak.py
#
# Implements verbal output to the user utilizing pyttsx3 module for 
# speech synthesis. A single static class should be utilized for all 
# speech_server interactions. 
#
# Manages a single thread with a queue, handling the edge case of 
# multiple threads requesting to speak or output sounds at the same 
# time. 
#
# All interactions should occur via the speak thread - none of the
# other methods in this class should be called directly to avoid
# threading issues with pyaudio and to handle race conditions properly.

from subprocess import run
import threading
import wave
import pyaudio
import time

class SpeechSpeak:
  # We use multiprocessing to output pyttsx3 text.
  subprocess_location = "speech_speak_pyttsx3.py"

  # Addressing the command line call to execute the subprocess.
  # Try using python3 first, and if that fails, remember and use
  # python instead.
  use_python3 = True
  use_python3_attempted = False

  # Primary thread that executes all output. Any requests that 
  # come in must come in via the speech_speak_events thread and
  # will be processed first-come-first-served.
  speak_thrd_instance = None

  # Like-indexed lists that act as a joint queue for incoming
  # speak events. event_types provides the event type, while 
  # event_contents is optional depending on the type. 
  speak_thrd_event_types = []
  speak_thrd_event_contents = []
  speak_thrd_tick = 0.25 # How many seconds the thread sleeps for. 
  speak_thrd_stop = False

  chime_location = None
  startup_location = None
  shutdown_location = None
  timer_location = None

  def __init__(self, chime_location, startup_location, shutdown_location, timer_location):
    self.chime_location = chime_location
    self.startup_location = startup_location
    self.shutdown_location = shutdown_location
    self.timer_location = timer_location

    # Get the show on the road!
    self.initialize_speak_thrd()

  # Kicks off the thread. 
  def initialize_speak_thrd(self):
    print("[DEBUG] Starting Speak Thread.")
    self.speak_thrd_instance = threading.Thread(target=self.speak_thrd, daemon=True).start()

  # Primary function that allows other classes to append new events
  # for the thread to process in due time. Importantly, this method
  # BLOCKS their respective processing until it has been completed. 
  # An alternate method is available for non-blocking processing
  # called background_speak_event.
  def blocking_speak_event(self, event_type, event_content=None):
    print("[DEBUG] Creating new blocking speak event of type '" + event_type + "'.")
    self.speak_thrd_event_types.append(event_type)
    self.speak_thrd_event_contents.append(event_content)

    # Wait for the thread to execute all events. 
    while len(self.speak_thrd_event_types) > 0:
      time.sleep(0.1) # Check every 100ms until we're finished.

    print("[DEBUG] Speak event queue clean. Blocking operation complete.") 

  # Non-blocking processing. Kick it off and let it run - useful for
  # operations like playing sounds that don't have any immediate
  # follow-ups. 
  def background_speak_event(self, event_type, event_content=None):
    print("[DEBUG] Creating new background speak event of type '" + event_type + "'.")
    self.speak_thrd_event_types.append(event_type)
    self.speak_thrd_event_contents.append(event_content)

  # The Speak thread. Loops every 'tick' seconds and checks if any 
  # events needs to occur. 
  def speak_thrd(self):
    while self.speak_thrd_stop is False:

      # Clear the executed events once done. We don't just clear the
      # entire array at the end in the edge case that a new event 
      # comes in during the for loop. (More likely if executing
      # long strings of text.)
      indices_to_drop = []

      # Handle everything in the queue. 
      for i in range(0, len(self.speak_thrd_event_types)):
        event_type = self.speak_thrd_event_types[i]
        event_content = self.speak_thrd_event_contents[i]
        self.handle_speak_event(event_type = event_type, event_content = event_content)
        indices_to_drop.append(i)

      # Clear the queue once completed. Go backwards from the back
      # of the to-delete list.
      for i in range(len(indices_to_drop)-1, -1, -1):
        del self.speak_thrd_event_types[indices_to_drop[i]]
        del self.speak_thrd_event_contents[indices_to_drop[i]]
      
      time.sleep(self.speak_thrd_tick)

  # Given an event type (string) and event_content (can be None),
  # execute the action. 
  def handle_speak_event(self, event_type, event_content):
    if event_type == "speak_text":
      self.speak_text(event_content)
    elif event_type == "execute_startup":
      self.execute_startup()
    elif event_type == "execute_shutdown":
      self.execute_shutdown()
    elif event_type == "execute_chime":
      self.execute_chime()
    elif event_type == "execute_timer":
      self.execute_timer()
    else:
      print("[ERROR] Speak thrd recieved an unknown event type '" + str(event_type)+ "'!")

  # Convert text to speech using pyttsx3 engine. Note calling this by 
  # itself causes a block on the main thread. 
  def speak_text(self, output_text):
    if(output_text is not None and output_text != ""):
      print("[DEBUG] Speak Text executing output text: '"+output_text+"'")
      
      # Try two times - meant to accomodate an initial attempt to use
      # python3. 
      num_attempts = 1
      if self.use_python3_attempted is False:
        num_attempts = 2
      
      for i in range(0,num_attempts):
        try:
          if self.use_python3 is True:
            run(["python3", self.subprocess_location, output_text])
            self.use_python3_attempted = True
            print("[DEBUG] Speak Text output text execution complete. ")
            return
          else:
            run(["python", self.subprocess_location, output_text])
            self.use_python3_attempted = True
            print("[DEBUG] Speak Text output text execution complete. ")
            return
        except:
          if self.use_python3_attempted is False:
            self.use_python3 = not self.use_python3
            self.use_python3_attempted = True
          else:
            print("[ERROR] Failure to spawn subprocess '" + str(self.subprocess_location) + "'. Speak text failed.")
            return

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