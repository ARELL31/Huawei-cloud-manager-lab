import json
import pytest
from unittest.mock import MagicMock, patch

from config.connection import load_config, get_client, get_ecs_client, get_vpc_client
from tests.conftest import FAKE_CONFIG


def test_load_config_returns_dict(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(FAKE_CONFIG), encoding="utf-8")
    result = load_config(str(cfg))
    assert result["ak"] == "fake-ak"
    assert result["region"] == "la-north-2"
    assert result["project_id"] == "fake-project-id"


def test_load_config_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config("no_existe.json")


def _mock_builder():
    b = MagicMock()
    b.with_credentials.return_value = b
    b.with_region.return_value = b
    b.build.return_value = MagicMock()
    return b


def test_get_client_uses_global_credentials():
    builder = _mock_builder()
    with patch("config.connection.load_config", return_value=FAKE_CONFIG), \
         patch("config.connection.GlobalCredentials") as mock_creds, \
         patch("config.connection.IamClient") as mock_iam:
        mock_iam.new_builder.return_value = builder

        get_client()

        mock_creds.assert_called_once_with(ak="fake-ak", sk="fake-sk")
        mock_iam.new_builder.assert_called_once()
        builder.build.assert_called_once()


def test_get_client_returns_built_client():
    sentinel = object()
    builder = _mock_builder()
    builder.build.return_value = sentinel
    with patch("config.connection.load_config", return_value=FAKE_CONFIG), \
         patch("config.connection.GlobalCredentials"), \
         patch("config.connection.IamClient") as mock_iam:
        mock_iam.new_builder.return_value = builder
        assert get_client() is sentinel


def test_get_ecs_client_uses_basic_credentials():
    builder = _mock_builder()
    with patch("config.connection.load_config", return_value=FAKE_CONFIG), \
         patch("config.connection.BasicCredentials") as mock_creds, \
         patch("config.connection.EcsClient") as mock_ecs:
        mock_ecs.new_builder.return_value = builder

        get_ecs_client()

        mock_creds.assert_called_once_with(
            ak="fake-ak", sk="fake-sk", project_id="fake-project-id"
        )
        builder.build.assert_called_once()


def test_get_ecs_client_uses_region_from_config():
    builder = _mock_builder()
    with patch("config.connection.load_config", return_value=FAKE_CONFIG), \
         patch("config.connection.BasicCredentials"), \
         patch("config.connection.EcsClient") as mock_ecs, \
         patch("config.connection.EcsRegion") as mock_region:
        mock_ecs.new_builder.return_value = builder

        get_ecs_client()

        mock_region.value_of.assert_called_once_with("la-north-2")


def test_get_vpc_client_uses_basic_credentials():
    builder = _mock_builder()
    with patch("config.connection.load_config", return_value=FAKE_CONFIG), \
         patch("config.connection.BasicCredentials") as mock_creds, \
         patch("config.connection.VpcClient") as mock_vpc:
        mock_vpc.new_builder.return_value = builder

        get_vpc_client()

        mock_creds.assert_called_once_with(
            ak="fake-ak", sk="fake-sk", project_id="fake-project-id"
        )
        builder.build.assert_called_once()


def test_get_vpc_client_uses_region_from_config():
    builder = _mock_builder()
    with patch("config.connection.load_config", return_value=FAKE_CONFIG), \
         patch("config.connection.BasicCredentials"), \
         patch("config.connection.VpcClient") as mock_vpc, \
         patch("config.connection.VpcRegion") as mock_region:
        mock_vpc.new_builder.return_value = builder

        get_vpc_client()

        mock_region.value_of.assert_called_once_with("la-north-2")
