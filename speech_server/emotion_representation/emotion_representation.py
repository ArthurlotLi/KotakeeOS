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
import time

class EmotionRepresentation:
  # Relative to speech_speak.py. May pass in an override for this.
  emotion_videos_location = "./emotion_representation/emotion_media"

  # Provide maps from emotion category strings to the actual 
  # Blender 3D Character renders depicting someone expressing
  # that emotion while talking. There are three separate 
  # categories dependent on the time of day (a nice little touch
  # imo)
  #
  # All videos have frame ranges 0 to 120, hence the 0000-0120 
  # suffix. (I couldn't bother to rename the blender outputs.)

  emotion_video_map_sunlight = {
    "joy":"sunlight_joy0000-0120.mp4",
    "sadness":"sunlight_sadness0000-0120.mp4",
    "fear":"sunlight_fear0000-0120.mp4",
    "anger":"sunlight_anger0000-0120.mp4",
    "disgust":"sunlight_disgust0000-0120.mp4",
    "surprise":"sunlight_surprise0000-0120.mp4",
    "neutral":"sunlight_neutral0000-0120.mp4",
  }
  emotion_video_map_nightlight = {
    "joy":"nightlight_joy0000-0120.mp4",
    "sadness":"nightlight_sadness0000-0120.mp4",
    "fear":"nightlight_fear0000-0120.mp4",
    "anger":"nightlight_anger0000-0120.mp4",
    "disgust":"nightlight_disgust0000-0120.mp4",
    "surprise":"nightlight_surprise0000-0120.mp4",
    "neutral":"nightlight_neutral0000-0120.mp4",
  }
  emotion_video_map_sunset = {
    "joy":"sunset_joy0000-0120.mp4",
    "sadness":"sunset_sadness0000-0120.mp4",
    "fear":"sunset_fear0000-0120.mp4",
    "anger":"sunset_anger0000-0120.mp4",
    "disgust":"sunset_disgust0000-0120.mp4",
    "surprise":"sunset_surprise0000-0120.mp4",
    "neutral":"sunset_neutral0000-0120.mp4",
  }

  # Default sunset time and duration. This may be passed into the 
  # emotion function and overridden if the data is queried from
  # sources like the OpenWeatherMapAPI. 
  #
  # A sunset time will be set at the middle of the duration.
  sunset_default_time_hours = 17
  sunset_default_time_minutes = 30
  
  # Same deal for sunrise. 
  sunrise_default_time_hours = 6
  sunrise_default_time_minutes = 0

  sunset_sunrise_duration = 60

  def __init__(self, emotion_videos_location = None):
    if emotion_videos_location is not None:
      self.emotion_videos_location = emotion_videos_location

  # Expects a solution string directly from the output of the
  # emotion detection model (Ex) "joy"). Remember we're using Paul
  # Ekman's Discrete Emotion Model + "neutral".
  def display_emotion_simple(self, emotion_category, sunrise_hours = None, sunrise_minutes = None, sunset_hours = None, sunset_minutes = None, sunset_sunrise_duration= None):
    if emotion_category in self.emotion_video_map_sunlight:

      # Get the video location. 
      video_location = self.derive_video_location(
        emotion_category=emotion_category,  
        sunrise_hours = sunrise_hours, 
        sunrise_minutes = sunrise_minutes, 
        sunset_hours = sunset_hours, 
        sunset_minutes = sunset_minutes,
        sunset_sunrise_duration = sunset_sunrise_duration)

      # For windows, convert all slashes appropriately. OS.startfile
      # is sensitive to to this. 
      operating_system_name = os.name
      if (operating_system_name == "nt"):
        video_location = video_location.replace("/","\\")

      # Play the video. For now let's just use the simple startfile
      # with no way of knowing when it finishes and/or being able
      # to cancel it. TODO: Look into opencv and playing a video
      # frame by frame. We'll want to spawn a separate thread and
      # have that be able to stop given a flag when we're done speaking.
      print("[DEBUG] Emotion Representation playing video located at: " + video_location + ".")
      try:
        if (operating_system_name == "nt"):
          os.startfile(video_location)
        else:
          # Assumed mac. 
          # TODO: Currently FAR TOO MUCH HASSLE to get VLC working
          # on mac, especially considering this is a temporary measure. 
          pass 
      except Exception as e:
        print("[ERROR] Emotion Representation failed to play video! Exception: ")
        print(e)
    else:
      print("[ERROR] Emotion Representation does not support emotion '"+ str(emotion_category) + "'!")
  
  # TODO: Fully implement openCV's video playing using a thread. 
  def start_display_emotion(self, emotion_category):
    if emotion_category in self.emotion_video_map:
      #video_location = self.emotion_video_map[emotion_category]

      #print("[DEBUG] Emotion Representation playing video located at: " + video_location + ".")
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

  # Given the emotion category as well as optionally the sunset
  # and sunrise times for today, return a video correlated to the
  # emotion and current time.
  def derive_video_location(self, emotion_category, sunrise_hours = None, sunrise_minutes = None, sunset_hours = None, sunset_minutes = None, sunset_sunrise_duration = None):
    video_location = None

    # Get the current time relative to daylight/sunset/nightlight
    # in 24 hr format. 
    current_hours = int(time.strftime("%H", time.localtime()))
    current_minutes = int(time.strftime("%M", time.localtime()))

    # Apply defaults if not provided sunset/sunrise information.
    if sunrise_hours is None: sunrise_hours = self.sunrise_default_time_hours
    if sunrise_minutes is None: sunrise_minutes = self.sunrise_default_time_minutes
    if sunset_hours is None: sunset_hours = self.sunset_default_time_hours
    if sunset_minutes is None: sunset_minutes = self.sunset_default_time_minutes
    if sunset_sunrise_duration is None: sunset_sunrise_duration = self.sunset_sunrise_duration

    # Calculate the floors/ceilings for sunset/sunrise.
    sunset_time_ceiling_hours, sunset_time_ceiling_minutes = self.adjust_time_given_duration(
      sunset_hours, sunset_minutes, sunset_sunrise_duration/2)
    sunset_time_floor_hours, sunset_time_floor_minutes = self.adjust_time_given_duration(
      sunset_hours, sunset_minutes, -sunset_sunrise_duration/2)
    sunrise_time_ceiling_hours, sunrise_time_ceiling_minutes = self.adjust_time_given_duration(
      sunrise_hours, sunrise_minutes, sunset_sunrise_duration/2)
    sunrise_time_floor_hours, sunrise_time_floor_minutes = self.adjust_time_given_duration(
      sunrise_hours, sunrise_minutes, -sunset_sunrise_duration/2)

    # For easy calculation, combine hours and minutes. 
    # Ex) 15 32 to 1532. 
    current_time = current_hours*100 + current_minutes
    sunset_ceiling = sunset_time_ceiling_hours*100 + sunset_time_ceiling_minutes
    sunset_floor = sunset_time_floor_hours*100 + sunset_time_floor_minutes
    sunrise_ceiling = sunrise_time_ceiling_hours*100 + sunrise_time_ceiling_minutes
    sunrise_floor = sunrise_time_floor_hours*100 + sunrise_time_floor_minutes

    print("[DEBUG] Emotion Representation - Current: " + str(current_time) + " sunset: " + str(sunset_ceiling) + "/" + str(sunset_floor) + " sunrise: " + str(sunrise_ceiling) + "/" + str(sunrise_floor))

    if current_time < sunset_floor and current_time > sunrise_ceiling:
      # Daylight. 
      print("[DEBUG] Emotion Representation: Current time " + str(current_time) + " falls in daylight.")
      video_location = self.emotion_videos_location + "/" + self.emotion_video_map_sunlight[emotion_category]
    elif current_time > sunset_ceiling or current_time < sunrise_floor:
      # Night time.
      print("[DEBUG] Emotion Representation: Current time " + str(current_time) + " falls in nightlight.")
      video_location = self.emotion_videos_location + "/" + self.emotion_video_map_nightlight[emotion_category]
    else:
      # current time is either sunrise or sunset. 
      print("[DEBUG] Emotion Representation: Current time " + str(current_time) + " falls in sunset/sunrise.")
      video_location = self.emotion_videos_location + "/" + self.emotion_video_map_sunset[emotion_category]
    
    return video_location

  # Helper function - given a duration in minutes, adjust the
  # current minutes accordingly.  We're expecting realistic 
  # sunset/sunrise hours, so no thought is being given to 
  # things like day rollover or whatnot. 
  #
  # Duration can be positive or negative. 
  def adjust_time_given_duration(self, hours, minutes, duration):
    new_minutes = minutes + duration
    new_hours = hours
    if new_minutes > 60:
      # (Use // to get floor-rounded answer.)
      additional_hours = new_minutes//60
      new_minutes = new_minutes%60
      new_hours = new_hours + additional_hours
    elif new_minutes < 0:
      # Negate the minutes (Use // to get floor-rounded answer.)
      removed_hours = abs(new_minutes)//60 + 1
      new_minutes = 60*removed_hours + new_minutes
      new_hours = new_hours - removed_hours
    
    return new_hours, new_minutes

# Debug only.
if __name__ == "__main__":
  emotion_category = "joy"
  emotion_videos_location = "./emotion_media"

  emotion_representation = EmotionRepresentation(emotion_videos_location = emotion_videos_location)
  emotion_representation.display_emotion_simple(emotion_category=emotion_category)