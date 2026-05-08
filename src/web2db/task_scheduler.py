from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
from utils.common_tools import setup_logging
logger = setup_logging("task_scheduler")

""" 
This is a local job runner since the website block the IP of 
github actions so it can not run the on github. 
"""

def run_job():
    python_exe = r"C:\Users\LAP14354\miniconda3\envs\bds_scraper\python.exe"
    project_root = r"D:\scrape-batdongsan-data"

    try:
        logger.info(f"Starting subprocess at {project_root}...")
        subprocess.run(
            [python_exe, "-m", "src.web2db.request_html"],
            cwd=project_root,  # CRITICAL: This tells Python where 'src' is
            check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess failed with error: {e}")
    except FileNotFoundError:
        logger.error(f"ERROR: Could not find python.exe at {python_exe}")


scheduler = BlockingScheduler()
trigger = CronTrigger.from_crontab('0 9 * * 1') # every Monday at 9:00 AM
scheduler.add_job(run_job, trigger)


# Pro-tip: Run it once immediately so you don't have to wait 60 seconds for the first test
run_job()
logger.info("Scheduler started... (Running every Monday at 9:00 AM. Press Ctrl+C to stop)")
try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    logger.info("Scheduler stopped.")