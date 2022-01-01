#
# alarm_utility.py
#
# Passive module dynamically added by active module SimpleUtilties
# upon user command. When the event happens, play a jingle and 
# announce that the alarm has rung. Interact with the user
# and ask for a snooze or cancel. If no response is heard, a 
# snooze will be assumed, until the maximum number of snoozes
# have been reached.
# 
# If we are connected to the web server (optional, detected via 
# static object), trigger specific lights to turn on. Remember 
# which lights were on so we can keep them on and turn the rest
# off when the user completes interaction.
#
# Because waking up requires drastic measures, like blasting your
# irises with all your house lights. 

class AlarmUtility:
  pass