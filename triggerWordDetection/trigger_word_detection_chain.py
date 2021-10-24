#
# trigger_word_detection_chain.py
#
# Allows for multiple training sessions to occur at once utilizing
# class defined in trigger_word_detection.py. Utilizes processes
# to circumvent graphics card memory flushing issue for keras. 
#
# Note: expects all datasets to have been generated already. 

# TODO: Implement process usage to properly allow for multiple large-dataset training sessions to occur consecutively. 

from trigger_word_detection import TriggerWordDetection
 
import os

class TriggerWordDetectionChain:

  chain_train_results_location = "./chain_train_results"
  chain_train_results = []
  chain_train_dict = None

  def __init__(self, models_dict):
    self.chain_train_dict = models_dict

  def execute_chain_train(self):
    print("[INFO] Initializing Trigger Word Detection Chain Train...")
    for model_identifier in self.chain_train_dict:
      try:
        print("\n[INFO] Processing model variant with identifier " + str(model_identifier) + ".")
        model = self.chain_train_dict[model_identifier]

        trigger_word_detection = TriggerWordDetection()
        best_accuracy, acc = trigger_word_detection.main(generateDataset = False, datasetSize = 1, iternum = int(model["iternum"]), outputnum = model_identifier, model_parameters=model)

        if best_accuracy is None or acc is None:
          print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")
        else:
          print("[INFO] Model variant " + str(model_identifier) + " processing complete.")
          self.chain_train_results.append(str(model_identifier) + " Train Accuracy: %.8f Dev Accuracy: %.8f\n" % (best_accuracy*100,acc*100))
      except:
        # Use a try/except so that we still write the remaining stuff 
        # to file in case of a failure or the user cancels the rest.
        print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")

    # All results obtained. Write to file. 
    self.write_results()
    
  def write_results(self):
    print("[INFO] Chain train complete. Writing results to file...")
    try:
      results_folder_contents = os.listdir(self.chain_train_results_location)
      result_index = 0
      file_name_prefix = "chain_train_results_"
      file_name_suffix = ".txt"
      for file in results_folder_contents:
        file_number_str = file.replace(file_name_prefix, "").replace(file_name_suffix, "")
        file_number = -1
        try:
          file_number = int(file_number_str)
          if(file_number >= result_index):
            result_index = file_number + 1
        except:
          print("[WARN] Unexpected file in results directory. Ignoring...")

      f = open(self.chain_train_results_location + "/"+file_name_prefix+str(result_index)+file_name_suffix, "w")
      f.write("=================================\nChain Train Results\n=================================\n\n")
      # Write model specifications
      for model_identifier in self.chain_train_dict:
        f.write(str(model_identifier) + " - ")
        model = self.chain_train_dict[model_identifier]
        for key in model:
          f.write(str(key) + ":" + str(model[key]) + "  ")
        f.write("\n")
      f.write("\n")
      # Write results of each model. 
      for result in self.chain_train_results:
        f.write(result)
      f.close()
      print("[INFO] Write complete. Have a good night...")
    except:
      print("[ERROR] Failed to write results of " + str(model_identifier) + " to file!")

if __name__ == "__main__":

  # Each model identifier is the outputnum that the model wil be
  # saved as (don't let this overwrite other models.) The iternum
  # specified in each model's arguments refers to the dataset number
  # that will be used. 

  # Experiment 0
  """
  chain_dict = {
    "11005" : {
      "iternum" : "11000",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2500,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "11006" : {
      "iternum" : "10999",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 1000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }

  """
  # Experiment 1
  chain_dict = {
    "12001" : {
      "iternum" : "12000",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 1300,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }

  trigger_word_detection_chain = TriggerWordDetectionChain(chain_dict)
  trigger_word_detection_chain.execute_chain_train()
