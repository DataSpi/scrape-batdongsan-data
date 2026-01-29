import logging
import time
from dotenv import load_dotenv
import os
import platform
import shutil
import subprocess

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def load_env():
    load_dotenv()
    return os.environ

def prevent_sleep():
    system = platform.system().lower()
    if system == "darwin" and shutil.which("caffeinate"):
        return subprocess.Popen(["caffeinate"])
    if system == "linux" and shutil.which("systemd-inhibit"):
        proc = subprocess.Popen(
            [
                "systemd-inhibit",
                "--what=sleep",
                "--why=Scraping",
                "--mode=block",
                "sleep",
                "infinity"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(0.2)
        if proc.poll() is not None:
            logging.getLogger(__name__).warning("Sleep prevention not available (systemd-inhibit denied).")
            return None
        return proc
    logging.getLogger(__name__).warning("Sleep prevention not available on this system.")
    return None

def stop_sleep(proc):
    if proc:
        proc.terminate()

def format_worksheet(worksheet):
    worksheet.spreadsheet.batch_update({
        "requests": [
            # Resize column F
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 5,
                        "endIndex": 6
                    },
                    "properties": {"pixelSize": 500},
                    "fields": "pixelSize"
                }
            },
            # Resize column A & B
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": 2
                    },
                    "properties": {"pixelSize": 500},
                    "fields": "pixelSize"
                }
            },
            # Resize image column
            {
                "updateDimensionProperties": {
                    "range": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 10,
                        "endIndex": 20
                    },
                    "properties": {"pixelSize": 200},
                    "fields": "pixelSize"
                }
            },
            # Enable text wrapping
            {
                "repeatCell": {
                    "range": {
                        "sheetId": worksheet.id,
                        "startColumnIndex": 0,
                        "endColumnIndex": 20
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP"
                        }
                    },
                    "fields": "userEnteredFormat.wrapStrategy"
                }
            }
        ]
    })

# prevent_sleep()