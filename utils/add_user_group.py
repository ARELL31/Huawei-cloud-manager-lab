from config.connection import get_client
from huaweicloudsdkiam.v3 import (
    KeystoneListUsersRequest,
    KeystoneListGroupsRequest,
    KeystoneAddUserToGroupRequest,
)
from huaweicloudsdkcore.exceptions import exceptions


def find_user_id(client, username: str):
    request = KeystoneListUsersRequest()
    response = client.keystone_list_users(request)

    for user in response.users:
        if user.name == username:
            return user.id

    return None


def find_group_id(client, group_name: str):
    request = KeystoneListGroupsRequest()
    response = client.keystone_list_groups(request)

    for group in response.groups:
        if group.name == group_name:
            return group.id

    return None


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
