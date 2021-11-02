#
# hotwordPocketSphinx.py
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
# Usage: python3 hotwordTriggerWord.py 1 <- Uses iteration number 1 in the triggerWordDetection/models directory.
#

from commandParsing import CommandParser

import argparse

# Hotword logic imports
import numpy as np
import time
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

models_path = '../triggerWordDetection/models'

model = None
commandParser = CommandParser()

def runApplicationServer(iternum, useAlt, raspberryPi):
  print("[DEBUG] Initializing kotakeeOS speech application server with Trigger Word model iteration number " + str(iternum) + ".")

  global model

  # Load pretrained model
  if(int(iternum) <= 0):
    # If we're using 0 or less, we're using the pretrained model.
    # If so, we need to adjust becuase it was trained in tf1 and
    # we're using tf2. 
    tf.compat.v1.disable_v2_behavior()
    model = tf.compat.v1.keras.models.load_model(models_path + '/tr_model_'+str(iternum) +'.h5')
  else:
    # Load our model. 
    model = load_model(models_path + '/tr_model_'+str(iternum) +'.h5')

  if(model is None):
    print('[ERROR] Unable to load trigger word detection model. Path: '+models_path +'/tr_model_'+str(iternum) +'.h5. Stopping...')
    return
  
  # Experimental - query the server to turn on the LED to signal
  # Speech server is online. 
  if useAlt:
    commandParser.querySpeechServerLED(1, 2, 51)
  else:
    commandParser.querySpeechServerLED(1, 2, 52)
  commandParser.startupProcedureCustom("KotakeeOS Speech Server initialized. Machine learning model iteration " + str(iternum) + ".")
  
  #while stopServer is not True:
  listenForHotWord(raspberryPi)

  # Experimental - query the server to turn on the LED to signal
  # Speech server is no longer online. 
  if useAlt:
    commandParser.querySpeechServerLED(0, 2, 51)
  else:
    commandParser.querySpeechServerLED(0, 2, 52)
  print("Shutting down. Goodnight.")
  
  print("\n[DEBUG] Shutting down. Goodnight.")

# When run, listens for a single command and executes
# acceptable ones accordingly. This is the main method that
# is different between this and pocketspinx. 
def listenForHotWord(raspberryPi = False):
  global run, model
  stream = get_audio_input_stream(callback, raspberryPi)
  stream.start_stream()

  # For outputting debug message. Only output once
  # after every activation. 
  firstRun = True

  try:
    while run and commandParser.stopServer is False:
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
        commandParser.listenForCommand()
        # Once the command loop finishes. resume.
        if raspberryPi:
          # The raspberry pi is too slow and crashes if this block is not
          # present. 
          time.sleep(5)
        stream = get_audio_input_stream(callback, raspberryPi)
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

def get_audio_input_stream(callback, raspberryPi=False):
  input_device_index = 0
  if raspberryPi:
    input_device_index = 1

  stream = pyaudio.PyAudio().open(
      format=pyaudio.paInt16,
      channels=1,
      rate=fs,
      input=True,
      frames_per_buffer=chunk_samples,
      input_device_index=input_device_index,
      stream_callback=callback)
  return stream

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  parser.add_argument('-a', action='store_true', default=False) # TODO: maybe make this scalable to more than one server. 
  parser.add_argument('-r', action='store_true', default=False) 
  args = parser.parse_args()
  useAlt = args.a
  raspberryPi = args.r

  if(useAlt is True or useAlt is None):
    useAlt = True
  else:
    useAlt = False

  iternum = int(args.iternum)

  runApplicationServer(iternum, useAlt, raspberryPi)