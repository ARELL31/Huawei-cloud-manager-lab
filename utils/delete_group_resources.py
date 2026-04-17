import json
import time
from config.connection import get_client, get_ecs_client
from huaweicloudsdkiam.v3 import (
    KeystoneListUsersRequest,
    KeystoneListGroupsRequest,
    KeystoneListProjectPermissionsForGroupRequest,
    KeystoneRemoveProjectPermissionFromGroupRequest,
    KeystoneListGroupsForUserRequest,
    KeystoneRemoveUserFromGroupRequest,
    KeystoneDeleteGroupRequest,
    KeystoneDeleteUserRequest,
)
from huaweicloudsdkecs.v2 import (
    ListServersDetailsRequest,
    DeleteServersRequest,
    ServerId,
    DeleteServersRequestBody,
)
from huaweicloudsdkvpc.v2 import (
    VpcClient,
    ListVpcsRequest,
    DeleteVpcRequest,
    ListSubnetsRequest,
    DeleteSubnetRequest,
)
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions


def get_vpc_client(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    credentials = BasicCredentials(config["ak"], config["sk"], config["project_id"])
    return (
        VpcClient.new_builder()
        .with_credentials(credentials)
        .with_region(VpcRegion.value_of(config["region"]))
        .build()
    )


def find_group(client, group_name: str):
    response = client.keystone_list_groups(KeystoneListGroupsRequest())
    for g in response.groups:
        if g.name == group_name:
            return g
    return None


def get_group_users(client, group_id: str) -> list:
    from huaweicloudsdkiam.v3 import KeystoneListUsersForGroupByAdminRequest
    try:
        request = KeystoneListUsersForGroupByAdminRequest(group_id=group_id)
        response = client.keystone_list_users_for_group_by_admin(request)
        return response.users or []
    except exceptions.ClientRequestException as e:
        print(f"[WARN] No se pudieron listar usuarios del grupo: {e.error_msg}")
        return []


def delete_ecs_for_users(ecs_client, usernames: list[str]):
    try:
        request = ListServersDetailsRequest()
        response = ecs_client.list_servers_details(request)
        servers = response.servers or []

        to_delete = []
        for server in servers:
            owner = (server.metadata or {}).get("owner", "")
            if owner in usernames:
                to_delete.append(server)

        if not to_delete:
            print("[INFO] No se encontraron ECS con tag owner de estos usuarios.")
            return

        server_ids = [ServerId(id=s.id) for s in to_delete]
        del_request = DeleteServersRequest()
        del_request.body = DeleteServersRequestBody(
            delete_publicip=True,
            delete_volume=True,
            servers=server_ids
        )
        ecs_client.delete_servers(del_request)
        for s in to_delete:
            print(f"[OK] ECS eliminada: {s.name} ({s.id})")

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron eliminar ECS: {e.error_msg}")


def delete_subnets_and_vpc(vpc_client, group_name: str, config_file: str):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    project_id = config["project_id"]

    try:
        vpcs = vpc_client.list_vpcs(ListVpcsRequest()).vpcs or []
        vpc = next((v for v in vpcs if v.name == group_name), None)
        if not vpc:
            print(f"[INFO] No se encontro VPC con nombre: {group_name}")
            return

        subnets = vpc_client.list_subnets(ListSubnetsRequest(vpc_id=vpc.id)).subnets or []
        for subnet in subnets:
            try:
                vpc_client.delete_subnet(DeleteSubnetRequest(
                    vpc_id=vpc.id,
                    subnet_id=subnet.id
                ))
                print(f"[OK] Subnet eliminada: {subnet.name} ({subnet.id})")
            except exceptions.ClientRequestException as e:
                print(f"[ERROR] Subnet {subnet.name}: {e.error_msg}")

        print("[INFO] Esperando 10s para que las subnets se liberen...")
        time.sleep(10)

        vpc_client.delete_vpc(DeleteVpcRequest(vpc_id=vpc.id))
        print(f"[OK] VPC eliminada: {vpc.name} ({vpc.id})")

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] VPC/Subnets: {e.error_msg}")


def delete_group_resources(group_name: str, config_file: str = "config/config.json"):
    iam_client = get_client(config_file)
    ecs_client = get_ecs_client(config_file)
    vpc_client = get_vpc_client(config_file)

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

    delete_subnets_and_vpc(vpc_client, group_name, config_file)

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