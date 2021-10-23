#
# evaluate_model.py
#
# Given a dataset iteration number and and model parameters,
# execute 10-fold cross validation to observe performance. 

import argparse
import numpy as np

# Model declaration
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Activation, Dropout, Input, Conv1D, TimeDistributed, GRU, BatchNormalization
from tensorflow.keras.optimizers import Adam

# Model validation
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import KFold, cross_val_score

Tx = 5511 # The number of time steps input to the model from the spectrogram
n_freq = 101 # Number of frequencies input to the model at each time step of the spectrogram
Ty = 1375 # The number of time steps in the output of our model

learning_rate = 0.0001 # A healthy learning rate. 
loss_function = 'binary_crossentropy'
epochs = 20
batch_size=32 # In general, 32 is a good starting point, then try 64, 128, 256. Smaller but not too small is optimal for accuracy. 
validation_split = 0.2
opt = Adam(learning_rate=learning_rate)
verbose = True

# Given the iternum, load a model. 
def main(iternum):
  print("[INFO] Starting evaluate_model procedure with iternum " + str(iternum) + "...")

  # What we output for the model to use. 
  final_x = None
  final_y = None

  print("[INFO] Loading existing dataset file ./XY_train/X_"+str(iternum)+".npy...")
  final_x = np.load("./XY_train/X_"+str(iternum)+".npy")
  print("[INFO] Loading existing dataset file ./XY_train/Y_"+str(iternum)+".npy...")
  final_y = np.load("./XY_train/Y_"+str(iternum)+".npy")
  print("[DEBUG] final_x.shape is:", final_x.shape)  
  print("[DEBUG] final_y.shape is:", final_y.shape)

  if final_x is not None and final_y is not None:
    print("[INFO] Beginning evaluation... ")
    kfold = KFold(n_splits=10, shuffle=True)

    # TODO: Getting an error for an incorrect y shape? Not sure why. 
    results = cross_val_score(KerasClassifier(build_fn=model_fn, epochs=epochs, batch_size=batch_size, validation_split=validation_split, shuffle=True, verbose=verbose), final_x, final_y, cv=kfold)
    print("[INFO] Execution complete! Results: %.2f (%.2f)" % (results.mean()*100,results.std()*100))

  else:
    print("[ERROR] datasets x and/or y was None! Execution failed.")

def model_fn():
  model = define_model(input_shape = (Tx, n_freq))
  model.summary()
  model.compile(loss=loss_function, optimizers=opt, metrics=["accuracy"])
  return model

# TODO: We've copied over model declaration, but ideally we'd 
# have this in a class to share between the two files. 
def define_model(input_shape):
    """
    Function creating the model's graph in Keras.
    
    Argument:
    input_shape -- shape of the model's input data (using Keras conventions)

    Returns:
    model -- Keras model instance
    """
    
    X_input = Input(shape = input_shape)
    
    # Step 1: CONV layer (≈4 lines)
    X = Conv1D(196, kernel_size=15, strides=4)(X_input)                                 # CONV1D
    X = BatchNormalization()(X)                                 # Batch normalization
    X = Activation('relu')(X)                                 # ReLu activation
    X = Dropout(0.8)(X)                                 # dropout (use 0.8).
    # TODO note: changed all dropouts from 0.8 to 0.5

    # Step 2: First GRU Layer (≈4 lines)
    X = GRU(units = 128, return_sequences = True)(X) # GRU (use 128 units and return the sequences)
    X = Dropout(0.8)(X)                                 # dropout (use 0.8)
    X = BatchNormalization()(X)                                 # Batch normalization
    
    # Step 3: Second GRU Layer (≈4 lines)
    X = GRU(units = 128, return_sequences = True)(X)   # GRU (use 128 units and return the sequences)
    X = Dropout(0.8)(X)                                 # dropout (use 0.8)
    X = BatchNormalization()(X)                                  # Batch normalization
    X = Dropout(0.8)(X)                                  # dropout (use 0.8)
    
    # Step 4: Time-distributed dense layer (≈1 line)
    X = TimeDistributed(Dense(1, activation = "sigmoid"))(X) # time distributed  (sigmoid)

    model = Model(inputs = X_input, outputs = X)
    
    return model 

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument('iternum')
  args = parser.parse_args()

  iternum = int(args.iternum)

  main(iternum)