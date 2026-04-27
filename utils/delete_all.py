import time
from config.connection import get_client, get_ecs_client, get_vpc_client, get_eps_client
from huaweicloudsdkiam.v3 import (
    KeystoneListGroupsRequest,
    KeystoneRemoveUserFromGroupRequest,
    KeystoneDeleteGroupRequest,
    KeystoneDeleteUserRequest,
    KeystoneListUsersForGroupByAdminRequest,
    KeystoneListUsersRequest,
)
from huaweicloudsdkecs.v2 import (
    ListServersDetailsRequest,
    DeleteServersRequest,
    ServerId,
    DeleteServersRequestBody,
)
from huaweicloudsdkvpc.v2 import (
    ListVpcsRequest,
    DeleteVpcRequest,
    ListSubnetsRequest,
    DeleteSubnetRequest,
)
from huaweicloudsdkeps.v1 import (
    ListEnterpriseProjectRequest,
    DisableEnterpriseProjectRequest,
    DisableAction,
    DeleteEnterpriseProjectRequest,
)
from huaweicloudsdkcore.exceptions import exceptions


def find_group(client, group_name: str):
    response = client.keystone_list_groups(KeystoneListGroupsRequest())
    for g in response.groups:
        if g.name == group_name:
            return g
    return None


def get_group_users(client, group_id: str) -> list:
    try:
        request = KeystoneListUsersForGroupByAdminRequest(group_id=group_id)
        response = client.keystone_list_users_for_group_by_admin(request)
        return response.users or []
    except exceptions.ClientRequestException as e:
        print(f"[WARN] No se pudieron listar usuarios del grupo: {e.error_msg}")
        return []


def delete_ecs_for_users(ecs_client, usernames: list[str]):
    try:
        response = ecs_client.list_servers_details(ListServersDetailsRequest())
        servers = response.servers or []

        to_delete = [
            s for s in servers
            if (s.metadata or {}).get("owner", "") in usernames
        ]

        if not to_delete:
            print("[INFO] No se encontraron ECS con tag owner de estos usuarios.")
            return

        del_request = DeleteServersRequest()
        del_request.body = DeleteServersRequestBody(
            delete_publicip=True,
            delete_volume=True,
            servers=[ServerId(id=s.id) for s in to_delete]
        )
        ecs_client.delete_servers(del_request)
        for s in to_delete:
            print(f"[OK] ECS eliminada: {s.name} ({s.id})")

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron eliminar ECS: {e.error_msg}")


def delete_subnets_and_vpc(vpc_client, group_name: str):
    try:
        vpcs = vpc_client.list_vpcs(ListVpcsRequest()).vpcs or []
        vpc = next((v for v in vpcs if v.name == group_name), None)
        if not vpc:
            print(f"[INFO] No se encontro VPC con nombre: {group_name}")
            return

        subnets = vpc_client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        for subnet in subnets:
            try:
                vpc_client.delete_subnet(DeleteSubnetRequest(vpc_id=vpc.id, subnet_id=subnet.id))
                print(f"[OK] Subnet eliminada: {subnet.name} ({subnet.id})")
            except exceptions.ClientRequestException as e:
                print(f"[ERROR] Subnet {subnet.name}: {e.error_msg}")

        print("[INFO] Esperando 10s para que las subnets se liberen...")
        time.sleep(10)

        vpc_client.delete_vpc(DeleteVpcRequest(vpc_id=vpc.id))
        print(f"[OK] VPC eliminada: {vpc.name} ({vpc.id})")

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] VPC/Subnets: {e.error_msg}")


def delete_perm_groups(iam_client, usernames: list[str]):
    perm_names = {f"perm-{u}" for u in usernames}
    try:
        all_groups = iam_client.keystone_list_groups(KeystoneListGroupsRequest()).groups or []
        perm_groups = [g for g in all_groups if g.name in perm_names]
        if not perm_groups:
            print("[INFO] No se encontraron grupos perm-{username}.")
            return
        for g in perm_groups:
            try:
                iam_client.keystone_delete_group(KeystoneDeleteGroupRequest(group_id=g.id))
                print(f"[OK] Grupo de permisos eliminado: {g.name}")
            except exceptions.ClientRequestException as e:
                print(f"[ERROR] No se pudo eliminar grupo {g.name}: {e.error_msg}")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar grupos: {e.error_msg}")


def delete_enterprise_projects(eps_client, usernames: list[str]):
    username_set = set(usernames)
    try:
        response = eps_client.list_enterprise_project(ListEnterpriseProjectRequest())
        projects = response.enterprise_projects or []
        matches = [p for p in projects if p.name in username_set]
        if not matches:
            print("[INFO] No se encontraron enterprise projects para estos usuarios.")
            return
        print("[INFO] Esperando 15s antes de deshabilitar enterprise projects...")
        time.sleep(15)
        for p in matches:
            try:
                disable_req = DisableEnterpriseProjectRequest()
                disable_req.enterprise_project_id = p.id
                disable_req.body = DisableAction(action="disable")
                eps_client.disable_enterprise_project(disable_req)
                print(f"[OK] Enterprise project deshabilitado: {p.name} ({p.id})")
            except exceptions.ClientRequestException as e:
                print(f"[WARN] No se pudo deshabilitar EP {p.name}: {e.error_msg}")

            print("[INFO] Esperando 15s antes de eliminar enterprise project...")
            time.sleep(15)
            try:
                delete_req = DeleteEnterpriseProjectRequest()
                delete_req.enterprise_project_id = p.id
                eps_client.delete_enterprise_project(delete_req)
                print(f"[OK] Enterprise project eliminado: {p.name} ({p.id})")
            except exceptions.ClientRequestException as e:
                print(f"[ERROR] No se pudo eliminar EP {p.name}: {e.error_msg}")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar enterprise projects: {e.error_msg}")


def delete_single_user(username: str, group_name: str, config_file: str = "config/config.json"):
    iam_client = get_client(config_file)
    ecs_client = get_ecs_client(config_file)
    eps_client = get_eps_client(config_file)

    try:
        response = iam_client.keystone_list_users(KeystoneListUsersRequest())
        user = next((u for u in response.users if u.name == username), None)
        if not user:
            print(f"[ERROR] Usuario no encontrado: {username}")
            return
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo listar usuarios: {e.error_msg}")
        return

    delete_ecs_for_users(ecs_client, [username])
    print("[INFO] Esperando 15s para que las ECS se liberen...")
    time.sleep(15)

    if group_name:
        group = find_group(iam_client, group_name)
        if group:
            try:
                iam_client.keystone_remove_user_from_group(
                    KeystoneRemoveUserFromGroupRequest(group_id=group.id, user_id=user.id)
                )
                print(f"[OK] Usuario removido del grupo: {username}")
            except exceptions.ClientRequestException as e:
                print(f"[WARN] No se pudo remover {username} del grupo: {e.error_msg}")

    delete_perm_groups(iam_client, [username])
    delete_enterprise_projects(eps_client, [username])

    try:
        iam_client.keystone_delete_user(KeystoneDeleteUserRequest(user_id=user.id))
        print(f"[OK] Usuario eliminado: {username}")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo eliminar usuario {username}: {e.error_msg}")


def delete_single_ecs(server_name: str, config_file: str = "config/config.json"):
    ecs_client = get_ecs_client(config_file)
    try:
        response = ecs_client.list_servers_details(ListServersDetailsRequest())
        server = next((s for s in (response.servers or []) if s.name == server_name), None)
        if not server:
            print(f"[ERROR] ECS no encontrada: {server_name}")
            return

        del_request = DeleteServersRequest()
        del_request.body = DeleteServersRequestBody(
            delete_publicip=True,
            delete_volume=True,
            servers=[ServerId(id=server.id)]
        )
        ecs_client.delete_servers(del_request)
        print(f"[OK] ECS eliminada: {server.name} ({server.id})")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo eliminar la ECS '{server_name}': {e.error_msg}")


def delete_single_subnet(subnet_name: str, vpc_name: str, config_file: str = "config/config.json"):
    vpc_client = get_vpc_client(config_file)
    try:
        vpcs = vpc_client.list_vpcs(ListVpcsRequest()).vpcs or []
        vpc = next((v for v in vpcs if v.name == vpc_name), None)
        if not vpc:
            print(f"[ERROR] VPC no encontrada: {vpc_name}")
            return

        subnets = vpc_client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        subnet = next((s for s in subnets if s.name == subnet_name), None)
        if not subnet:
            print(f"[ERROR] Subnet no encontrada: {subnet_name}")
            return

        try:
            vpc_client.delete_subnet(DeleteSubnetRequest(vpc_id=vpc.id, subnet_id=subnet.id))
            print(f"[OK] Subnet eliminada: {subnet.name} ({subnet.id})")
        except exceptions.ClientRequestException as e:
            print(f"[ERROR] No se pudo eliminar la subnet '{subnet_name}': {e.error_msg}")
            print("[TIP] Verifica que no haya ECS activas dentro de esta subnet.")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] Error al buscar subnets: {e.error_msg}")


def delete_single_vpc(vpc_name: str, config_file: str = "config/config.json"):
    vpc_client = get_vpc_client(config_file)
    try:
        vpcs = vpc_client.list_vpcs(ListVpcsRequest()).vpcs or []
        vpc = next((v for v in vpcs if v.name == vpc_name), None)
        if not vpc:
            print(f"[ERROR] VPC no encontrada: {vpc_name}")
            return

        subnets = vpc_client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        if subnets:
            print(f"[ERROR] La VPC '{vpc_name}' aun tiene {len(subnets)} subnet(s). Eliminalas primero.")
            return

        try:
            vpc_client.delete_vpc(DeleteVpcRequest(vpc_id=vpc.id))
            print(f"[OK] VPC eliminada: {vpc.name} ({vpc.id})")
        except exceptions.ClientRequestException as e:
            print(f"[ERROR] No se pudo eliminar la VPC '{vpc_name}': {e.error_msg}")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] Error al buscar VPCs: {e.error_msg}")


def delete_all(group_name: str, config_file: str = "config/config.json"):
    iam_client = get_client(config_file)
    ecs_client = get_ecs_client(config_file)
    vpc_client = get_vpc_client(config_file)
    eps_client = get_eps_client(config_file)

    group = find_group(iam_client, group_name)
    if not group:
        print(f"[ERROR] Grupo no encontrado: {group_name}")
        return

    users = get_group_users(iam_client, group.id)
    usernames = [u.name for u in users]
    user_ids = {u.name: u.id for u in users}
    print(f"[INFO] Usuarios en el grupo: {usernames or 'ninguno'}")

    if usernames:
        delete_ecs_for_users(ecs_client, usernames)
        print("[INFO] Esperando 15s para que las ECS se liberen...")
        time.sleep(15)

    delete_subnets_and_vpc(vpc_client, group_name)

    if usernames:
        delete_perm_groups(iam_client, usernames)

    for username, user_id in user_ids.items():
        try:
            iam_client.keystone_remove_user_from_group(
                KeystoneRemoveUserFromGroupRequest(group_id=group.id, user_id=user_id)
            )
            print(f"[OK] Usuario removido del grupo: {username}")
        except exceptions.ClientRequestException as e:
            print(f"[WARN] No se pudo remover {username} del grupo: {e.error_msg}")

        try:
            iam_client.keystone_delete_user(KeystoneDeleteUserRequest(user_id=user_id))
            print(f"[OK] Usuario eliminado: {username}")
        except exceptions.ClientRequestException as e:
            print(f"[ERROR] No se pudo eliminar usuario {username}: {e.error_msg}")

    try:
        iam_client.keystone_delete_group(KeystoneDeleteGroupRequest(group_id=group.id))
        print(f"[OK] Grupo eliminado: {group_name}")
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo eliminar el grupo: {e.error_msg}")

    if usernames:
        print("[INFO] Esperando 30s para que se liberen los recursos del EP...")
        time.sleep(30)
        delete_enterprise_projects(eps_client, usernames)
