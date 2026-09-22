import csv
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from validator import validate_employee
from audit_logger import log_event


# =========================================================
# PROJECT PATHS
# =========================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = ROOT / "data" / "employees.csv"
APP_FILE = ROOT / "app" / "employee_app.html"


# =========================================================
# CONFIGURATION
# =========================================================

# Delay between actions so we can visually observe the bot
ACTION_DELAY = 1

# Playwright delay between browser actions
BROWSER_SLOW_MO = 300


# =========================================================
# LOAD EMPLOYEE DATA
# =========================================================

def load_employees():

    with open(
        DATA_FILE,
        newline="",
        encoding="utf-8"
    ) as file:

        return list(csv.DictReader(file))


# =========================================================
# HUMAN-LIKE PAUSE
# =========================================================

def human_pause(seconds=ACTION_DELAY):

    time.sleep(seconds)


# =========================================================
# MAIN RPA WORKFLOW
# =========================================================

def run_bot():

    employees = load_employees()

    print("=" * 60)
    print("RPA EMPLOYEE DATA ENTRY BOT")
    print("=" * 60)

    print(f"Loaded {len(employees)} employee records")

    # Counters
    successful = 0
    business_exceptions = 0
    system_exceptions = 0

    # -----------------------------------------------------
    # START BROWSER
    # -----------------------------------------------------

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            slow_mo=BROWSER_SLOW_MO
        )

        page = browser.new_page()

        try:

            # =================================================
            # OPEN APPLICATION
            # =================================================

            print("\nOpening Employee Management application...")

            page.goto(
                APP_FILE.as_uri(),
                wait_until="domcontentloaded"
            )

            human_pause(2)

            print("Application opened successfully.")

            # =================================================
            # PROCESS EACH EMPLOYEE
            # =================================================

            for employee in employees:

                name = employee.get(
                    "Name",
                    ""
                ).strip()

                print("\n" + "-" * 60)
                print(f"Processing: {name}")
                print("-" * 60)

                # =================================================
                # STEP 1 — BUSINESS VALIDATION
                # =================================================

                errors = validate_employee(
                    employee
                )

                if errors:

                    business_exceptions += 1

                    details = "; ".join(errors)

                    print(
                        "❌ BUSINESS EXCEPTION"
                    )

                    print(
                        f"Employee: {name}"
                    )

                    for error in errors:

                        print(
                            f"   - {error}"
                        )

                    # Write exception to audit log
                    log_event(
                        employee=name,
                        status="BUSINESS_EXCEPTION",
                        details=details
                    )

                    print(
                        "Skipping this employee."
                    )

                    continue

                # =================================================
                # STEP 2 — UI AUTOMATION
                # =================================================

                try:

                    # -------------------------------------------------
                    # NAME
                    # -------------------------------------------------

                    print(
                        "→ Clicking Name field"
                    )

                    page.locator(
                        "#name"
                    ).click()

                    human_pause()

                    print(
                        f"→ Entering Name: "
                        f"{employee['Name']}"
                    )

                    page.locator(
                        "#name"
                    ).fill(
                        employee["Name"]
                    )

                    human_pause()

                    # -------------------------------------------------
                    # DEPARTMENT
                    # -------------------------------------------------

                    print(
                        "→ Selecting Department"
                    )

                    page.locator(
                        "#department"
                    ).click()

                    human_pause(0.5)

                    page.locator(
                        "#department"
                    ).select_option(
                        label=employee["Department"]
                    )

                    human_pause()

                    # -------------------------------------------------
                    # LOCATION
                    # -------------------------------------------------

                    print(
                        f"→ Entering Location: "
                        f"{employee['Location']}"
                    )

                    page.locator(
                        "#location"
                    ).click()

                    human_pause(0.5)

                    page.locator(
                        "#location"
                    ).fill(
                        employee["Location"]
                    )

                    human_pause()

                    # -------------------------------------------------
                    # EMAIL
                    # -------------------------------------------------

                    print(
                        f"→ Entering Email: "
                        f"{employee['Email']}"
                    )

                    page.locator(
                        "#email"
                    ).click()

                    human_pause(0.5)

                    page.locator(
                        "#email"
                    ).fill(
                        employee["Email"]
                    )

                    human_pause()

                    # =================================================
                    # STEP 3 — SUBMIT
                    # =================================================

                    print(
                        "→ Clicking Add Employee"
                    )

                    page.locator(
                        "#addEmployee"
                    ).click()

                    human_pause(2)

                    # =================================================
                    # STEP 4 — VERIFY RESULT
                    # =================================================

                    status = page.locator(
                        "#status"
                    ).inner_text()

                    print(
                        f"→ Application response: "
                        f"{status}"
                    )

                    expected = (
                        f"Employee "
                        f"{employee['Name']} "
                        f"added successfully."
                    )

                    if status != expected:

                        raise RuntimeError(
                            "Unexpected application "
                            f"response: {status}"
                        )

                    # =================================================
                    # STEP 5 — SUCCESS
                    # =================================================

                    successful += 1

                    log_event(
                        employee=employee["Name"],
                        status="SUCCESS",
                        details=(
                            "Employee created successfully"
                        )
                    )

                    print(
                        f"✓ SUCCESS: "
                        f"{employee['Name']} processed"
                    )

                    human_pause(2)

                # =================================================
                # SYSTEM EXCEPTION
                # =================================================

                except Exception as error:

                    system_exceptions += 1

                    print(
                        "❌ SYSTEM EXCEPTION"
                    )

                    print(
                        f"Employee: {name}"
                    )

                    print(
                        f"Error: {error}"
                    )

                    # Write system error to audit log
                    log_event(
                        employee=name,
                        status="SYSTEM_EXCEPTION",
                        details=str(error)
                    )

                    # Continue with next employee
                    continue

            # =================================================
            # PROCESS SUMMARY
            # =================================================

            print("\n")

            print("=" * 60)
            print("RPA PROCESS SUMMARY")
            print("=" * 60)

            print(
                f"Total records:       {len(employees)}"
            )

            print(
                f"Successful:          {successful}"
            )

            print(
                f"Business exceptions: {business_exceptions}"
            )

            print(
                f"System exceptions:   {system_exceptions}"
            )

            print("=" * 60)

            # Keep browser open so the user can inspect results
            input(
                "\nPress ENTER to close the browser..."
            )

        finally:

            browser.close()


# =========================================================
# PROGRAM ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_bot()