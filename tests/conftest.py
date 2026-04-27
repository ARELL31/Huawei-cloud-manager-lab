import pytest
from unittest.mock import MagicMock
from huaweicloudsdkcore.exceptions.exceptions import ClientRequestException


@pytest.fixture
def make_api_error():
    def _factory(msg="error simulado"):
        sdk_err = MagicMock()
        sdk_err.error_msg = msg
        sdk_err.error_code = "SDK.0000"
        sdk_err.request_id = "mock-req-id"
        sdk_err.encoded_auth_msg = None
        return ClientRequestException(400, sdk_err)
    return _factory


FAKE_CONFIG = {
    "ak": "fake-ak",
    "sk": "fake-sk",
    "domain_id": "fake-domain-id",
    "project_id": "fake-project-id",
    "region": "la-north-2",
    "ecs": {},
}
