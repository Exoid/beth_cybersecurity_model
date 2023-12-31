import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, GRU
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder

# Load the datasets
columns_to_use = ["processId", "parentProcessId", "userId", "mountNamespace", "eventId", "argsNum", "returnValue", "sus"]
train_data = pd.read_csv('../labelled_training_data.csv', usecols=columns_to_use, nrows=8000)
val_data = pd.read_csv('../labelled_validation_data.csv', usecols=columns_to_use, nrows=2000)
test_data = pd.read_csv('../labelled_testing_data.csv', usecols=columns_to_use, nrows=2000)

# Define a function for preprocessing
def preprocess(data):
    data["processId"] = data["processId"].map(lambda x: 0 if x in [0, 1, 2] else 1)
    data["parentProcessId"] = data["parentProcessId"].map(lambda x: 0 if x in [0, 1, 2] else 1)
    data["userId"] = data["userId"].map(lambda x: 0 if x < 1000 else 1)
    data["mountNamespace"] = data["mountNamespace"].map(lambda x: 0 if x == 4026531840 else 1)
    data["eventId"] = data["eventId"]
    data["returnValue"] = data["returnValue"].map(lambda x: 0 if x == 0 else (1 if x > 0 else 2))

    # Apply label encoding for specific columns that are not numerical
    le = LabelEncoder()
    columns_to_encode = ['sus', 'eventId', 'argsNum']
    for column in columns_to_encode:
        data[column] = le.fit_transform(data[column])

    # Normalize 'eventId' and 'argsNum'
    scaler = MinMaxScaler()
    data[['eventId', 'argsNum']] = scaler.fit_transform(data[['eventId', 'argsNum']])
    
    return data

# Preprocess the datasets
train_data = preprocess(train_data)
val_data = preprocess(val_data)
test_data = preprocess(test_data)

# Convert DataFrames to sequences
def df_to_sequences(data):
    sequences = [data[i-50:i].values for i in range(50, len(data))]
    X = pad_sequences(sequences)
    y = data['sus'][50:]
    return X, y

X_train, y_train = df_to_sequences(train_data)
X_val, y_val = df_to_sequences(val_data)
X_test, y_test = df_to_sequences(test_data)

# Define the LSTM model
model_lstm = Sequential()
model_lstm.add(LSTM(50, input_shape=(X_train.shape[1], X_train.shape[2])))
model_lstm.add(Dense(1, activation='sigmoid'))
model_lstm.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# Train the LSTM model
history_lstm = model_lstm.fit(X_train, y_train, epochs=10, validation_data=(X_val, y_val))

# Define the GRU model
model_gru = Sequential()
model_gru.add(GRU(50, input_shape=(X_train.shape[1], X_train.shape[2])))
model_gru.add(Dense(1, activation='sigmoid'))
model_gru.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# Train the GRU model
history_gru = model_gru.fit(X_train, y_train, epochs=10, validation_data=(X_val, y_val))

# Plot LSTM accuracy
plt.figure(figsize=(12,6))
plt.plot(history_lstm.history['accuracy'])
plt.plot(history_lstm.history['val_accuracy'])
plt.title('LSTM Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend(['Train', 'Validation'])
plt.show()

# Plot GRU accuracy
plt.figure(figsize=(12,6))
plt.plot(history_gru.history['accuracy'])
plt.plot(history_gru.history['val_accuracy'])
plt.title('GRU Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend(['Train', 'Validation'])
plt.show()

# Evaluate LSTM model
lstm_results = model_lstm.evaluate(X_test, y_test)
print(f"LSTM Test Loss: {lstm_results[0]}, LSTM Test Accuracy: {lstm_results[1]}")

# Evaluate GRU model
gru_results = model_gru.evaluate(X_test, y_test)
print(f"GRU Test Loss: {gru_results[0]}, GRU Test Accuracy: {gru_results[1]}")

