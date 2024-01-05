import numpy as np #type: ignore
import tensorflow as tf #type: ignore
from tensorflow import keras #type: ignore

flag_text = "hrsCTF{sp00ky}"
flag_encoded = [ord(char) for char in flag_text]

model = keras.Sequential([
    keras.layers.Input(shape=(len(flag_encoded),)),
    keras.layers.Dense(14, activation='relu'),
    keras.layers.Dense(1)
])

model.layers[1].set_weights([np.array([flag_encoded], dtype=np.float32).T, np.array([0.0])])
