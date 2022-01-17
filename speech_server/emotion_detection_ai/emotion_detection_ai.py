#
# emotion_detection_ai.py
#
# "Production" utilization of generated emotion detection models.
# Utilizes models saved in the local "model" folder to predict
# an emotion category given an input text. 
#
# This implementation is based upon the Paul Ekman Discrete Emotion
# Model (DEM) of human emotion with 6 categories, alongside an
# additional "neutral" category. Together, the 7 possible solutions
# for the model are:
#  0 Joy
#  1 Sadness
#  2 Fear
#  3 Anger
#  4 Disgust
#  5 Surprise
#  6 Neutral

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

class EmotionDetectionAi:
  model_variants_location = "./models"

  model = None
  tokenizer = None
  device = None

  # Mapping integers to their solutions. Should be synchronized with
  # solution_string_map class variables found in supporting classes.
  solution_int_map = ["joy", "sadness", "fear", "anger", "disgust", "surprise", "neutral"]

  # Maximum input for the model is 256 by default(see emotion 
  # detection harness class variable). However, in the interest
  # of speed, you may specify a lower number than this to truncate
  # incoming text. 
  max_seq_length = 256
    
  # Upon initialization, attempt to load the model specified.
  def __init__(self, model_num, use_cpu = True):
    print("[DEBUG] Initializing EmotionDetectionAI with model number "+str(model_num)+"...")

    model, tokenizer, device = self.load_tokenizer_and_model(model_num=model_num, device=None, use_cpu=use_cpu)

    if model is None or tokenizer is None or device is None:
      print("[ERROR] Failed to load model, tokenizer, or device properly. Initialization failed.")
    else:
      self.model = model
      self.tokenizer = tokenizer
      self.device = device
      print("[DEBUG] EmotionDetectionAI initialized successfully.")

  # Given a model_num, return the tokenizer and model stored at the
  # expected location. Loads the device to run it on if it is not 
  # provided. Also returns the device in case it is needed.
  def load_tokenizer_and_model(self, model_num, device = None, use_cpu = False):
    # Grab the device first if we don't have it. 
    if device is None:
      device = self.train_model_load_device(use_cpu = use_cpu)

    try:
      model_path = self.model_variants_location + "/" + str(model_num)
      print("[DEBUG] Loading Tokenizer for model " + str(model_num) + " from '" + model_path + "'.")
      tokenizer = AutoTokenizer.from_pretrained(model_path)
      print("[DEBUG] Loading Model for model " + str(model_num) + " from '" + model_path + "'.")
      model = AutoModelForSequenceClassification.from_pretrained(model_path)

      print("[DEBUG] Loading Model onto device.")
      model.to(device)

      return model, tokenizer, device
    except Exception as e:
      print("[ERROR] Unable to load model " + str(model_num) + ". Exception: ")
      print(e)
    return None, None, None

  # Load the device for torch work. Expects a boolean indicating whether
  # we'll be using the CPU. Returns None in the event of a GPU CUDA load
  # failure.
  def train_model_load_device(self, use_cpu):
    device = None

    if not use_cpu:
      # Note we expect to be using CUDA for this training session. If we
      # encounter an error, we'll just stop. 
      try:
        print("[DEBUG] Verifying CUDA: ", end="")
        print(torch.zeros(1).cuda())
        print("[DEBUG] CUDA version: ", end="")
        print(torch.version.cuda)
        print("[DEBUG] Torch CUDA is available: " + str(torch.cuda.is_available()))
      except:
        print("[ERROR] Unable to access Torch CUDA - was pytorch installed from pytorch.org with the correct version?")
        return None
      
      device = torch.device("cuda") 
      print("[DEBUG] GPU with CUDA successfully added as device.")
    else:
      device = torch.device("cpu") # Use the CPU for better debugging messages. 
      print("[DEBUG] CPU successfully added as device.")
    
    return device

  # Execute predictions given a string. Returns the solution string
  # itself (Ex) "joy")
  def predict_emotion(self, text):
    # In case of a failed initialization, just use neutral.
    if self.model is None or self.tokenizer is None or self.device is None:
      print("[WARNING] EmotionDetectionAI failed initialization - defaulting to neutral emotion.")
      return "neutral"

    # TODO: Remove stop words?

    print("[INFO] EmotionDetectionAI processing given text of length "+str(len(text))+"...")

    # Encode the text with the tokenizer we loaded.
    encoded_text = self.tokenizer.encode_plus(
      text, 
      return_tensors="pt", 
      max_length = self.max_seq_length, 
      truncation=True)
    
    # Send the text to the device.
    sequence = encoded_text["input_ids"].to(self.device)

    # Make predictions with the model we loaded.
    outputs = self.model(sequence)
    logits = outputs[0]
    prediction_vector = logits.detach().cpu().tolist()[0]

    # We now have a prediction vector listing confidence of all
    # of the classes
    # Ex) [-0.14414964616298676, -0.06529509276151657, -0.49382615089416504, 2.442490339279175, 1.221635341644287, -0.23346763849258423, -1.888406753540039]
    #
    # Parse the vector and grab the 3rd highest confidence 
    # options. (Kinda messy, but as far as I believe this is
    # fastest way)
    max_prediction_index = None
    max_prediction_confidence = -9999
    second_max_prediction_index = None
    second_max_prediction_confidence = None
    third_max_prediction_index = None
    third_max_prediction_confidence = None
    for i in range(0, len(prediction_vector)):
      prediction = prediction_vector[i]
      if prediction > max_prediction_confidence:
        # Shuffle the three. 
        third_max_prediction_index = second_max_prediction_index
        third_max_prediction_confidence = second_max_prediction_confidence
        second_max_prediction_index = max_prediction_index
        second_max_prediction_confidence = max_prediction_confidence
        max_prediction_index = i
        max_prediction_confidence = prediction

    max_prediction = self.solution_int_map[max_prediction_index]
    second_max_prediciton = self.solution_int_map[second_max_prediction_index]
    third_max_prediction = self.solution_int_map[third_max_prediction_index]

    # Output the results for debug and return the maximum
    # confidence. 
    print("[INFO] Best Prediction: " + str(max_prediction) + " ["+str(max_prediction_confidence)+"]")
    print("                   2nd: " + str(second_max_prediciton) + " ["+str(second_max_prediction_confidence)+"]")
    print("                   3nd: " + str(third_max_prediction) + " ["+str(third_max_prediction_confidence)+"]")

    return max_prediction

# For debug purposes only, test a simple text for emotion category. 
if __name__ == "__main__":
  model_num = 1
  text = "this is the worst!"

  emotion_detection = EmotionDetectionAi(model_num=model_num)
  emotion_detection.predict_emotion(text = text)