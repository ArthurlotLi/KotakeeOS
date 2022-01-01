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
#
# Utilizes multiprocessing to execute pyttsx3 interactions. Required
# in order to iteratively execute text output without blocking and 
# also without initializing the engine needlessly (which has 
# significant overhead). In this respect, the overhead for socket
# interactions with the subprocess is preferred. 

from subprocess import Popen, PIPE
from multiprocessing.connection import Client
import threading
import wave
import pyaudio
import time

class SpeechSpeak:
  # We use multiprocessing to output pyttsx3 text.
  subprocess_location = "speech_speak_pyttsx3.py"
  subprocess_address = "localhost"
  subprocess_port = 0 # Randomly selected. 
  subprocess_key = b"speech_speak"
  subprocess_instance = None
  subprocess_shutdown_code = "SHUTDOWN" # No incoming text should be uppercase. 

  # Addressing the command line call to execute the subprocess.
  # Try using python3 first, and if that fails, remember and use
  # python instead.
  use_python3 = True

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

    if self.initialize_subprocess() is False:
      print("[ERROR] Failed to initialize subprocess. Speech Server initialization failed.")  
      return

    # Get the show on the road!
    self.initialize_speak_thrd()

  # Initializes the subprocess.
  def initialize_subprocess(self):
    successful_initialization = False
    # Try two times - meant to accomodate an initial attempt to use
    # python3. Use subprocess Popen as we don't want to block for 
    # a process we want to keep running. We'll interact with it
    # using multiprocessing's wrapped sockets. 
    for i in range(0,2):
      try:
        if self.use_python3 is True:
          self.subprocess_instance = Popen(["python3", self.subprocess_location, ""], stdout=PIPE)
        else:
          self.subprocess_instance = Popen(["python", self.subprocess_location, ""], stdout=PIPE)
        successful_initialization = True
      except:
        self.use_python3 = not self.use_python3

    if successful_initialization is False:
      print("[ERROR] Failure to spawn subprocess '" + str(self.subprocess_location) + "'. Speak text failed.")
    else:
      print("[DEBUG] Speak Text subprocess spawned successfully.")
      self.wait_for_subprocess_port()
    return successful_initialization

  # Read the stdout of the subprocess until we get a complete port. 
  # output should be terminated by / character. Ex) 42312/
  def wait_for_subprocess_port(self):
    print("[DEBUG] Waiting for subprocess port number...")
    complete_output = ""
    while self.subprocess_port == 0:
      output = self.subprocess_instance.stdout.readline()
      if output:
        complete_output = complete_output + output
        if "/" in complete_output:
          print("[DEBUG] Successfully recieved subprocess port number: " + port_string)
          port_string = complete_output.replace("/", "")
          self.subprocess_port = int(port_string)

  
  def shutdown_process(self):
    print("[DEBUG] Speak Text shutting down existing process.")
    # Socket interaction using multiprocessing library. 
    address = (self.subprocess_address, self.subprocess_port)
    connection = Client(address, authkey=self.subprocess_key)
    connection.send(self.subprocess_shutdown_code)
    connection.close()

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

  # Shuts down both the thread and the process. Blocking behavior
  # ensures that the process is fully shut down before we close. 
  def shutdown_speak_thrd(self):
    self.speak_thrd_stop = True
    self.shutdown_process()

  # The Speak thread. Loops every 'tick' seconds and checks if any 
  # events needs to occur. 
  def speak_thrd(self):
    try:
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
    except Exception as e:
      print("[ERROR] Speech Thread ran into an exception! Exception text:")
      print(e)
      
    # Shutdown has occured. Stop the process.
    print("[DEBUG] Speech Thread closed successfully. ")

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

      # Socket interaction using multiprocessing library. 
      address = (self.subprocess_address, self.subprocess_port)
      connection = Client(address, authkey=self.subprocess_key)
      connection.send(output_text)
      # Wait for the subprocess to reply with anything. When you
      # do get that message, continue. Contents are ignored. 
      _ = connection.recv()
      connection.close()

      print("[DEBUG] Speak Text text output complete.")

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