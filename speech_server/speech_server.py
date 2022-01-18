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
#
# Usage: (full)
# python speech_server.py 13602
#
# Alt Usage: (query)
# python speech_server.py -1 
#
# Note: to facilitate subprocesses (used by speech speak), you may
# need to specify to use the command "python" instead of the 
# default "python3". To do this, add the -p flag:
# python speech_server.py 13561 -p

from web_server_status import WebServerStatus
from speech_speak import SpeechSpeak
from speech_listen import SpeechListen
from hotword_trigger_word import HotwordTriggerWord
from interaction_active import InteractionActive
from interaction_passive import InteractionPassive

import argparse

class SpeechServer:
  # Configurable constants passed down to components. 
  trigger_word_models_path = '../triggerWordDetection/models'

  speech_speak_chime_location = "./assets/hotword.wav"
  speech_speak_startup_location = "./assets/startup.wav"
  speech_speak_shutdown_location = "./assets/shutdown.wav"
  speech_speak_timer_location = "./assets/timer.wav"
  speech_speak_alarm_location = "./assets/timer.wav"
  speech_speak_use_python3 = True

  # Which model to use for emotion detection + emotion representation
  # attached to the speech speak module. If the value is negative, 
  # Emotion Detection + Representation will be disabled. 
  speech_speak_emotion_detection_model_num = 1
  speech_speak_emotion_detection_location = "./emotion_detection_ai/emotion_detection_ai"
  speech_speak_emotion_detection_class_name = "EmotionDetectionAi"
  speech_speak_emotion_representation_location = "./emotion_representation/emotion_representation"
  speech_speak_emotion_representation_class_name = "EmotionRepresentation" 

  speech_listen_led_state_on = 1
  speech_listen_led_state_off = 0
  speech_listen_led_room_id = 2
  speech_listen_led_action_id = 51
  web_server_ip_address = "http://192.168.0.197:8080"

  # Required upon initialization. 
  trigger_word_iternum = None
  
  # Class variables - should only be one instance of each throughout
  # entire server architecture.
  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None
  interaction_active = None
  hotword_trigger_word = None

  def __init__(self, trigger_word_iternum, speech_speak_use_python3 = True):
    self.trigger_word_iternum = trigger_word_iternum
    self.speech_speak_use_python3 = speech_speak_use_python3

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
    self.speech_speak.background_speak_event(event_type="speak_text", event_content="Kotakee AI: model iteration " + str(self.trigger_word_iternum) + ".")
    
    # Initialization succeeded. Execute runtime functions. 
    self.hotword_trigger_word.listen_hotword()
    self.shutdown_server()
    print("[INFO] KotakeeOS Speech Server Shutdown. Goodnight.\n")

  # Handle the case in which the Speech Server is only handling a
  # single active query from a user (likely by button press on the 
  # web application).
  def run_server_query(self):
    print("[INFO] Initializing KotakeeOS Speech Server (active query).")
    if self.initialize_components_query() is False:
      print("[ERROR] Initialization failed. Unable to execute speech server correctly. Exiting...")
      return
    
    # Initialization succeeded. Execute runtime functions. 
    self.interaction_active.listen_for_command()
    self.shutdown_server()
    print("[INFO] KotakeeOS Speech Server Shutdown.")

  def shutdown_server(self):
    if self.speech_speak is not None: 
      self.speech_speak.shutdown_speak_thrd()

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

  # Only initialize components relevant to active interactions. Do
  # not initialize hotword_trigger_word.
  def initialize_components_query(self):
    if self.initialize_speech_speak() is False: return False
    if self.initialize_web_server_status() is False: return False
    if self.initialize_speech_listen() is False: return False
    if self.initialize_passive_interaction() is False: return False
    if self.initialize_active_interaction() is False: return False
    return True

  # Initialize Speak handler.
  def initialize_speech_speak(self):
    self.speech_speak = SpeechSpeak(
      chime_location=self.speech_speak_chime_location, 
      startup_location=self.speech_speak_startup_location, 
      shutdown_location=self.speech_speak_shutdown_location,
      timer_location=self.speech_speak_timer_location,
      alarm_location=self.speech_speak_alarm_location,
      emotion_detection_location=self.speech_speak_emotion_detection_location,
      emotion_detection_class_name = self.speech_speak_emotion_detection_class_name,
      emotion_representation_location=self.speech_speak_emotion_representation_location,
      emotion_representation_class_name = self.speech_speak_emotion_representation_class_name,
      use_python3=self.speech_speak_use_python3,
      emotion_detection_model_num = self.speech_speak_emotion_detection_model_num)
    if self.speech_speak is None: 
      print("[ERROR] Failed to initialize Speak handler.") 
      return False
    return True

  # Initialize Web Server Status handler. 
  def initialize_web_server_status(self):
    self.web_server_status = WebServerStatus(ip_address=self.web_server_ip_address)
    if self.web_server_status is None: 
      print("[ERROR] Failed to initialize Web Server Status handler.") 
      return False
    return True
  
  # Initialize Listen handler. Requires Speak and Web Server Status
  # components. 
  def initialize_speech_listen(self):
    if self.speech_speak is None: 
      return None
    self.speech_listen = SpeechListen(
      speech_speak=self.speech_speak, 
      web_server_status=self.web_server_status,
      led_state_on=self.speech_listen_led_state_on,
      led_state_off=self.speech_listen_led_state_off,
      led_room_id=self.speech_listen_led_room_id,
      led_action_id=self.speech_listen_led_action_id)
    if self.speech_listen is None: 
      print("[ERROR] Failed to initialize Listen handler.") 
      return False
    return True

  # Initialize Passive Interaction handler. Requires Speak, Listen,
  # and Web Server Status components.
  def initialize_passive_interaction(self):
    self.interaction_passive = InteractionPassive(
      speech_speak=self.speech_speak,
      speech_listen=self.speech_listen,
      web_server_status=self.web_server_status)
    if self.interaction_passive is None:
      print("[ERROR] Failed to initialize Passive Interaction handler.")
      return False
    return True

  # Initialize Active Interaction handler. Requires Speak, Listen, 
  # Web Server Status, and Passive Interaction components. 
  def initialize_active_interaction(self):
    self.interaction_active = InteractionActive(
      speech_speak = self.speech_speak, 
      speech_listen = self.speech_listen, 
      web_server_status = self.web_server_status,
      interaction_passive = self.interaction_passive)
    if self.interaction_active is None:
      print("[ERROR] Failed to initialize Active Interaction handler.")
      return False
    return True

  # Initialize Hotword handler. Requires Active Interaction and Listen 
  # component. 
  def initialize_hotword_trigger_word(self):
    self.hotword_trigger_word = HotwordTriggerWord(
      interaction_active=self.interaction_active, 
      speech_listen=self.speech_listen,
      model_path = self.trigger_word_models_path, 
      speech_speak=self.speech_speak)
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
  parser.add_argument('-p', action='store_true', default=False)
  args = parser.parse_args()

  trigger_word_iternum = int(args.iternum)
  use_python3 = not args.p == True

  speech_server = SpeechServer(trigger_word_iternum=trigger_word_iternum, speech_speak_use_python3=use_python3)

  # If a negative number is passed, execute as a direct query. 
  if (trigger_word_iternum < 0):
    speech_server.run_server_query()
  else:
    speech_server.run_server_full()