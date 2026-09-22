REQUIRED_FIELDS = [
    "Name",
    "Department",
    "Location",
    "Email",
]


def validate_employee(employee):
    errors = []

    for field in REQUIRED_FIELDS:
        value = employee.get(field, "").strip()

        if not value:
            errors.append(f"{field} is required")

    return errors