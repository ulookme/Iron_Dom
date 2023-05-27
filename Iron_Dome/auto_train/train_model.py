import os
import pandas as pd
import psutil
import schedule
import time
import threading
from sklearn import svm
from sklearn.preprocessing import StandardScaler
from joblib import dump

# Check if a process is running
def is_running(script_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == script_name:
            return True
    return False

#print("Current working directory:", os.getcwd())

# Function to load data and train the model
def train_model():
    #print("Attempting to train model...")
    # Check if the data file exists
    data_file = 'data/system_stats.csv'
    if not os.path.exists(data_file):
        print(f'Data file {data_file} does not exist.')
        return

    # Load the data
    df = pd.read_csv(data_file, sep=',')
    #print(f'Data loaded from {data_file}:\n{df}')
    # Preprocess the data
    scaler = StandardScaler()
    X = scaler.fit_transform(df[['cpu_percent', 'read_count', 'write_count']])

    # Train a One-Class SVM model
    clf = svm.OneClassSVM(nu=0.1, kernel="rbf", gamma=0.1)
    clf.fit(X)

    # Save the model
    dump(clf, 'model/svm_model.joblib')
    # Save the scaler
    dump(scaler, 'model/scaler.joblib')
    #print('Model and scaler trained and saved.')

# Function to start the training as soon as collect_stats.py is running
def start_training_when_ready():
    while not is_running('collect_stats.py'):
        time.sleep(1)  # Wait for 1 second
    train_model()

# Start the initial training in a separate thread when collect_stats.py is running
threading.Thread(target=start_training_when_ready).start()

# Train the model initially
train_model()

# Schedule the model to be retrained every three days
schedule.every(3).days.at("00:00").do(train_model)

while True:
    schedule.run_pending()
    time.sleep(1)