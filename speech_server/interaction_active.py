#
# interaction_active.py
#
# Handling of command parsing given a recognized keyword, providing 
# harmonized functionality of abstracted active modules.
#
# Expects interaction_active.json specifying directories of 
# primary module classes. 

class InteractionActive:
  # Flag to shut down the entire speech server. 
  stop_server = False

  # Constants that may be configured.
  cancel_words = ["stop", "cancel", "go away", "quit", "no thanks", "sleep"] # stops query.
  stop_server_commands = ["goodnight", "good night", "freeze all motor functions", "turn yourself off", "shutdown", "deactivate"]
  command_split_keywords = ["break", "brake"]

  speech_speak = None
  speech_listen = None

  def __init__(self, speech_speak, speech_listen):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen

  # Key method executing level one user interactions. 
  def listen_for_command(self):
    print("[INFO] Interaction Active initializing level one user command routine.")
    user_command = self.speech_listen.listen_response(execute_chime=True)

    # Abort if any key cancel words are present in registered text. 
    if any(x in user_command for x in self.cancel_words):
      print("[DEBUG] User requested cancellation. Stopping command parsing...")
      return

    self.parse_command(user_command)

  # Given a command, trickle down the list of active modules and test
  # to see if any of them activate. 
  def parse_command(self, full_command):
    # TODO
    print("GOT HERE! Full command is: " + full_command)
    pass