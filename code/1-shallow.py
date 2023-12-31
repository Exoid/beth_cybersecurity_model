import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve

# Hyperparameters and dataset size definition
dataset_size = 8000
split_percent = int(dataset_size * 0.2)

#SVM
C = 1.0
kernel = 'rbf'
defined_consecute_observations = 50

# Load the datasets
columns_to_use = ["processId", "parentProcessId", "userId", "mountNamespace", "eventId", "argsNum", "returnValue", "sus"] # "evil"
train_data = pd.read_csv('../labelled_training_data.csv', usecols=columns_to_use, nrows=dataset_size)
val_data = pd.read_csv('../labelled_validation_data.csv', usecols=columns_to_use, nrows=split_percent)
test_data = pd.read_csv('../labelled_testing_data.csv', usecols=columns_to_use, nrows=split_percent)

# Define a function for preprocessing
def preprocess(data):
    data["processId"] = data["processId"].map(lambda x: 1 if x in [0, 1, 2] else 0)
    data["parentProcessId"] = data["parentProcessId"].map(lambda x: 1 if x in [0, 1, 2] else 0)
    data["userId"] = data["userId"].map(lambda x: 0 if x < 1000 else 1)
    data["mountNamespace"] = data["mountNamespace"].map(lambda x: 0 if x == 4026531840 else 1)
    data["eventId"] = data["eventId"]
    data['returnValue'] = data['returnValue'].map(lambda x: -1 if x < 0 else (0 if x == 0 else 1))

    # Apply label encoding for specific columns that are not numerical
    le = LabelEncoder()
    columns_to_encode = ['sus', 'eventId', 'argsNum'] #'evil', 
    for column in columns_to_encode:
        data[column] = le.fit_transform(data[column])

    return data

# Function to convert DataFrames to sequences
def df_to_sequences(data):
    sequences = [data[i-defined_consecute_observations:i].values for i in range(defined_consecute_observations, len(data))]
    X = np.array([seq.reshape(-1) for seq in sequences])
    y = data['sus'][defined_consecute_observations:].values
    return X, y

# Preprocess the datasets
train_data = preprocess(train_data)
val_data = preprocess(val_data)
test_data = preprocess(test_data)

# Convert DataFrames to sequences
X_train, y_train = df_to_sequences(train_data)
X_val, y_val = df_to_sequences(val_data)
X_test, y_test = df_to_sequences(test_data)

# Define the SVM model
model_svm = SVC(kernel=kernel, C=C, probability=True, random_state=42, verbose=False)

# Train the SVM model
model_svm.fit(X_train, y_train)

# Get probabilities instead of predicted labels, for AUROC calculation
svm_test_proba = model_svm.predict_proba(X_test)[:, 1]

# Calculate AUROC
svm_test_auc = roc_auc_score(y_test, svm_test_proba)
print(f"SVM Test AUROC: {svm_test_auc}")

# Calculate ROC curve points
svm_test_fpr, svm_test_tpr, _ = roc_curve(y_test, svm_test_proba)

# Plot the ROC curve for the testing set
plt.figure(figsize=(10,6))
plt.plot(svm_test_fpr, svm_test_tpr, label=f'SVM Test (AUROC = {svm_test_auc:.3f})')
plt.plot([0,1], [0,1], color='navy', linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.show()