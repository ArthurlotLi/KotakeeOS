#
# interaction_active.py
#
# Handling of command parsing given a recognized keyword, providing 
# harmonized functionality of abstracted active modules.
#
# Expects interaction_active.json specifying directories of 
# primary module classes. 

from os import sep
import time
from datetime import date

class InteractionActive:
  # Flag to shut down the entire speech server. 
  stop_server = False

  # Constants that may be configured.
  cancel_words = ["stop", "cancel", "go away", "quit", "no thanks", "sleep"] # stops query.
  stop_server_commands = ["goodnight", "good night", "freeze all motor functions", "turn yourself off", "shutdown", "deactivate"]
  stop_server_prompt = "Understood. Shutting down."
  command_split_keywords = ["break", "brake"]
  successful_command_prompt = "" # By default, don't say anything and just activate something. 

  speech_speak = None
  speech_listen = None
  web_server_status = None

  def __init__(self, speech_speak, speech_listen, web_server_status):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status

  # Key method executing level one user interactions. 
  def listen_for_command(self):
    print("[INFO] Interaction Active initializing user command level 1 routine.")

    # Spawn a thread to run in the background querying the server for
    # it's status in advance of the command. 
    self.web_server_status.execute_query_server_thread()

    user_command = self.speech_listen.listen_response(execute_chime=True, indicate_led=True)

    # Abort if any key cancel words are present in registered text. 
    if any(x in user_command for x in self.cancel_words):
      print("[DEBUG] User requested cancellation. Stopping command parsing...")
      return

    self.parse_command(user_command)

  # Given a command, trickle down the list of active modules and test
  # to see if any of them activate. 
  def parse_command(self, full_command):
    confirmation_prompt = self.successful_command_prompt
    valid_command = False

    if any(x in full_command for x in self.stop_server_commands):
      self.speech_speak.speak_text(self.stop_server_prompt)
      self.stop_server = True
      return True

    # Multi-command parsing. Break the command phrase in two
    # given the array of keywords.
    commands = [full_command]
    for keyword in self.command_split_keywords:
      new_commands = []
      for i in range(0, len(commands)):
        split_commands = commands[i].split(keyword)
        for group in split_commands:
          new_commands.append(group)
      commands = new_commands

    # Parse command chronologically.
    for command in commands:
      # TODO: ACTIVE MODULE PARSING! 
      queries = []
      if("weather" in command or "like outside" in command or "how hot" in command or "how cold" in command):
        if(self.web_server_status.home_status is not None):
          weatherString = "It is currently " + str(int(self.web_server_status.home_status["weatherData"]["main"]["temp"])) + " degrees Fahrenheit, " +str(self.web_server_status.home_status["weatherData"]["weather"][0]["description"]) + ", with a maximum of " + str(int(self.web_server_status.home_status["weatherData"]["main"]["temp_max"])) + " and a minimum of " + str(int(self.web_server_status.home_status["weatherData"]["main"]["temp_min"])) + ". Humidity is " +  str(self.web_server_status.home_status["weatherData"]["main"]["humidity"]) + " percent."
          self.speech_speak.speak_text(weatherString)
          valid_command = True
      elif("everything" in command or "all modules" in command):
        if(self.web_server_status.action_states is not None):
          if("off" in command or "on" in command):
            # Manage prompt. 
            promptOnOff = "on"
            toState = 1
            if("off" in command):
              promptOnOff = "off"
              toState = 0
            confirmation_prompt = "Turning everything " + promptOnOff + "."
            queries.append(self.web_server_status.web_server_ip_address + "/moduleToggleAll/" + str(toState))
      elif("thermostat" in command):
        if(self.web_server_status.home_status is not None and self.web_server_status.home_status["moduleInput"] is not None and self.web_server_status.home_status["moduleInput"]['2'] is not None):
          if(self.web_server_status.home_status["moduleInput"]['2']['5251'] is not None and self.web_server_status.home_status["moduleInput"]['2']['5251']["offHeat"] is not None and self.web_server_status.home_status["moduleInput"]['2']['5251']["onHeat"] is not None):
            onHeat = self.web_server_status.home_status["moduleInput"]['2']['5251']["onHeat"]
            offHeat = self.web_server_status.home_status["moduleInput"]['2']['5251']["offHeat"]
            newTemp = self.text2int(command)
            print("[DEBUG] Parsed number " + str(newTemp) + " from thermostat request.")
            if(newTemp > 30 and newTemp < 100):
              onHeat = newTemp+1
              offHeat = onHeat-2
              newHomeStatus = self.web_server_status.home_status["moduleInput"]['2']
              newHomeStatus['5251']["onHeat"] = onHeat
              newHomeStatus['5251']["offHeat"] = offHeat
              data_to_send = {
                "roomId": 2,
                "newModuleInput": newHomeStatus
              }
              self.web_server_status.generate_and_execute_post_query(data_to_send)

              self.speech_speak.speak_text("Setting thermostat to " + str(newTemp) + ".")
              valid_command = True
      elif("temperature" in command):
        # Handle temperatures. Expects a state like "27.70_42.20".
        lr_2_state = self.web_server_status.action_states["2"]["5251"].split("_")
        br_state = self.web_server_status.action_states["1"]["5250"].split("_")
        # Convert to Farenheit. 
        lr_2_temp = str(round(((float(lr_2_state[0]) * 9) / 5) + 32))
        br_temp = str(round(((float(br_state[0]) * 9) / 5) + 32))

        # Operational server status
        statusString = "The Living Room is currently " + lr_2_temp + " degrees. The Bedroom is currently " + br_temp + " degrees."
        self.speech_speak.speak_text(statusString)
        valid_command = True
      elif(("auto" in command or "input" in command or "automatic" in command) and ("off" in command or "on" in command or "enable" in command or "disable" in command)):
        if(self.web_server_status.home_status is not None and self.web_server_status.home_status["moduleInputDisabled"] is not None):
          newState = "true"
          if("activate" in command or "turn on" in command or "enable" in command):
            newState = "false"
          queries.append(self.web_server_status.web_server_ip_address + "/moduleInputDisabled/" + newState)
          # Manage prompt. 
          if(newState == "false"):
            confirmation_prompt = "Enabling automatic server actions."
          else:
            confirmation_prompt = "Disabling automatic server actions."
      elif("server" in command and ("off" in command or "on" in command or "enable" in command or "disable" in command)):
        if(self.web_server_status.home_status is not None and self.web_server_status.home_status["serverDisabled"] is not None):
          newState = "true"
          if("activate" in command or "turn on" in command or "enable" in command):
            newState = "false"
          queries.append(self.web_server_status.web_server_ip_address + "/serverDisabled/" + newState)
          # Manage prompt. 
          if(newState == "false"):
            confirmation_prompt = "Enabling central server operations."
          else:
            confirmation_prompt = "Disabling central server operations."
      elif("status" in command and ("home" in command or "system" in command or "server" in command)):
        if(self.web_server_status.home_status is not None and self.web_server_status.action_states is not None):
          # Report all information. 
          serverDisabled = "enabled"
          if(self.web_server_status.home_status["serverDisabled"] == "true" or self.web_server_status.home_status['serverDisabled'] == True):
            serverDisabled = "disabled"
          moduleInputDisabled = "enabled"
          if(self.web_server_status.home_status["moduleInputDisabled"] == "true" or self.web_server_status.home_status['moduleInputDisabled'] == True):
            moduleInputDisabled = "disabled"
          onHeat = int(self.web_server_status.home_status["moduleInput"]['2']['5251']["onHeat"])

          # Handle temperatures. Expects a state like "27.70_42.20".
          lr_2_state = self.web_server_status.action_states["2"]["5251"].split("_")
          br_state = self.web_server_status.action_states["1"]["5250"].split("_")
          # Convert to Farenheit. 
          lr_2_temp = str(round(((float(lr_2_state[0]) * 9) / 5) + 32))
          br_temp = str(round(((float(br_state[0]) * 9) / 5) + 32))

          # Operational server status
          statusString = "KotakeeOS is currently " + serverDisabled + " with automatic actions " + moduleInputDisabled + ". There are " + str(self.web_server_status.home_status["modulesCount"]) + " connected modules. The thermostat is currently set to " + str(onHeat - 1) + " degrees."
          # Action states status
          statusString = statusString + " The Living Room is currently " + lr_2_temp + " degrees. The Bedroom is currently " + br_temp + " degrees."
          self.speech_speak.speak_text(statusString)
          valid_command = True
      elif("time" in command or "clock" in command):
        currentTime = time.strftime("%H%M", time.localtime())
        # Separate the time with spaces + periods so the text synthesizer 
        # reads it out digit by digit. 
        separated_time_string = ""
        for character in currentTime:
          separated_time_string = separated_time_string + character + ". "
        timeString = "It is currently " + separated_time_string
        self.speech_speak.speak_text(timeString)
        valid_command = True
      elif("date" in command or "day" in command or "month" in command or "today" in command):
        dateToday = date.today()
        dateString = "Today is "+ time.strftime("%A", time.localtime()) + ", " + time.strftime("%B", time.localtime()) + " " + str(dateToday.day) + ", " + str(dateToday.year)
        self.speech_speak.speak_text(dateString)
        valid_command = True
        """
      elif("question" in command):
        # If we asked for advanced output or "8 ball", our output should be
        # different.
        output_type = 0
        if("advanced" in command or "detailed" in command): output_type = 1
        elif("eight ball" in command or "8-ball" in command or "8 ball" in command): output_type = 2
        # Initialize if it's not running. Only do this once and keep it up
        # afterwards because the quest_ai_parser takes a while to get running. 
        if(self.quest_ai_parser is None):
          self.speech_speak.speak_text("Initializing Quest AI... please wait.")
          self.quest_ai_parser = QuestAiParsing(recognizer = self.r2, engine = self.engine, pause_threshold = self.pauseThreshold)
        self.quest_ai_parser.standard_query(output_type = output_type, online_functionality=self.web_server_status.action_states is not None)
        valid_command = True
        """
      elif("calculator" in command or "calculate" in command):
        # Get the first number and then the second number in the query. Ignore
        # all others if there are any. Fail if there are not enough numbers.
        # Fail if there is not a specifying operator. 
        first_term = None
        second_term = None
        operator = None # Term used in final message as well. 
        negative_term = False
        for word in command.split():
          # Test as an operator.
          if operator is None:
            if word == "add" or word == "plus" or word == "+":
              operator = "plus"
              continue
            elif word == "subtract" or word == "minus" or word == "-":
              operator = "minus"
              continue
            elif word == "multiply" or word == "times" or word == "*" or word == "x":
              operator = "times"
              continue
            elif word == "divide" or word == "divided" or word == "/":
              operator = "divided by"
              continue
          # Test as a number or a "negative" term.
          if first_term is None or second_term is None:
            if word == "negative":
              negative_term = True
            else:
              # Parse as a number. 
              possible_term = self.text2int(word)
              if possible_term != 0:
                if negative_term is True:
                  possible_term = -possible_term
                  negative_term = False
                if first_term is None:
                  first_term = possible_term
                else:
                  second_term = possible_term
                
        # We've now theoretically gotten everything.
        if first_term is not None and second_term is not None and operator is not None:
          solution = None
          if operator == "plus":
            solution = first_term + second_term
          elif operator == "minus":
            solution = first_term - second_term
          elif operator == "times":
            solution = first_term * second_term
          else:
            solution = first_term / second_term
          self.speech_speak.speak_text(str(first_term) + " " + operator + " " + str(second_term) + " equals {:.2f}.".format(solution)) 
          valid_command = True
      else:
        if("bedroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
          queries.append(self.web_server_status.generate_query(command, 1, 50, 1, 0))
        if("living" in command and ("light" in command or "lights" in command or "lamp" in command)):
          queries.append(self.web_server_status.generate_query(command, 2, 50, 1, 0))
        if("speaker" in command or "soundbar" in command or ("sound" in command and "bar" in command)):
          queries.append(self.web_server_status.generate_query(command, 2, 250, 12, 10))
        if("ceiling" in command and ("light" in command or "lights" in command or "lamp" in command)):
          queries.append(self.web_server_status.generate_query(command, 2, 251, 12, 10))
        if("kitchen" in command and ("light" in command or "lights" in command or "lamp" in command)):
          queries.append(self.web_server_status.generate_query(command, 2, 350, 22, 20))
        if("bathroom" in command and ("light" in command or "lights" in command or "lamp" in command)):
          queries.append(self.web_server_status.generate_query(command, 3, 350, 22, 20))
        if("bathroom" in command and ("fan" in command or "vent")):
          queries.append(self.web_server_status.generate_query(command, 3, 351, 22, 20))
        if("bathroom" in command and ("led" in command or "night" in command)):
          queries.append(self.web_server_status.generate_query(command, 3, 50, 1, 0))
        if("printer" in command):
          queries.append(self.web_server_status.generate_query(command, 2, 252, 12, 10))
        if("bedroom" in command and ("night" in command or "red led" in command or "red leds" in command)):
          queries.append(self.web_server_status.generate_query(command, 1, 1000, 108, 100))
        if("living" in command and ("night" in command or "red led" in command or "red leds" in command)):
          queries.append(self.web_server_status.generate_query(command, 2, 1000, 108, 100))
        if("bedroom" in command and ("led" in command or "party" in command or "rgb" in command)):
          queries.append(self.web_server_status.generate_query(command, 1, 1000, 107, 100))
        if("living" in command and ("led" in command or "party" in command or "rgb" in command)):
          queries.append(self.web_server_status.generate_query(command, 2, 1000, 107, 100))

      if len(queries) > 0:
        # We have received at least one valid command. Query the server. 
        for query in queries:
          self.web_server_status.execute_get_query(query)

        if(confirmation_prompt is not None and confirmation_prompt != ""):
          self.speech_speak.speak_text(confirmation_prompt)
        valid_command = True

    if valid_command != True:
      print("[DEBUG] No valid command was received.")
    return valid_command

  # Helper function I got off stack overflow - really sweet code!
  # Slightly modified to allow non-number characters. 
  # https://stackoverflow.com/questions/493174/is-there-a-way-to-convert-number-words-to-integers
  def text2int(self, textnum, numwords={}):
    if not numwords:
      units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
      ]

      tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

      scales = ["hundred", "thousand", "million", "billion", "trillion"]

      numwords["and"] = (1, 0)
      for idx, word in enumerate(units):    numwords[word] = (1, idx)
      for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
      for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

    current = result = 0
    for word in textnum.split():
        if word not in numwords:
          print("[DEBUG] text2int parsing invalid word: " + str(word))
          if self.intTryParse(word) is True:
            return int(word)
          continue
          #raise Exception("Illegal word: " + word)

        scale, increment = numwords[word]
        current = current * scale + increment
        if scale > 100:
            result += current
            current = 0

    return result + current
    
  # Dunno why this isn't standard. 
  def intTryParse(self, value):
    try:
      int(value)
      return True
    except ValueError:
      return False