#
# quest_ai_parsing.py
#
# Provides speech interfacing capability with QuestAI, abstracting
# functionality from commandParsing. Interacts with user who has
# activated QuestAI, prompting for a question, receiving the 
# questions, and providing a response.
#
# A potential enhancement to this class is a follow-up prompt
# asking for the success/failure of the prediction (if applicable
# to the question).

import speech_recognition as sr
import pyttsx3
import threading
import pyaudio
import time

from quest_ai import QuestAi

class QuestAiParsing:
  # Dictates whether we use Google or Pocket Sphinx (former is online)
  online_functionality = True 

  # Speech recognition
  r2 = None
  engine = None

  # Configuration parameters
  pause_threshold = 1.0
  max_response_attempts = 2
  response_timeout = 5
  response_phrase_timeout = 20

  # Cancel response must exactly equal these strings (otherwise they might
  # accidentally stop questions with these words in them.)
  cancelWords = ["stop", "cancel", "go away", "quit", "no thanks", "sleep"]

  questAi = None

  # Initialize speech recognition + pyttsx stuff.
  def __init__(self, online_functionality = True):
    self.r2 = sr.Recognizer()
    self.engine = pyttsx3.init()
    self.r2.pause_threshold = self.pause_threshold
    self.online_functionality = online_functionality
    # Initialize QuestAI. 
    self.questAi = QuestAi()

  # Primary loop for this functionality. A user has activated 
  # QuestAI, and we handle further interactions here. 
  def standard_query(self):
    print("[DEBUG] Initializing QuestAI Standard Query procedure.")
    user_response = self.listenForResponse(prompt="What would you like to know?", sleep_duration=1.5)
    if user_response in self.cancelWords:
      print("[DEBUG] User requested cancellation. Stopping QuestAI...")
      self.speakText("Stopping Quest AI...")
      return
    # We now have a question. Pass it to the model class - we
    # expect a boolean back + confidence. 
    # TODO: Handle confidence - perhaps implement 8 ball class in 
    #       a separate file? 
    ai_response, ai_confidence = self.questAi.generate_response(user_response)
    print("[DEBUG] QuestAI Standard Query returned response: " + str(ai_response) + " - Confidence: " + str(ai_confidence) + ".")
    if ai_response is True:
      self.executeTextThread("I believe so.")
      time.sleep(2) # Enough time to allow the speech prompt to complete. 
    else:
      self.executeTextThread("I don't think so.")
      time.sleep(2) # Enough time to allow the speech prompt to complete. 
    
    # TODO In the future, we should add a mechanism to prompt for 
    # whether we did good in that prediction (so we can append 
    # the transcript to a SQL database or something as a new data point)

  # Attempt to listen for valid text using Google speech recogntiion.
  # Returns valid text if recieved and None if not recieved. 
  # May provide a verbal prompt every loop. Can be specified with a
  # sleep duration (how long to wait before starting to listen)
  def listenForResponse(self, prompt = None, sleep_duration = 1):
    user_response_text = None

    with sr.Microphone() as source2:
      self.r2.adjust_for_ambient_noise(source2, duration=0.7)
      # Try for as many attempts as allowed. 
      for i in range(self.max_response_attempts): 
        try:
          # Prompt the user each loop attempt. 
          if prompt is not None:
            self.executeTextThread(prompt)
            time.sleep(sleep_duration) # Enough time to allow the speech prompt to complete. 
          print("[DEBUG] Now Listening for Response...")
          start = time.time()
          audio2 = self.r2.listen(source2, timeout=self.response_timeout,phrase_time_limit=self.response_phrase_timeout)
          if self.online_functionality is not None:
            # Use Google's API to recognize the audio.
            user_response_text = self.r2.recognize_google(audio2)
          else:
            # Use offline CMU Sphinx recognizer
            user_response_text = self.r2.recognize_sphinx(audio2)
          # String cleanup
          user_response_text = user_response_text.lower()
          end = time.time()
          print("[DEBUG] Recognized response audio: '" + user_response_text + "' in " + str(end-start) + " ")
          # All done, let's return the text. 
          break
        except sr.RequestError as e:
          print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
        except sr.UnknownValueError:
          print("[Warning] Last sentence was not understood.")
        except sr.WaitTimeoutError:
          print("[Warning] Timeout occured.")
  
    return user_response_text

  # Non-blocking text to speech. Do be warned this
  # might interefere with the speech recognition. 
  def executeTextThread(self, command):
    print("[DEBUG] Starting thread for text output: '"+command+"'")
    textThread = threading.Thread(target=self.speakText, args=(command,), daemon=True).start()
    
  # Convert text to speech using pyttsx3 engine.
  # Note calling this by itself causes a block
  # on the main thread. 
  def speakText(self, command):
    if self.engine._inLoop:
      self.engine.endLoop()
    self.engine.say(command)
    self.engine.runAndWait()