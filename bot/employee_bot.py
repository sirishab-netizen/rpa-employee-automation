import csv
import time
from datetime import datetime
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

SCREENSHOT_DIR = ROOT / "screenshots"


# =========================================================
# CONFIGURATION
# =========================================================

# Make the bot slow enough that we can see its actions.
ACTION_DELAY = 1

# Playwright delay between browser actions.
BROWSER_SLOW_MO = 300

# Number of retries after a system failure.
MAX_RETRIES = 2

# ---------------------------------------------------------
# Set this to True ONLY when testing failure recovery.
# Keep it False for normal operation.
# ---------------------------------------------------------

SIMULATE_FAILURE = False


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
# TAKE SCREENSHOT
# =========================================================

def take_failure_screenshot(page, employee_name):

    SCREENSHOT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    safe_name = (
        employee_name
        .replace(" ", "_")
        .replace("/", "_")
    )

    screenshot_path = (
        SCREENSHOT_DIR
        / f"{safe_name}_{timestamp}.png"
    )

    page.screenshot(
        path=str(screenshot_path),
        full_page=True
    )

    print(
        f"📸 Screenshot saved: "
        f"{screenshot_path}"
    )

    return screenshot_path


# =========================================================
# PROCESS ONE EMPLOYEE
# =========================================================

def process_employee(page, employee):

    name = employee.get(
        "Name",
        ""
    ).strip()

    print(
        f"\nProcessing: {name}"
    )

    # =====================================================
    # STEP 1 — BUSINESS VALIDATION
    # =====================================================

    errors = validate_employee(
        employee
    )

    if errors:

        details = "; ".join(errors)

        print(
            "❌ BUSINESS EXCEPTION"
        )

        for error in errors:

            print(
                f"   - {error}"
            )

        log_event(
            employee=name,
            status="BUSINESS_EXCEPTION",
            details=details
        )

        return "BUSINESS_EXCEPTION"

    # =====================================================
    # STEP 2 — ENTER NAME
    # =====================================================

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

    # =====================================================
    # STEP 3 — SELECT DEPARTMENT
    # =====================================================

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

    # =====================================================
    # STEP 4 — ENTER LOCATION
    # =====================================================

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

    # =====================================================
    # STEP 5 — ENTER EMAIL
    # =====================================================

    print(
        f"→ Entering Email: "
        f"{employee['Email']}"
    )

    page.locator(
        "#email"
    ).click()

    human_pause(0.5)

    # -----------------------------------------------------
    # CONTROLLED FAILURE TEST
    # -----------------------------------------------------

    if SIMULATE_FAILURE:

        print(
            "⚠️ SIMULATING SYSTEM FAILURE"
        )

        page.locator(
            "#email-does-not-exist"
        ).fill(
            employee["Email"]
        )

    else:

        page.locator(
            "#email"
        ).fill(
            employee["Email"]
        )

    human_pause()

    # =====================================================
    # STEP 6 — SUBMIT
    # =====================================================

    print(
        "→ Clicking Add Employee"
    )

    page.locator(
        "#addEmployee"
    ).click()

    human_pause(2)

    # =====================================================
    # STEP 7 — VERIFY RESULT
    # =====================================================

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
            f"Unexpected application response: "
            f"{status}"
        )

    # =====================================================
    # SUCCESS
    # =====================================================

    print(
        f"✓ SUCCESS: {name}"
    )

    log_event(
        employee=name,
        status="SUCCESS",
        details="Employee created successfully"
    )

    return "SUCCESS"


# =========================================================
# RETRY LOGIC
# =========================================================

def process_with_retry(page, employee):

    name = employee.get(
        "Name",
        ""
    ).strip()

    total_attempts = MAX_RETRIES + 1

    for attempt in range(
        1,
        total_attempts + 1
    ):

        print(
            f"\nAttempt {attempt} "
            f"of {total_attempts} "
            f"for {name}"
        )

        try:

            result = process_employee(
                page,
                employee
            )

            # -------------------------------------------------
            # Business exceptions are not retried.
            # -------------------------------------------------

            if result == "BUSINESS_EXCEPTION":

                return result

            return "SUCCESS"

        except Exception as error:

            print(
                f"❌ System failure on "
                f"attempt {attempt}"
            )

            print(
                f"Error: {error}"
            )

            # -------------------------------------------------
            # Capture evidence
            # -------------------------------------------------

            screenshot = (
                take_failure_screenshot(
                    page,
                    name
                )
            )

            # -------------------------------------------------
            # Retry if attempts remain
            # -------------------------------------------------

            if attempt < total_attempts:

                print(
                    "↻ Retrying transaction..."
                )

                human_pause(2)

                # Reset the application
                page.goto(
                    APP_FILE.as_uri(),
                    wait_until="domcontentloaded"
                )

                human_pause(2)

            else:

                print(
                    "❌ All retry attempts failed"
                )

                log_event(
                    employee=name,
                    status="SYSTEM_EXCEPTION",
                    details=(
                        f"Error: {error}; "
                        f"Screenshot: {screenshot}"
                    )
                )

                return "SYSTEM_EXCEPTION"


# =========================================================
# MAIN BOT
# =========================================================

def run_bot():

    employees = load_employees()

    print()
    print("=" * 60)
    print("RPA EMPLOYEE DATA ENTRY BOT")
    print("=" * 60)

    print(
        f"Loaded {len(employees)} employee records"
    )

    if SIMULATE_FAILURE:

        print()
        print(
            "⚠️ FAILURE SIMULATION IS ENABLED"
        )

    successful = 0
    business_exceptions = 0
    system_exceptions = 0

    # =====================================================
    # START PLAYWRIGHT
    # =====================================================

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

            print()
            print(
                "Opening Employee Management..."
            )

            page.goto(
                APP_FILE.as_uri(),
                wait_until="domcontentloaded"
            )

            human_pause(2)

            print(
                "✓ Application opened"
            )

            # =================================================
            # PROCESS EMPLOYEES
            # =================================================

            for employee in employees:

                result = process_with_retry(
                    page,
                    employee
                )

                # -------------------------------------------------
                # Track outcome
                # -------------------------------------------------

                if result == "SUCCESS":

                    successful += 1

                elif result == "BUSINESS_EXCEPTION":

                    business_exceptions += 1

                elif result == "SYSTEM_EXCEPTION":

                    system_exceptions += 1

            # =================================================
            # FINAL SUMMARY
            # =================================================

            print()
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

            # Keep browser open
            input(
                "\nPress ENTER to close the browser..."
            )

        finally:

            browser.close()


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_bot()