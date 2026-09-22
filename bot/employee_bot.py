import csv
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "employees.csv"
APP_FILE = ROOT / "app" / "employee_app.html"


def load_employees():
    with open(DATA_FILE, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def human_pause(seconds=1):
    time.sleep(seconds)


def run_bot():

    employees = load_employees()

    print(f"Loaded {len(employees)} employees")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=300
        )

        page = browser.new_page()

        print("Opening employee application...")
        page.goto(APP_FILE.as_uri())

        human_pause(2)

        for employee in employees:

            print(f"\nProcessing {employee['Name']}")

            # HUMAN ACTION 1
            print("→ Looking for Name field")
            page.locator("#name").click()
            human_pause(1)

            # HUMAN ACTION 2
            print(f"→ Typing name: {employee['Name']}")
            page.locator("#name").fill(employee["Name"])
            human_pause(1)

            # HUMAN ACTION 3
            print("→ Selecting department")
            page.locator("#department").click()
            human_pause(0.5)

            page.locator("#department").select_option(
                label=employee["Department"]
            )
            human_pause(1)

            # HUMAN ACTION 4
            print(f"→ Typing location: {employee['Location']}")
            page.locator("#location").click()
            page.locator("#location").fill(employee["Location"])
            human_pause(1)

            # HUMAN ACTION 5
            print(f"→ Typing email: {employee['Email']}")
            page.locator("#email").click()
            page.locator("#email").fill(employee["Email"])
            human_pause(1)

            # HUMAN ACTION 6
            print("→ Clicking Add Employee")
            page.locator("#addEmployee").click()

            human_pause(2)

            # VERIFY
            status = page.locator("#status").inner_text()

            print(f"→ Application response: {status}")

            expected = (
                f"Employee {employee['Name']} added successfully."
            )

            if status != expected:
                raise RuntimeError(
                    f"Unexpected application response: {status}"
                )

            print(f"✓ {employee['Name']} successfully processed")

            human_pause(2)

        print("\n================================")
        print("RPA PROCESS COMPLETED")
        print("================================")

        input("\nPress ENTER to close the browser...")

        browser.close()


if __name__ == "__main__":
    run_bot()