from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import os
from utils.common_tools import setup_logging
logger = setup_logging()

""" 
This is a local job runner since the website block the IP of 
github actions so it can not run the on github. 
"""

def run_job(url):
    python_exe = r"C:\Users\LAP14354\miniconda3\envs\bds_scraper\python.exe"
    project_root = r"D:\scrape-batdongsan-data"

    custom_env = os.environ.copy()
    custom_env["URL"] = url

    try:
        logger.info(f"Starting subprocess at {project_root}...")
        subprocess.run(
            [python_exe, "-m", "src.web2db.request_html"],
            cwd=project_root,  # CRITICAL: This tells Python where 'src' is
            check=True, 
            env=custom_env  
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess failed with error: {e}")
    except FileNotFoundError:
        logger.error(f"ERROR: Could not find python.exe at {python_exe}")

def main():
    scheduler = BlockingScheduler()

    jobs = [
        ("https://batdongsan.com.vn/ban-can-ho-chung-cu-trellia-cove", '0 9 * * 1'),
        ("https://batdongsan.com.vn/ban-can-ho-chung-cu-ehomes-nam-sai-gon", '3 9 * * 1'),
    ]

    for url, cron_expr in jobs:
        trigger = CronTrigger.from_crontab(cron_expr)
        scheduler.add_job(run_job, trigger, args=[url])
        logger.info(f"Running immediate test job for: {url}")
        run_job(url)

    logger.info("Scheduler started... (Running every Monday at 9:00/9:03 AM. Press Ctrl+C to stop)")
    scheduler.start()


if __name__ == "__main__":
    main()