import sys
from utils.iam.create_users import create_users
from utils.iam.enable_users import enable_users
from utils.iam.disable_users import disable_users
from utils.delete_all import delete_all, delete_single_user, delete_single_ecs, delete_single_subnet, delete_single_vpc
from utils.list_resources import (
    list_groups,
    list_group_users,
    list_ecs_for_group,
    list_ecs_for_user,
    list_vpcs,
    list_subnets_for_vpc,
)

MENU_PRINCIPAL = """
==============================
   Huawei Cloud IAM Manager
==============================
1. Crear
2. Eliminar
3. Listar
------------------------------
0. Salir
------------------------------
Selecciona una opcion: """

MENU_CREAR = """
--- Crear --------------------
1. Crear usuarios desde CSV
2. Habilitar usuarios desde CSV
3. Deshabilitar usuarios desde CSV
------------------------------
0. Volver
------------------------------
Selecciona una opcion: """

MENU_ELIMINAR = """
--- Eliminar -----------------
1. Eliminar grupo y sus recursos
2. Eliminar usuario individual
3. Eliminar ECS individual
4. Eliminar Subnet individual
5. Eliminar VPC individual
------------------------------
0. Volver
------------------------------
Selecciona una opcion: """

MENU_LISTAR = """
--- Listar -------------------
1. Listar grupos IAM
2. Listar usuarios de un grupo
3. Listar ECS de un grupo
4. Listar ECS de un usuario
5. Listar VPCs
6. Listar Subnets de una VPC
------------------------------
0. Volver
------------------------------
Selecciona una opcion: """


def pedir_csv():
    csv_file = input("Ruta del archivo CSV: ").strip()
    if not csv_file:
        print("[AVISO] No ingresaste una ruta.")
        return None
    return csv_file


# --- Handlers de Crear ---

def menu_crear_usuarios():
    csv_file = pedir_csv()
    if not csv_file:
        return
    group_name = input("Nombre del grupo a crear al finalizar (Enter para omitir): ").strip()
    if not group_name:
        print("[AVISO] No ingresaste nombre de grupo. Solo se crearan los usuarios.")
        create_users(csv_file)
        return
    create_users(csv_file, group_name=group_name)


def menu_habilitar_usuarios():
    csv_file = pedir_csv()
    if csv_file:
        enable_users(csv_file)


def menu_deshabilitar_usuarios():
    csv_file = pedir_csv()
    if csv_file:
        disable_users(csv_file)


# --- Handlers de Eliminar ---

def menu_eliminar_grupo():
    group_name = input("Nombre del grupo a eliminar (y todos sus recursos): ").strip()
    if not group_name:
        print("[AVISO] No ingresaste nombre de grupo.")
        return
    confirm = input(f"Esto eliminara usuarios, ECS, subnets y VPC del grupo '{group_name}'. Confirmar? (s/n): ").strip().lower()
    if confirm != "s":
        print("[AVISO] Operacion cancelada.")
        return
    delete_all(group_name)


def menu_eliminar_usuario():
    username = input("Nombre del usuario a eliminar: ").strip()
    if not username:
        print("[AVISO] No ingresaste nombre de usuario.")
        return
    group_name = input("Nombre del grupo al que pertenece (Enter para omitir): ").strip()
    confirm = input(f"Esto eliminara al usuario '{username}' y sus ECS. Confirmar? (s/n): ").strip().lower()
    if confirm != "s":
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_user(username, group_name)


def menu_eliminar_ecs():
    server_name = input("Nombre de la ECS a eliminar: ").strip()
    if not server_name:
        print("[AVISO] No ingresaste nombre de ECS.")
        return
    confirm = input(f"Esto eliminara la ECS '{server_name}' junto con su volumen e IP publica. Confirmar? (s/n): ").strip().lower()
    if confirm != "s":
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_ecs(server_name)


def menu_eliminar_subnet():
    subnet_name = input("Nombre de la Subnet a eliminar: ").strip()
    if not subnet_name:
        print("[AVISO] No ingresaste nombre de subnet.")
        return
    vpc_name = input("Nombre de la VPC a la que pertenece: ").strip()
    if not vpc_name:
        print("[AVISO] No ingresaste nombre de VPC.")
        return
    confirm = input(f"Esto eliminara la subnet '{subnet_name}' de la VPC '{vpc_name}'. Confirmar? (s/n): ").strip().lower()
    if confirm != "s":
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_subnet(subnet_name, vpc_name)


def menu_eliminar_vpc():
    vpc_name = input("Nombre de la VPC a eliminar: ").strip()
    if not vpc_name:
        print("[AVISO] No ingresaste nombre de VPC.")
        return
    confirm = input(f"Esto eliminara la VPC '{vpc_name}' (debe no tener subnets). Confirmar? (s/n): ").strip().lower()
    if confirm != "s":
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_vpc(vpc_name)


# --- Handlers de Listar ---

def menu_listar_grupos():
    list_groups()


def menu_listar_usuarios_grupo():
    group_name = input("Nombre del grupo: ").strip()
    if not group_name:
        print("[AVISO] No ingresaste nombre de grupo.")
        return
    list_group_users(group_name)


def menu_listar_ecs_grupo():
    group_name = input("Nombre del grupo: ").strip()
    if not group_name:
        print("[AVISO] No ingresaste nombre de grupo.")
        return
    list_ecs_for_group(group_name)


def menu_listar_ecs_usuario():
    username = input("Nombre del usuario: ").strip()
    if not username:
        print("[AVISO] No ingresaste nombre de usuario.")
        return
    list_ecs_for_user(username)


def menu_listar_vpcs():
    list_vpcs()


def menu_listar_subnets():
    vpc_name = input("Nombre de la VPC: ").strip()
    if not vpc_name:
        print("[AVISO] No ingresaste nombre de VPC.")
        return
    list_subnets_for_vpc(vpc_name)


# --- Submenus ---

OPCIONES_CREAR = {
    "1": menu_crear_usuarios,
    "2": menu_habilitar_usuarios,
    "3": menu_deshabilitar_usuarios,
}

OPCIONES_ELIMINAR = {
    "1": menu_eliminar_grupo,
    "2": menu_eliminar_usuario,
    "3": menu_eliminar_ecs,
    "4": menu_eliminar_subnet,
    "5": menu_eliminar_vpc,
}

OPCIONES_LISTAR = {
    "1": menu_listar_grupos,
    "2": menu_listar_usuarios_grupo,
    "3": menu_listar_ecs_grupo,
    "4": menu_listar_ecs_usuario,
    "5": menu_listar_vpcs,
    "6": menu_listar_subnets,
}


def submenu(prompt: str, opciones: dict):
    while True:
        opcion = input(prompt).strip()
        if opcion == "0":
            return
        action = opciones.get(opcion)
        if action:
            action()
        else:
            print("[AVISO] Opcion no valida, intenta de nuevo.")


# --- Menu principal ---

OPCIONES_PRINCIPAL = {
    "1": lambda: submenu(MENU_CREAR, OPCIONES_CREAR),
    "2": lambda: submenu(MENU_ELIMINAR, OPCIONES_ELIMINAR),
    "3": lambda: submenu(MENU_LISTAR, OPCIONES_LISTAR),
}


def main():
    while True:
        opcion = input(MENU_PRINCIPAL).strip()
        if opcion == "0":
            print("Saliendo...")
            sys.exit(0)
        action = OPCIONES_PRINCIPAL.get(opcion)
        if action:
            action()
        else:
            print("[AVISO] Opcion no valida, intenta de nuevo.")


if __name__ == "__main__":
    main()
