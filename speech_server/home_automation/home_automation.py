#
# home_automation.py
#
# All interactions related to the manipulation or querying of the
# KotakeeOS home automation web server. 

class HomeAutomation:

  speech_speak = None
  web_server_status = None

  def __init__(self, speech_speak, web_server_status):
    self.speech_speak = speech_speak
    self.web_server_status = web_server_status
