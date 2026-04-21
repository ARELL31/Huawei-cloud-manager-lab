from config.connection import get_client, load_config
from huaweicloudsdkiam.v3 import (
    KeystoneCreateGroupRequest,
    KeystoneCreateGroupRequestBody,
    KeystoneCreateGroupOption,
)
from huaweicloudsdkcore.exceptions import exceptions


def create_user_group(
    group_name: str,
    description: str = "Este grupo albergara a los usuarios",
    config_file: str = "config/config.json"
):
    client = get_client(config_file)
    config = load_config(config_file)
    domain_id = config["domain_id"]

    try:
        request = KeystoneCreateGroupRequest()
        groupbody = KeystoneCreateGroupOption(
            description=description,
            domain_id=domain_id,
            name=group_name
        )
        request.body = KeystoneCreateGroupRequestBody(group=groupbody)

        response = client.keystone_create_group(request)
        print(f"[OK] Grupo creado: {response.group.name}")
        return response.group

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] Grupo {group_name}: {e.error_msg}")
        return None
