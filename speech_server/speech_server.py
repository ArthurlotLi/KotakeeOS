#
# speech_server.py
#
# Principal class of the KotakeeOS speech server. Faciltiates the
# functionality of passive interactions and active interactions, 
# utilizing a specified trigger word detection method for the latter.
# 
# Utilizes speech_speak.py and speech_listen.py components throughout
# all children classes as well within its content. Also utilizes 
# web_server_status.py for all interactions with the KotakeeOS home
# automation web server. 

from web_server_status import WebServerStatus
from speech_speak import SpeechSpeak
from speech_listen import SpeechListen
from hotword_trigger_word import HotwordTriggerWord
from interaction_active import InteractionActive

import argparse

class SpeechServer:
  # Configurable Constants
  trigger_word_models_path = '../triggerWordDetection/models'
  speech_listen_chime_location = "./assets/hotword.wav"
  speech_listen_startup_location = "./assets/startup.wav"
  web_server_ip_address = "http://192.168.0.197:8080"

  trigger_word_iternum = None
  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None
  interaction_active = None
  hotword_trigger_word = None

  def __init__(self, trigger_word_iternum):
    self.trigger_word_iternum = trigger_word_iternum  

  #
  # Runtime functions
  #
  
  # Primary runtime function when the server is being utilized in the
  # capacity of a full-time AI assistant. Ensure initialization succeeds 
  # correctly before executing runtime logic. 
  def run_server_full(self):
    print("[INFO] Initializing KotakeeOS Speech Server (full functionality).")
    if self.initialize_components_full() is False:
      print("[ERROR] Initialization failed. Unable to execute speech server correctly. Exiting...")
      return

    self.speech_speak.speak_text("Kotakee AI is online: Model iteration " + str(self.trigger_word_iternum) + ".")
    
    # Initialization succeeded. Execute runtime functions. 
    self.hotword_trigger_word.listen_hotword()

  # Handle the case in which the Speech Server is only handling a
  # single active query from a user (likely by button press on the 
  # web application).
  def run_server_query(self):
    print("[INFO] Initializing KotakeeOS Speech Server (active query).")
    if self.initialize_components_query() is False:
      print("[ERROR] Initialization failed. Unable to execute speech server correctly. Exiting...")
      return
    
    # Initialization succeeded. Execute runtime functions. 
    # TODO

  #
  # Initialization logic
  #

  # Speech Server is being used in the capacity of a full-time AI
  # assistant. Initialize all components - return False if failure
  # occurs.
  def initialize_components_full(self):
    if self.initialize_speech_speak() is False: return False
    if self.initialize_web_server_status() is False: return False
    if self.initialize_speech_listen() is False: return False
    if self.initialize_passive_interaction() is False: return False
    if self.initialize_active_interaction() is False: return False
    if self.initialize_hotword_trigger_word() is False: return False
    return True

  # Only initialize components relevant to active interactions. 
  def initialize_components_query(self):
    if self.initialize_speech_speak() is False: return False
    if self.initialize_web_server_status() is False: return False
    if self.initialize_speech_listen() is False: return False
    if self.initialize_active_interaction() is False: return False
    return True

  # Initialize Speak handler
  def initialize_speech_speak(self):
    self.speech_speak = SpeechSpeak()
    if self.speech_speak is None: 
      print("[ERROR] Failed to initialize Speak handler.") 
      return False
    return True

  # Initialize Web Server Status handler
  def initialize_web_server_status(self):
    self.web_server_status = WebServerStatus(ip_address=self.web_server_ip_address)
    if self.web_server_status is None: 
      print("[ERROR] Failed to initialize Web Server Status handler.") 
      return False
    return True
  
  # Initialize Listen handler
  def initialize_speech_listen(self):
    if self.speech_speak is None: 
      return None
    self.speech_listen = SpeechListen(speech_speak=self.speech_speak, chime_location=self.speech_listen_chime_location, startup_location=self.speech_listen_startup_location, web_server_status=self.web_server_status)
    if self.speech_listen is None: 
      print("[ERROR] Failed to initialize Listen handler.") 
      return False
    return True

  # Initialize Passive Interaction handler
  def initialize_passive_interaction(self):
    # TODO
    return True

  # Initialize Active Interaction handler
  def initialize_active_interaction(self):
    self.interaction_active = InteractionActive(speech_speak = self.speech_speak, speech_listen = self.speech_listen, web_server_status = self.web_server_status)
    if self.interaction_active is None:
      print("[ERROR] Failed to initialize Active Interaction handler.")
      return False
    return True

  # Initialize Hotword + Active Interaction handler)
  def initialize_hotword_trigger_word(self):
    self.hotword_trigger_word = HotwordTriggerWord(model_path = self.trigger_word_models_path, interaction_active=self.interaction_active, speech_listen=self.speech_listen)
    if self.hotword_trigger_word.load_model(self.trigger_word_iternum) is False:
      print("[ERROR] Failed to initialize Hotword handler.")
      return False
    return True

#
# Startup Argparse
#

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  args = parser.parse_args()

  trigger_word_iternum = int(args.iternum)

  speech_server = SpeechServer(trigger_word_iternum)
  speech_server.run_server_full()