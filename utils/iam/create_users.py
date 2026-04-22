from config.connection import get_client, load_config
from utils.convert_cvs import csv_to_iam_users
from utils.iam.create_user_group import create_user_group
from utils.iam.add_user_group import add_users_to_group
from utils.iam.grant_user_group import grant_group_role
from utils.vpc.create_vpc import create_vpc
from utils.vpc.create_user_subnets import create_user_subnets
from utils.ecs.create_user_ecs import create_user_ecs
from huaweicloudsdkiam.v3 import (
    CreateUserRequest,
    CreateUserRequestBody,
    CreateUserOption,
)
from huaweicloudsdkcore.exceptions import exceptions


def _print_summary(
    all_usernames: list[str],
    iam_created: list[str],
    iam_failed: list[str],
    subnets_created: dict,       # {username: subnet_id}
    ecs_report: dict | None,     # {'created': [...], 'failed': [...]} o None si no se llegó
):
    LINE = "─" * 54
    print(f"\n{'═' * 54}")
    print("[RESUMEN] Resultado de la operación")
    print(LINE)

    # IAM
    iam_skip = len(all_usernames) - len(iam_created) - len(iam_failed)
    print(f"  Usuarios IAM : {len(iam_created):>3} creados  "
          f"{len(iam_failed):>3} fallaron  {iam_skip:>3} omitidos")

    # Subnets
    if subnets_created is not None:
        subnets_failed_names = [u for u in iam_created if u not in subnets_created]
        print(f"  Subnets      : {len(subnets_created):>3} creadas   "
              f"{len(subnets_failed_names):>3} fallaron")
    else:
        print("  Subnets      :   — (no se intentó)")

    # ECS
    if ecs_report is not None:
        print(f"  ECS          : {len(ecs_report['created']):>3} creadas   "
              f"{len(ecs_report['failed']):>3} fallaron")
    else:
        print("  ECS          :   — (no se intentó)")

    # Recursos huérfanos
    orphaned = []
    if ecs_report and subnets_created:
        for username in ecs_report["failed"]:
            subnet_id = subnets_created.get(username)
            if subnet_id:
                orphaned.append((username, subnet_id))

    if iam_failed:
        print(f"\n  Usuarios IAM que fallaron:")
        for u in iam_failed:
            print(f"    • {u}")

    if orphaned:
        print(f"\n  Subnets huérfanas (ECS falló — subnet queda activa):")
        for username, subnet_id in orphaned:
            print(f"    • {username:<25}  subnet-id: {subnet_id}")
        print()
        print("  Para limpiarlas: Eliminar › Subnet individual")
        print("  (ingresa el nombre de subnet y el nombre del grupo como VPC)")

    print("═" * 54)


def create_users(
    csv_file: str,
    group_name: str = None,
    config_file: str = "config/config.json"
):
    client = get_client(config_file)
    config = load_config(config_file)
    domain_id = config["domain_id"]

    users = csv_to_iam_users(csv_file)
    all_usernames = [u["name"] for u in users]

    iam_created = []
    iam_failed = []

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
            iam_created.append(user["name"])

            estado = "habilitado" if user["enabled"] else "deshabilitado"
            print(f"[OK] Usuario creado: {response.user.name} ({estado})")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] {user['name']}: {e.error_msg}")
            iam_failed.append(user["name"])

    if not group_name:
        _print_summary(all_usernames, iam_created, iam_failed,
                       subnets_created=None, ecs_report=None)
        return

    if not iam_created:
        print("[AVISO] No se creó ningún usuario. Se omiten grupo, VPC y ECS.")
        _print_summary(all_usernames, iam_created, iam_failed,
                       subnets_created=None, ecs_report=None)
        return

    group = create_user_group(group_name, config_file=config_file)
    if not group:
        print("[AVISO] No se pudo crear el grupo. Se omiten membresía, política, VPC y ECS.")
        _print_summary(all_usernames, iam_created, iam_failed,
                       subnets_created=None, ecs_report=None)
        return

    add_users_to_group(iam_created, group_name, config_file=config_file)
    grant_group_role(group_name, config_file=config_file)

    vpc = create_vpc(vpc_name=group_name, cidr="10.0.0.0/16", config_file=config_file)
    if not vpc:
        print("[AVISO] No se pudo crear la VPC. Se omiten subnets y ECS.")
        _print_summary(all_usernames, iam_created, iam_failed,
                       subnets_created=None, ecs_report=None)
        return

    subnets_created = create_user_subnets(
        vpc_id=vpc.id,
        usernames=iam_created,
        config_file=config_file
    )

    if not subnets_created:
        print("[AVISO] No se creó ninguna subnet. Se omite la creación de ECS.")
        _print_summary(all_usernames, iam_created, iam_failed,
                       subnets_created=subnets_created, ecs_report=None)
        return

    ecs_report = create_user_ecs(
        vpc_id=vpc.id,
        user_subnets=subnets_created,
        config_file=config_file
    )

    _print_summary(all_usernames, iam_created, iam_failed,
                   subnets_created=subnets_created, ecs_report=ecs_report)
