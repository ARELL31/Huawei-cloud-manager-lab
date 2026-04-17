import sys
from utils.create_users import create_users
from utils.enable_users import enable_users
from utils.disable_users import disable_users
from utils.delete_group_resources import delete_group_resources  # <-- nuevo


MENU = """
==============================
   Huawei Cloud IAM Manager
==============================
1. Crear usuarios desde CSV
2. Habilitar usuarios desde CSV
3. Deshabilitar usuarios desde CSV
4. Eliminar grupo y sus recursos
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
    delete_group_resources(group_name)


OPTIONS = {
    "1": menu_crear_usuarios,
    "2": menu_habilitar_usuarios,
    "3": menu_deshabilitar_usuarios,
    "4": menu_eliminar_grupo,
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