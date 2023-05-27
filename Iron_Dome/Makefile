.PHONY: all environment install-requirements create-log run-irondome run-all run_all_programme kill-all

PYTHON := /home/neural/cyber-env/bin/python3

all: environment install-requirements create-log run-all

environment:
	@echo "Creating Python virtual environment..."
	python3 -m venv cyber-env
	@echo "Python virtual environment created successfully."

install-requirements:
	@echo "Activating Python virtual environment and installing requirements..."
	. ./cyber-env/bin/activate; pip install -r requirements.txt
	@echo "Requirements installed successfully."

create-log:
	@echo "Creating log directory and file..."
	mkdir -p /var/log/irondome/
	touch /var/log/irondome/irondome.log
	sudo chown -R $$USER:$$USER /var/log/irondome/
	@echo "Log directory and file created successfully."



run-irondome: create-log install-requirements
	@echo "Running Iron Dome..."
	sudo $(PYTHON) iron_dom.py /var/log /home/neural/Iron_Dome/ &

run_collect_stats:
	@echo "Running collect_stats.py..."
	sudo $(PYTHON) /home/neural/Iron_Dome/auto_train/collect_stats.py 

run_train_model:
	@echo "Running train_model.py..."
	sudo $(PYTHON) /home/neural/Iron_Dome/auto_train/train_model.py

run-all: run-irondome run_collect_stats run_train_model
	@echo "All programs are running"

run-all-independ:
	@echo "Running all programs..." 
	@echo "Running collect_stats.py..."
	sudo $(PYTHON) /home/neural/Iron_Dome/auto_train/collect_stats.py &
	@echo "Running train_model.py..."
	sudo $(PYTHON) /home/neural/Iron_Dome/auto_train/train_model.py &
	@echo "Pausing for 5 minutes before running Iron Dome..."
	@sleep 300
	@echo "Running Iron Dome..."
	sudo $(PYTHON) iron_dom.py /var/log/ /home/neural/Iron_Dome/ &
	@echo "All programs are running"


kill-all:
	@echo "Killing all processes..."
	sudo pkill -f iron_dom.py
	sudo pkill -f collect_stats.py
	sudo pkill -f train_model.py
	@echo "All processes have been killed."



help:
	@echo "Available targets:"
	@echo "  all: Create environment, install requirements, create log, and run all programs"
	@echo "  environment: Create Python virtual environment"
	@echo "  install-requirements: Activate virtual environment and install requirements"
	@echo "  create-log: Create log directory and file"
	@echo "  run-irondome: Run Iron Dome program"
	@echo "  run-all: Run all programs"
	@echo "  run-all-independ:: Run all programs for you "
	@echo "  kill-all:: KILL all process in sudo"
	@echo "  help: Display this help message"
	@echo "  read-log: Read activities from the log"

read-log:
	@echo "Reading activities from the log..."
	@sudo cat /var/log/irondome/irondome.log

read-log_real_time:
	@echo "Reading activities real time"	
	@sudo tail -f /var/log/irondome/irondome.log