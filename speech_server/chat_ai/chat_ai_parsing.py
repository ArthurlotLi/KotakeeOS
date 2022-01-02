#
# chat_ai_parsing.py
#
# Handles user interactions with the chat_ai class - active module
# utilized by interaction_active. 

from chat_ai import ChatAi

class ChatAiParsing:
  speech_speak = None
  speech_listen = None

  chat_ai = None

  def __init__(self, speech_speak, speech_listen):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen

    # Initialize ChatAI.
    self.chat_ai = ChatAi()

  # Level 1 standard routine. 
  def parse_command(self, command):
    valid_command = False

    #TODO.

    return valid_command