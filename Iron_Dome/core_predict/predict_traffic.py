import os
import pandas as pd
import psutil
import time
from sklearn.preprocessing import StandardScaler
from joblib import load

# Load the model
clf = load('/model/svm_model.joblib')

# Preprocess the data
scaler = StandardScaler()

# Collect system stats
def collect_system_stats():
    cpu_percent = psutil.cpu_percent()
    disk_io = psutil.disk_io_counters()
    read_count = disk_io.read_count
    write_count = disk_io.write_count

    return [cpu_percent, read_count, write_count]

while True:
    # Collect the system stats
    system_stats = collect_system_stats()

    # Scale the data
    X = scaler.transform([system_stats])

    # Make a prediction
    prediction = clf.predict(X)

    # Print the prediction
    print(f'Prediction: {prediction}')

    # Wait for 1 second before the next prediction
    time.sleep(1)