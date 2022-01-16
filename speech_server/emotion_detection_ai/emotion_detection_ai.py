#
# emotion_detection_ai.py
#
# "Production" utilization of generated emotion detection models.
# Utilizes models saved in the local "model" folder to predict
# an emotion category given an input text. 
#
# This implementation is based upon the Paul Ekman Discrete Emotion
# Model (DEM) of human emotion with 6 categories, alongside an
# additional "neutral" category. Together, the 7 possible solutions
# for the model are:
#  - Joy
#  - Sadness
#  - Fear
#  - Anger
#  - Disgust
#  - Surprise
#  - Neutral

class EmotionDetectionAi:
  
  # Upon initialization, attempt to load the model specified.
  def __init__(self, model_iternum):
    pass

  # Execute predictions given a string. Returns the solution string
  # itself (Ex) "joy")
  def predict_emotion(self, text):
    return "neutral"