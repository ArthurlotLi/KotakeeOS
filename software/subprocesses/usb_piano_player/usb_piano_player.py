#
# usb_piano_player.py
#
# Given a direct line to a piano via MIDI USB, play a piano song. 
# Self-contained, only plays a single song when directed. Expects
# a song in the form of either a midi file or a base64 encoded
# string (i.e. one sent over HTTP). Songs provided via base64 
# encoded string will have temporary files created that are then
# deleted upon termination of the program. 

import mido
from mido import MidiFile
import base64
import argparse
import os

from flask import Flask
from flask_restful import Resource, Api, reqparse
from gevent.pywsgi import WSGIServer
import time

# How many seconds to wait for the web server to send the song to
# play over HTTP before perishing. 
_recieve_song_timeout = 20

class UsbPianoPlayer:
  # Relative to the location of server.js.
  piano_songs_location = "./subprocesses/usb_piano_player/piano_songs"

  port = None
  playing = False
  stop_song = False

  def __init__(self):
    available_ports = mido.get_output_names()
    print("[DEBUG] UsbPianoPlayer available ports: " + str(available_ports))

    if len(available_ports) > 0:
      print("[INFO] UsbPianoPlayer opening default output port.")
      # Open the (system specific) default port. 
      self.port = mido.open_output()
    else:
      print("[ERROR] UsbPianoPlayer could not find an output port!")

  # Bread and butter for this class. Given either a location or a 
  # pair of song_name + base64 string, load the song and play it
  # over the port to the connected Yamaha. 
  def play_midi(self, location = None, song_name = None, base_64_string = None):
    if self.port is None:
      print("[ERROR] UsbPianoPlayer is unable to play with a closed output port. Cancelling...")
      return

    self.playing = True
    midi_song = None
    created_song_location = None
    if location is not None:
      midi_song = self.load_midi_file(location = location)
    elif song_name is not None and base_64_string is not None:
      midi_song, created_song_location = self.decode_midi_string(base_64_string=base_64_string, song_name = song_name)
    
    if midi_song is not None:
      try:
        # Play it. 
        print("[INFO] UsbPianoPlayer Now Playing!")
        for msg in midi_song.play():
          if self.stop_song is True:
            break
          self.port.send(msg)
        print("[INFO] UsbPianoPlayer song complete!")
        self.stop_song = False
      except Exception as e:
        print("[ERROR] UsbPianoPlayer ran into an exception while playing!")

    # Once we're done, if we decoded a string, delete the file we
    # created.
    if created_song_location is not None:
      self.delete_midi_file(created_song_location)
    self.playing = False
    print("[INFO] UsbPianoPlayer Complete. Closing.")

  # Given a file location, load a file. 
  def load_midi_file(self, location):
    print("[DEBUG] UsbPianoPlayer loading song located: " + str(location) + ".")
    midi_song = None
    try:
      midi_song = MidiFile(location)
    except Exception as e:
      print("[ERROR] UsbPianoPlayer was unable to load song from location '" + str(location) + "'. Exception: ")
      print(e)
    return midi_song

  # Given a file location, delete the file. 
  def delete_midi_file(self, created_song_location):
    print("[DEBUG] UsbPianoPlayer deleting song located: " + str(created_song_location) + ".")
    try:
      os.remove(created_song_location)
    except Exception as e:
      print("[ERROR] UsbPianoPlayer was unable to delete song from location '" + str(created_song_location) + "'. Exception: ")
      print(e)

  # Given a base 64 encoded string, decode it and create a midi
  # file. Then load it. 
  def decode_midi_string(self, base_64_string, song_name):
    new_file_location = self.piano_songs_location + "/" + song_name + ".mid"
    print("[DEBUG] UsbPianoPlayer Writing base 64 string and song name to file: " + new_file_location)
    decoded_midi_file = base64.b64decode(base_64_string)
    new_song_file = open(new_file_location, "wb")
    new_song_file.write(decoded_midi_file)
    new_song_file.close()

    # Now load the file. 
    return self.load_midi_file(location = new_file_location), new_file_location

class PianoPlayerWebServer:
  """
  A Mayflower web server. In order to communicate between the web
  server and the main process (in a manner that avoid complicated
  stuff), prop up a HTTP restful API for managing playing a single
  song. 

  During playing of a song, the following abnormal actions may take
  place given instruction from the web server:

  1. Stop the song - just terminate the web server here. 
  2. Replace the song - start playing something else. 
  """
  def __init__(self, application_port, player):
    # Define the application.
    app = Flask(__name__)

    application_port = int(application_port)

    self.player = player

    # Define the API, which we will add our endpoints onto. 
    api = Api(app)

    # Starting new songs (and replacing existing songs)
    def post_start_song(self, player=player):
      """
      Parses all arguments as Unicode strings. 
      """
      parser = reqparse.RequestParser()
      parser.add_argument("song_name", type=str)
      parser.add_argument("midi_contents", type=str)
      args = parser.parse_args()

      if player.playing is True:
        # Stop the current song. 
        player.stop_song = False

      while player.playing is True:
        time.sleep(1)

      player.play_midi(location = None, base_64_string = args.midi_contents, song_name = args.song_name)

    endpoint_class = type("startSong", (Resource,), {
      "post": post_start_song,
    })
    api.add_resource(endpoint_class, '/%s' % "startSong")

    # Stopping playing songs.
    def get_stop_song(self, player=player):
      if player.playing is True:
        # Stop the current song. 
        player.stop_song = False
    
    endpoint_class = type("stopSong", (Resource,), {
      "get": get_stop_song,
    })
    api.add_resource(endpoint_class, '/%s' % "stopSong")

    print("[INFO] Server is now online at http://%s:%d." % ("localhost", application_port))
    app.debug = True 
    http_server = WSGIServer(("localhost", application_port), app)
    http_server.serve_forever() 

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("application_port")
  args = parser.parse_args()
  application_port = args.application_port

  player = UsbPianoPlayer()
  PianoPlayerWebServer(application_port, player)

  """
  else:
    #location = "./piano_songs/westworld.mid" 
    song_name = "test"
    base_64_string = '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'

  player = UsbPianoPlayer()
  player.play_midi(location = location, base_64_string = base_64_string, song_name = song_name)
  """
  
