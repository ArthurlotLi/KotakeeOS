#
# web_server_status.py
#
# Implements interfacing with the KotakeeOS central home automation
# web server. A single static class should be utilized for all 
# speech_server interactions.

import threading
import requests
import json

class WebServerStatus:
  web_server_ip_address = None

  action_states = None
  home_status = None
  action_states_last_update = 0
  home_status_last_update = 0

  def __init__(self, ip_address):
    self.web_server_ip_address = ip_address

  # Non-blocking query to fill status objects.
  def execute_query_server_thread(self):
    query_action_states_thread = threading.Thread(target=self.query_action_states, daemon=True).start()
    query_home_status_thread = threading.Thread(target=self.query_home_status, daemon=True).start()

  # Queries server for states of all modules. 
  def query_action_states(self):
    query = self.web_server_ip_address + "/actionStates/" + str(self.action_states_last_update)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        self.action_states = json.loads(response.text)
        self.action_states_last_update = self.action_states['lastUpdate']
        print("[DEBUG] Action States request received successfully. action_states_last_update is now: " + str(self.action_states_last_update))
        #print(str(action_states))
      elif(response.status_code != 204):
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] query_action_states unable to connect to server.")

  # Queries server for misc non-module information
  def query_home_status(self):
    query = self.web_server_ip_address + "/homeStatus/" + str(self.home_status_last_update)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        self.home_status = json.loads(response.text)
        self.home_status_last_update = self.home_status['lastUpdate']
        print("[DEBUG] Home Status request received successfully. home_status_last_update is now: " + str(self.home_status_last_update))
        #print(str(home_status))
      elif(response.status_code != 204):
        print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] query_home_status unable to connect to server.")

  # Experimental - queries server to turn speech server signal light on/off. 
  def query_speech_server_led(self, toState, roomId, actionId):
    query = self.web_server_ip_address + "/moduleToggle/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] query_speech_server_led request received successfully.")
      elif(response.status_code != 204):
        print("[WARNING] Server rejected query_speech_server_led request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] query_speech_server_led unable to connect to server.")

  # Experimental - queries server providing input. 
  def query_speech_server_input(self, toState, roomId, actionId):
    query = self.web_server_ip_address + "/moduleInput/"+str(roomId)+"/"+str(actionId)+"/" + str(toState)
    print("[DEBUG] Querying server: " + query)
    try:
      response = requests.get(query)
      if(response.status_code == 200):
        print("[DEBUG] query_speech_server_input request received successfully.")
      elif(response.status_code != 204):
        print("[WARNING] Server rejected query_speech_server_input request with status code " + str(response.status_code) + ".")
    except:
      print("[WARNING] query_speech_server_input unable to connect to server.")

  # Executes a simple GET query and expects the status code to be 200. 
  def execute_get_query(self, query):
    print("[DEBUG] Sending query: " + query)
    response = requests.get(query)
    if(response.status_code == 200):
      print("[DEBUG] Request received successfully.")
    else:
      print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

  # Creates, formats, and executes a simple POST query.
  def generate_and_execute_post_query(self, data_to_send):
    query = self.web_server_ip_address + "/moduleInputModify"
    print("[DEBUG] Sending query: " + query + " with body:")
    print(data_to_send)
    response = requests.post(query, data=json.dumps(data_to_send, indent = 4), headers = {'Content-Type': 'application/json'}, timeout=5)
    if(response.status_code == 200):
      print("[DEBUG] Request received successfully.")
    else:
      print("[WARNING] Server rejected request with status code " + str(response.status_code) + ".")

  # Given the possible command string, roomId, actionId, and 
  # a binary set of states, return a query. 
  # 
  # If the command contains the keyword "virtual", a virtual 
  # module toggle will be created instead of physical. 
  def generate_query(self, command, roomId, actionId, onState, offState):
    endpoint = "/moduleToggle/"
    if "virtual" in command:
      endpoint = "/moduleVirtualToggle/"
    if("off" in command or "deactivate" in command):
      return self.web_server_ip_address + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(offState)
    elif("on" in command or "activate" in command or "initialize" in command):
      return self.web_server_ip_address + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(onState)
    else:
      # No on or off specified. Check queried information. 
      if(self.action_states is not None):
        if(self.action_states[str(roomId)][str(actionId)] == int(onState)):
          return self.web_server_ip_address + endpoint +str(roomId)+"/"+str(actionId)+"/" + str(offState)
        else:
          return self.web_server_ip_address + endpoint+str(roomId)+"/"+str(actionId)+"/" + str(onState)
