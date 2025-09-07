import logging
from dotenv import load_dotenv
import os

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
    import subprocess
    return subprocess.Popen(['caffeinate'])

def stop_sleep(proc):
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
