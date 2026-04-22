import re
from utils.convert_cvs import csv_to_iam_users


def _check_email(email: str) -> str | None:
    if not email:
        return "email vacio"
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return f"email malformado '{email}'"
    return None


def _check_password(password: str) -> list[str]:
    issues = []
    if len(password) < 8:
        issues.append("minimo 8 caracteres")
    if not re.search(r'[A-Z]', password):
        issues.append("sin mayusculas")
    if not re.search(r'[a-z]', password):
        issues.append("sin minusculas")
    if not re.search(r'\d', password):
        issues.append("sin digitos")
    if not re.search(r'[^a-zA-Z0-9]', password):
        issues.append("sin caracteres especiales")
    return issues


def get_validation_report(csv_file: str) -> dict | None:
    try:
        users = csv_to_iam_users(csv_file)
    except FileNotFoundError:
        print(f"[ERROR] Archivo no encontrado: {csv_file}")
        return None
    except Exception as e:
        print(f"[ERROR] No se pudo leer el CSV: {e}")
        return None

    errors, warnings = [], []

    seen = {}
    for row, user in enumerate(users, start=2):
        name = user["name"]
        if name in seen:
            errors.append(f"fila {row}: username '{name}' duplicado (primera aparicion en fila {seen[name]})")
        else:
            seen[name] = row

    for row, user in enumerate(users, start=2):
        label = f"fila {row} ({user['name']})"
        email_issue = _check_email(user["email"])
        if email_issue:
            warnings.append(f"{label}: {email_issue}")
        password_issues = _check_password(user["password"])
        if password_issues:
            warnings.append(f"{label}: contraseña debil ({', '.join(password_issues)})")

    return {"users": users, "errors": errors, "warnings": warnings}


def validate_csv(csv_file: str) -> bool:
    report = get_validation_report(csv_file)
    if report is None:
        return False

    users = report["users"]
    errors = report["errors"]
    warnings = report["warnings"]

    if not users:
        print("[ERROR] El CSV esta vacio o no tiene filas de datos.")
        return False

    print(f"\n  Validando '{csv_file}' — {len(users)} usuario(s)")
    print("  " + "─" * 50)

    if not errors and not warnings:
        print("  [OK] Sin problemas encontrados.\n")
        return True

    if errors:
        print(f"\n  Errores criticos ({len(errors)}) — no se puede continuar:")
        for msg in errors:
            print(f"    [ERROR] {msg}")

    if warnings:
        print(f"\n  Advertencias ({len(warnings)}):")
        for msg in warnings:
            print(f"    [AVISO] {msg}")

    print()

    if errors:
        print("  Corrige los errores en el CSV antes de continuar.\n")
        return False

    confirm = input("  Hay advertencias. Deseas continuar de todas formas? (s/n): ").strip().lower()
    print()
    return confirm == "s"
