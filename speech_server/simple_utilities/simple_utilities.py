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
  timer_confirmation_threshold = 1800 # Amount of time required to ask for confirmation of new timer.
  timer_ids = [] # Note this may contain stale data - need to check each id, asking if they exist first.  

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

    # Check timer first, then time (because timer has time in it).
    # List timers command lists all timers and then asks the user
    # if they want to clear all timers. 
    if("list timers" in command or "list all timers" in command 
    or "all timers" in command or "delete timers" in command 
    or "clear timers" in command or "clear all timers" in command 
    or "delete all timers" in command):
      timer_list_prompt = ""
      # List all active timers. Ask the user if they want to delete
      # any afterwards. 
      for i in range(len(self.timer_ids)-1,-1,-1):
        # Check if it exists. If not, delete it. 
        timer_module = self.interaction_passive.get_module_by_id(self.timer_ids[i])
        if timer_module is None:
          del self.timer_ids[i]
        else:
          timer_list_prompt = timer_list_prompt + " " + str(timer_module.additional_data["timer_duration"]) + " " + str(timer_module.additional_data["timer_units"]) + ", "
      
      if timer_list_prompt == "":
        self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="There are currently no active timers.")
      else:
        # List all timers and ask if they want to clear all timers. 
        # Singular vs plural.
        num_timers = len(self.timer_ids)
        timer_list_prompt = timer_list_prompt + ". Would you like to clear all timers?"  
        if num_timers == 1:
          timer_list_prompt = "There one active timer. It's duration is: " + timer_list_prompt
        else:  
          timer_list_prompt = "There are " + str(num_timers) + " active timers. Their durations are: " + timer_list_prompt
        user_response = self.speech_listen.listen_response(prompt=timer_list_prompt, execute_chime = True)

        if user_response is not None and any(x in user_response for x in self.user_confirmation_words):
          # Got confirmation. Delete all timers. 
          for timer_id in self.timer_ids:
            self.interaction_passive.clear_module_by_id(timer_id)
          self.speech_speak.blocking_speak_event(event_type="speak_text", event_content="All timers have now been deleted.")

    elif("timer" in command):
      valid_command = True

      duration, duration_seconds, units = self.parse_duration_from_command(command)
      if duration is not None and units is not None:
        # Level 2 subroutine for confirming the parsed information. 
        # Only activated if threshold is exceeded (don't sweat it 
        # for timers that are short.)
        user_response_requied = False
        user_response = None
        if int(duration_seconds) > self.timer_confirmation_threshold:
          user_response_requied = True
          user_prompt = "Confirm set timer for " + str(duration) + " " + str(units) + "?"
          user_response = self.speech_listen.listen_response(prompt=user_prompt, execute_chime = True)

        if user_response_requied is False or (user_response is not None and any(x in user_response for x in self.user_confirmation_words)):
          # Timer module will add the TimerUtility passive module to the 
          # passive_thrd routine with a first_event time equivalent to the
          # specified time. 
          current_ticks = self.interaction_passive.passive_thrd_ticks_since_start
          first_event_time = current_ticks + (float(duration_seconds)/self.interaction_passive.passive_thrd_tick) # Append seconds. 
          print("[DEBUG] Setting timer for " + str(duration_seconds) + " seconds. Passive ticks: " + str(current_ticks) + ". Targeted ticks: " + str(first_event_time) + ".")
          timer_additional_data = { "timer_duration" : duration, "timer_seconds":duration_seconds, "timer_units": units }

          # Create a timer that we can add to our list of known timers. 
          # Later on if asked, we can ping interaction_passive with the
          # id to retrive the additional data dict and report it's info.
          # Before it's triggered, naturally. 
          timer_id = "simple_utilities_timer_" + str(first_event_time)
          self.timer_ids.append(timer_id)
 
          # Create a new passive module given the path to this folder.
          self.interaction_passive.create_module_passive(
            class_location = self.timer_class_location,
            first_event = first_event_time,
            additional_data=timer_additional_data,
            id = timer_id)

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
      if "minutes" in command or "minute" in command:
        if duration > 1: 
          units = "minutes"
        else:
          units = "minute"
        duration_seconds = duration * 60
      elif "hours" in command or "hour" in command:
        if duration > 1:
          units = "hours"
        else:
          units = "hour"
        duration_seconds = duration * 3600
      else:
        # Otherwise we assume the units are seconds. 
        duration_seconds = duration
        if duration == 1:
          units = "second" # Not that I'd know why a 1 second timer would be useful. 


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