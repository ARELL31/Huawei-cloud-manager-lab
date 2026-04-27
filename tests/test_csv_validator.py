import pytest
from utils.csv_validator import get_validation_report, validate_csv


def _write_csv(tmp_path, rows, header="username,email,password,enabled"):
    f = tmp_path / "users.csv"
    f.write_text("\n".join([header] + rows), encoding="utf-8")
    return str(f)


def test_valid_user_no_issues(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,alumno01@test.com,Pass1234!,true"])
    report = get_validation_report(path)
    assert report is not None
    assert report["errors"] == []
    assert report["warnings"] == []


def test_multiple_valid_users(tmp_path):
    path = _write_csv(tmp_path, [
        "alumno01,a01@test.com,Pass1234!,true",
        "alumno02,a02@test.com,Pass5678@,false",
    ])
    report = get_validation_report(path)
    assert len(report["users"]) == 2
    assert report["errors"] == []


def test_duplicate_username_is_critical_error(tmp_path):
    path = _write_csv(tmp_path, [
        "alumno01,a01@test.com,Pass1234!,true",
        "alumno01,a02@test.com,Pass5678@,true",
    ])
    report = get_validation_report(path)
    assert any("duplicado" in e for e in report["errors"])


def test_bad_email_is_warning(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,notanemail,Pass1234!,true"])
    report = get_validation_report(path)
    assert any("email" in w for w in report["warnings"])


def test_empty_email_is_warning(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,,Pass1234!,true"])
    report = get_validation_report(path)
    assert any("email" in w for w in report["warnings"])


def test_weak_password_short_is_warning(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,a@b.com,Ab1!,true"])
    report = get_validation_report(path)
    assert any("contraseña" in w for w in report["warnings"])


def test_weak_password_no_uppercase_is_warning(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,a@b.com,pass1234!,true"])
    report = get_validation_report(path)
    assert any("contraseña" in w for w in report["warnings"])


def test_weak_password_no_digit_is_warning(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,a@b.com,Password!,true"])
    report = get_validation_report(path)
    assert any("contraseña" in w for w in report["warnings"])


def test_weak_password_no_special_char_is_warning(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,a@b.com,Password1,true"])
    report = get_validation_report(path)
    assert any("contraseña" in w for w in report["warnings"])


def test_missing_file_returns_none():
    report = get_validation_report("no_existe.csv")
    assert report is None


def test_validate_csv_empty_file_returns_false(tmp_path):
    path = _write_csv(tmp_path, [])
    assert validate_csv(path) is False


def test_validate_csv_missing_file_returns_false():
    assert validate_csv("no_existe.csv") is False


def test_validate_csv_with_critical_error_returns_false(tmp_path):
    path = _write_csv(tmp_path, [
        "alumno01,a@b.com,Pass1234!,true",
        "alumno01,b@b.com,Pass5678@,true",
    ])
    assert validate_csv(path) is False


def test_validate_csv_clean_file_returns_true(tmp_path):
    path = _write_csv(tmp_path, ["alumno01,a@b.com,Pass1234!,true"])
    assert validate_csv(path) is True
