import pytest
from unittest.mock import MagicMock, patch

from utils.ecs.manage_ecs import (
    get_servers_for_user, get_servers_for_group,
    batch_start, batch_stop, batch_reboot,
    list_resize_flavors, resize_server,
)


def _server(name, owner, status="ACTIVE"):
    s = MagicMock()
    s.name = name
    s.id = f"id-{name}"
    s.status = status
    s.metadata = {"owner": owner}
    return s


def _group(name, gid):
    g = MagicMock()
    g.name = name
    g.id = gid
    return g


def _user(name):
    u = MagicMock()
    u.name = name
    return u


def test_get_servers_for_user_filters_by_owner():
    ecs = MagicMock()
    ecs.list_servers_details.return_value.servers = [
        _server("vm-a01", "alumno01"),
        _server("vm-a02", "alumno02"),
    ]
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        result = get_servers_for_user("alumno01")
    assert len(result) == 1
    assert result[0].name == "vm-a01"


def test_get_servers_for_user_no_match_returns_empty():
    ecs = MagicMock()
    ecs.list_servers_details.return_value.servers = [_server("vm-a02", "alumno02")]
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert get_servers_for_user("alumno01") == []


def test_get_servers_for_user_api_error_returns_empty(make_api_error):
    ecs = MagicMock()
    ecs.list_servers_details.side_effect = make_api_error()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert get_servers_for_user("alumno01") == []


def test_get_servers_for_user_none_servers_returns_empty():
    ecs = MagicMock()
    ecs.list_servers_details.return_value.servers = None
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert get_servers_for_user("alumno01") == []


def test_get_servers_for_group_returns_group_members_ecs():
    iam = MagicMock()
    ecs = MagicMock()

    iam.keystone_list_groups.return_value.groups = [_group("Grupo-A", "gid-1")]
    iam.keystone_list_users_for_group_by_admin.return_value.users = [_user("alumno01")]
    ecs.list_servers_details.return_value.servers = [
        _server("vm-a01", "alumno01"),
        _server("vm-otro", "otro"),
    ]

    with patch("utils.ecs.manage_ecs.get_client", return_value=iam), \
         patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        result = get_servers_for_group("Grupo-A")

    assert len(result) == 1
    assert result[0].name == "vm-a01"


def test_get_servers_for_group_not_found_returns_empty():
    iam = MagicMock()
    iam.keystone_list_groups.return_value.groups = []
    with patch("utils.ecs.manage_ecs.get_client", return_value=iam), \
         patch("utils.ecs.manage_ecs.get_ecs_client", return_value=MagicMock()):
        assert get_servers_for_group("NoExiste") == []


def test_get_servers_for_group_users_api_error_returns_empty(make_api_error):
    iam = MagicMock()
    iam.keystone_list_groups.return_value.groups = [_group("Grupo-A", "gid-1")]
    iam.keystone_list_users_for_group_by_admin.side_effect = make_api_error()

    with patch("utils.ecs.manage_ecs.get_client", return_value=iam), \
         patch("utils.ecs.manage_ecs.get_ecs_client", return_value=MagicMock()):
        assert get_servers_for_group("Grupo-A") == []


def test_batch_start_returns_job_id():
    ecs = MagicMock()
    ecs.batch_start_servers.return_value.job_id = "job-start-001"
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        result = batch_start([_server("vm-1", "u1")])
    assert result == "job-start-001"


def test_batch_start_api_error_returns_none(make_api_error):
    ecs = MagicMock()
    ecs.batch_start_servers.side_effect = make_api_error()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert batch_start([_server("vm-1", "u1")]) is None


def test_batch_start_sends_correct_server_ids():
    ecs = MagicMock()
    ecs.batch_start_servers.return_value.job_id = "job-001"
    servers = [_server("vm-1", "u1"), _server("vm-2", "u2")]
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        batch_start(servers)
    body = ecs.batch_start_servers.call_args[0][0].body
    ids = [sid.id for sid in body.os_start.servers]
    assert set(ids) == {"id-vm-1", "id-vm-2"}


def test_batch_stop_soft_type():
    ecs = MagicMock()
    ecs.batch_stop_servers.return_value.job_id = "job-stop-001"
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        batch_stop([_server("vm-1", "u1")], force=False)
    body = ecs.batch_stop_servers.call_args[0][0].body
    assert body.os_stop.type == "SOFT"


def test_batch_stop_hard_type():
    ecs = MagicMock()
    ecs.batch_stop_servers.return_value.job_id = "job-stop-002"
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        batch_stop([_server("vm-1", "u1")], force=True)
    body = ecs.batch_stop_servers.call_args[0][0].body
    assert body.os_stop.type == "HARD"


def test_batch_stop_api_error_returns_none(make_api_error):
    ecs = MagicMock()
    ecs.batch_stop_servers.side_effect = make_api_error()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert batch_stop([_server("vm-1", "u1")]) is None


def test_batch_reboot_soft_type():
    ecs = MagicMock()
    ecs.batch_reboot_servers.return_value.job_id = "job-reboot-001"
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        batch_reboot([_server("vm-1", "u1")], force=False)
    body = ecs.batch_reboot_servers.call_args[0][0].body
    assert body.reboot.type == "SOFT"


def test_batch_reboot_hard_type():
    ecs = MagicMock()
    ecs.batch_reboot_servers.return_value.job_id = "job-reboot-002"
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        batch_reboot([_server("vm-1", "u1")], force=True)
    body = ecs.batch_reboot_servers.call_args[0][0].body
    assert body.reboot.type == "HARD"


def test_batch_reboot_api_error_returns_none(make_api_error):
    ecs = MagicMock()
    ecs.batch_reboot_servers.side_effect = make_api_error()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert batch_reboot([_server("vm-1", "u1")]) is None


def test_list_resize_flavors_returns_list():
    f1 = MagicMock()
    f1.id = "c3.xlarge.4"
    f1.vcpus = "4"
    f1.ram = "8192"

    ecs = MagicMock()
    ecs.list_resize_flavors.return_value.flavors = [f1]

    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        result = list_resize_flavors("server-id-1")

    assert len(result) == 1
    assert result[0].id == "c3.xlarge.4"
    ecs.list_resize_flavors.assert_called_once()


def test_list_resize_flavors_none_returns_empty():
    ecs = MagicMock()
    ecs.list_resize_flavors.return_value.flavors = None
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert list_resize_flavors("server-id-1") == []


def test_list_resize_flavors_api_error_returns_empty(make_api_error):
    ecs = MagicMock()
    ecs.list_resize_flavors.side_effect = make_api_error()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert list_resize_flavors("server-id-1") == []


def test_resize_server_returns_true_on_success():
    ecs = MagicMock()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert resize_server("server-id-1", "c3.xlarge.4") is True


def test_resize_server_calls_with_correct_ids():
    ecs = MagicMock()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        resize_server("server-id-1", "c3.xlarge.4")
    req = ecs.resize_server.call_args[0][0]
    assert req.server_id == "server-id-1"
    assert req.body.resize.flavor_ref == "c3.xlarge.4"


def test_resize_server_api_error_returns_false(make_api_error):
    ecs = MagicMock()
    ecs.resize_server.side_effect = make_api_error()
    with patch("utils.ecs.manage_ecs.get_ecs_client", return_value=ecs):
        assert resize_server("server-id-1", "c3.xlarge.4") is False
