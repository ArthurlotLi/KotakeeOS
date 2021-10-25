# Small utility program to run a specified model iteration
# against dev set to see accuracy. 

# TODO: I imported everythign because I"m lazy. Please remove unecessary imports later. 
#import matplotlib.pyplot as plt
#from scipy.io import wavfile
import os
#from pydub import AudioSegment

import argparse

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model

def test_model(iternum, use_checkpointed_model):
  models_path = './models'
  model_path = None

  if(use_checkpointed_model):
    model_path = models_path + '/tr_model_weights_'+str(iternum) +'.h5'
  else:
    model_path = models_path + '/tr_model_'+str(iternum) +'.h5'

  # Load pretrained model
  if(int(iternum) <= 0):
    # If we're using 0 or less, we're using the pretrained model.
    # If so, we need to adjust becuase it was trained in tf1 and
    # we're using tf2. 
    tf.compat.v1.disable_v2_behavior()
    model = tf.compat.v1.keras.models.load_model(model_path)
  else:
    # Load our model. 
    model = load_model(model_path)

  if(model is None):
    print('[ERROR] Unable to load trigger word detection model. Path: '+models_path +'/tr_model_'+str(iternum) +'.h5. Stopping...')
    return
  
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

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  parser.add_argument('-c', action='store_true', default=False)
  args = parser.parse_args()

  iternum = int(args.iternum)
  use_checkpointed_model = args.c

  test_model(iternum, use_checkpointed_model)