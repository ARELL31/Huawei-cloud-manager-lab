from config.connection import get_client, load_config
from utils.iam.helpers import find_user_id
from utils.iam.create_custom_policy import create_custom_policy
from huaweicloudsdkiam.v3 import (
    KeystoneCreateGroupRequest,
    KeystoneCreateGroupRequestBody,
    KeystoneCreateGroupOption,
    KeystoneAddUserToGroupRequest,
    AssociateRoleToGroupOnEnterpriseProjectRequest,
)
from huaweicloudsdkcore.exceptions import exceptions


def _create_perm_group(client, username: str, domain_id: str):
    group_name = f"perm-{username}"
    try:
        request = KeystoneCreateGroupRequest()
        request.body = KeystoneCreateGroupRequestBody(
            group=KeystoneCreateGroupOption(
                name=group_name,
                domain_id=domain_id,
                description=f"Permisos VNC/SSH para {username}",
            )
        )
        response = client.keystone_create_group(request)
        return response.group
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] Grupo perm para {username}: {e.error_msg}")
        return None


def grant_enterprise_permissions_batch(
    usernames: list[str],
    ep_ids: dict[str, str],
    config_file: str = "config/config.json",
    on_progress=None,
) -> dict:
    client = get_client(config_file)
    config = load_config(config_file)
    domain_id = config["domain_id"]

    policy_id = create_custom_policy(config_file=config_file)
    if not policy_id:
        print("[ERROR] No se pudo obtener la politica ECS_VNC_SSH_Only. Abortando permisos.")
        return {"granted": [], "failed": list(usernames)}

    granted = []
    failed = []
    total = len(usernames)

    for i, username in enumerate(usernames, start=1):
        ep_id = ep_ids.get(username)
        if not ep_id:
            print(f"[WARN] Sin enterprise project para {username}. Se omite asignacion de permisos.")
            failed.append(username)
            if on_progress:
                on_progress(i, total)
            continue

        user_id = find_user_id(client, username)
        if not user_id:
            print(f"[ERROR] Usuario no encontrado en IAM: {username}")
            failed.append(username)
            if on_progress:
                on_progress(i, total)
            continue

        group = _create_perm_group(client, username, domain_id)
        if not group:
            failed.append(username)
            if on_progress:
                on_progress(i, total)
            continue

        try:
            client.keystone_add_user_to_group(
                KeystoneAddUserToGroupRequest(group_id=group.id, user_id=user_id)
            )
        except exceptions.ClientRequestException as e:
            print(f"[ERROR] No se pudo agregar {username} a perm-{username}: {e.error_msg}")
            failed.append(username)
            if on_progress:
                on_progress(i, total)
            continue

        try:
            client.associate_role_to_group_on_enterprise_project(
                AssociateRoleToGroupOnEnterpriseProjectRequest(
                    enterprise_project_id=ep_id,
                    group_id=group.id,
                    role_id=policy_id,
                )
            )
            print(f"[OK] Permisos VNC/SSH asignados a {username} en EP {ep_id}")
            granted.append(username)
        except exceptions.ClientRequestException as e:
            print(f"[ERROR] Asignacion de permisos para {username}: {e.error_msg}")
            failed.append(username)

        if on_progress:
            on_progress(i, total)

    return {"granted": granted, "failed": failed}
