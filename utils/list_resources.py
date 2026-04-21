from config.connection import get_client, get_ecs_client, get_vpc_client
from utils.iam.helpers import find_group_id
from huaweicloudsdkiam.v3 import (
    KeystoneListGroupsRequest,
    KeystoneListUsersForGroupByAdminRequest,
)
from huaweicloudsdkecs.v2 import ListServersDetailsRequest
from huaweicloudsdkvpc.v2 import ListVpcsRequest, ListSubnetsRequest
from huaweicloudsdkcore.exceptions import exceptions


def _print_table(headers: list[tuple[str, int]], rows: list[list[str]]):
    header_line = "  " + "  ".join(f"{h:<{w}}" for h, w in headers)
    separator = "  " + "  ".join("-" * w for _, w in headers)
    print(header_line)
    print(separator)
    for row in rows:
        print("  " + "  ".join(f"{str(v):<{w}}" for v, (_, w) in zip(row, headers)))


def list_groups(config_file: str = "config/config.json") -> list:
    client = get_client(config_file)
    try:
        groups = client.keystone_list_groups(KeystoneListGroupsRequest()).groups or []
        if not groups:
            print("[INFO] No se encontraron grupos.")
            return []

        print(f"\nGrupos IAM ({len(groups)} encontrados):")
        _print_table(
            [("Nombre", 35), ("ID", 40), ("Descripcion", 40)],
            [[g.name, g.id, g.description or "-"] for g in groups]
        )
        return groups
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar grupos: {e.error_msg}")
        return []


def list_group_users(group_name: str, config_file: str = "config/config.json") -> list:
    client = get_client(config_file)

    group_id = find_group_id(client, group_name)
    if not group_id:
        print(f"[ERROR] Grupo no encontrado: {group_name}")
        return []

    try:
        users = client.keystone_list_users_for_group_by_admin(
            KeystoneListUsersForGroupByAdminRequest(group_id=group_id)
        ).users or []

        if not users:
            print(f"[INFO] No hay usuarios en el grupo '{group_name}'.")
            return []

        print(f"\nUsuarios en el grupo '{group_name}' ({len(users)} encontrados):")
        _print_table(
            [("Nombre", 30), ("ID", 40), ("Estado", 15)],
            [[u.name, u.id, "Habilitado" if u.enabled else "Deshabilitado"] for u in users]
        )
        return users
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar usuarios del grupo: {e.error_msg}")
        return []


def list_ecs_for_user(username: str, config_file: str = "config/config.json") -> list:
    client = get_ecs_client(config_file)
    try:
        servers = [
            s for s in (client.list_servers_details(ListServersDetailsRequest()).servers or [])
            if (s.metadata or {}).get("owner", "") == username
        ]

        if not servers:
            print(f"[INFO] No se encontraron ECS para el usuario '{username}'.")
            return []

        print(f"\nECS del usuario '{username}' ({len(servers)} encontradas):")
        _print_table(
            [("Nombre", 30), ("ID", 40), ("Estado", 15)],
            [[s.name, s.id, s.status] for s in servers]
        )
        return servers
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar ECS: {e.error_msg}")
        return []


def list_ecs_for_group(group_name: str, config_file: str = "config/config.json") -> list:
    iam_client = get_client(config_file)
    ecs_client = get_ecs_client(config_file)

    group_id = find_group_id(iam_client, group_name)
    if not group_id:
        print(f"[ERROR] Grupo no encontrado: {group_name}")
        return []

    try:
        users = iam_client.keystone_list_users_for_group_by_admin(
            KeystoneListUsersForGroupByAdminRequest(group_id=group_id)
        ).users or []
        usernames = {u.name for u in users}
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar usuarios del grupo: {e.error_msg}")
        return []

    try:
        servers = [
            s for s in (ecs_client.list_servers_details(ListServersDetailsRequest()).servers or [])
            if (s.metadata or {}).get("owner", "") in usernames
        ]

        if not servers:
            print(f"[INFO] No se encontraron ECS para el grupo '{group_name}'.")
            return []

        print(f"\nECS del grupo '{group_name}' ({len(servers)} encontradas):")
        _print_table(
            [("Nombre", 30), ("Propietario", 25), ("ID", 40), ("Estado", 15)],
            [[s.name, (s.metadata or {}).get("owner", "-"), s.id, s.status] for s in servers]
        )
        return servers
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar ECS: {e.error_msg}")
        return []


def list_vpcs(config_file: str = "config/config.json") -> list:
    client = get_vpc_client(config_file)
    try:
        vpcs = client.list_vpcs(ListVpcsRequest()).vpcs or []

        if not vpcs:
            print("[INFO] No se encontraron VPCs.")
            return []

        print(f"\nVPCs disponibles ({len(vpcs)} encontradas):")
        _print_table(
            [("Nombre", 30), ("ID", 40), ("CIDR", 20), ("Estado", 15)],
            [[v.name, v.id, v.cidr, v.status] for v in vpcs]
        )
        return vpcs
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar VPCs: {e.error_msg}")
        return []


def list_subnets_for_vpc(vpc_name: str, config_file: str = "config/config.json") -> list:
    client = get_vpc_client(config_file)
    try:
        vpcs = client.list_vpcs(ListVpcsRequest()).vpcs or []
        vpc = next((v for v in vpcs if v.name == vpc_name), None)
        if not vpc:
            print(f"[ERROR] VPC no encontrada: {vpc_name}")
            return []

        subnets = client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        if not subnets:
            print(f"[INFO] No se encontraron subnets en la VPC '{vpc_name}'.")
            return []

        print(f"\nSubnets en la VPC '{vpc_name}' ({len(subnets)} encontradas):")
        _print_table(
            [("Nombre", 30), ("ID", 40), ("CIDR", 20), ("Estado", 15)],
            [[s.name, s.id, s.cidr, s.status] for s in subnets]
        )
        return subnets
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar subnets: {e.error_msg}")
        return []
