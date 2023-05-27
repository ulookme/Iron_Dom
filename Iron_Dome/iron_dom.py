import math
import collections
import psutil
import time
import logging
import argparse
import os
import stat
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sklearn.preprocessing import StandardScaler
from joblib import load
import json

# Set up logging
logging.basicConfig(filename='/var/log/irondome/irondome.log', level=logging.INFO)

# List of processes known for their use of cryptographic functions
crypto_processes = ['openssl', 'gpg']

# Check if model and scaler exist and load
model_path = '/model/svm_model.joblib'
scaler_path = '/model/scaler.joblib'
model_exists = os.path.exists(model_path) and os.path.exists(scaler_path)
if model_exists:
    clf = load(model_path)
    scaler = load(scaler_path)

# Where to store the last_modified_times
last_modified_times_file = '/var/log/irondome/st_modified_times.json'

# Try to load the last_modified_times from the file
try:
    with open(last_modified_times_file, 'r') as f:
        file_content = f.read()
        if file_content:
            last_modified_times = json.loads(file_content)
        else:
            last_modified_times = {}
except FileNotFoundError:
    # If the file doesn't exist, start with an empty dictionary
    last_modified_times = {}

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global last_modified_times
        # Convert src_path to an absolute path
        absolute_path = os.path.abspath(event.src_path)
        # Ignore modifications to the log file
        if '/var/log/irondome/irondome.log' != absolute_path:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            last_modified_time = last_modified_times.get(absolute_path)
            if last_modified_time is None or last_modified_time != current_time:
                logging.info(f'{current_time}: File {absolute_path} has been modified')
                last_modified_times[absolute_path] = current_time
                # Save the updated last_modified_times to the file
                with open(last_modified_times_file, 'w') as f:
                    json.dump(last_modified_times, f)

# Monitor a folder for file changes
def monitor_folder(path):
    observer = Observer()
    observer.schedule(MyHandler(), path=path, recursive=True)
    observer.start()
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    logging.info(f'{current_time}: Monitoring directory: {path}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def monitor_path(path):
    original_permissions = stat.S_IMODE(os.lstat(path).st_mode)
    change_permissions(path, 0o777)  # Change permissions to allow read access
    if is_encrypted(path):
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        logging.warning(f'{current_time}: File {path} appears to be encrypted')
    change_permissions(path, original_permissions)  # Restore original permissions
    monitor_thread = threading.Thread(target=monitor_folder, args=(path,))
    monitor_thread.start()
    while True:
        monitor_crypto_activity()
        detect_entropy_change(path)
        make_prediction()  # Make predictions if model exists
        time.sleep(1)

# Collect system stats
def collect_system_stats():
    cpu_percent = psutil.cpu_percent()
    disk_io = psutil.disk_io_counters()
    read_count = disk_io.read_count
    write_count = disk_io.write_count

    return [cpu_percent, read_count, write_count]

# Make a prediction
def make_prediction():
    if model_exists:
        # Collect the system stats
        system_stats = collect_system_stats()
        
        # Log the system stats
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        logging.info(f'{current_time}: System stats: CPU={system_stats[0]}, Read Count={system_stats[1]}, Write Count={system_stats[2]}')

        # Scale the data
        X = scaler.transform([system_stats])

        # Make a prediction
        prediction = clf.predict(X)

        # Log the prediction
        logging.info(f'{current_time}: Prediction: {prediction}')
        if prediction[0] == 1:
            logging.warning(f'{current_time}: Anomaly detected!')
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in crypto_processes:
                    logging.info(f'{current_time}: Anomalous process: {proc.info["name"]}')
                    proc.terminate()
                    logging.info(f'{current_time}: Process {proc.info["name"]} terminated')

        # Wait for 1 second before the next prediction
        time.sleep(1)

# Monitor the system for cryptographic activity
def monitor_crypto_activity():
    for proc in psutil.process_iter(['name', 'open_files']):
        if proc.info['name'] in crypto_processes:
            cpu_percent = proc.cpu_percent()
            if cpu_percent > 50:  # If CPU usage is more than 50%
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                logging.warning(f'{current_time}: High CPU usage detected by process {proc.info["name"]}: {cpu_percent}%')
                # Log the files opened by the process
                try:
                    for file in proc.info['open_files']:
                        logging.info(f'{current_time}: File opened by {proc.info["name"]}: {file.path}')
                except psutil.AccessDenied:
                    logging.error(f'{current_time}: Access denied when trying to get the files opened by the process')

# Calculate the entropy of a file
def calculate_entropy(file_path):
    try:
        with open(file_path, 'rb') as f:
            byte_counts = collections.Counter(f.read())
            entropy = 0.0
            total = sum(byte_counts.values())
            for count in byte_counts.values():
                # Calculate the probability
                p_x = count / total
                entropy += - p_x * math.log2(p_x)
        return entropy
    except Exception as e:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        logging.error(f'{current_time}: Error calculating entropy for {file_path}: {str(e)}')
        return None

# Keep track of the entropy of each file
file_entropies = {}

# Detect significant changes in file entropy
def detect_entropy_change(path):
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            new_entropy = calculate_entropy(file_path)
            if new_entropy is not None:
                old_entropy = file_entropies.get(file_path)
                if old_entropy is not None and abs(new_entropy - old_entropy) > 0.01:  # If entropy change is significant
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                    logging.warning(f'{current_time}: Entropy of file {file_path} changed from {old_entropy} to {new_entropy}')
                file_entropies[file_path] = new_entropy

# Check if the current user is root
def is_root():
    return os.getuid() == 0

# Change the permissions of a file or directory
def change_permissions(path, mode):
    try:
        os.chmod(path, mode)
    except Exception as e:
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        logging.error(f'{current_time}: Error changing permissions for {path}: {str(e)}')

# Check if a file is encrypted
def is_encrypted(path):
    entropy = calculate_entropy(path)
    if entropy is not None:
        return entropy > 7.5  # If the entropy is above 7.5, the file is likely encrypted
    else:
        return False

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("paths", nargs='+', help="The paths to the directories or files to monitor")
args = parser.parse_args()

# Check if the current user is root
if not is_root():
    print("This program must be run as root")
    exit(1)

# Monitor the specified paths
for path in args.paths:
    monitor_path(path)