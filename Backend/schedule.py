import schedule
import time
import subprocess

def job():
    print("Running mailing.py script...")
    subprocess.run(["python", "mailing.py"])

schedule.every(12).hours.do(job)

print("Scheduler started. Running mailing.py every 12 hours.")

while True:
    schedule.run_pending()
    time.sleep(1)
