import pytest
from unittest.mock import MagicMock, patch

from utils.iam.helpers import read_usernames, find_user_id, find_group_id, set_users_enabled


def test_read_usernames_returns_list(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\nalumno01,a@b.com,x\nalumno02,b@b.com,y",
                 encoding="utf-8")
    assert read_usernames(str(f)) == ["alumno01", "alumno02"]


def test_read_usernames_strips_whitespace(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text(" username ,email\n alumno01 ,x\n", encoding="utf-8")
    assert read_usernames(str(f)) == ["alumno01"]


def test_read_usernames_skips_empty_rows(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email\nalumno01,a@b.com\n,b@b.com\n", encoding="utf-8")
    names = read_usernames(str(f))
    assert "" not in names
    assert "alumno01" in names


def _make_user(name, uid):
    u = MagicMock()
    u.name = name
    u.id = uid
    return u


def test_find_user_id_found():
    client = MagicMock()
    client.keystone_list_users.return_value.users = [
        _make_user("alumno01", "uid-123"),
        _make_user("alumno02", "uid-456"),
    ]
    assert find_user_id(client, "alumno01") == "uid-123"


def test_find_user_id_not_found():
    client = MagicMock()
    client.keystone_list_users.return_value.users = [_make_user("alumno01", "uid-1")]
    assert find_user_id(client, "noexiste") is None


def test_find_user_id_empty_list():
    client = MagicMock()
    client.keystone_list_users.return_value.users = []
    assert find_user_id(client, "alumno01") is None


def _make_group(name, gid):
    g = MagicMock()
    g.name = name
    g.id = gid
    return g


def test_find_group_id_found():
    client = MagicMock()
    client.keystone_list_groups.return_value.groups = [
        _make_group("Grupo-A", "gid-1"),
        _make_group("Grupo-B", "gid-2"),
    ]
    assert find_group_id(client, "Grupo-A") == "gid-1"


def test_find_group_id_not_found():
    client = MagicMock()
    client.keystone_list_groups.return_value.groups = []
    assert find_group_id(client, "noexiste") is None


def test_set_users_enabled_calls_update(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\nalumno01,a@b.com,x", encoding="utf-8")

    client = MagicMock()
    client.keystone_list_users.return_value.users = [_make_user("alumno01", "uid-1")]

    with patch("utils.iam.helpers.get_client", return_value=client):
        set_users_enabled(str(f), enabled=True)

    client.keystone_update_user_by_admin.assert_called_once()


def test_set_users_enabled_false_also_works(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\nalumno01,a@b.com,x", encoding="utf-8")

    client = MagicMock()
    client.keystone_list_users.return_value.users = [_make_user("alumno01", "uid-1")]

    with patch("utils.iam.helpers.get_client", return_value=client):
        set_users_enabled(str(f), enabled=False)

    client.keystone_update_user_by_admin.assert_called_once()


def test_set_users_enabled_user_not_found_skips(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\nalumno01,a@b.com,x", encoding="utf-8")

    client = MagicMock()
    client.keystone_list_users.return_value.users = []

    with patch("utils.iam.helpers.get_client", return_value=client):
        set_users_enabled(str(f), enabled=True)

    client.keystone_update_user_by_admin.assert_not_called()


def test_set_users_enabled_api_error_continues(tmp_path, make_api_error):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\nalumno01,a@b.com,x\nalumno02,b@b.com,y",
                 encoding="utf-8")

    client = MagicMock()
    client.keystone_list_users.return_value.users = [
        _make_user("alumno01", "uid-1"),
        _make_user("alumno02", "uid-2"),
    ]
    client.keystone_update_user_by_admin.side_effect = [make_api_error(), None]

    with patch("utils.iam.helpers.get_client", return_value=client):
        set_users_enabled(str(f), enabled=True)

    assert client.keystone_update_user_by_admin.call_count == 2


def test_set_users_enabled_calls_progress(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\nalumno01,a@b.com,x\nalumno02,b@b.com,y",
                 encoding="utf-8")

    client = MagicMock()
    client.keystone_list_users.return_value.users = [
        _make_user("alumno01", "uid-1"),
        _make_user("alumno02", "uid-2"),
    ]

    calls = []
    with patch("utils.iam.helpers.get_client", return_value=client):
        set_users_enabled(str(f), enabled=True, on_progress=lambda c, t: calls.append((c, t)))

    assert calls == [(1, 2), (2, 2)]


def test_set_users_enabled_empty_csv_exits_early(tmp_path):
    f = tmp_path / "users.csv"
    f.write_text("username,email,password\n", encoding="utf-8")

    client = MagicMock()

    with patch("utils.iam.helpers.get_client", return_value=client):
        set_users_enabled(str(f), enabled=True)

    client.keystone_list_users.assert_not_called()
