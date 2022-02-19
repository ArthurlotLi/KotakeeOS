#
# multispeaker_synthesis_utility.py
#
# "Production" utilization of the generated multispeaker synthesis
# models. Utilizes models saved in the local "model" folder to generate
# output audio combining speaker attributes extracted from reference
# audio of a target speaker and output text. 
#
# Allows for integration with an Emotion Detection model as an upstream 
# component, integrating an "emotion prior" into the output audio by
# selectively choosing the input reference audio depending on the
# provided emotion label. This allows for a more "involved" output
# relevant to the content of the text itself. 

import time

class MultispeakerSynthesisUtility:
  # Default is based off the speech_server level. May be 
  # overridden during initialization.
  model_variants_location = "../multispeaker_synthesis/models"
  speakers_location = "../multispeaker_synthesis/speakers"

  model = None

  # Upon initialization, attempt to load the model specified.
  # Allow user to provide model location and override the default.
  def __init__(self, model_num, model_variants_location = None, speakers_location = None):
    print("[DEBUG] Initializing MultispeakerSynthesisUtility with model number "+str(model_num)+"...")

    # Override the default location if provided. This is because
    # the default is based off the speech_server level. 
    if model_variants_location is not None:
      self.model_variants_location = model_variants_location
    if speakers_location is not None:
      self.speakers_location = speakers_location

    # TODO: load model. 

  # Interface with Emotion Detection upstream model output. Given
  # an emotion category, choose a wav file from the specified
  # directory of the target speaker speaking with that emotion. 
  # This "injects" the inferred emotion prior into our output.
  # Requires speaker_id as well. 
  #
  # The speaker directory should contain files labeled as such
  # per speaker:
  #
  # speaker_id_joy.wav
  # speaker_id_sadness.wav
  # speaker_id_fear.wav
  # speaker_id_anger.wav
  # speaker_id_disgust.wav
  # speaker_id_surprise.wav
  # speaker_id_neutral.wav
  def synthesize_emotional_speech(self, emotion_category, output_text, speaker_id):
    print("[DEBUG] Multispeaker Synthesis received emotion " + str(emotion_category) + " and speaker_id " + str(speaker_id) + ".")
    reference_wav_location = self.speakers_location + "/" + str(speaker_id) + "_" + str(emotion_category) + ".wav"
    self.synthesize_speech(output_text=output_text, reference_wav_location=reference_wav_location)

  # Given a path to a wav file containing untranscribed speech of
  # the target speaker as well as output text, synthesize a waveform
  # of the target speaker "speaking" the text. 
  def synthesize_speech(self, output_text, reference_wav_location):
    # Attempt toload the wav file. 
    loaded_ref = self.load_wav(reference_wav_location)

    if loaded_ref is not None:
      print("[DEBUG] Multispeaker Synthesis synthesizing output text '" +  str(output_text) + "'.")
      start_time = time.time()

      # TODO: Run the model here. 

      print("[DEBUG] Multispeaker Synthesis completed synthesis in " + str(time.time() - start_time) + " seconds.")

      # TODO: Output the text. 

  # Attempts to load a wav form at the specified location. Returns
  # none if it failed.
  def load_wav(self, location):
    return None

# For debug purposes only. 
if __name__ == "__main__":
  model_variants_location = "../../multispeaker_synthesis/models"
  speakers_location = "../../multispeaker_synthesis/speakers"
  model_num = 1

  utility = MultispeakerSynthesisUtility(model_num=model_num, model_variants_location=model_variants_location, speakers_location=speakers_location)