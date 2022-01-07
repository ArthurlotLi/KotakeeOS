#
# emotion_detection_harness.py
#
# Foray into Emotion Detection (EA), a subset of Sentiment Analysis 
# (SA) that is a subfield of Natural Language Processing (NLP). 
# Specifically, develop a textual-based Emotion Detection learning
# solution. 
#
# Given a sentence, predict the category of emotion of the author
# penning the sentence. 
#
# This implementation is based upon the Paul Ekman Discrete Emotion
# Model (DEM) of human emotion with 6 categories, alongside an
# additional "neutral" category. Together, the 7 possible solutions
# for the model are:
#  - Joy
#  - Sadness
#  - Fear
#  - Anger
#  - Disgust
#  - Surprise
#  - Neutral
#
# Train the model on a combination of datasets obtained from online
# resources, as well as with homegrown personally labelled datsets. 
# Allow for different combinations of datasets to account for unknown
# differences between subjective labels and/or quality of data. 
# The datasets that may be combined are:
#  1 ISEAR
#    https://www.kaggle.com/shrivastava/isears-dataset
#
#  2 WASSA-2017 Emotion Intensities(EmoInt)
#    http://alt.qcri.org/semeval2017/task4/index.php?id=download-the-full-training-data-for-semeval-2017-task-4 
#
#  3 Cecilia Ovesdotter Alm's Affect data
#    http://people.rc.rit.edu/∼coagla/affectdata/index.html
#
#  4 DailyDialog
#    https://www.aclweb.org/anthology/I17-1099/
#
#  5 Emotion Stimulus
#    http://www.site.uottawa.ca/∼diana/resources/emotion_stimulus_data
#
#  6 MELD
#    https://github.com/SenticNet/MELD
#
#  7 SMILE dataset
#    https://figshare.com/articles/smile_annotations_final_csv/3187909 

from emotion_detection_dataset import EmotionDetectionDataset

import pandas as pd
import argparse

class EmotionDetectionHarness:
  dataset_variants_location = "./dataset_variants"
  test_dataset_suffix = "_test"
  train_dataset_suffix = "_train"

  # If the dataset is already generated, provide this method with the
  # variant number and the written csv files will be utilized.
  def load_and_train_model(self, variant_num):
    print("[INFO] Loading existing dataset and training for emotion detection dataset variant " + str(variant_num) + ".")
    train_set, test_set = self.load_test_train(variant_num = variant_num)
    self.train_model(variant_num=variant_num,train_set=train_set, test_set=test_set)

  # Given a variant number, loads train and test datasets. Returns
  # a none tuple of length two if an error is encountered.
  def load_test_train(self, variant_num):
    print("[INFO] Loading emotion detection dataset variant " + str(variant_num) + ".")
    train_set = None
    test_set = None
    train_location = self.dataset_variants_location + "/" + str(variant_num) + self.train_dataset_suffix + ".csv"
    test_location = self.dataset_variants_location + "/" + str(variant_num) + self.test_dataset_suffix + ".csv"
    try:
      print("[DEBUG] Attempting to read dataset train file " + str(train_location) + ".")
      train_set = pd.read_csv(train_location)
      test_set = pd.read_csv(test_location)
    except Exception as e:
      print("[ERROR] Failed to read files " + str(train_location) + " and "+str(test_location)+". Error:")
      print(e)
      return None, None

    print("[INFO] Train and Test datasets loaded successfully.")
    return train_set, test_set

  # Given a dataset variation number, execute a model training session.
  # Expects train and test dataframes. 
  def train_model(self, variant_num, train_set, test_set):
    print("[INFO] Beginning Emotion Detection training session with variant num " + str(variant_num) + ".")
    if train_set is None or test_set is None:
      print("[ERROR] train_model recieved empty train/test sets. Stopping...")
      return
    
    # Loaded successfully. Continue. TODO
    print("[INFO] Utilizing Train set "  + str(train_set.shape) + " and Test set " + str(test_set.shape) + ".")


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("variant_num")
  args = parser.parse_args()

  variant_num = args.variant_num

  emotion_detection = EmotionDetectionHarness()
  emotion_detection.load_and_train_model(variant_num=variant_num)