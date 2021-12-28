#
# module_active.py
#
# Harmonizing class for all active modules. Provides a layer of 
# abstraction between component modules and the calling class
# interaction_active. Utilizes standardized json files specifying
# the way the module should be handled. 
#
# The ultimate goal of this architecture is to eliminate necessary
# changes to the core components of the speech server when adding
# new capaabilities - only the supporting .json file specifying
# what modules are supported called "interaction_active.json".
#
# Emphasis on graceful failure - the core components should 
# continue to run in the event of a lower level module exception. 
# Error messages should allow for ease of debugging during future
# development. 

import json
import sys

class ModuleActive:
  # Indicates successful initialization. If at any point an exception
  # is encountered, this flag should prevent the calling class from 
  # utilizing this module anymore.
  valid_module = False

  module_active_json_filename = "module_active.json"

  # We expect all active module json files to provide these properties
  # with the exact same names. 
  require_online = None
  require_web_server = None
  dispose_timeout = None
  init_on_startup = None

  require_speech_speak = None
  require_speech_listen = None
  require_web_server_status = None

  # Variants derived from the class_location string provided on init. 
  class_location = None
  class_name = None
  module_location = None
  module_folder_location = None

  # Central class. We expect this class to have standard methods 
  # allowing us to interface with interaction_active from here.
  module_class = None
  module_class_instance = None

  # Expects json from module_active.json in the subject directory.
  # If the json is malformatted, fails gracefully and keeps 
  # valid flag as false so the corrupted module is not used. 
  #
  # Expects input parameter class_location as a local path, for example,
  # "./home_automation/home_automation/HomeAutomation"
  # (folder/filename/ClassName). This specified class should be
  # the one designed to interface with interaction_active. 
  #
  # Also expects the 3 static handlers for speak, listen, and web
  # server status. If they are not necessary, they will not be used. 
  def __init__(self, class_location, speech_speak, speech_listen, web_server_status):
    module_json = None

    self.class_location = class_location

    # Convert into a file path. Drop the class in the path to 
    # get the folder. Load the module_active.json file.
    try:
      split_class_path = self.class_location.rsplit(".", 1)
      self.module_location = split_class_path[0] 
      self.class_name = split_class_path[1]
      self.module_folder_location = self.module_location.rsplit("/", 1)[0]
    except:
      print("[ERROR] module_active was provided an invalid class string: '" + str(self.class_location) + "'.")
      return

    # Attempt to load the class. 
    self.module_class = self.load_class(self.module_location, self.class_name)

    if self.module_class is None:
      print("[ERROR] Was unable to load class: '" + str(self.class_location) + "'.")
      return

    module_json_file_location = self.module_folder_location + "/" + self.module_active_json_filename
    #module_json_file_location = module_json_file_location.replace(".","/")
    try:
      module_json_file = open(module_json_file_location)
      module_json = json.load(module_json_file)
    except:
      print("[ERROR] Unable to load module_json from: '" + str(module_json_file_location) + "'.")
      return

    # Extract module qualities from the module_active.json file. 
    # Convert types accordingly. 
    try:
      self.require_online = module_json["require_online"] == 'True'
      self.require_web_server = module_json["require_web_server"] == 'True'
      self.dispose_timeout = int(module_json["dispose_timeout"])
      self.init_on_startup = module_json["init_on_startup"] == 'True'

      self.require_speech_speak = module_json["require_speech_speak"] == 'True'
      self.require_speech_listen = module_json["require_speech_listen"] == 'True'
      self.require_web_server_status = module_json["require_web_server_status"] == 'True'
    except:
      print("[ERROR] Unacceptable module_json present in class location '" + str(self.class_location) + "'.")
      return

    # Initialize the class. Provide arguments necessary according
    # to the json file. Unfortunately rather clumsy, but for the 
    # sake of all possibilities we'll handle all 8 cases of the 3
    # binary conditions. 
    try:
      if(self.require_speech_speak is True and
         self.require_speech_listen is True and
         self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          speech_speak=speech_speak, 
          speech_listen=speech_listen,
          web_server_status=web_server_status)
      elif(self.require_speech_speak is False and
           self.require_speech_listen is True and
           self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          speech_listen=speech_listen, 
          web_server_status=web_server_status)
      elif(self.require_speech_speak is True and
           self.require_speech_listen is False and
           self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          speech_speak=speech_speak, 
          web_server_status=web_server_status)
      elif(self.require_speech_speak is True and
           self.require_speech_listen is True and
           self.require_web_server_status is False):
         self.module_class_instance = self.module_class(
          speech_speak=speech_speak, 
          speech_listen=speech_listen)
      elif(self.require_speech_speak is False and
           self.require_speech_listen is False and
           self.require_web_server_status is True):
         self.module_class_instance = self.module_class(
          web_server_status=web_server_status)
      elif(self.require_speech_speak is True and
           self.require_speech_listen is False and
           self.require_web_server_status is False):
         self.module_class_instance = self.module_class(
          speech_speak=speech_speak)
      elif(self.require_speech_speak is False and
           self.require_speech_listen is True and
           self.require_web_server_status is False):
         self.module_class_instance = self.module_class(
          speech_listen=speech_listen)
      else:
         self.module_class_instance = self.module_class()
    except:
      print("[ERROR] Unable to load class " + str(self.class_name) + " from '" + str(self.class_location) + "'.")
      return

    self.valid_module = True
    print("[DEBUG] Successfully loaded class " + str(self.class_name) + " from '" + str(self.class_location) + "'.")
      
  # Dynamic class import. Changes sys.path to navigate directories. 
  # Expects module_name Ex) ./home_automation/home_automation
  # and class_name Ex) HomeAutomation
  def load_class(self,  module_name, class_name):
    module = None
    imported_class = None
    module_file_name = None

    # Ex) ./home_automation - split by last slash. 
    # Don't bother if the original file is not within a subdirectory.
    split_module_name = module_name.rsplit("/", 1)
    module_folder_path = split_module_name[0]
    if(module_folder_path != "." and len(split_module_name) > 1):
      sys.path.append(module_folder_path)
      module_file_name = split_module_name[1]
    else:
      module_file_name = module_name.replace("./", "")

    # Fetch the module first.
    try:
      module = __import__(module_file_name)
    except:
      print("[ERROR] Failed to import module " + module_file_name + " from subdirectory '" + module_folder_path + "'.")
      return None

    # Return the class. 
    try:
      imported_class = getattr(module, class_name)
    except:
      print("[ERROR] Failed to import class_name " + class_name + ".")
      return None

    return imported_class