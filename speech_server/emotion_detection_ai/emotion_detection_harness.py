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
import numpy as np
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AdamW, AutoConfig
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from tqdm import tqdm
import os
import matplotlib.pyplot as plt

class EmotionDetectionHarness:
  dataset_variants_location = "./dataset_variants"
  model_variants_location = "./models"
  test_dataset_suffix = "_test"
  dev_dataset_suffix = "_dev"
  train_dataset_suffix = "_train"

  # Configurable model training settings/hyperparameters.
  adam_learning_rate = 0.00001 
  max_seq_length = 200

  # Note 32 is the upper limit that my GPU VRAM can handle. 
  dataloader_batch_size = 32
  model_epochs = 2
  model_grad_acc_steps = 4

  solution_string_map = {
    "joy" : 0,
    "sadness" : 1,
    "fear" : 2,
    "anger" : 3,
    "disgust" : 4,
    "surprise" : 5,
    "neutral" : 6,
  }

  # If the dataset is already generated, provide this method with the
  # variant number and the written csv files will be utilized.
  def load_and_train_model(self, variant_num, model_num, use_cpu = False):
    print("[INFO] Loading existing dataset and training for emotion detection dataset variant " + str(variant_num) + ".")
    train_set, dev_set, test_set = self.load_train_dev_test(variant_num = variant_num)
    model = self.train_model(model_num=model_num, variant_num=variant_num, train_set=train_set, dev_set = dev_set, test_set=test_set, use_cpu=use_cpu)

  # Given a variant number, loads train and test datasets. Returns
  # a none tuple of length two if an error is encountered.
  def load_train_dev_test(self, variant_num):
    print("[INFO] Loading emotion detection dataset variant " + str(variant_num) + ".")
    train_set = None
    dev_set = None
    test_set = None
    train_location = self.dataset_variants_location + "/" + str(variant_num) + self.train_dataset_suffix + ".csv"
    dev_location = self.dataset_variants_location + "/" + str(variant_num) + self.dev_dataset_suffix + ".csv"
    test_location = self.dataset_variants_location + "/" + str(variant_num) + self.test_dataset_suffix + ".csv"
    try:
      print("[DEBUG] Attempting to read dataset train file " + str(train_location) + ".")
      train_set = pd.read_csv(train_location)
      print("[DEBUG] Attempting to read dataset dev file " + str(dev_location) + ".")
      dev_set = pd.read_csv(dev_location)
      print("[DEBUG] Attempting to read dataset test file " + str(test_location) + ".")
      test_set = pd.read_csv(test_location)
    except Exception as e:
      print("[ERROR] Failed to read files " + str(train_location) + ", "+str(dev_location) + ", and "+str(test_location)+". Error:")
      print(e)
      return None, None, None

    print("[INFO] Train, Dev, and Test datasets loaded successfully.")
    return train_set, dev_set, test_set

  # Given a dataset variation number, execute a model training session.
  # Expects train and test dataframes. 
  #
  # We'll be using RoBERTa Large and fine-tuning it to produce the 
  # emotion categories we desire. 
  def train_model(self, model_num, variant_num, train_set, dev_set, test_set, use_cpu = False):
    print("[INFO] Beginning Emotion Detection training session with variant num " + str(variant_num) + " and model num "+str(model_num)+".")
    if train_set is None or dev_set is None or test_set is None:
      print("[ERROR] train_model recieved empty train/dev/test sets. Stopping...")
      return None
    print("[INFO] Utilizing Train set "  + str(train_set.shape) + ", Dev set " + str(dev_set.shape)+", and Test set " + str(test_set.shape) + ".")

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
      print("[INFO] GPU with CUDA successfully added.")
    else:
      print("[INFO] NOTE!! CPU is being utilized! Do not use this for proper training!")
      device = torch.device("cpu") # Use the CPU for better debugging messages. 

    # Grab roberta-large model + tokenizer from huggingface.
    print("[INFO] Obtaining RoBERTa-Large tokenizer.")
    tokenizer = AutoTokenizer.from_pretrained("roberta-large") 

    print("[INFO] Obtaining RoBERTa-Large config.")
    # Set the model's labels. Make sure the class numbers start with 0. 
    # If this is not present, you'll get the Target # is out of bounds
    # given then default RoBERTa model.
    config = AutoConfig.from_pretrained("roberta-large", num_labels=len(self.solution_string_map))

    print("[INFO] Obtaining RoBERTa-Large model.")
    model = AutoModelForSequenceClassification.from_pretrained("roberta-large", config=config)

    # Send the model to the GPU. 
    model.to(device)

    # Declare our optimizer, providing it the pretrained model's
    # parameters. 
    optimizer = AdamW(model.parameters(), lr=self.adam_learning_rate)

    # Encode the data, preparing the data for input into the model. 
    print("[INFO] Preparing train, dev, and test data for RoBERTa Large model via encoding.")
    sentences_train = train_set["text"]
    sentences_dev = dev_set["text"]
    sentences_test = test_set["text"]
    input_ids_train, attention_masks_train = self.train_model_encode_data(tokenizer, sentences_train)
    input_ids_dev, attention_masks_dev = self.train_model_encode_data(tokenizer, sentences_dev)
    input_ids_test, attention_masks_test = self.train_model_encode_data(tokenizer, sentences_test)

    # Mush everything together into length 3 tuples for the model.
    # (input id, attention mask, solutions)
    solutions_train = train_set["solution"].astype(int)
    solutions_dev = dev_set["solution"].astype(int)
    solutions_test = test_set["solution"].astype(int)
    features_train = (input_ids_train, attention_masks_train, solutions_train)
    features_dev = (input_ids_dev, attention_masks_dev, solutions_dev)
    features_test = (input_ids_test, attention_masks_test, solutions_test)

    # Place the created data into torch objects useful for training. 
    print("[INFO] Creating TensorDatasets and DataLoaders.")
    features_train_tensors = [torch.tensor(feature, dtype=torch.long) for feature in features_train]
    features_dev_tensors = [torch.tensor(feature, dtype=torch.long) for feature in features_dev]
    features_test_tensors = [torch.tensor(feature, dtype=torch.long) for feature in features_test]
    dataset_train = TensorDataset(*features_train_tensors)
    dataset_dev = TensorDataset(*features_dev_tensors)
    dataset_test = TensorDataset(*features_test_tensors)

    # Create DataLoaders from the datasets, first declaring Samplers. 
    sampler_train = RandomSampler(dataset_train)
    sampler_dev = SequentialSampler(dataset_dev)
    sampler_test = SequentialSampler(dataset_test)
    dataloader_train = DataLoader(dataset_train, sampler=sampler_train, batch_size=self.dataloader_batch_size)
    dataloader_dev = DataLoader(dataset_dev, sampler=sampler_dev, batch_size=self.dataloader_batch_size)
    dataloader_test = DataLoader(dataset_test, sampler=sampler_test, batch_size=self.dataloader_batch_size)

    # Now we're ready to train! We'll be doing this rather "manually",
    # fine-tuning the RoBERTa Large model for a number of epochs. 
    print("[INFO] Beginning training session.")
    train_loss_values = []
    dev_acc_values = []
    # TQDM - a fast, Extensible progress bar for Python and CLI. 
    # Pretty neat to use for this purpose. 
    #for epoch in tqdm(range(self.model_epochs), desc="Model epoch:"):
    for epoch in range(0, self.model_epochs):
      # For every epoch. 
      epoch_train_loss = 0
      # Set the model in training mode. 
      model.train()
      # Clear previously calculated gradients
      model.zero_grad()
      # Load the data from the train dataset using our dataloader
      # with the random sampler for each epoch. 
      #for step, batch in enumerate(dataloader_train):
      for step, batch in tqdm(enumerate(dataloader_train), desc="Epoch " +str(epoch+1) + "/" + str(self.model_epochs) + " Training", total=len(dataloader_train)):
        # For each batch of samples, predict the outputs.
        input_ids = batch[0].to(device)
        attention_masks = batch[1].to(device)
        labels = batch[2].to(device)
        # Get model predictions for the current batch.
        outputs = model(input_ids, attention_mask=attention_masks, labels=labels)

        # Calculate a step to take for optimizing the model. 
        loss = outputs[0]
        loss = loss / self.model_grad_acc_steps
        epoch_train_loss += loss.item()
        loss.backward()

        # Adjust the model every few steps.
        if (step+1) % self.model_grad_acc_steps == 0:
          torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
          optimizer.step()
          model.zero_grad()

      # Once all done iterating through all of the training data,
      # calculate the total loss and keep it for our records.
      train_loss = epoch_train_loss / len(dataloader_train)
      train_loss_values.append(train_loss)

      # Now that we've modified the model, let's use the dev set
      # to determine how good the model is at this point in time. 
      epoch_dev_acc = 0
      # Set the model in evaluation mode. 
      model.eval()
      for batch in tqdm(dataloader_dev, desc="Epoch " +str(epoch+1) + "/" + str(self.model_epochs) + " Dev Eval", total=len(dataloader_dev)):
        # For each batch of samples, predict the outputs. 
        input_ids = batch[0].to(device)
        attention_masks = batch[1].to(device)
        labels = batch[2]
        with torch.no_grad():
          outputs = model(input_ids, token_type_ids=None, attention_mask=attention_masks)

        # Given the outputs, calculate the accuracy. 
        logits = outputs[0]
        logits = logits.detach().cpu().numpy()
        predictions = np.argmax(logits, axis=1).flatten()
        labels = labels.numpy().flatten()
        # Accuracy is # correct / # labels. 
        epoch_dev_acc += np.sum(predictions == labels) / len(labels)
      
      # Once all done iterating through all of the dev data,
      # Calculate the total dev acc and keep it for our records. 
      epoch_dev_acc = epoch_dev_acc / len(dataloader_dev)
      dev_acc_values.append(epoch_dev_acc)

      # Each epoch, output the results. 
      print("Epoch: "+str(epoch+1)+" - Train Loss: " + str(train_loss) + " | Dev Acc: " + str(epoch_dev_acc)+ "\n")

    # Training routine complete! We've completed our fine-tuning and
    # should save the model. 
    print("[INFO] Training complete. Saving model " +str(model_num)+"...")
    self.save_model(model = model, tokenizer = tokenizer, model_num = model_num)

    # Now we should save our training history. 
    self.save_model_history(train_loss_values = train_loss_values, dev_acc_values = dev_acc_values, model_num = model_num)

    # TODO: Evaluate with test dataset. Perhaps this can be part
    # of another class that we can call independently? 

  # Encode the data into attention masks to let the model train.
  # Uses the RoBERTa Large tokenizer, which is in charge of
  # preparing the inputs for a model. 
  def train_model_encode_data(self, tokenizer, sentences):
    print("[DEBUG] Encoding a set of " + str(len(sentences)) + " sentences with RoBERTa Large's preprocessing tokenizer.")
    input_ids = []
    attention_masks = []
    # For each sentence, generate an input_id and an attention_mask.
    for sentence in sentences:
      encoded_data = tokenizer.encode_plus(
        sentence,
        max_length=self.max_seq_length, 
        padding = "max_length",
        truncation_strategy="longest_first",
        truncation=True)
      input_ids.append(encoded_data["input_ids"])
      attention_masks.append(encoded_data["attention_mask"])
    print("[DEBUG] Encoding complete: generated " + str(len(attention_masks)) + " attention masks.")
    return np.array(input_ids), np.array(attention_masks)

  # Saves the model in the self.model_variants_location under a 
  # subdirectory labeled with the provided model_num. Overwrites
  # any existing files in the folder if they exist. 
  def save_model(self, model, tokenizer, model_num):
    model_folder = self.model_variants_location + "/" + str(model_num)
    print("[INFO] Saving model " +str(model_num)+" at location: '" + model_folder + "'.")
    
    # Ensure the folders are there. 
    self.create_model_folder(model_folder=model_folder, model_num=model_num)

    print("[DEBUG] Saving pretrained model.")
    model.save_pretrained(model_folder)
    print("[DEBUG] Saving pretrained tokenizer.")
    tokenizer.save_pretrained(model_folder)

    print("[INFO] Model iteration " + str(model_num)+ " saved successfully!")

  # Given the training history of the model, save the information
  # in the same folder as the model under a subdirectory. 
  # 
  # Provide graphs as well as the raw lists just in case. 
  def save_model_history(self, train_loss_values, dev_acc_values, model_num):
    model_folder = self.model_variants_location + "/" + str(model_num)
    model_history_folder = model_folder + "/train_history"
    print("[INFO] Saving model training history at location: '" + model_folder + "'.")
    
    # Ensure the folders are there. 
    self.create_model_folder(model_folder=model_folder, model_num=model_num)

    # Create the training history subdirectory. 
    if not os.path.exists(model_history_folder):
      print("[INFO] Creating model history subfolder '" + model_history_folder + "'.")
      os.makedirs(model_history_folder)

    # Save the raw lists. 
    train_loss_values_file = model_history_folder + "/train_loss.txt"
    train_loss_graph_file = model_history_folder + "/train_loss" # Suffix will be added by plt.
    dev_acc_values_file = model_history_folder + "/dev_acc.txt"
    dev_acc_graph_file = model_history_folder + "/dev_acc" # Suffix will be added by plt.

    with open(train_loss_values_file, "w") as output_file:
      print("[DEBUG] Writing train loss values: '" + train_loss_values_file + "'.")
      output_file.write(str(train_loss_values))
      output_file.close()
    with open(dev_acc_values_file, "w") as output_file:
      print("[DEBUG] Writing dev acc values: '" + dev_acc_values_file + "'.")
      output_file.write(str(dev_acc_values))
      output_file.close()

    graph_width_inches = 13
    graph_height_inches = 7
    
    # Generate training loss graph. 
    fig = plt.figure(1)
    fig.suptitle("Training Loss Over Time")
    fig.set_size_inches(graph_width_inches,graph_height_inches)
    plt.plot(train_loss_values, label="train_loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.legend()
    plt.xticks(np.arange(0, self.model_epochs))
    # Save to file.
    print("[DEBUG] Writing train loss graph: '" + train_loss_graph_file + "'.")
    fig.savefig(train_loss_graph_file)
    plt.close("all")

    # Generate training dev accuracy graph. 
    fig = plt.figure(1)
    fig.suptitle("Dev Accuracy Over Time")
    fig.set_size_inches(graph_width_inches,graph_height_inches)
    plt.plot(dev_acc_values, label="dev_acc")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.xticks(np.arange(0, self.model_epochs))
    # Save to file. 
    print("[DEBUG] Writing dev acc graph: '" + dev_acc_graph_file + "'.")
    fig.savefig(dev_acc_graph_file)
    plt.close("all")

  # Guarantees that both the models directory and the model directory
  # are present. Push out messages for these cases separately for 
  # clarity's sake. 
  def create_model_folder(self, model_folder, model_num):
    # Determine if the models folder exists first. If it doesn't,
    # create it. 
    if not os.path.exists(self.model_variants_location):
      print("[INFO] Creating model variants folder '" + self.model_variants_location + "'.")
      os.makedirs(self.model_variants_location)
    
    # Determine of the model num folder exists. If it doesn't, 
    # create it. 
    if not os.path.exists(model_folder):
      print("[INFO] Creating model iteration " +str(model_num)+ " subfolder '" + model_folder + "'.")
      os.makedirs(model_folder)

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("variant_num")
  parser.add_argument("model_num")
  args = parser.parse_args()

  variant_num = args.variant_num
  model_num = args.model_num

  emotion_detection = EmotionDetectionHarness()
  emotion_detection.load_and_train_model(variant_num=variant_num, model_num=model_num)