import schedule
import time
import csv
import psutil
import os
import glob

def write_data(filename, data, write_header=False):
    # Vérifiez si vous avez les autorisations d'écriture
    if os.access(os.path.dirname(filename), os.W_OK):
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['cpu_percent', 'read_count', 'write_count'])  # Écrire l'en-tête
            writer.writerow(data)
    else:
        print(f"Cannot write to {filename}. Check your write permissions.")

def collect_system_stats():
    # Préparez le nom du fichier CSV
    filename = 'data/system_stats.csv'

    # Si le fichier n'existe pas, écrire l'en-tête
    if not os.path.isfile(filename):
        write_data(filename, [], write_header=True)

    # Collecter des statistiques toutes les 0,5 secondes pendant environ 3 jours (259200 secondes)
    collect_stats(filename, 0.5, 259200)

def collect_stats(filename, interval, duration):
    iterations = int(duration / interval)

    for _ in range(iterations):
        cpu_percent = psutil.cpu_percent()
        disk_io = psutil.disk_io_counters()
        read_count = disk_io.read_count
        write_count = disk_io.write_count
        write_data(filename, [cpu_percent, read_count, write_count])
        time.sleep(interval)

def delete_old_csv():
    # Supprimer l'ancien fichier CSV, s'il existe
    old_files = glob.glob('data/system_stats.csv')
    for old_file in old_files:
        os.remove(old_file)

# Créer le répertoire 'data' s'il n'existe pas
os.makedirs('data', exist_ok=True)

# Première exécution immédiate
collect_system_stats()

# Planifier la suppression du fichier CSV et la collecte de nouvelles statistiques tous les 3 jours à 00:00
schedule.every(3).days.at("00:38").do(delete_old_csv)
schedule.every(3).days.at("00:38").do(collect_system_stats)

while True:
    # Exécuter les tâches planifiées
    schedule.run_pending()
    time.sleep(1)