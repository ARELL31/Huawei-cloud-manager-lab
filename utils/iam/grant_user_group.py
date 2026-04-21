from config.connection import get_client, load_config
from utils.iam.helpers import find_group_id
from utils.iam.create_custom_policy import create_custom_policy
from huaweicloudsdkiam.v3 import KeystoneAssociateGroupWithDomainPermissionRequest
from huaweicloudsdkcore.exceptions import exceptions


def grant_group_role(group_name: str, config_file: str = "config/config.json"):
    client = get_client(config_file)
    config = load_config(config_file)
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
