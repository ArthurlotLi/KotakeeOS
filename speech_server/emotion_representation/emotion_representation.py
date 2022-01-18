#
# emotion_representation.py
#
# A companion project to Emotion Detection AI - given an emotion
# category, display a visual simulation of the corresponding 
# emotion. 
#
# Intended to be integrated in with Kotakee Speech Server's 
# Speech Speak so that every time any text is provided to the
# user, an emotion is provided with it in the form of one of 
# the videos we'll play from here. 
#
# A pretty silly way to use a legitimately useful model. 

import os

class EmotionRepresentation:
  emotion_videos_location = "./emotion_media"
  emotion_video_map = {
    "joy":emotion_videos_location + "/joy.mp4",
    "sadness":emotion_videos_location + "/sadness.mp4",
    "fear":emotion_videos_location + "/fear.mp4",
    "anger":emotion_videos_location + "/anger.mp4",
    "disgust":emotion_videos_location + "/disgust.mp4",
    "surprise":emotion_videos_location + "/surprise.mp4",
    "neutral":emotion_videos_location + "/neutral.mp4",
  }

  def __init__(self):
    pass

  # Expects a solution string directly from the output of the
  # emotion detection model (Ex) "joy"). Remember we're using Paul
  # Ekman's Discrete Emotion Model + "neutral".
  def display_emotion_simple(self, emotion_category):
    if emotion_category in self.emotion_video_map:
      video_location = self.emotion_video_map[emotion_category]

      # Play the video. For now let's just use the simple startfile
      # with no way of knowing when it finishes and/or being able
      # to cancel it. TODO: Look into opencv and playing a video
      # frame by frame. We'll want to spawn a separate thread and
      # have that be able to stop given a flag when we're done speaking.
      print("[DEBUG] Emotion Representation playing video located at: " + video_location + ".")
      try:
        os.startfile(video_location)
      except Exception as e:
        print("[ERROR] Emotion Representation failed to play video! Exception: ")
        print(e)
    else:
      print("[ERROR] Emotion Representation does not support emotion '"+ str(emotion_category) + "'!")
  
  # TODO: Fully implement openCV's video playing using a thread. 
  def start_display_emotion(self, emotion_category):
    if emotion_category in self.emotion_video_map:
      video_location = self.emotion_video_map[emotion_category]

      print("[DEBUG] Emotion Representation playing video located at: " + video_location + ".")
      try:
        # If we're currently display an emotion, replace the emotion.
        # TODO
        # https://www.geeksforgeeks.org/python-play-a-video-using-opencv/
        pass
      except Exception as e:
        print("[ERROR] Emotion Representation failed to play video! Exception: ")
        print(e)
    else:
      print("[ERROR] Emotion Representation does not support emotion '"+ str(emotion_category) + "'!")
  
  # Stops the thread immediately - we've stopped speaking.
  def stop_display_emotion(self):
    # TODO: If we're currently displaying an emotion, stop the thread
    # entirely.
    pass