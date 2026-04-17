import csv


def parse_enabled(value: str) -> bool:
    return str(value).strip().lower() in ("true", "1", "si", "sí", "yes", "y")


def csv_to_iam_users(csv_file: str) -> list[dict]:
    users = []

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames]

        for row in reader:
            clean_row = {
                key.strip(): value.strip() if value else ""
                for key, value in row.items()
            }

            users.append({
                "name": clean_row["username"],
                "email": clean_row["email"],
                "password": clean_row["password"],
                "enabled": parse_enabled(clean_row.get("enabled", "true")),
            })

    return users
