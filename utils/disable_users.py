import csv
from config.connection import get_client
from huaweicloudsdkiam.v3 import (
    KeystoneListUsersRequest,
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


def find_user_id(client, username: str):
    request = KeystoneListUsersRequest()
    response = client.keystone_list_users(request)

    for user in response.users:
        if user.name == username:
            return user.id

    return None


def disable_users(csv_file: str, config_file="config/config.json"):
    client = get_client(config_file)
    usernames = read_usernames(csv_file)

    if not usernames:
        print("[AVISO] No se encontraron usernames en el CSV.")
        return

    for username in usernames:
        try:
            user_id = find_user_id(client, username)

            if not user_id:
                print(f"[ERROR] Usuario no encontrado: {username}")
                continue

            request = KeystoneUpdateUserByAdminRequest(user_id=user_id)
            request.body = KeystoneUpdateUserByAdminRequestBody(
                user=KeystoneUpdateUserOption(enabled=False)
            )

            client.keystone_update_user_by_admin(request)
            print(f"[OK] Usuario deshabilitado: {username}")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] {username}: {e.error_msg}")
