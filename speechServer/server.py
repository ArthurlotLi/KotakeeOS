#
# sever.py
#
# Root program for speech recognition application server designed
# to interface with the kotakeeOS Web Server. This sends requests
# to activate-deactivate modules just like any other regular 
# web application. 
#
# Initial code based off of:
# https://www.geeksforgeeks.org/python-convert-speech-to-text-and-text-to-speech/
#
# Usage: python3 server.py
#

import speech_recognition as sr
import pyttsx3

import requests

# Application constants.
webServerIpAddress = "http://192.168.0.197:8080"

def runApplicationServer():
  print("Initializing kotakeeOS speech application server...")

  # Initialize the recognizer
  r = sr.Recognizer()

  # Loop forever, waiting for user to speak. 
  while(1):
    try:
      print("[DEBUG] Now Listening...")
      # Specify the microphone as the input source.
      with sr.Microphone() as source2:
        # Wait a moment to allow the recognizer to adjust
        # the energy threshold based on surrounding noise
        # level...
        r.adjust_for_ambient_noise(source2, duration=0.2)

        # Listen for input
        audio2 = r.listen(source2)

        # Use Google's API to recognize the audio.
        #recognizedText = r.recognize_google(audio2)

        # Use offline CMU Sphinx recognizer
        recognizedText = r.recognize_sphinx(audio2)

        # String cleanup
        recognizedText = recognizedText.lower()

        print("[DEBUG] Recognized audio: '" + recognizedText + "'")
        #speakText(recognizedText)

        # Parse recognized text
        keyword = "" # No keyword for now
        if(keyword in recognizedText): 
          command = recognizedText.replace(keyword, "")
          query = None

          # Ex) http://192.168.0.197:8080/moduleToggle/1/50/1
          if("bedroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
            if("on" in command):
              query = webServerIpAddress + "/moduleToggle/1/50/1"
            elif("off" in command):
              query = webServerIpAddress + "/moduleToggle/1/50/0"

          if("living" in command and ("light" in command or "lights" in command or "lamp" in command)):
            if("on" in command):
              query = webServerIpAddress + "/moduleToggle/2/50/1"
            elif("off" in command):
              query = webServerIpAddress + "/moduleToggle/2/50/0"
          
          if("soundbar" in command):
            if("on" in command):
              query = webServerIpAddress + "/moduleToggle/2/250/12"
            elif("off" in command):
              query = webServerIpAddress + "/moduleToggle/2/250/10"
          
          if("ceiling" in command and ("light" in command or "lights" in command or "lamp" in command)):
            if("on" in command):
              query = webServerIpAddress + "/moduleToggle/2/251/12"
            elif("off" in command):
              query = webServerIpAddress + "/moduleToggle/2/251/10"

          if("kitchen" in command and ("light" in command or "lights" in command or "lamp" in command)):
            if("on" in command):
              query = webServerIpAddress + "/moduleToggle/2/350/22"
            elif("off" in command):
              query = webServerIpAddress + "/moduleToggle/2/350/20"

          if query is not None:
            # We have received a valid command. Query the server. 
            print("[DEBUG] Valid command received. Sending query: " + query)
            response = requests.get(query)
            if(response.status_code == 200):
              print("[DEBUG] Request received successfully.")
            else:
              print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

    except sr.RequestError as e:
      print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
    except sr.UnknownValueError:
      print("[Warning] Last sentence was not understood.")

  
# Convert text to speech using pyttsx3 engine. 
def speakText(command):
  engine = pyttsx3.init()
  engine.say(command)
  engine.runAndWait()

if __name__ == "__main__":
  runApplicationServer()