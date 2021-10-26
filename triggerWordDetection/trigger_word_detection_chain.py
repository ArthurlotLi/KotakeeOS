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
import multiprocessing
import time

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
        time_start = time.time()

        # Execute training as a separate process. Use a queue to
        # obtain results. 
        ret_dict = {"best_accuracy":None, "acc":None}
        queue = multiprocessing.Queue()
        queue.put(ret_dict)

        print("[INFO] Executing new process...")
        p = multiprocessing.Process(target=self.trigger_word_detection_worker, args=(queue, model, model_identifier,))
        p.start()
        p.join()
        ret_dict_result = queue.get()
        print("\n[INFO] Process complete; result: ")
        print(ret_dict_result)
        best_accuracy = ret_dict_result["best_accuracy"]
        acc = ret_dict_result["acc"]

        time_end = time.time()
        time_elapsed_seconds = time_end - time_start # time in seconds. 
        time_elapsed_hours = time_elapsed_seconds/3600 

        if best_accuracy is None or acc is None:
          print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")
          self.chain_train_results.append(str(model_identifier) + " EXECUTION FAILED!\n")
        else:
          print("[INFO] Model variant " + str(model_identifier) + " processing complete.")
          self.chain_train_results.append(str(model_identifier) + " Train Accuracy: %.8f Dev Accuracy: %.8f Time: %.4f hrs\n" % (best_accuracy*100,acc*100, time_elapsed_hours))
      except:
        # Use a try/except so that we still write the remaining stuff 
        # to file in case of a failure or the user cancels the rest.
        print("[ERROR] Failed to process model variant " + str(model_identifier) + "!")

    # All results obtained. Write to file. 
    self.write_results()

  # Executed as a separate process so it can be purged as a
  # seperate process, allowing Tensorflow to clear out the
  # memory of the GPU and not freak out when we train another
  # right after.
  def trigger_word_detection_worker(self, queue, model, model_identifier):
    trigger_word_detection = TriggerWordDetection()
    best_accuracy, acc = trigger_word_detection.main(generateDataset = False, datasetSize = 1, iternum = int(model["iternum"]), outputnum = model_identifier, model_parameters=model)
    ret_dict = queue.get()
    ret_dict["best_accuracy"] = best_accuracy
    ret_dict["acc"] = acc
    queue.put(ret_dict)
    
  def write_results(self):
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

      filename = self.chain_train_results_location + "/"+file_name_prefix+str(result_index)+file_name_suffix
      f = open(filename, "w")
      print("\n[INFO] Chain train complete. Writing results to file '"+filename+"'...")
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
  """
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
  """
  # Experiment 2
  """
  chain_dict = {
    "12151" : {
      "iternum" : "12051",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12152" : {
      "iternum" : "12052",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12153" : {
      "iternum" : "12053",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12154" : {
      "iternum" : "12054",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12155" : {
      "iternum" : "12055",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12156" : {
      "iternum" : "12056",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12157" : {
      "iternum" : "12057",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12158" : {
      "iternum" : "12058",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12159" : {
      "iternum" : "12059",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }
  """
  # Experiment 3
  """
  chain_dict = {
    "12160" : {
      "iternum" : "12060",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 800,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12161" : {
      "iternum" : "12060",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 1500,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }
  """
  # Experiment 4
  """
  chain_dict = {
    "12162" : {
      "iternum" : "12062",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }
  """
  # Experiment 5
  """
  chain_dict = {
    "12163" : {
      "iternum" : "12063",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }
  """
  # Experiment 6
  """
  chain_dict = {
    "12164" : {
      "iternum" : "12064",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }
  """
  # Experiment 7
  chain_dict = {
    "12165" : {
      "iternum" : "12065",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12166" : {
      "iternum" : "12066",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12167" : {
      "iternum" : "12067",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
    "12168" : {
      "iternum" : "12068",
      "learning_rate" : 0.0001,
      "loss_function" : 'binary_crossentropy',
      "epochs" : 2000,
      "batch_size" : 32, 
      "validation_split" : 0.2,
    },
  }

  trigger_word_detection_chain = TriggerWordDetectionChain(chain_dict)
  trigger_word_detection_chain.execute_chain_train()
