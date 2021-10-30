#
# generate_dev_set.py
#
# Given recordings present in raw_data_kotakee_dev, generate
# X_dev_kotakee_#.npy accordingly. 
#
# Note the solution numpy arrays Y_dev_kotakee_#.npy, aka the
# labels, must be manually defined and created here. 
#
# NOTE that audacity outputs by default with metadata that 
# python's wavfile does not like. Suggest you make sure to 
# clear the wav file's metadata for each clip. 

import os
import numpy as np
from td_utils import * # The file we're using directly from the ref project.
from trigger_word_detection import TriggerWordDetection

class GenerateDevSet:
  # Constants
  Tx = 5511 # The number of time steps input to the model from the spectrogram
  n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
  Ty = 1375 # The number of time steps in the output of our model

  dev_recordings_location = "./raw_data_kotakee_dev"
  dev_output_location = "./XY_dev_kotakee"
  dev_x_name = "X_dev_kotakee.npy"
  dev_y_name = "Y_dev_kotakee.npy"

  # Small test function to refer to the dev sets given to us. 
  def check_ref_dev(self):
    original_X = "./XY_dev/X_dev.npy"
    original_Y = "./XY_dev/Y_dev.npy"
    X = np.load(original_X)
    Y = np.load(original_Y)
    print("Original X: ")
    print(X.shape)
    #print(X)
    print("Original Y: ")
    print(Y.shape)
    print(Y)

  # Given the recordings provided in the dev_recordings_location,
  # automatically generate the X dev set npy array. Simple. Use
  # the same functions as the proper model procedure.
  #
  # Expects a dictionary of arrays, with the keys being the
  # filename and the values being arrays of timesteps (can
  # be empty) where a trigger word was just said.
  def generate_XY(self, timesteps):
    print("[INFO] Generating X and Y values for dev recordings...")

    trigger_word_detection = TriggerWordDetection()

    totalFiles = 0
    array_x = []
    array_y = []
    for filename in os.listdir(self.dev_recordings_location):
        #if filename.endswith("wav"):
        if filename.endswith("01.wav"): # TODO: Testing. 
            # Process x by reading in file. 
            x = graph_spectrogram(self.dev_recordings_location + "/"+filename)
            if x.shape == (101, 5511):
              array_x.append(np.transpose(x, (1, 0)))
            else:
              print("[WARNING] File "+filename+" had an X array of incorrect shape!")
              return

            # Process y by generating array from provided timestep entry. 
            if(filename not in timesteps):
              print("[ERROR] No corresponding timestep entry for filename " + filename + "was found!")
              return

            # We are given the ms. Need to convert to ts. (x = 0.1375t) where
            # t is in milliseconds and x is the resulting timestep. 
            num_activates = 0 # For debug info only. 
            activates_string = "" # For debug info only. 

            # Initialize y (label vector) of zeros (≈ 1 line).
            y = np.zeros((1, self.Ty))

            for timestep in timesteps[filename]:
              y = trigger_word_detection.insert_ones(y, segment_end_ms=timestep)

              # Debug information
              num_activates = num_activates + 1
              segment_end_y = int(timestep * self.Ty / 10000.0)
              activates_string = activates_string + str(timestep) + "(" + str(segment_end_y) + ") "

            if y.shape == (1, 1375):
              array_y.append(np.transpose(y, (1, 0))) # We want to go from (1, 1375) to (1375, 1)
            else:
              print("[WARNING] File "+filename+" was provided a Y array of incorrect shape!")
              return

            totalFiles = totalFiles + 1
            print("[INFO] Processed WAV file " + str(totalFiles) + " " + self.dev_recordings_location + "/"+filename + ".")
            print("       " + str(num_activates) + " trigger words added with timesteps: " + activates_string)

    print("[INFO] Combining all generated x arrays...")
    final_x = np.array(array_x)
    print("[INFO] Combining all generated y arrays...")
    final_y = np.array(array_y)

    print("[DEBUG] final_x.shape is:", final_x.shape)  
    print("[DEBUG] final_y.shape is:", final_y.shape)

    print("[INFO] Saving final_x to file...")
    np.save(self.dev_output_location + "/" + self.dev_x_name, final_x) 
    print("[INFO] Saving final_y to file...")
    np.save(self.dev_output_location + "/" + self.dev_y_name, final_y) 

    print("[INFO] Complete! Goodnight...")

if __name__ == "__main__":
  generate_dev_set = GenerateDevSet()
  generate_dev_set.check_ref_dev()

  # To determine the timestep of a given ms, multiply it
  # by 10,000ms/1375ts to get the ts. Provide the ms of 
  # the activation time via this timesteps dictionary and
  # the program will convert it automatically. 
  timesteps = {
    "raw_data_kotakee_dev-01.wav": [4601, 9848],
    "raw_data_kotakee_dev-02.wav": [],
    "raw_data_kotakee_dev-03.wav": [],
    "raw_data_kotakee_dev-04.wav": [],
    "raw_data_kotakee_dev-05.wav": [],
    "raw_data_kotakee_dev-06.wav": [],
    "raw_data_kotakee_dev-07.wav": [],
    "raw_data_kotakee_dev-08.wav": [],
    "raw_data_kotakee_dev-09.wav": [],
    "raw_data_kotakee_dev-10.wav": [],
    "raw_data_kotakee_dev-11.wav": [],
    "raw_data_kotakee_dev-12.wav": [],
    "raw_data_kotakee_dev-13.wav": [],
    "raw_data_kotakee_dev-14.wav": [],
    "raw_data_kotakee_dev-15.wav": [],
    "raw_data_kotakee_dev-16.wav": [],
    "raw_data_kotakee_dev-17.wav": [],
    "raw_data_kotakee_dev-18.wav": [],
    "raw_data_kotakee_dev-19.wav": [],
    "raw_data_kotakee_dev-20.wav": [],
    "raw_data_kotakee_dev-21.wav": [],
    "raw_data_kotakee_dev-22.wav": [],
    "raw_data_kotakee_dev-23.wav": [],
    "raw_data_kotakee_dev-24.wav": [],
    "raw_data_kotakee_dev-25.wav": [],
    "raw_data_kotakee_dev-26.wav": [],
    "raw_data_kotakee_dev-27.wav": [],
    "raw_data_kotakee_dev-28.wav": [],
    "raw_data_kotakee_dev-29.wav": [],
    "raw_data_kotakee_dev-30.wav": [],
    "raw_data_kotakee_dev-31.wav": [],
    "raw_data_kotakee_dev-32.wav": [],
    "raw_data_kotakee_dev-33.wav": [],
    "raw_data_kotakee_dev-34.wav": [],
    "raw_data_kotakee_dev-35.wav": [],
    "raw_data_kotakee_dev-36.wav": [],
    "raw_data_kotakee_dev-37.wav": [],
    "raw_data_kotakee_dev-38.wav": [],
    "raw_data_kotakee_dev-39.wav": [],
    "raw_data_kotakee_dev-40.wav": [],
    "raw_data_kotakee_dev-41.wav": [],
    "raw_data_kotakee_dev-42.wav": [],
    "raw_data_kotakee_dev-43.wav": [],
    "raw_data_kotakee_dev-44.wav": [],
    "raw_data_kotakee_dev-45.wav": [],
    "raw_data_kotakee_dev-46.wav": [],
    "raw_data_kotakee_dev-47.wav": [],

  }

  generate_dev_set.generate_XY(timesteps)