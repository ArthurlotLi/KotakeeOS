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

import numpy as np
from pydub import AudioSegment
import random
import sys
import io
import os
import glob
import IPython
from td_utils import * # The file we're using directly from the ref project.

Tx = 5511 # The number of time steps input to the model from the spectrogram
n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
Ty = 1375 # The number of time steps in the output of our model

# Primary function that executes the main steps:
# 1. Load the wav files that will make the dataset.
# 2. Dynamically generate the dataset.
# 3. Train the model with the generated dataset.
# 3. Save the model.
def main():
  print("[DEBUG] Initializing main...")
  dataset = None
  dataset = create_dataset()
  if dataset is not None:
    model = None
    model = train_model(dataset)
    if model is not None:
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

  # Load audio segments using pydub 
  activates, negatives, backgrounds = load_raw_audio()

  # Examples of the loaded raw audio. 
  print("backgrounds len: " + str(len(backgrounds[0])))    # Should be 10,000, since it is a 10 sec clip
  print("activates[0] len: " + str(len(activates[0])))     # Maybe around 1000, since an "activate" audio clip is usually around 1 sec (but varies a lot)
  print("activates[1] len: " + str(len(activates[1])))     # Different "activate" clips can have different lengths 
  print("negatives[0] len: " + str(len(negatives[0])))
  print("negatives[1] len: " + str(len(negatives[1])))

  # Demonstration of is_overlapping
  #overlap1 = is_overlapping((950, 1430), [(2000, 2550), (260, 949)])
  #overlap2 = is_overlapping((2305, 2950), [(824, 1532), (1900, 2305), (3424, 3656)])
  #print("Overlap 1 = ", overlap1)
  #print("Overlap 2 = ", overlap2)

  # Demonstration of insert_audio_clip (will generate insert_test.wav).
  #np.random.seed(5)
  #audio_clip, segment_time = insert_audio_clip(backgrounds[0], activates[0], [(3790, 4400)])
  #audio_clip.export("insert_test.wav", format="wav")
  #print("Segment Time: ", segment_time)
  #IPython.display.Audio("insert_test.wav")

  # Demonstration of insert_ones
  #arr1 = insert_ones(np.zeros((1, Ty)), 9700)
  #plt.plot(insert_ones(arr1, 4251)[0,:])
  #plt.show()
  #print("sanity checks:", arr1[0][1333], arr1[0][634], arr1[0][635])

  # Demonstration of create_training_example. (will generate train.wav).
  #x, y = create_training_example(backgrounds[0], activates, negatives)
  #print("y.shape is:", y.shape)

  # This was just to plot/figure out what y[0] was. It plotted
  # weird (like a spectrograph for some reason) but can be
  # confirmed to be a list of 0s and 1s. 
  #plt.plot(y[0])
  # print out what y[0] is (labels))
  #np.set_printoptions(threshold=sys.maxsize)
  #print(y[0])
  #f = open("train.txt", "w")
  #f.write(str(y[0]))
  #f.close()
  #plt.show()

  # To generate our dataset: select a random background and push that
  # into the create_training_example loop. Repeat this for as many times
  # as you'd like. Write all that stuff to a file and you're done? 
  clips_to_generate = 10
  final_x = None
  final_y = None
  array_x = []
  array_y = []
  for i in range(clips_to_generate):
    random_indices = np.random.randint(len(backgrounds), size=1)
    random_background = random_indices[0]
    x, y = create_training_example(backgrounds[random_background], activates, negatives)
    array_x.append(x)
    array_y.append(y)
  # A nice little learning moment here for numpy arrays. You can use
  # array() to create a new dimension, while concatenate() and vstack()
  # work on existing dimensions. 
  final_x = np.array(array_x)
  final_y = np.array(array_y)
  
  print("final_x.shape is:", final_x.shape)  
  print("final_y.shape is:", final_y.shape)    

  # Save the generated datasets to file. 
  np.save("./XY_train/X.npy", final_x)
  np.save("./XY_train/Y.npy", final_y)

  print("[DEBUG]Successfully saved final_x and final_y to XY_train folder.")

  return

def get_random_time_segment(segment_ms):
  """
  Gets a random time segment of duration segment_ms in a 10,000 ms audio clip.
  
  Arguments:
  segment_ms -- the duration of the audio clip in ms ("ms" stands for "milliseconds")
  
  Returns:
  segment_time -- a tuple of (segment_start, segment_end) in ms
  """
  
  # TODO: Here I just randomly threw in 1000 so as to make sure that, if
  # a positive is inserted into the latest possible moment, there will
  # still be silence left over to fill with positive labels. 
  segment_start = np.random.randint(low=0, high=10000-segment_ms-1000)   # Make sure segment doesn't run past the 10sec background 
  segment_end = segment_start + segment_ms - 1
  
  return (segment_start, segment_end)

# GRADED FUNCTION: is_overlapping

def is_overlapping(segment_time, previous_segments):
  """
  Checks if the time of a segment overlaps with the times of existing segments.
  
  Arguments:
  segment_time -- a tuple of (segment_start, segment_end) for the new segment
  previous_segments -- a list of tuples of (segment_start, segment_end) for the existing segments
  
  Returns:
  True if the time segment overlaps with any of the existing segments, False otherwise
  """
  
  segment_start, segment_end = segment_time
  
  ### START CODE HERE ### (≈ 4 line)
  # Step 1: Initialize overlap as a "False" flag. (≈ 1 line)
  overlap = False
  
  # Step 2: loop over the previous_segments start and end times.
  # Compare start/end times and set the flag to True if there is an overlap (≈ 3 lines)
  for previous_start, previous_end in previous_segments:
      if segment_start <= previous_end and segment_end >= previous_start:
          overlap = True
  ### END CODE HERE ###

  return overlap

# GRADED FUNCTION: insert_audio_clip

def insert_audio_clip(background, audio_clip, previous_segments):
  """
  Insert a new audio segment over the background noise at a random time step, ensuring that the 
  audio segment does not overlap with existing segments.
  
  Arguments:
  background -- a 10 second background audio recording.  
  audio_clip -- the audio clip to be inserted/overlaid. 
  previous_segments -- times where audio segments have already been placed
  
  Returns:
  new_background -- the updated background audio
  """
  
  # Get the duration of the audio clip in ms
  segment_ms = len(audio_clip)
  
  ### START CODE HERE ### 
  # Step 1: Use one of the helper functions to pick a random time segment onto which to insert 
  # the new audio clip. (≈ 1 line)
  segment_time = get_random_time_segment(segment_ms)
  
  # Step 2: Check if the new segment_time overlaps with one of the previous_segments. If so, keep 
  # picking new segment_time at random until it doesn't overlap. (≈ 2 lines)
  numTries = 0
  while is_overlapping(segment_time, previous_segments):
      if numTries > 100:
        print("[WARNING] insert_audio_clip failed to insert a segment!")
        # Return existing background and no segment time - we failed. 
        return background, None
      segment_time = get_random_time_segment(segment_ms)
      numTries = numTries + 1


  # Step 3: Add the new segment_time to the list of previous_segments (≈ 1 line)
  previous_segments.append(segment_time)
  ### END CODE HERE ###
  
  # Step 4: Superpose audio segment and background
  new_background = background.overlay(audio_clip, position = segment_time[0])
  
  return new_background, segment_time

# GRADED FUNCTION: insert_ones

def insert_ones(y, segment_end_ms):
  """
  Update the label vector y. The labels of the 50 output steps strictly after the end of the segment 
  should be set to 1. By strictly we mean that the label of segment_end_y should be 0 while, the
  50 followinf labels should be ones.
  
  
  Arguments:
  y -- numpy array of shape (1, Ty), the labels of the training example
  segment_end_ms -- the end time of the segment in ms
  
  Returns:
  y -- updated labels
  """
  
  # duration of the background (in terms of spectrogram time-steps)
  segment_end_y = int(segment_end_ms * Ty / 10000.0)
  
  # Add 1 to the correct index in the background label (y)
  ### START CODE HERE ### (≈ 3 lines)
  for i in range(segment_end_y + 1, segment_end_y + 51):
      if i < Ty:
          y[0, i] = 1
  ### END CODE HERE ###
  
  return y

# GRADED FUNCTION: create_training_example

def create_training_example(background, activates, negatives):
  """
  Creates a training example with a given background, activates, and negatives.
  
  Arguments:
  background -- a 10 second background audio recording
  activates -- a list of audio segments of the word "activate"
  negatives -- a list of audio segments of random words that are not "activate"
  
  Returns:
  x -- the spectrogram of the training example
  y -- the label at each time step of the spectrogram
  """
  
  # Set the random seed
  #np.random.seed(18)
  
  # Make background quieter
  background = background - 20

  ### START CODE HERE ###
  # Step 1: Initialize y (label vector) of zeros (≈ 1 line)
  y = np.zeros((1, Ty))

  # Step 2: Initialize segment times as empty list (≈ 1 line)
  previous_segments = []
  ### END CODE HERE ###
  
  # Select 0-3 random "activate" audio clips from the entire list of "activates" recordings
  number_of_activates = np.random.randint(0, 4)
  print("[DEBUG] Attempting to insert", number_of_activates, "activates.")
  random_indices = np.random.randint(len(activates), size=number_of_activates)
  random_activates = [activates[i] for i in random_indices]
  
  ### START CODE HERE ### (≈ 3 lines)
  # Step 3: Loop over randomly selected "activate" clips and insert in background
  for random_activate in random_activates:
      # Insert the audio clip on the background
      background, segment_time = insert_audio_clip(background, random_activate, previous_segments)
      # Handle the case where we simply could not insert another audio clip. 
      if(segment_time is not None):
        # Retrieve segment_start and segment_end from segment_time
        segment_start, segment_end = segment_time
        # Insert labels in "y"
        y = insert_ones(y, segment_end_ms=segment_end)
  ### END CODE HERE ###

  # Select 0-3 random negatives audio recordings from the entire list of "negatives" recordings
  number_of_negatives = np.random.randint(0, 4)
  random_indices = np.random.randint(len(negatives), size=number_of_negatives)
  random_negatives = [negatives[i] for i in random_indices]
  print("[DEBUG] Attempting to insert", number_of_negatives, "negatives.")

  ### START CODE HERE ### (≈ 2 lines)
  # Step 4: Loop over randomly selected negative clips and insert in background
  for random_negative in random_negatives:
      # Insert the audio clip on the background 
      background, _ = insert_audio_clip(background, random_negative, previous_segments)
  ### END CODE HERE ###
  
  # Standardize the volume of the audio clip 
  background = match_target_amplitude(background, -20.0)

  # Export new training example 
  file_handle = background.export("train" + ".wav", format="wav")
  #print("File (train.wav) was saved in your directory.")
  
  # Get and plot spectrogram of the new recording (background with superposition of positive and negatives)
  x = graph_spectrogram("train.wav")
  
  return x, y

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