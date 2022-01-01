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

import socketserver

class SpeechSpeakPyttsx3:
  subprocess_address = "localhost"
  subprocess_port = 0 # Selected by OS
  subprocess_key = b"speech_speak"
  
  shutdown_code = "SHUTDOWN" # No incoming text should be uppercase. 
  stop_process = False

  engine = None
  listener = None

  def __init__(self): 
    self.engine = pyttsx3.init()

    # Find a open port (unfortunately multiprocessing.connection does
    # not do this for us.) Source:
    # https://stackoverflow.com/questions/1365265/on-localhost-how-do-i-pick-a-free-port-number
    with socketserver.TCPServer((self.subprocess_address, 0), None) as s:
      self.subprocess_port = s.server_address[1]

    address = (self.subprocess_address, self.subprocess_port)
    print("[DEBUG] Initializing Speech Speak Subprocess with address: ")
    print(address)

    # Maximum attempts to start the process by making any clones 
    # shut down. 
    #for i in range (0, 3):
    try:
      self.listener = Listener(address, authkey=self.subprocess_key)
      self.subprocess_port = self.listener.address[1]
      print(str(self.subprocess_port) + "/")
    except Exception as e:
      # If an exception occurs, a clone process is lingering. Attempt
      # to send it a message to shutdown. 
      print("[WARN] Exception occured when attempting to start Speech Speak subprocess. Exception:")
      print(e)
      #self.shutdown_clones(address) 

  # Attempts to shutdown any lingering processes caused by a botched
  # shutdown (which should ideally never happen)
  def shutdown_clones(self, address):
    print("[DEBUG] Attempting to connect to existing process...")
    try:
      connection = Client(address, authkey=self.subprocess_key)
      connection.send(self.shutdown_code)
      connection.close()
      time.sleep(1) # Give them time to recieve the message and shutdown. 
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
speech_speak_pyttsx3 = SpeechSpeakPyttsx3()
while speech_speak_pyttsx3.stop_process is False:
  speech_speak_pyttsx3.listen_for_connection()

print("[DEBUG] Speech Speak subprocess shut down successfully.")