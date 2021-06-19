#
# sever_reference_code.py
#
# Root program for speech recognition application server designed
# to interface with the kotakeeOS Web Server. This sends requests
# to activate-deactivate modules just like any other regular 
# web application. 
#
# Utilizes sample pretrained model and code from Keras-Trigger-Word
# repository project. Meant to serve as a proof of concept of the
# performance of the described neural network - if this works
# well, then we can implement our own tweaked model.
#
# Usage: python3 server_reference_code.py
#

# Server logic imports
import speech_recognition as sr
import pyttsx3
import requests
import time
import threading
import json

# Hotword logic imports
import numpy as np
#import time
from pydub import AudioSegment
import random
import sys
import io
import os
import glob
import IPython
from td_utils import *
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
# To generate wav file from np array.
from scipy.io.wavfile import write
#%matplotlib inline

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.models import Model, load_model, Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout, Input, Masking, TimeDistributed, LSTM, Conv1D
from tensorflow.keras.layers import GRU, Bidirectional, BatchNormalization, Reshape
from tensorflow.keras.optimizers import Adam

import pyaudio
from queue import Queue
from threading import Thread
#import sys
#import time

#
# Server Logic Constants
#

webServerIpAddress = "http://192.168.0.197:8080"

#hotWord = "iris"
#hotWord = "california" # Triggers activation of google query. 
#hotWords = ["california", "america", "initial", "initialize", "system", "iris"]

cancelWords = ["stop", "cancel", "go away", "quit", "no thanks"] # stops google query.
hotWordReceiptPrompt = "Yes?"
successfulCommandPrompt = "Understood."
cancellationPrompt = "Going back to sleep."
failedCommandPrompt = "Sorry, I didn't understand that."
stopServerPrompt = "Understood. Good night."

# We use speech recognition for the command parsing 
# just like before. 
r2 = sr.Recognizer()

# Initialize the python text to speech engine.
engine = pyttsx3.init()

# Kill swith
stopServer = False

# JSON objects to query for.
actionStates = None
homeStatus = None
actionStatesLastUpdate = 0
homeStatusLastUpdate = 0

#
# Hotword logic constants
#

# Use 1101 for 2sec input audio
Tx = 5511 # The number of time steps input to the model from the spectrogram
n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram

# Use 272 for 2sec input audio
Ty = 1375# The number of time steps in the output of our model

chunk_duration = 0.5 # Each read length in seconds from mic.
fs = 44100 # sampling rate for mic
chunk_samples = int(fs * chunk_duration) # Each read length in number of samples.

# Each model input data duration in seconds, need to be an integer numbers of chunk_duration
feed_duration = 10
feed_samples = int(fs * feed_duration)

assert feed_duration/chunk_duration == int(feed_duration/chunk_duration)

# Queue to communiate between the audio callback and main thread
q = Queue()

run = True

silence_threshold = 100

# Run the demo for a timeout seconds
timeout = time.time() + 999999*60  # Basically no timeout. 

# Data buffer for the input wavform
data = np.zeros(feed_samples, dtype='int16')

model = None

# 
# HOTWORD LOGIC
#

def runApplicationServer():
  print("[DEBUG] Initializing kotakeeOS speech application server...")
  global model

  # Load pretrained model
  tf.compat.v1.disable_v2_behavior() # model trained in tf1
  model = tf.compat.v1.keras.models.load_model('./models/tr_model.h5')

  if(model is None):
    print("[ERROR] Unable to load trigger word detection model. Stopping...")
    return
  
  #while stopServer is not True:
  listenForHotWord()
  
  print("\n[DEBUG] Shutting down. Goodnight.")

# When run, listens for a single command and executes
# acceptable ones accordingly. This is the main method that
# is different between this and pocketspinx. 
def listenForHotWord():
  global run, model
  stream = get_audio_input_stream(callback)
  stream.start_stream()

  # For outputting debug message. Only output once
  # after every activation. 
  firstRun = True

  try:
    while run:
      if firstRun:
        print("[DEBUG] Now listening...")
        firstRun = False
      data = q.get()
      spectrum = get_spectrogram(data)
      preds = detect_triggerword_spectrum(spectrum)
      new_trigger = has_new_triggerword(preds, chunk_duration, feed_duration)
      if new_trigger:
        print('1')
        # Plunges code into server logic loop. 
        print("\n[DEBUG] Hotword recognized!")
        # Stop the stream momentarily. 
        stream.stop_stream()
        stream.close()
        listenForCommand()
        # Once the command loop finishes. resume.
        stream = get_audio_input_stream(callback)
        stream.start_stream()
        firstRun = True
  except (KeyboardInterrupt, SystemExit):
    stream.stop_stream()
    stream.close()
    timeout = time.time()
    run = False
        
  stream.stop_stream()
  stream.close()

  return

def callback(in_data, frame_count, time_info, status):
  global run, timeout, data, silence_threshold, model   
  if time.time() > timeout:
    run = False        
  data0 = np.frombuffer(in_data, dtype='int16')
  if np.abs(data0).mean() < silence_threshold:
    print('-', end='')
    return (in_data, pyaudio.paContinue)
  else:
    print('.', end='')
  data = np.append(data,data0)    
  if len(data) > feed_samples:
    data = data[-feed_samples:]
    # Process data async by sending a queue.
    q.put(data)
  return (in_data, pyaudio.paContinue)

"""
Function to predict the location of the trigger word.

Argument:
x -- spectrum of shape (freqs, Tx)
i.e. (Number of frequencies, The number time steps)

Returns:
predictions -- flattened numpy array to shape (number of output time steps)
"""
def detect_triggerword_spectrum(x):
  global model
  # the spectogram outputs  and we want (Tx, freqs) to input into the model
  x  = x.swapaxes(0,1)
  x = np.expand_dims(x, axis=0)
  predictions = model.predict(x)
  return predictions.reshape(-1)

"""
Function to detect new trigger word in the latest chunk of input audio.
It is looking for the rising edge of the predictions data belongs to the
last/latest chunk.

Argument:
predictions -- predicted labels from model
chunk_duration -- time in second of a chunk
feed_duration -- time in second of the input to model
threshold -- threshold for probability above a certain to be considered positive

Returns:
True if new trigger word detected in the latest chunk
"""
def has_new_triggerword(predictions, chunk_duration, feed_duration, threshold=0.5):
  predictions = predictions > threshold
  chunk_predictions_samples = int(len(predictions) * chunk_duration / feed_duration)
  chunk_predictions = predictions[-chunk_predictions_samples:]
  level = chunk_predictions[0]
  for pred in chunk_predictions:
    if pred > level:
      return True
    else:
      level = pred
  return False

"""
Function to compute a spectrogram.

Argument:
predictions -- one channel / dual channel audio data as numpy array

Returns:
pxx -- spectrogram, 2-D array, columns are the periodograms of successive segments.
"""
def get_spectrogram(data):
  nfft = 200 # Length of each window segment
  fs = 8000 # Sampling frequencies
  noverlap = 120 # Overlap between windows
  nchannels = data.ndim
  if nchannels == 1:
      pxx, _, _ = mlab.specgram(data, nfft, fs, noverlap = noverlap)
  elif nchannels == 2:
      pxx, _, _ = mlab.specgram(data[:,0], nfft, fs, noverlap = noverlap)
  return pxx

"""
Function to compute and plot a spectrogram.

Argument:
predictions -- one channel / dual channel audio data as numpy array

Returns:
pxx -- spectrogram, 2-D array, columns are the periodograms of successive segments.
"""
def plt_spectrogram(data):
  nfft = 200 # Length of each window segment
  fs = 8000 # Sampling frequencies
  noverlap = 120 # Overlap between windows
  nchannels = data.ndim
  if nchannels == 1:
      pxx, _, _, _ = plt.specgram(data, nfft, fs, noverlap = noverlap)
  elif nchannels == 2:
      pxx, _, _, _ = plt.specgram(data[:,0], nfft, fs, noverlap = noverlap)
  return pxx

def get_audio_input_stream(callback):
  stream = pyaudio.PyAudio().open(
      format=pyaudio.paInt16,
      channels=1,
      rate=fs,
      input=True,
      frames_per_buffer=chunk_samples,
      input_device_index=0,
      stream_callback=callback)
  return stream

# 
# SERVER LOGIC (Not relevant to Hotword detection)
#

# Uses far more intelligent google API to parse a command. 
def listenForCommand():
  successfulCommand = False

  # When the hotword has been said, kick off a thread
  # to query the server for the latest homeStatus and
  # states. This should be fast enough so that it's always
  # done by the time the user says the command. 
  executeQueryServerThread()

  # Try three times, or until user cancels, or command was
  # executed.
  for i in range(3): 
    try:
      # Specify the microphone as the input source.
      with sr.Microphone() as source2:
        # Wait a moment to allow the recognizer to adjust
        # the energy threshold based on surrounding noise
        # level...
        r2.adjust_for_ambient_noise(source2)
        executeTextThread(hotWordReceiptPrompt)
        time.sleep(0.7) # Try not to detet the prompt. 
        print("[DEBUG] Now Listening for Command...")
        start = time.time()

        # Listen for input
        audio2 = r2.listen(source2)

        # Use Google's API to recognize the audio.
        recognizedText = r2.recognize_google(audio2)

        # String cleanup
        recognizedText = recognizedText.lower()
        end = time.time()

        print("[DEBUG] Recognized command audio: '" + recognizedText + "' in " + str(end-start) + " ")

        # Parse recognized text
        if any(x in recognizedText for x in cancelWords):
          print("[DEBUG] User requested cancellation. Stopping command parsing...")
          break
        else:
          if parseAndExecuteCommand(recognizedText):
            successfulCommand = True
            break

    except sr.RequestError as e:
      print("[ERROR] Could not request results from speech_recognition; {0}.format(e)")
    except sr.UnknownValueError:
      print("[Warning] Last sentence was not understood.")
  
  # Stopping. Let user know big brother google is no longer
  # listening. 
  if successfulCommand is False:
    executeTextThread(cancellationPrompt)

# Non-blocking text to speech. Do be warned this
# might interefere with the speech recognition. 
def executeTextThread(command):
  textThread = threading.Thread(target=speakText, args=(command,), daemon=True).start()
  
# Convert text to speech using pyttsx3 engine.
# Note calling this by itself causes a block
# on the main thread. 
def speakText(command):
  if engine._inLoop:
    engine.endLoop()
  engine.say(command)
  engine.runAndWait()

# Non-blocking query to fill status objects.
def executeQueryServerThread():
  queryActionStatesThread = threading.Thread(target=queryActionStates, daemon=True).start()
  queryHomeStatusThread = threading.Thread(target=queryHomeStatus, daemon=True).start()

# Queries server for states of all modules. 
def queryActionStates():
  global actionStatesLastUpdate
  global actionStates
  query = webServerIpAddress + "/actionStates/" + str(actionStatesLastUpdate)
  print("[DEBUG] Querying server: " + query)
  response = requests.get(query)
  if(response.status_code == 200):
    actionStates = json.loads(response.text)
    actionStatesLastUpdate = actionStates['lastUpdate']
    print("[DEBUG] Action States request received successfully. actionStatesLastUpdate is now: " + str(actionStatesLastUpdate))
    #print(str(actionStates))
  elif(response.status_code != 204):
    print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

# Queries server for misc non-module information
def queryHomeStatus():
  global homeStatusLastUpdate
  global homeStatus
  query = webServerIpAddress + "/homeStatus/" + str(homeStatusLastUpdate)
  print("[DEBUG] Querying server: " + query)
  response = requests.get(query)
  if(response.status_code == 200):
    homeStatus = json.loads(response.text)
    homeStatusLastUpdate = homeStatus['lastUpdate']
    print("[DEBUG] Home Status request received successfully. homeStatusLastUpdate is now: " + str(homeStatusLastUpdate))
    #print(str(homeStatus))
  elif(response.status_code != 204):
    print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

# Given a queried command from the google text recognition
# API, parse and execute accordingly.
def parseAndExecuteCommand(command):
  global stopServer
  global homeStatus
  global actionStates
  # Ex) http://192.168.0.197:8080/moduleToggle/1/50/1
  queries = []

  if ("good night" in command or "freeze all motor functions" in command or "goodnight" in command):
    executeTextThread(stopServerPrompt)
    time.sleep(5) # Enough time to allow the speech prompt to complete. 
    stopServer = True
    return True
  elif("weather" in command or "like outside" in command or "how hot" in command or "how cold" in command):
    if(homeStatus is not None):
      weatherString = "It is currently " + str(int(homeStatus["weatherData"]["main"]["temp"])) + " degrees Fahrenheit, " +str(homeStatus["weatherData"]["weather"][0]["main"]) + ", with a maximum of " + str(int(homeStatus["weatherData"]["main"]["temp_max"])) + " and a minimum of " + str(int(homeStatus["weatherData"]["main"]["temp_min"])) + ". Humidity is " +  str(homeStatus["weatherData"]["main"]["humidity"]) + " percent."
      executeTextThread(weatherString)
      time.sleep(10) # Enough time to allow the speech prompt to complete. 
      return True
  elif("everything" in command):
    if("off" in command):
      queries.append(webServerIpAddress + "/moduleToggle/1/50/0")
      queries.append(webServerIpAddress + "/moduleToggle/2/50/0")
      queries.append(webServerIpAddress + "/moduleToggle/2/250/10")
      queries.append(webServerIpAddress + "/moduleToggle/2/251/10")
      queries.append(webServerIpAddress + "/moduleToggle/2/350/20")
    elif("on" in command):
      queries.append(webServerIpAddress + "/moduleToggle/1/50/1")
      queries.append(webServerIpAddress + "/moduleToggle/2/50/1")
      queries.append(webServerIpAddress + "/moduleToggle/2/250/12")
      queries.append(webServerIpAddress + "/moduleToggle/2/251/12")
      queries.append(webServerIpAddress + "/moduleToggle/2/350/22")
  else:
    if("bedroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/1/50/0") # query off first, because on is in one. 
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/1/50/1")
      else:
        #No on or off specified. Check queried information. 
        if(actionStates is not None):
          if(actionStates["1"]["50"] == 1):
            queries.append(webServerIpAddress + "/moduleToggle/1/50/0")
          else:
            queries.append(webServerIpAddress + "/moduleToggle/1/50/1")

    if("living" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/50/0")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/50/1")
      else:
        #No on or off specified. Check queried information. 
        if(actionStates is not None):
          if(actionStates["2"]["50"] == 1):
            queries.append(webServerIpAddress + "/moduleToggle/2/50/0")
          else:
            queries.append(webServerIpAddress + "/moduleToggle/2/50/1")
    
    if("speaker" in command or "soundbar" in command or ("sound" in command and "bar" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/250/10")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/250/12")
      else:
        #No on or off specified. Check queried information. 
        if(actionStates is not None):
          if(actionStates["2"]["250"] == 12):
            queries.append(webServerIpAddress + "/moduleToggle/2/250/10")
          else:
            queries.append(webServerIpAddress + "/moduleToggle/2/250/12")
    
    if("ceiling" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/251/10")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/251/12")
      else:
        #No on or off specified. Check queried information. 
        if(actionStates is not None):
          if(actionStates["2"]["251"] == 12):
            queries.append(webServerIpAddress + "/moduleToggle/2/251/10")
          else:
            queries.append(webServerIpAddress + "/moduleToggle/2/251/12")

    if("kitchen" in command and ("light" in command or "lights" in command or "lamp" in command)):
      if("off" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/350/20")
      elif("on" in command):
        queries.append(webServerIpAddress + "/moduleToggle/2/350/22")
      else:
        #No on or off specified. Check queried information. 
        if(actionStates is not None):
          if(actionStates["2"]["350"] == 22):
            queries.append(webServerIpAddress + "/moduleToggle/2/350/20")
          else:
            queries.append(webServerIpAddress + "/moduleToggle/2/350/22")

  if len(queries) > 0:
    # We have received a valid command. Query the server. 
    for query in queries:
      print("[DEBUG] Sending query: " + query)
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] Request received successfully.")
      else:
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
    executeTextThread(successfulCommandPrompt)
    return True
  else:
    #executeTextThread(failedCommandPrompt)
    print("[DEBUG] No valid command was received.")
    return False

if __name__ == "__main__":
  runApplicationServer()