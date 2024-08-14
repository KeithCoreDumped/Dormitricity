import csv
from datetime import datetime

log_file = "log.csv"

def log_run():
    with open(log_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now()])

if __name__ == "__main__":
    log_run()