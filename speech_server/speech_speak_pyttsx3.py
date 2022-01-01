#
# speech_speak_pyttsx3.py
#
# Subprocess companion for speech_speak. Unfortunately working with
# pyttsx3 and threads means that it's very difficult (impossible?) 
# to detect when a speech execution has completed. So we're using
# multiprocessing. 
# 
# Also uses the multiprocessing library to recieve information 
# from the main program via it's wrapped socket library. 

from multiprocessing.connection import Listener, Client
import pyttsx3
import time

class SpeechSpeakPyttsx3:
  subprocess_address = "localhost"
  subprocess_port = 45016 # Randomly selected. 
  subprocess_key = b"speech_speak"
  
  shutdown_code = "SHUTDOWN" # No incoming text should be uppercase. 
  stop_process = False

  engine = None
  listener = None

  def __init__(self): 
    self.engine = pyttsx3.init()
    address = (self.subprocess_address, self.subprocess_port)

    # Maximum attempts to start the process by making any clones 
    # shut down. 
    for i in range (0, 3):
      try:
        self.listener = Listener(address, authkey=self.subprocess_key)
      except:
        # If an exception occurs, a clone process is lingering. Attempt
        # to send it a message to shutdown. 
        print("[WARN] Exception occured when attempting to start Speech Speak subprocess. Attempting to shut down any copy processes...")
        self.shutdown_clones(address) 

  # Attempts to shutdown any lingering processes caused by a botched
  # shutdown (which should ideally never happen)
  def shutdown_clones(self, address):
    try:
      connection = Client(address, authkey=self.subprocess_key)
      connection.send(self.subprocess_shutdown_code)
      connection.close()
      time.sleep(0.5) # Give them time to recieve the message and shutdown. 
      print("[INFO] Existing clone purge request sent successfully.")
      return True
    except Exception as e:
      print("[ERROR] Unable to reach any clones occupying the stated port. Ensure the port is empty on the system. Exception:")
      print(e)
    
    return False

  def listen_for_connection(self):
    connection = self.listener.accept()
    # Connection accepted. Execute the input text before replying
    # with a finished message. 
    input_text = connection.recv()
    if input_text == self.shutdown_code:
      self.stop_process = True
      return
    self.execute_text(input_text)
    connection.send("200") # Contents of the message don't matter. 
    connection.close()
    
  # Blocking execution of the given input text. 
  def execute_text(self, input_text):
    self.engine.say(input_text)
    self.engine.runAndWait() # Blocks the thread until it completes.

# Execution code - listen indefinitely for connections and 
# execute incoming text. 
print("[DEBUG] Speech Speak subprocess initialized and running.")

speech_speak_pyttsx3 = SpeechSpeakPyttsx3()
while speech_speak_pyttsx3.stop_process is False:
  speech_speak_pyttsx3.listen_for_connection()

print("[DEBUG] Speech Speak subprocess shut down successfully.")