#
# emotion_detection_dataset.py
#
# Dataset selection and precprocessing for Emotion Detection AI 
# project. Selectively combine datasets together and preprocess
# them as specified by the calling class/user. 

import argparse
import pandas as pd
import os

class EmotionDetectionDataset:
  raw_data_location = "./raw_data"
  output_data_location = "./dataset_variants"

  # It is assumed all of these are of the .csv suffix. 
  subset_filenames = None

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
  # tests ALL dataset variants. 
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
    print("[DEBUG] Discovered " +  str(len(raw_data_files)) + " in the raw data folder " + str(self.raw_data_location) + ".")
        
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
        csv_filename = self.output_data_location + "/" + str(variant_num) + ".csv"
        txt_filename = self.output_data_location + "/" + str(variant_num) + ".txt"
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
        txt_file.write(str(variant_flags))
        txt_file.write("\n\n")
        txt_file.write(str(frequency_dict))
        
        print("[INFO] Write complete. All done - goodnight!")

    return product_data

# If called directly, we will nominally create an all-in-one
# dataset. 
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("variant_num")
  args = parser.parse_args()

  variant_num = args.variant_num
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

  emotion_detection_dataset = EmotionDetectionDataset()
  #emotion_detection_dataset.generate_dataset_variant(variant_num = variant_num, variant_flags = variant_flags)
  emotion_detection_dataset.generate_dataset_variant(variant_num = variant_num, variant_code = variant_code)