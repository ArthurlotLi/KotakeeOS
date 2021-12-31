#
# test_model_chain.py
#
# Tests all models currently present in a specified directory
# given the class defined in test_model. 

from test_model import TestModel
 
import os
import multiprocessing
import argparse
import numpy as np

class TestModelChain:
  X_dev_location = "./XY_dev_kotakee/X_dev_kotakee.npy"
  Y_dev_location = "./XY_dev_kotakee/Y_dev_kotakee.npy"
  use_gpu = False # Change to True if your test set is huge. 

  chain_test_results_location = "./chain_test_results"
  chain_test_results = {}
  chain_test_results_acc_map = {}
  test_model_location = None

  def __init__(self, location):
    self.test_model_location = location

  def execute_chain_test(self):
    print("[INFO] Initializing Test Model Chain...")
    filename_uid = 0 # for sorting.

    X_dev = None
    Y_dev = None

    # Load the dev datset once and pass to all workers.  
    try:
      print("[INFO] Loading dev dataset X file " + self.X_dev_location + "...")
      X_dev = np.load(self.X_dev_location)
      print("[INFO] Loading dev dataset Y file " + self.Y_dev_location + "...")
      Y_dev = np.load(self.Y_dev_location)
      print("[DEBUG] X_dev.shape is:", X_dev.shape)  
      print("[DEBUG] Y_dev.shape is:", Y_dev.shape) 
    except:
      print("[WARN] Error loading X_dev and/or Y/dev.")
      return -1

    for filename in os.listdir(self.test_model_location):
      if filename.endswith("h5"):
        try:
          print("\n[INFO] Processing model " + str(filename) + ".")
          
          # Execute test as a separate process. Use a queue to
          # obtain results. 
          ret_dict = {"acc":None}
          queue = multiprocessing.Queue()
          queue.put(ret_dict)

          print("[INFO] Executing new process...")
          p = multiprocessing.Process(target=self.test_model_worker, args=(queue, self.test_model_location + "/" + filename, X_dev, Y_dev))
          p.start()
          p.join()
          ret_dict_result = queue.get()
          print("\n[INFO] Process complete; result: ")
          print(ret_dict_result)
          acc = ret_dict_result["acc"]
        
          if acc is None:
            print("[ERROR] Failed to process model " + str(filename) + "!")
            self.chain_test_results[filename_uid] = "00.00000000 - " + str(filename) + " TEST FAILED!\n"
            self.chain_test_results_acc_map[-1] = filename_uid
          else:
            print("[INFO] Model " + str(filename) + " processing complete.")
            self.chain_test_results[filename_uid] = "%.8f - " % (acc*100) + str(filename) + "\n"
            self.chain_test_results_acc_map[acc] = filename_uid
        except:
          # Use a try/except so that we still write the remaining stuff 
          # to file in case of a failure or the user cancels the rest.
          print("[ERROR] Failed to process model " + str(filename) + "!")
        
        filename_uid = filename_uid + 1

    if(filename_uid == 0):
      print("[WARNING] No models found at location '" + self.test_model_location + "'. Please specify another location with an argument (example: python test_model_chain.py ./model_checkpoints) or move/copy the model(s) accordingly.")
      return

    # Sort the results.
    self.chain_test_results_acc_map = dict(sorted(self.chain_test_results_acc_map.items(), key=lambda item: item[0]))

    # All results obtained. Write to file. 
    self.write_results()

  # Executed as a separate process so it can be purged as a
  # seperate process, allowing Tensorflow to clear out the
  # memory of the GPU and not freak out when we train another
  # right after. If the GPU is disabled, this still allows the 
  # memory to be handled properly. 
  def test_model_worker(self, queue, model_path, X_dev = None, Y_dev = None):
    test_model = TestModel()
    acc = test_model.test_model(model_path = model_path, X_dev = X_dev, Y_dev = Y_dev, use_gpu = self.use_gpu)
    ret_dict = queue.get()
    ret_dict["acc"] = acc
    queue.put(ret_dict)
    
  def write_results(self):
    try:
      results_folder_contents = os.listdir(self.chain_test_results_location)
      result_index = 0
      file_name_prefix = "chain_test_results_"
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

      filename = self.chain_test_results_location + "/"+file_name_prefix+str(result_index)+file_name_suffix
      f = open(filename, "w")
      print("\n[INFO] Chain test complete. Writing results to file '"+filename+"'...")
      f.write("=================================\nChain Test Results\n=================================\n\n")
      # Write results of each model, sorted.
      for key in self.chain_test_results_acc_map:
        f.write(self.chain_test_results[self.chain_test_results_acc_map[key]])
      f.close()
      print("[INFO] Write complete. Have a good night...")
    except:
      print("[ERROR] Failed to write results to file!")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  # Add a '?' to make the argument optional
  parser.add_argument("location", nargs='?', default="./model_chain_test")
  args = parser.parse_args()

  location = args.location

  test_model_chain = TestModelChain(location)
  test_model_chain.execute_chain_test()
