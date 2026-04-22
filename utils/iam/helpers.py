import csv
from config.connection import get_client
from huaweicloudsdkiam.v3 import (
    KeystoneListUsersRequest,
    KeystoneListGroupsRequest,
    KeystoneUpdateUserByAdminRequest,
    KeystoneUpdateUserByAdminRequestBody,
    KeystoneUpdateUserOption,
)
from huaweicloudsdkcore.exceptions import exceptions


def read_usernames(csv_file: str) -> list[str]:
    usernames = []
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
        for row in reader:
            clean_row = {
                key.strip(): value.strip() if value else ""
                for key, value in row.items()
            }
            username = clean_row.get("username", "")
            if username:
                usernames.append(username)
    return usernames


def find_user_id(client, username: str) -> str | None:
    request = KeystoneListUsersRequest()
    response = client.keystone_list_users(request)
    for user in response.users:
        if user.name == username:
            return user.id
    return None


def find_group_id(client, group_name: str) -> str | None:
    request = KeystoneListGroupsRequest()
    response = client.keystone_list_groups(request)
    for group in response.groups:
        if group.name == group_name:
            return group.id
    return None


def set_users_enabled(
    csv_file: str,
    enabled: bool,
    config_file: str = "config/config.json",
    on_progress=None,
):
    client = get_client(config_file)
    usernames = read_usernames(csv_file)

    if not usernames:
        print("[AVISO] No se encontraron usernames en el CSV.")
        return

    estado = "habilitado" if enabled else "deshabilitado"
    total = len(usernames)

    for i, username in enumerate(usernames, start=1):
        try:
            user_id = find_user_id(client, username)
            if not user_id:
                print(f"[ERROR] Usuario no encontrado: {username}")
                continue

            request = KeystoneUpdateUserByAdminRequest(user_id=user_id)
            request.body = KeystoneUpdateUserByAdminRequestBody(
                user=KeystoneUpdateUserOption(enabled=enabled)
            )
            client.keystone_update_user_by_admin(request)
            print(f"[OK] Usuario {estado}: {username}")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] {username}: {e.error_msg}")

        if on_progress:
            on_progress(i, total)
