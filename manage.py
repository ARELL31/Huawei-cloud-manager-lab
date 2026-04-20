import sys
from utils.iam.create_users import create_users
from utils.iam.enable_users import enable_users
from utils.iam.disable_users import disable_users
from utils.delete_all import delete_all, delete_single_user, delete_single_ecs, delete_single_subnet, delete_single_vpc


MENU = """
==============================
   Huawei Cloud IAM Manager
==============================
1. Crear usuarios desde CSV
2. Habilitar usuarios desde CSV
3. Deshabilitar usuarios desde CSV
4. Eliminar grupo y sus recursos
--- Eliminacion individual ---
5. Eliminar usuario individual
6. Eliminar ECS individual
7. Eliminar Subnet individual
8. Eliminar VPC individual
0. Salir
------------------------------
Selecciona una opcion: """


def pedir_csv():
    csv_file = input("Ruta del archivo CSV: ").strip()
    if not csv_file:
        print("[AVISO] No ingresaste una ruta.")
        return None
    return csv_file


def menu_crear_usuarios():
    csv_file = pedir_csv()
    if not csv_file:
        return
    group_name = input("Nombre del grupo a crear al finalizar: ").strip()
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
    group_name = input("Nombre del grupo al que pertenece (dejar vacio si no aplica): ").strip()
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


OPTIONS = {
    "1": menu_crear_usuarios,
    "2": menu_habilitar_usuarios,
    "3": menu_deshabilitar_usuarios,
    "4": menu_eliminar_grupo,
    "5": menu_eliminar_usuario,
    "6": menu_eliminar_ecs,
    "7": menu_eliminar_subnet,
    "8": menu_eliminar_vpc,
}


def main():
    while True:
        opcion = input(MENU).strip()
        if opcion == "0":
            print("Saliendo...")
            sys.exit(0)
        action = OPTIONS.get(opcion)
        if action:
            action()
        else:
            print("[AVISO] Opcion no valida, intenta de nuevo.")


if __name__ == "__main__":
    main()