#
# simple_utilities.py
#
# Module allowing for simple assistant tasks that do not require
# internet connectivity nor the presence of the home automation
# web server. 

import time
from datetime import date

class SimpleUtilites:
  speech_speak = None
  web_server_status = None

  def __init__(self, speech_speak, web_server_status):
    self.speech_speak = speech_speak
    self.web_server_status = web_server_status

  # Standard routine. 
  def parse_command(self, command):
    valid_command = False

    if("time" in command):
      currentTime = time.strftime("%H%M", time.localtime())
      # Separate the time with spaces + periods so the text synthesizer 
      # reads it out digit by digit. 
      separated_time_string = ""
      for character in currentTime:
        separated_time_string = separated_time_string + character + ", "
      timeString = "It is currently " + separated_time_string + "."
      self.speech_speak.speak_text(timeString)
      valid_command = True
    elif("date" in command or "day" in command or "month" in command or "today" in command):
      dateToday = date.today()
      dateString = "Today is "+ time.strftime("%A", time.localtime()) + ", " + time.strftime("%B", time.localtime()) + " " + str(dateToday.day) + ", " + str(dateToday.year)
      self.speech_speak.speak_text(dateString)
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
        self.speech_speak.speak_text(str(first_term) + " " + operator + " " + str(second_term) + " equals {:.2f}.".format(solution)) 
        valid_command = True
    
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