import json
from config.connection import get_client
from utils.convert_cvs import csv_to_iam_users
from utils.create_user_group import create_user_group
from utils.add_user_group import add_users_to_group
from utils.grant_user_group import grant_group_role
from utils.create_vpc import create_vpc
from utils.create_user_subnets import create_user_subnets
from utils.create_user_ecs import create_user_ecs
from huaweicloudsdkiam.v3 import (
    CreateUserRequest,
    CreateUserRequestBody,
    CreateUserOption,
)
from huaweicloudsdkcore.exceptions import exceptions


def create_users(
    csv_file: str,
    group_name: str = None,
    config_file: str = "config/config.json"
):
    client = get_client(config_file)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    domain_id = config["domain_id"]
    users = csv_to_iam_users(csv_file)
    created_usernames = []

    for user in users:
        try:
            request = CreateUserRequest()
            userbody = CreateUserOption(
                name=user["name"],
                domain_id=domain_id,
                email=user["email"],
                password=user["password"],
                enabled=user["enabled"],
                pwd_status=True,
            )
            request.body = CreateUserRequestBody(user=userbody)

            response = client.create_user(request)
            created_usernames.append(user["name"])

            estado = "habilitado" if user["enabled"] else "deshabilitado"
            print(f"[OK] Usuario creado: {response.user.name} ({estado})")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] {user['name']}: {e.error_msg}")

    if not group_name:
        return

    if not created_usernames:
        print("[AVISO] No se crearon usuarios. No se creará grupo, política, VPC ni subnets.")
        return

    group = create_user_group(group_name, config_file=config_file)
    if not group:
        print("[AVISO] No se pudo crear el grupo. Se omiten membresía, política, VPC y subnets.")
        return

    add_users_to_group(created_usernames, group_name, config_file=config_file)
    grant_group_role(group_name, config_file=config_file)

    vpc = create_vpc(
        vpc_name=group_name,
        cidr="10.0.0.0/16",
        config_file=config_file
    )

    if not vpc:
        print("[AVISO] No se pudo crear el VPC. Se omiten subnets y ECS.")
        return

    user_subnets = create_user_subnets(
        vpc_id=vpc.id,
        usernames=created_usernames,
        config_file=config_file
    )

    if not user_subnets:
        print("[AVISO] No se crearon subnets. Se omite creación de ECS.")
        return

    create_user_ecs(
        vpc_id=vpc.id,
        user_subnets=user_subnets,
        config_file=config_file
    )

