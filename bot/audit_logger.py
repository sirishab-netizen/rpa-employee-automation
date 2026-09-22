import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

LOG_FILE = ROOT / "logs" / "rpa_audit.csv"


def initialize_log():

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not LOG_FILE.exists():

        with open(
            LOG_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "employee",
                "status",
                "details"
            ])


def log_event(
    employee,
    status,
    details
):

    initialize_log()

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            timestamp,
            employee,
            status,
            details
        ])