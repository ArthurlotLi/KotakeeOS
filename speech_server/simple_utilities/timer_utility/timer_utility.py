#
# timer_utility.py
#
# Passive module dynamically added by active module SimpleUtilties
# upon user command. When the event happens, play a jingle and 
# announce that the timer has completed. Simple.

class TimerUtility:
  speech_speak = None

  # When initializing from a thread, be warned that arguments
  # come through as tuples (Ex) speech_speak = (speech_speak.SpeechSpeak,))
  def __init__(self, speech_speak):
    self.speech_speak = speech_speak[0]

  # Standard routine triggered when the event time is triggered
  # by the passive interaction thread. 
  def activate_event(self):
    print("[INFO] Timer event triggered. Executing timer and text.")
    self.speech_speak.execute_timer()
    self.speech_speak.speak_text("Timer finished.")
    print("[DEBUG] Timer event complete.")