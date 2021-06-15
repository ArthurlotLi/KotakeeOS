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
#
# Usage: python3 trigger_word_detection.py
#

def executeModel():
  pass


if __name__ == "__main__":
  executeModel()