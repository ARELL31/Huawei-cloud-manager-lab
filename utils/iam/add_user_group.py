from config.connection import get_client
from utils.iam.helpers import find_user_id, find_group_id
from huaweicloudsdkiam.v3 import KeystoneAddUserToGroupRequest
from huaweicloudsdkcore.exceptions import exceptions


def add_users_to_group(usernames: list[str], group_name: str, config_file="config/config.json"):
    client = get_client(config_file)

    group_id = find_group_id(client, group_name)
    if not group_id:
        print(f"[ERROR] Grupo no encontrado: {group_name}")
        return

    for username in usernames:
        try:
            user_id = find_user_id(client, username)
            if not user_id:
                print(f"[ERROR] Usuario no encontrado: {username}")
                continue

            request = KeystoneAddUserToGroupRequest(
                group_id=group_id,
                user_id=user_id
            )
            client.keystone_add_user_to_group(request)
            print(f"[OK] Usuario agregado al grupo: {username} -> {group_name}")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] {username}: {e.error_msg}")
