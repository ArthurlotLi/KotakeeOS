#
# simple_utilities.py
#
# Module allowing for simple assistant tasks that do not require
# internet connectivity nor the presence of the home automation
# web server. 

import time
from datetime import date

class SimpleUtilities:
  # Paths relative to where interaction_active is. 
  timer_class_location = "./simple_utilities/timer_utility/timer_utility.TimerUtility"

  speech_speak = None
  speech_listen = None
  web_server_status = None
  interaction_passive = None

  user_confirmation_words = ["sure", "yep", "go ahead", "okay", "yeah", "affirm", "that's it", "ok", "yes", "go for it"]

  def __init__(self, speech_speak, speech_listen, web_server_status, interaction_passive):
    self.speech_speak = speech_speak
    self.speech_listen = speech_listen
    self.web_server_status = web_server_status
    self.interaction_passive = interaction_passive

  # Level 1 standard routine.
  def parse_command(self, command):
    valid_command = False

    # Check timer first, then time (because timer has time in it)
    if("timer" in command):
      valid_command = True

      duration, duration_seconds, units = self.parse_duration_from_command(command)
      if duration is not None and units is not None:
        # Level 2 subroutine for confirming the parsed information. 
        user_prompt = "Confirm set timer for " + str(duration) + " " + str(units) + "?"
        user_response = self.speech_listen.listen_response(prompt=user_prompt, execute_chime = False)

        if user_response is not None and any(x in user_response for x in self.user_confirmation_words):
          # Timer module will add the TimerUtility passive module to the 
          # passive_thrd routine with a first_event time equivalent to the
          # specified time. 
          current_ticks = self.interaction_passive.passive_thrd_ticks_since_start
          first_event_time = current_ticks + (float(duration_seconds)/self.interaction_passive.passive_thrd_tick) # Append seconds. 
          print("[DEBUG] Setting timer for " + str(duration_seconds) + " seconds. Passive ticks: " + str(current_ticks) + ". Targeted ticks: " + str(first_event_time) + ".")
 
          # Create a new passive module given the path to this folder.
          self.interaction_passive.create_module_passive(
            class_location = self.timer_class_location,
            first_event = first_event_time)

          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="Timer set for " + str(duration) + " " + str(units) + ".")

    elif("time" in command):
      currentTime = time.strftime("%H%M", time.localtime())
      # Separate the time with spaces + periods so the text synthesizer 
      # reads it out digit by digit. 
      separated_time_string = ""
      for character in currentTime:
        separated_time_string = separated_time_string + character + ", "
      timeString = "It is currently " + separated_time_string + "."
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=timeString)
      valid_command = True

    elif("date" in command or "day" in command or "month" in command or "today" in command):
      dateToday = date.today()
      dateString = "Today is "+ time.strftime("%A", time.localtime()) + ", " + time.strftime("%B", time.localtime()) + " " + str(dateToday.day) + ", " + str(dateToday.year)
      self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=dateString)
      valid_command = True

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
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content=str(first_term) + " " + operator + " " + str(second_term) + " equals {:.2f}.".format(solution)) 
        valid_command = True
    
    return valid_command

  # Given a command, parse a duration in seconds. This can be a rather
  # painful non-trivial task. Return a tuple of 
  # (duration, duration in seconds, units string). Returns a none tuple otherwise.
  def parse_duration_from_command(self, command):
    units = "seconds"
    duration = self.text2int(command)
    if duration is not None and int(duration) > 0:
      # TODO: For now we only support a single denomination
      # Ex) 50 minutes, 120 minutes, 1 hour, etc. We don't
      # yet support multiple, Ex) 1 minute, 20 seconds. 
      if "minutes" in command:
        units = "minutes"
        duration_seconds = duration * 60
      elif "hours" in command:
        units = "hours"
        duration_seconds = duration * 3600
      else:
        # Otherwise we assume the units are seconds. 
        duration_seconds = duration

      return duration, duration_seconds, units

    return None, None

    
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