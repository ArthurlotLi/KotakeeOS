#
# speech_listen.py
#
# Implements verbal input from the user utilizing assorted speech 
# recognition methods. A single static class should be utilized for
# all speech_server interactions. 
#
# Requries a SpeechSpeak object to be passed on initialization, 
# utilized in the case that a prompt is passed to listen_for_response.

import speech_recognition as sr
import time
import wave
import pyaudio

class SpeechListen:
  chime_location = None
  startup_location = None
  shutdown_location = None
  led_state_on = None
  led_state_off = None
  led_room_id = None
  led_action_id = None

  r2 = None
  speech_speak = None
  web_server_status = None

  # A flag for hotword_trigger_word to halt operations in the case
  # that a separate thread is using the microphone. 
  speech_listen_active = False

  # Configuration parameters
  default_pause_threshold = 1.0
  default_max_response_attempts = 1
  default_response_timeout = 5
  default_response_phrase_timeout = 5
  default_ambient_noise_duration = 1.0

  def __init__(self, speech_speak, web_server_status, chime_location, startup_location, shutdown_location, led_state_on, led_state_off, led_room_id, led_action_id):
    self.speech_speak = speech_speak
    self.chime_location = chime_location
    self.startup_location = startup_location
    self.shutdown_location = shutdown_location
    self.r2 = sr.Recognizer()
    self.web_server_status = web_server_status

    self.led_state_on = led_state_on
    self.led_state_off = led_state_off
    self.led_room_id = led_room_id
    self.led_action_id = led_action_id

  # Attempt to listen for valid text using Google speech recogntiion.
  # Returns valid text if recieved and None if not recieved. 
  # May provide a verbal prompt every loop. Can be specified with a
  # sleep duration (how long to wait before starting to listen)
  #
  # Can also take in a delay before attempting to take control of
  # the microphone - useful for other threads that need to wait for
  # hotword_tirgger_word to release the mic stream. Delay is in 
  # seconds (float).
  def listen_response(self, prompt = None, indicate_led = True, execute_chime = False, pause_threshold = None, max_response_attempts = None, response_timeout = None, response_phrase_timeout = None, ambient_noise_duration = None, start_delay = None):
    user_response_text = None

    # Inidicate that we're active. Tells the hotword parsing to 
    # stop listening if we're being called from a separate thread. 
    self.speech_listen_active = True

    if start_delay is not None:
      print("[DEBUG] Speech Listen pausing for " + str(start_delay) + " seconds.")
      time.sleep(start_delay)

    # Use defaults if not specified by the caller. 
    if pause_threshold is None:
      pause_threshold = self.default_pause_threshold
    if max_response_attempts is None:
      max_response_attempts = self.default_max_response_attempts
    if response_timeout is None:
      response_timeout = self.default_response_timeout
    if response_phrase_timeout is None:
      response_phrase_timeout = self.default_response_phrase_timeout
    if ambient_noise_duration is None:
      ambient_noise_duration = self.default_ambient_noise_duration

    self.r2.pause_threshold = pause_threshold

    with sr.Microphone() as source2:
      self.r2.adjust_for_ambient_noise(source2, duration=ambient_noise_duration)

      # Indicate that you are currently active. 
      if indicate_led is True:
        self.web_server_status.query_speech_server_module_toggle(self.led_state_on, self.led_room_id, self.led_action_id)

      # Try for as many attempts as allowed. 
      for i in range(max_response_attempts): 
        try:
          if execute_chime is True:
            self.execute_chime()
          elif prompt is not None:
            # Prompt the user each loop attempt if specified. 
            self.speech_speak.speak_text(prompt)

          use_google = self.web_server_status.online_status is True

          if use_google is True: print("[INFO] Speech Listen (Online: Google) now awaiting user response...")
          else: print("[INFO] Speech Listen (Offline: Pocket Sphinx) now awaiting user response...")

          start = time.time()
          audio2 = self.r2.listen(source2, timeout=response_timeout,phrase_time_limit=response_phrase_timeout)
          if use_google is True:
            # Use Google's API to recognize the audio.
            user_response_text = self.r2.recognize_google(audio2)
          else:
            # Use offline CMU Sphinx recognizer
            user_response_text = self.r2.recognize_sphinx(audio2)
          # String cleanup
          user_response_text = user_response_text.lower()
          end = time.time()
          print("[INFO] Recognized response audio: '" + user_response_text + "' in " + str(end-start) + " ")
          # All done, let's return the text. 
          break
        except sr.RequestError as e:
          print("[ERROR] Speech Listen could not request results from speech_recognition; {0}.format(e)")
        except sr.UnknownValueError:
          print("[WARNING] Speech Listen did not understand the last sentence.")
        except sr.WaitTimeoutError:
          print("[WARNING] Speech Listen limeout occured.")

      # Indicate that you are currently active. 
      if indicate_led is True:
        self.web_server_status.query_speech_server_module_toggle(self.led_state_off, self.led_room_id, self.led_action_id)
  
    # All done. Disable the flag and let the hotword parsing continue.
    self.speech_listen_active = False

    return user_response_text

  def execute_startup(self):
    self.execute_sound(self.startup_location)

  def execute_shutdown(self):
    self.execute_sound(self.shutdown_location)

  def execute_chime(self):
    self.execute_sound(self.chime_location)

  # Let out a chime to indicate that you're listening. This code
  # is not mine, but it works like a charm!
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