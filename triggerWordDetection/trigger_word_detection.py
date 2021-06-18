#
# trigger_word_detection.py
#
# Keras deep learning model designed to detect a specific
# tigger word in a live audio stream. Model is designed to
# take in a 10 second spectrograph and output predictions
# of which timesteps immediately floow a trigger word. 
# This model is then adapted for use with a live audio
# stream by feeding model 10 second audio clips with
# differences of 0.5 second steps. 
#
# Reference code is below.
#
# Initial code and model concept from:
# https://www.dlology.com/blog/how-to-do-real-time-trigger-word-detection-with-keras/
# https://github.com/Tony607/Keras-Trigger-Word 
#
# Usage: python3 trigger_word_detection.py
#

import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
from pydub import AudioSegment

# Primary function that executes the main steps:
# 1. Load the wav files that will make the dataset.
# 2. Dynamically generate the dataset.
# 3. Train the model with the generated dataset.
# 4. Make test predictions with the created model. 
# 5. Save the model.
def main():
  print("[DEBUG] Initializing main...")
  dataset = None
  dataset = create_dataset()
  if dataset is not None:
    model = None
    model = train_model(dataset)
    if model is not None:
      execute_model(model)
      save_model(model)
    else:
      print("[ERROR] model was None! Execution failed.")
  else:
      print("[ERROR] dataset was None! Execution failed.")


# 1. Load wav files that will make the dataset
# 2. Dynamically generate the dataset.
# Expects raw data to be in the raw_data folder in subfolders
# named activates, backgrounds, and negatives. 
def create_dataset():
  print("[DEBUG] Running create_dataset...")

  # Let's load the data! Recall our raw data that will be used
  # to generate the dataset will consist of three categories:
  # activations (the word), negatives (misses), and backgrounds.
  activates = []
  backgrounds = []
  negatives = []

  for filename in os.listdir("./raw_data/activates"):
    if filename.endswith("wav"):
      print("[DEBUG] Adding activates file " + filename + ".")
      activate = AudioSegment.from_wav("./raw_data/activates/"+filename)
      activates.append(activate)
  for filename in os.listdir("./raw_data/backgrounds"):
    if filename.endswith("wav"):
      print("[DEBUG] Adding background file " + filename + ".")
      background = AudioSegment.from_wav("./raw_data/backgrounds/"+filename)
      backgrounds.append(background)
  for filename in os.listdir("./raw_data/negatives"):
    if filename.endswith("wav"):
      print("[DEBUG] Adding negatives file " + filename + ".")
      negative = AudioSegment.from_wav("./raw_data/negatives/"+filename)
      negatives.append(negative)

  if(len(activates) > 0 and len(backgrounds) > 0 and len(negatives) > 0):
    return
  else:
    print("[ERROR] Did not find data samples for activates, backgrounds, and negatives!")
    return

# Helper utilities for dataset creation.

# Loading a wav file's rate and data separately.
def get_wav_info(wav_file):
  rate, data = wavfile.read(wav_file)
  return rate, data

# Calculating and plotting a wav file's spectrogram.
def graph_spectrogram(wav_file):
  rate, data = get_wav_info(wav_file)
  nfft = 200 # Length of each window segment
  fs = 8000 # sampling frequencies
  noverlap = 120 # Overlap between windows
  # We only want one channel, so if it's dual channel grab the first one.
  # pyplot.specgram returns spectrum (2D array), freqs (array), t (array), 
  # and im (image). We only want the spectrum data. 
  nchannels = data.ndim
  if nchannels == 1:
    pxx, freqs, bins, im = plt.specgram(data, nfft, fs, noverlap = noverlap)
  elif nchannels ==2:
    pxx, freqs, bins, im = plt.specgram(data[:,0], nfft, fs, noverlap = noverlap)
  return pxx

# Standardizing the volume of an audio clip so it's
# most usable for us. Requires the data and the
# target decibel frequency.
def match_target_amplitude(sound, target_dBFS):
  change_in_dBFS = target_dBFS - sound.dBFS
  return sound.apply_gain(change_in_dBFS)

# 3. Train the model with the generated model.
def train_model(dataset):
  print("[DEBUG] Running train_model...")
  pass

# 4. Make test predictions with the brand new model.
def execute_model(model):
  print("[DEBUG] Running execute_model...")
  pass

# 5. Save the model.
def save_model(model):
  print("[DEBUG] Running save_model...")
  pass


if __name__ == "__main__":
  main()