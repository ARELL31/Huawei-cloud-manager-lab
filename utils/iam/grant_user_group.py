import json
from config.connection import get_client
from utils.iam.create_custom_policy import create_custom_policy
from huaweicloudsdkiam.v3 import (
    KeystoneListGroupsRequest,
    KeystoneAssociateGroupWithDomainPermissionRequest,
)
from huaweicloudsdkcore.exceptions import exceptions


def find_group_id(client, group_name: str):
    request = KeystoneListGroupsRequest()
    response = client.keystone_list_groups(request)
    for group in response.groups:
        if group.name == group_name:
            return group.id
    return None


def grant_group_role(
    group_name: str,
    config_file: str = "config/config.json"
):
    client = get_client(config_file)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    domain_id = config["domain_id"]

    group_id = find_group_id(client, group_name)
    if not group_id:
        print(f"[ERROR] Grupo no encontrado: {group_name}")
        return

    policy_id = create_custom_policy(config_file=config_file)
    if not policy_id:
        print("[ERROR] No se pudo obtener la politica custom. Abortando asignacion.")
        return

    try:
        request = KeystoneAssociateGroupWithDomainPermissionRequest(
            domain_id=domain_id,
            group_id=group_id,
            role_id=policy_id
        )
        client.keystone_associate_group_with_domain_permission(request)
        print(f"[OK] Politica 'ECS_Owner_Access' asignada al grupo: {group_name}")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo asignar la politica: {e.error_msg}")