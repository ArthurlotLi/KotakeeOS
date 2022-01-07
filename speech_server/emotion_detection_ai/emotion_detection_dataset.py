#
# emotion_detection_dataset.py
#
# Dataset selection and precprocessing for Emotion Detection AI 
# project. Selectively combine datasets together and preprocess
# them as specified by the calling class/user. 
#
# Allows for the automatic splitting of the datset into test
# and train files. Returns all values direclty in addition to
# writing them to disk. 
#
# Functions based on the contents of the raw_data folder - if
# new datasets are generated in the future and placed in the
# folder, this program does not need to be modified. 

import argparse
import pandas as pd
import os
from sklearn.model_selection import train_test_split

class EmotionDetectionDataset:
  raw_data_location = "./raw_data"
  output_data_location = "./dataset_variants"

  test_dataset_suffix = "_test"
  train_dataset_suffix = "_train"

  # Default 20% test set size. 
  default_test_ratio = 0.20

  # It is assumed all of these are of the .csv suffix. 
  subset_filenames = None
  variant_flags = None

  # Primary function that allows callers to both create a dataset and
  # split it at the same time. 
  def generate_split_variant(self, variant_num, variant_flags = None, variant_code = None, test_ratio = None):
    print("[INFO] Beginning Emotion Detection generate split variant with variant num " + str(variant_num) + ".")
    full_data = self.generate_dataset_variant(variant_num=variant_num, variant_flags=variant_flags, variant_code=variant_code)
    train_set, test_set = self.split_dataset_variant(variant_num=variant_num, full_data=full_data, test_ratio=test_ratio)
    print("[INFO] Generate split variant finished for variant num " + str(variant_num) + ". Goodnight.")
    return train_set, test_set

  # Given a combination of flags demarcating what datasets to
  # use, as well as a dataset variant number, generate a new 
  # dataset variant. Each flag should be equivalent to the 
  # name of the csv file (excluding the suffix .csv).
  #
  # Calling classes may alternatively provide a variant_code,
  # which correspondes to the base 10 value of the base 2 
  # vector of active/inactive subsets. 
  # i.e. [0,0,0,0,1,0,0] = 4
  # This is to allow for an iterative training method that
  # tests ALL dataset variants easily.
  #
  # In addition to writing the new variant to file, we return
  # the complete dataset to calling classes. 
  def generate_dataset_variant(self, variant_num, variant_flags = None, variant_code = None):
    print("[INFO] Beginning Emotion Detection Dataset variant generation.")
    product_data = None

    # Get the contents of the raw_data folder.
    raw_data_files = []
    for filename in os.listdir(self.raw_data_location):
      if filename.endswith(".csv"):
        raw_data_files.append(filename.replace(".csv", ""))
    self.subset_filenames = raw_data_files
    print("[DEBUG] Discovered " +  str(len(raw_data_files)) + " files in the raw data folder " + str(self.raw_data_location) + ".")
        
    # If no flags are provided, provide all flags to create a
    # dataset with all subsets. 
    if variant_flags is None and variant_code is None:
      print("[INFO] No variant flags provided. Utilizing all subsets.")
      variant_flags = self.subset_filenames

    # Bitmask parsing. 
    elif variant_flags is None:
      variant_flags = []
      # variant_code provided. Translate from base 10 to 2.
      # We assign flags arbitrarily - the first file in the list
      # gets bitmask 1, the second 2, the third 4, etc. 
      for i in range(0,len(self.subset_filenames)):
        bitmask = i
        if i == 0: bitmask = 0.5 # To get us bitmask 1 first. 
        print("[DEBUG] Testing if " + str(variant_code) + " passes bitmask " + str(int(bitmask*2)) + " for file "  + str(self.subset_filenames[i]) + ".")
        if variant_code & int(bitmask*2): 
          print("        ...Passed!")
          variant_flags.append(self.subset_filenames[i])
        else:
          print("        ...Failed.")
    
    # Retain for writing to txt purposes. 
    self.variant_flags = variant_flags

    # For each dataset, append the info to our list. 
    read_files_data = []

    for variant in variant_flags:
      if variant not in self.subset_filenames:
        print("[ERROR] Recieved a variant that is not present in the raw data folder!")
      else:
        file_data = pd.read_csv(self.raw_data_location + "/" + variant + ".csv")
        read_files_data.append(file_data)
    
    # Combine all dataframes together with pd concat.
    if len(read_files_data) <= 0:
      print("[ERROR] No valid files were read. Stopping...")
    else:
      product_data = read_files_data[0]
      for i in range(1, len(read_files_data)):
        product_data = pd.concat([product_data, read_files_data[i]], axis=0)

      # We've now combined our product dataset. Let's write it. 
      if product_data is not None:
        self.write_csv_txt(self.output_data_location + "/" + str(variant_num), product_data)

        print("[INFO] Dataset generation for variant "+str(variant_num)+" successful.")

    return product_data

  # Given an iternum, splits a dataset variant into test and train
  # given a ratio (default is 20% for test). Does not read from 
  # file if given dataframe via full_data.
  #
  # Returns the train_set and the test_set in that order. 
  def split_dataset_variant(self, variant_num, full_data = None, test_ratio = None):
    print("[INFO] Beginning Dataset Variant Split operation.")
    if full_data is None:
      try:
        dataset_location = self.output_data_location + "/" + str(variant_num) + ".csv"
        print("[DEBUG] Attempting to read dataset variant file " + str(dataset_location) + ".")
        full_data = pd.read_csv(dataset_location)
      except Exception as e:
        print("[ERROR] Failed to read file " + str(dataset_location) + ". Error:")
        print(e)
        return

    # Full data read in successfully. 
    if test_ratio is None:
      print("[INFO] No test ratio specified - using default test ratio " + str(self.default_test_ratio) + ".")
      test_ratio = self.default_test_ratio
    
    # Everything's here, let's split the data randomly. 
    print("[INFO] Executing Test Train Split with data shape ", end="")
    print(full_data.shape, end="")
    print(" and test ratio " + str(test_ratio) + ".")
    train_set, test_set = train_test_split(full_data, test_size = test_ratio)

    # Write to file for both of them.
    self.write_csv_txt(self.output_data_location + "/" + str(variant_num) + self.train_dataset_suffix, train_set)
    self.write_csv_txt(self.output_data_location + "/" + str(variant_num) + self.test_dataset_suffix, test_set)

    print("[INFO] Train and Test dataset generation for variant "+str(variant_num)+" successful.")

    return train_set, test_set

  # Writes a csv and txt file given a dataframe and a filename.
  # The txt file describes the contents of the dataframe itself.
  # Prints out solution frequency as well as what subsets were
  # included. 
  def write_csv_txt(self, filename, product_data):
    csv_filename = filename + ".csv"
    txt_filename = filename + ".txt"

    print("[INFO] Writing " + csv_filename + " with data shape of ", end="")
    print(product_data.shape, end="")
    print(".") 
    frequency_dict = product_data["solution"].value_counts()
    print("[INFO] Solution Frequency:")
    print(frequency_dict)

    # Write the CSV.
    product_data.to_csv(csv_filename, encoding='utf-8', index=False)

    print("[INFO] Writing " + txt_filename + " with iteration information.")
    txt_file = open(txt_filename, "w")
    if self.variant_flags is not None:
      txt_file.write(str(self.variant_flags))
      txt_file.write("\n\n")
    txt_file.write(str(product_data.shape))
    txt_file.write("\n\n")
    txt_file.write(str(frequency_dict))

# If called directly, we will nominally create an all-in-one
# dataset. 
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("variant_num")
  args = parser.parse_args()

  variant_num = args.variant_num
  variant_flags = None
  variant_code = None
  """
  variant_flags = [
    "cecilia",
    "dailydialog", 
    "emotionstimulus",
    "isear",
    "meld",
    "smile",
    "wassa2017"
  ]
  variant_code = 127
  """

  emotion_detection_dataset = EmotionDetectionDataset()
  #emotion_detection_dataset.generate_dataset_variant(variant_num = variant_num, variant_flags = variant_flags)
  emotion_detection_dataset.generate_split_variant(variant_num = variant_num, variant_flags = variant_flags, variant_code = variant_code)