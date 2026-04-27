import csv
import json
import pytest
from unittest.mock import MagicMock, patch

from utils.export_snapshot import collect_snapshot, write_csv, write_json, _extract_ips


def _group(name, gid):
    g = MagicMock()
    g.name = name
    g.id = gid
    return g


def _user(name, uid, enabled=True):
    u = MagicMock()
    u.name = name
    u.id = uid
    u.enabled = enabled
    return u


def _server(name, sid, owner, status="ACTIVE", ips=None):
    s = MagicMock()
    s.name = name
    s.id = sid
    s.status = status
    s.metadata = {"owner": owner}
    if ips:
        addr = MagicMock()
        addr.addr = ips[0]
        s.addresses = {"net": [addr]}
    else:
        s.addresses = {}
    return s


def _mock_clients(groups, users_per_group, servers):
    iam = MagicMock()
    ecs = MagicMock()
    iam.keystone_list_groups.return_value.groups = groups
    iam.keystone_list_users_for_group_by_admin.return_value.users = users_per_group
    ecs.list_servers_details.return_value.servers = servers
    return iam, ecs


def test_collect_snapshot_group_structure():
    iam, ecs = _mock_clients(
        groups=[_group("Grupo-A", "gid-1")],
        users_per_group=[_user("alumno01", "uid-1")],
        servers=[_server("vm-a01", "sid-1", "alumno01", ips=["10.0.0.1"])],
    )
    with patch("utils.export_snapshot.get_client", return_value=iam), \
         patch("utils.export_snapshot.get_ecs_client", return_value=ecs):
        snapshot = collect_snapshot()

    assert len(snapshot) == 1
    group = snapshot[0]
    assert group["nombre"] == "Grupo-A"
    assert group["id"] == "gid-1"


def test_collect_snapshot_user_fields():
    iam, ecs = _mock_clients(
        groups=[_group("Grupo-A", "gid-1")],
        users_per_group=[_user("alumno01", "uid-1", enabled=True)],
        servers=[],
    )
    with patch("utils.export_snapshot.get_client", return_value=iam), \
         patch("utils.export_snapshot.get_ecs_client", return_value=ecs):
        snapshot = collect_snapshot()

    user = snapshot[0]["usuarios"][0]
    assert user["nombre"] == "alumno01"
    assert user["id"] == "uid-1"
    assert user["estado"] == "habilitado"
    assert user["ecs"] == []


def test_collect_snapshot_disabled_user_estado():
    iam, ecs = _mock_clients(
        groups=[_group("G1", "g1")],
        users_per_group=[_user("alumno01", "uid-1", enabled=False)],
        servers=[],
    )
    with patch("utils.export_snapshot.get_client", return_value=iam), \
         patch("utils.export_snapshot.get_ecs_client", return_value=ecs):
        snapshot = collect_snapshot()

    assert snapshot[0]["usuarios"][0]["estado"] == "deshabilitado"


def test_collect_snapshot_ecs_linked_to_owner():
    iam, ecs = _mock_clients(
        groups=[_group("G1", "g1")],
        users_per_group=[_user("alumno01", "uid-1"), _user("alumno02", "uid-2")],
        servers=[
            _server("vm-a01", "sid-1", "alumno01", ips=["10.0.0.1"]),
            _server("vm-a02", "sid-2", "alumno02"),
        ],
    )
    with patch("utils.export_snapshot.get_client", return_value=iam), \
         patch("utils.export_snapshot.get_ecs_client", return_value=ecs):
        snapshot = collect_snapshot()

    usuarios = {u["nombre"]: u for u in snapshot[0]["usuarios"]}
    assert len(usuarios["alumno01"]["ecs"]) == 1
    assert usuarios["alumno01"]["ecs"][0]["ips"] == ["10.0.0.1"]
    assert len(usuarios["alumno02"]["ecs"]) == 1


def test_collect_snapshot_on_progress_called_per_group():
    iam, ecs = _mock_clients(
        groups=[_group("G1", "g1"), _group("G2", "g2")],
        users_per_group=[],
        servers=[],
    )
    calls = []
    with patch("utils.export_snapshot.get_client", return_value=iam), \
         patch("utils.export_snapshot.get_ecs_client", return_value=ecs):
        collect_snapshot(on_progress=lambda c, t: calls.append((c, t)))

    assert calls == [(1, 2), (2, 2)]


def test_collect_snapshot_empty_cloud():
    iam, ecs = _mock_clients(groups=[], users_per_group=[], servers=[])
    with patch("utils.export_snapshot.get_client", return_value=iam), \
         patch("utils.export_snapshot.get_ecs_client", return_value=ecs):
        snapshot = collect_snapshot()
    assert snapshot == []


def _snapshot_one_group():
    return [{
        "nombre": "G1", "id": "gid-1",
        "usuarios": [
            {
                "nombre": "alumno01", "id": "uid-1", "estado": "habilitado",
                "ecs": [{"nombre": "vm-1", "id": "sid-1", "estado": "ACTIVE",
                         "ips": ["10.0.0.1", "10.0.0.2"]}],
            },
            {
                "nombre": "alumno02", "id": "uid-2", "estado": "deshabilitado",
                "ecs": [],
            },
        ],
    }]


def test_write_csv_returns_correct_counts(tmp_path):
    path = str(tmp_path / "out.csv")
    n_groups, n_users, n_ecs = write_csv(_snapshot_one_group(), path)
    assert n_groups == 1
    assert n_users == 2
    assert n_ecs == 1


def test_write_csv_user_with_ecs_row(tmp_path):
    path = str(tmp_path / "out.csv")
    write_csv(_snapshot_one_group(), path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ecs_row = next(r for r in rows if r["usuario_nombre"] == "alumno01")
    assert ecs_row["ecs_nombre"] == "vm-1"
    assert ecs_row["ecs_estado"] == "ACTIVE"
    assert "10.0.0.1" in ecs_row["ecs_ips"]


def test_write_csv_user_without_ecs_row(tmp_path):
    path = str(tmp_path / "out.csv")
    write_csv(_snapshot_one_group(), path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    empty_row = next(r for r in rows if r["usuario_nombre"] == "alumno02")
    assert empty_row["ecs_nombre"] == ""
    assert empty_row["ecs_id"] == ""
    assert empty_row["grupo_nombre"] == "G1"


def test_write_csv_creates_file(tmp_path):
    path = str(tmp_path / "out.csv")
    write_csv(_snapshot_one_group(), path)
    assert (tmp_path / "out.csv").exists()


def test_write_json_returns_correct_counts(tmp_path):
    path = str(tmp_path / "out.json")
    n_groups, n_users, n_ecs = write_json(_snapshot_one_group(), path)
    assert n_groups == 1
    assert n_users == 2
    assert n_ecs == 1


def test_write_json_structure(tmp_path):
    path = str(tmp_path / "out.json")
    write_json(_snapshot_one_group(), path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert "snapshot_at" in data
    assert data["totales"] == {"grupos": 1, "usuarios": 2, "ecs": 1}
    assert len(data["grupos"]) == 1


def test_write_json_is_valid_json(tmp_path):
    path = str(tmp_path / "out.json")
    write_json(_snapshot_one_group(), path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_extract_ips_single_network():
    addr = MagicMock()
    addr.addr = "10.0.0.1"
    server = MagicMock()
    server.addresses = {"net": [addr]}
    assert _extract_ips(server) == ["10.0.0.1"]


def test_extract_ips_multiple_networks():
    a1 = MagicMock(); a1.addr = "10.0.0.1"
    a2 = MagicMock(); a2.addr = "192.168.1.1"
    server = MagicMock()
    server.addresses = {"net1": [a1], "net2": [a2]}
    assert set(_extract_ips(server)) == {"10.0.0.1", "192.168.1.1"}


def test_extract_ips_no_addresses():
    server = MagicMock()
    server.addresses = {}
    assert _extract_ips(server) == []


def test_extract_ips_none_addresses():
    server = MagicMock()
    server.addresses = None
    assert _extract_ips(server) == []
