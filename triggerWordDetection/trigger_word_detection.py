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
# Usage Examples: 
# python3 trigger_word_detection.py 25 1  <- Creates dataset of size 10 iter 1
# python3 trigger_word_detection.py -d 0 1 <- -d Specifies not to create a dataset and loads dataset with iter 1. 
#

import matplotlib.pyplot as plt
from scipy.io import wavfile
import os
from pydub import AudioSegment

import argparse

import numpy as np
from pydub import AudioSegment
import random
import sys
import io
import os
import glob
import IPython
from td_utils import * # The file we're using directly from the ref project.

from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.models import Model, load_model, Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout, Input, Masking, TimeDistributed, LSTM, Conv1D
from tensorflow.keras.layers import GRU, Bidirectional, BatchNormalization, Reshape
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers import RMSprop

from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint, TensorBoard

Tx = 5511 # The number of time steps input to the model from the spectrogram
n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
Ty = 1375 # The number of time steps in the output of our model

# Primary function that executes the main steps:
# A) Dataset Processing
#   1. Load the wav files that will make the dataset.
#   2. Dynamically generate the dataset.
# B) Model Processing
#    3. Train the model with the generated dataset.
#    4. Save the model.
#
# Takes in two arguments:
# generateDataset (True/False)
# datasetSize (int) - Will be ignored if generateDataset is False. 
def main(generateDataset, datasetSize, iternum):
  print("[INFO] Initializing main...")
  x = None
  y = None
  x, y = create_dataset(generateDataset, datasetSize, iternum)
  if x is not None and y is not None:
    model = None
    model = train_model(x, y)
    if model is not None:
      result = save_model(model, iternum)
      if result:
        print("[INFO] Program finished successfully! Goodnight...")
      else:
        print("[ERROR] Unable to save the model! Execution failed.")
    else:
      print("[ERROR] model was None! Execution failed.")
  else:
      print("[ERROR] datasets x and/or y was None! Execution failed.")

#
# A) DATASET CREATION AND PROCESSING
#

# 1. Load wav files that will make the dataset
# 2. Dynamically generate the dataset.
# Expects raw data to be in the raw_data folder in subfolders
# named activates, backgrounds, and negatives. 
def create_dataset(generateDataset, datasetSize, iternum):
  print("[INFO] Running create_dataset...")

  # What we output for the model to use. 
  final_x = None
  final_y = None

  # Ask for confirmation, because we might be overwriting stuff.
  promptInput = None
  if generateDataset:
    print("[INFO] Loading raw audio (This may take some time)...")
    # Load audio segments using pydub 
    activates, negatives, backgrounds = load_raw_audio()
    print("[INFO] Raw audio loaded!")

    # To generate our dataset: select a random background and push that
    # into the create_training_example loop. Repeat this for as many times
    # as you'd like. Write all that stuff to a file and you're done? 
    clips_to_generate = datasetSize

    while promptInput is None or (promptInput != "y" and promptInput != "n"):
      promptInput = input("[NOTICE] A new training dataset of size " +str(clips_to_generate)+" will be generated. Continue? (y/n)\n")
      promptInput = promptInput.lower()
    
    if promptInput == "y":
      print("[INFO] Initiating dataset generation...")
      array_x = []
      array_y = []
      for i in range(clips_to_generate):
        print("[DEBUG] Generating clip " + str(i) + "...")
        random_indices = np.random.randint(len(backgrounds), size=1)
        random_background = random_indices[0]
        x, y = create_training_example(backgrounds[random_background], activates, negatives)
        if x.shape == (101, 5511) and y.shape == (1, 1375):
          array_x.append(np.transpose(x, (1, 0)))
          array_y.append(np.transpose(y, (1, 0))) # We want to go from (1, 1375) to (1375, 1)
        else:
          print("[WARNING] Generated x and y of incorrect shapes! Discarding...")
      # A nice little learning moment here for numpy arrays. You can use
      # array() to create a new dimension, while concatenate() and vstack()
      # work on existing dimensions. 
      print("[INFO] Combining all generated x arrays...")
      final_x = np.array(array_x)
      print("[INFO] Combining all generated y arrays...")
      final_y = np.array(array_y)
      
      print("[DEBUG] final_x.shape is:", final_x.shape)  
      print("[DEBUG] final_y.shape is:", final_y.shape)    

      # Save the generated datasets to file. 
      print("[INFO] Saving final_x to file...")
      np.save("./XY_train/X_"+str(iternum)+".npy", final_x)
      print("[INFO] Saving final_y to file...")
      np.save("./XY_train/Y_"+str(iternum)+".npy", final_y)

      print("[INFO] Successfully saved X_"+str(iternum)+".npy and Y_"+str(iternum)+".npy to XY_train folder.")
    else:
      print("[INFO] Skipping dataset generation...")
  else:
    print("[INFO] Skipping dataset generation...")

  if final_x is None and final_y is None:
    print("[INFO] Loading existing dataset file ./XY_train/X_"+str(iternum)+".npy...")
    final_x = np.load("./XY_train/X_"+str(iternum)+".npy")
    print("[INFO] Loading existing dataset file ./XY_train/Y_"+str(iternum)+".npy...")
    final_y = np.load("./XY_train/Y_"+str(iternum)+".npy")
    print("[DEBUG] final_x.shape is:", final_x.shape)  
    print("[DEBUG] final_y.shape is:", final_y.shape) 

  return final_x, final_y

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
  #segment_start = np.random.randint(low=0, high=10000-segment_ms-1000)   # Make sure segment doesn't run past the 10sec background 
  segment_start = np.random.randint(low=0, high=10000-segment_ms) # Maybe this change was causing the model to freak out? 
  segment_end = segment_start + segment_ms - 1
  
  return (segment_start, segment_end)

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
  
  # Select 0-4 random "activate" audio clips from the entire list of "activates" recordings
  number_of_activates = np.random.randint(0, 5)
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

  # Select 0-2 random negatives audio recordings from the entire list of "negatives" recordings
  number_of_negatives = np.random.randint(0, 3)
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

#
# B) MODEL CREATION AND TRAINING
#

# 3. Train the model with the generated model.
def train_model(X, Y):
  print("[INFO] Running train_model...")

  model = define_model(input_shape = (Tx, n_freq))

  model.summary()

  # Tuning parameters that can be tweaked. 
  learning_rate = 0.0001 # A healthy learning rate. 
  loss_function = 'binary_crossentropy'
  epochs = 200 
  batch_size=32 # In general, 32 is a good starting point, then try 64, 128, 256. Smaller but not too small is optimal for accuracy. 
  validation_split = 0.2
  rlr_patience = 5
  rlr_factor = 0.5
  es_patience = 8 # Don't want overfitting!!
  es_min_delta = 1e-10
  verbose = True

  # Compiling the Neural Network with all of this, using RMSprop optimizer, with no callbacks. 
  # This resulted in a model that was overfit at around 98% train accuracy. 
  #opt = RMSprop(learning_rate=learning_rate) # This was suggested on the github issues. 
  #model.compile(optimizer=opt, loss = loss_function, metrics=["accuracy"])
  #history = model.fit(X, Y, shuffle=True, epochs=epochs, validation_split=validation_split, verbose=verbose, batch_size=batch_size)

  # A simplified version.
  # Resulted in a model that was apparently underfit at 93-95 train accuracy trained on 0s. 
  #opt = Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999, decay=0.01) # Let's try it? 
  #model.compile(optimizer=opt, loss = loss_function, metrics=["accuracy"])
  #history = model.fit(X, Y, epochs=epochs, verbose=verbose, batch_size=batch_size)

  # A more complicated version using Adam and various measures against overfitting.
  # Resulted in a model that was apparently underfit at 93-95 train accuracy trained on 0s. 
  #opt = Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999, decay=0.01) I don't know what these mean
  #opt = Adam(learning_rate=learning_rate)
  #opt = Adam(lr=learning_rate, beta_1=0.9, beta_2=0.999, decay=0.01) # Let's try it? 
  # Define early stopping to save time (don't train if nothing's improving.)
  #es = EarlyStopping(monitor='accuracy', min_delta = es_min_delta, patience = es_patience, verbose = verbose)
  # Similarily, start spinning down the learning rate when a plateau has been detected.
  #rlr = ReduceLROnPlateau(monitor='accuracy', factor = rlr_factor, patience = rlr_patience, verbose = verbose)
  # Define checkpointing so that we can revert in time if we end up worse than we were before. 
  #mcp = ModelCheckpoint(filepath='./models/tr_model_weights_'+str(iternum)+'.h5', monitor='accuracy', verbose=1,save_best_only=True, save_weights_only=True)
  #history = model.fit(X, Y, shuffle=True, epochs=epochs, callbacks=[es, rlr, mcp], validation_split=validation_split, verbose=verbose, batch_size=batch_size)

  # And a new training parameter set to address both underfitting and overfitting (I think)
  # 
  # Observations:
  # - Resulted in a model that had 86% DEV set accuracy trained on 1000 samples! Heck yeah! Ran for 343 epochs out of 400. 
  # - Resulted in a homegrown trigger wrod model that had overfit on 1500 samples at exactly 500 epochs out of 500. 
  #opt = RMSprop(learning_rate=learning_rate) # This was suggested on the github issues. 
  #model.compile(optimizer=opt, loss = loss_function, metrics=["accuracy"])
  # Define early stopping to save time (don't train if nothing's improving.)
  #es = EarlyStopping(monitor='accuracy', min_delta = es_min_delta, patience = es_patience, verbose = verbose)
  # Similarily, start spinning down the learning rate when a plateau has been detected.
  #rlr = ReduceLROnPlateau(monitor='accuracy', factor = rlr_factor, patience = rlr_patience, verbose = verbose)
  # Define checkpointing so that we can revert in time if we end up worse than we were before. 
  #mcp = ModelCheckpoint(filepath='./models/tr_model_weights_'+str(iternum)+'.h5', monitor='accuracy', verbose=1,save_best_only=True, save_weights_only=True)
  #history = model.fit(X, Y, shuffle=True, epochs=epochs, callbacks=[mcp], validation_split=validation_split, verbose=verbose, batch_size=batch_size)

  # And yet another one, this one trying to mimic the original model as much as possible.
  #opt = Adam(learning_rate=learning_rate, beta_1=0.9, beta_2=0.999, decay=0.01) # Results in a model that hangs on 87%.
  opt = Adam(learning_rate=learning_rate)
  #opt = RMSprop(learning_rate=learning_rate)
  model.compile(optimizer=opt, loss = loss_function, metrics=["accuracy"])
  mcp = ModelCheckpoint(filepath='./models/tr_model_weights_'+str(iternum)+'.h5', monitor='accuracy', verbose=1,save_best_only=True, save_weights_only=True)
  history = model.fit(X, Y, shuffle=True, epochs=epochs, callbacks=[mcp], validation_split=validation_split, verbose=verbose, batch_size=batch_size)

  best_accuracy = min(history.history['accuracy'])

  print("\nModel training complete. Best accuracy: " + str(best_accuracy))

  try:
    print("[INFO] Loading dev dataset file ./XY_dev/X_dev.npy...")
    X_dev = np.load("./XY_dev/X_dev.npy")
    print("[INFO] Loading existing dataset file ./XY_dev/Y_dev.npy...")
    Y_dev = np.load("./XY_dev/Y_dev.npy")
    print("[DEBUG] X_dev.shape is:", X_dev.shape)  
    print("[DEBUG] Y_dev.shape is:", Y_dev.shape) 

    loss, acc = model.evaluate(X_dev, Y_dev)
    print("[INFO] Dev set accuracy is: ", acc) 
    if(float(acc) <= 0.94 and float(acc) >= 0.90):
      #print("[INFO] ...Unfortunately this one doesn't look too good. The model underfit and likely trained on 0s.")
      print("[INFO] When checked against clips of absolutely no positives, looks okay (should've given us all 0s.)")
  except:
    print("[WARN] Error loading X_dev and/or Y/dev.")

  return model

def define_model(input_shape):
    """
    Function creating the model's graph in Keras.
    
    Argument:
    input_shape -- shape of the model's input data (using Keras conventions)

    Returns:
    model -- Keras model instance
    """
    
    X_input = Input(shape = input_shape)
    
    ### START CODE HERE ###
    
    # Step 1: CONV layer (≈4 lines)
    X = Conv1D(196, kernel_size=15, strides=4)(X_input)                                 # CONV1D
    X = BatchNormalization()(X)                                 # Batch normalization
    X = Activation('relu')(X)                                 # ReLu activation
    X = Dropout(0.8)(X)                                 # dropout (use 0.8).
    # TODO note: changed all dropouts from 0.8 to 0.5

    # Step 2: First GRU Layer (≈4 lines)
    X = GRU(units = 128, return_sequences = True)(X) # GRU (use 128 units and return the sequences)
    X = Dropout(0.8)(X)                                 # dropout (use 0.8)
    X = BatchNormalization()(X)                                 # Batch normalization
    
    # Step 3: Second GRU Layer (≈4 lines)
    X = GRU(units = 128, return_sequences = True)(X)   # GRU (use 128 units and return the sequences)
    X = Dropout(0.8)(X)                                 # dropout (use 0.8)
    X = BatchNormalization()(X)                                  # Batch normalization
    X = Dropout(0.8)(X)                                  # dropout (use 0.8)
    
    # Step 4: Time-distributed dense layer (≈1 line)
    X = TimeDistributed(Dense(1, activation = "sigmoid"))(X) # time distributed  (sigmoid)

    ### END CODE HERE ###

    model = Model(inputs = X_input, outputs = X)
    
    return model 

# 4. Save the model.
#
# Returns true or false depending on execution status. 
def save_model(model, iternum):
  print("[INFO] Running save_model...")

  model.save('./models/tr_model_'+str(iternum)+'.h5')

  print('[INFO] model successfully saved at ./models/tr_model_'+str(iternum)+'.h5.')

  return True


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('datasetSize')
  parser.add_argument('iternum')
  parser.add_argument('-d', action='store_false', default=True)
  parser.add_argument('-g', action='store_true', default=False)
  args = parser.parse_args()

  datasetSize = int(args.datasetSize)
  iternum = int(args.iternum)
  generateDataset = args.d
  stopGpu = args.g

  if(stopGpu is True or stopGpu is None):
    # In case you have a CUDA enabled GPU and don't want to use it. 
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 

  main(generateDataset, datasetSize, iternum)