import argparse
import os
import sys
from datetime import datetime

from utils.iam.create_users import create_users
from utils.iam.enable_users import enable_users
from utils.iam.disable_users import disable_users
from utils.delete_all import (
    delete_all, delete_single_user, delete_single_ecs,
    delete_single_subnet, delete_single_vpc,
)
from utils.csv_validator import validate_csv
from utils.list_resources import (
    list_groups, list_group_users,
    list_ecs_for_group, list_ecs_for_user,
    list_vpcs, list_subnets_for_vpc,
)
from utils.ecs.manage_ecs import (
    get_servers_for_group, get_servers_for_user,
    batch_start, batch_stop, batch_reboot,
    list_resize_flavors, resize_server,
)
from utils.export_snapshot import collect_snapshot, write_csv, write_json

# ── Menús ─────────────────────────────────────────────────────────────────────

MENU_PRINCIPAL = """
==============================
   Huawei Cloud Computer Laboratory
==============================
1. Crear
2. Eliminar
3. Gestión ECS
4. Listar
5. Exportar
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

MENU_ECS = """
--- Gestión ECS --------------
1. Iniciar ECS
2. Detener ECS
3. Reiniciar ECS
4. Cambiar flavor (upgrade/downgrade)
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

MENU_EXPORTAR = """
--- Exportar -----------------
1. Exportar snapshot en CSV
2. Exportar snapshot en JSON
------------------------------
0. Volver
------------------------------
Selecciona una opcion: """

# ── Helpers comunes ───────────────────────────────────────────────────────────

def pedir_csv():
    path = input("Ruta del archivo CSV: ").strip()
    if not path:
        print("[AVISO] No ingresaste una ruta.")
        return None
    return path


def confirmar(mensaje: str) -> bool:
    return input(f"{mensaje} (s/n): ").strip().lower() == "s"


def _pedir_objetivo() -> list | None:
    """Pide grupo o usuario y devuelve la lista de servidores encontrados."""
    tipo = input("Buscar por (g=Grupo / u=Usuario): ").strip().lower()
    if tipo not in ("g", "u"):
        print("[AVISO] Opcion invalida.")
        return None
    nombre = input("Nombre: ").strip()
    if not nombre:
        print("[AVISO] El nombre no puede estar vacio.")
        return None

    print("[INFO] Buscando ECS...")
    servers = get_servers_for_group(nombre) if tipo == "g" else get_servers_for_user(nombre)

    if not servers:
        print("[INFO] No se encontraron instancias.")
        return None

    print(f"\n{len(servers)} instancia(s) encontrada(s):")
    for i, s in enumerate(servers, 1):
        owner = (s.metadata or {}).get("owner", "—")
        print(f"  {i}. {s.name:<30} {owner:<25} [{s.status}]")
    return servers


def _elegir_servidor(servers: list):
    """Pide al usuario que elija uno de los servidores listados."""
    if len(servers) == 1:
        return servers[0]
    while True:
        try:
            idx = int(input("Numero de la instancia: ").strip()) - 1
            if 0 <= idx < len(servers):
                return servers[idx]
            print("[AVISO] Numero fuera de rango.")
        except ValueError:
            print("[AVISO] Ingresa un numero valido.")

# ── Crear ─────────────────────────────────────────────────────────────────────

def menu_crear_usuarios():
    csv_file = pedir_csv()
    if not csv_file:
        return
    if not validate_csv(csv_file):
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

# ── Eliminar ──────────────────────────────────────────────────────────────────

def menu_eliminar_grupo():
    group_name = input("Nombre del grupo a eliminar (y todos sus recursos): ").strip()
    if not group_name:
        print("[AVISO] No ingresaste nombre de grupo.")
        return
    if not confirmar(f"Esto eliminara usuarios, ECS, subnets y VPC del grupo '{group_name}'."):
        print("[AVISO] Operacion cancelada.")
        return
    delete_all(group_name)


def menu_eliminar_usuario():
    username = input("Nombre del usuario a eliminar: ").strip()
    if not username:
        print("[AVISO] No ingresaste nombre de usuario.")
        return
    group_name = input("Nombre del grupo al que pertenece (Enter para omitir): ").strip()
    if not confirmar(f"Esto eliminara al usuario '{username}' y sus ECS."):
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_user(username, group_name)


def menu_eliminar_ecs():
    server_name = input("Nombre de la ECS a eliminar: ").strip()
    if not server_name:
        print("[AVISO] No ingresaste nombre de ECS.")
        return
    if not confirmar(f"Esto eliminara la ECS '{server_name}' junto con su volumen e IP publica."):
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
    if not confirmar(f"Esto eliminara la subnet '{subnet_name}' de la VPC '{vpc_name}'."):
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_subnet(subnet_name, vpc_name)


def menu_eliminar_vpc():
    vpc_name = input("Nombre de la VPC a eliminar: ").strip()
    if not vpc_name:
        print("[AVISO] No ingresaste nombre de VPC.")
        return
    if not confirmar(f"Esto eliminara la VPC '{vpc_name}' (debe no tener subnets)."):
        print("[AVISO] Operacion cancelada.")
        return
    delete_single_vpc(vpc_name)

# ── Gestión ECS ───────────────────────────────────────────────────────────────

def menu_ecs_iniciar():
    servers = _pedir_objetivo()
    if not servers:
        return
    if not confirmar(f"Iniciar {len(servers)} instancia(s)?"):
        print("[AVISO] Operacion cancelada.")
        return
    batch_start(servers)


def menu_ecs_detener():
    servers = _pedir_objetivo()
    if not servers:
        return
    force = input("Forzar apagado (HARD)? (s/n, Enter=no): ").strip().lower() == "s"
    modo = " (HARD)" if force else " (SOFT)"
    if not confirmar(f"Detener{modo} {len(servers)} instancia(s)?"):
        print("[AVISO] Operacion cancelada.")
        return
    batch_stop(servers, force=force)


def menu_ecs_reiniciar():
    servers = _pedir_objetivo()
    if not servers:
        return
    force = input("Forzar reinicio (HARD)? (s/n, Enter=no): ").strip().lower() == "s"
    modo = " (HARD)" if force else " (SOFT)"
    if not confirmar(f"Reiniciar{modo} {len(servers)} instancia(s)?"):
        print("[AVISO] Operacion cancelada.")
        return
    batch_reboot(servers, force=force)


def menu_ecs_resize():
    servers = _pedir_objetivo()
    if not servers:
        return

    server = _elegir_servidor(servers)

    current = getattr(server.flavor, "name", "—") if server.flavor else "—"
    print(f"\n[INFO] Instancia: {server.name}  |  Flavor actual: {current}")
    print("[INFO] Cargando flavors disponibles...")
    flavors = list_resize_flavors(server.id)

    if not flavors:
        print("[AVISO] No se encontraron flavors disponibles para esta instancia.")
        return

    flavors_sorted = sorted(flavors, key=lambda f: (int(f.vcpus or 0), int(f.ram or 0)))
    print(f"\n{len(flavors_sorted)} flavor(s) disponibles:")
    print(f"  {'#':<4} {'Nombre':<25} {'vCPU':>5} {'RAM (GB)':>10}  ID")
    print(f"  {'-'*4} {'-'*25} {'-'*5} {'-'*10}  {'-'*36}")
    for i, f in enumerate(flavors_sorted, 1):
        ram_gb = round(int(f.ram or 0) / 1024, 1)
        print(f"  {i:<4} {f.name or '':<25} {str(f.vcpus or ''):>5} {ram_gb:>10}  {f.id}")

    chosen = _elegir_servidor(flavors_sorted)

    if not confirmar(f"Cambiar '{server.name}' de {current} a {chosen.name}?"):
        print("[AVISO] Operacion cancelada.")
        return
    resize_server(server.id, chosen.id)

# ── Listar ────────────────────────────────────────────────────────────────────

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

# ── Exportar ──────────────────────────────────────────────────────────────────

def _menu_exportar(fmt: str):
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    default = os.path.join("exports", f"snapshot_{ts}.{fmt.lower()}")
    path = input(f"Ruta de salida [{default}]: ").strip() or default

    print("\n[INFO] Recolectando datos del cloud...")
    snapshot = collect_snapshot()

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    writer = write_csv if fmt == "CSV" else write_json
    n_groups, n_users, n_ecs = writer(snapshot, path)

    print(f"[OK] Snapshot exportado — {n_groups} grupo(s), {n_users} usuario(s), {n_ecs} ECS")
    print(f"[OK] Archivo: {os.path.abspath(path)}")


def menu_exportar_csv():
    _menu_exportar("CSV")


def menu_exportar_json():
    _menu_exportar("JSON")

# ── Tablas de opciones ────────────────────────────────────────────────────────

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

OPCIONES_ECS = {
    "1": menu_ecs_iniciar,
    "2": menu_ecs_detener,
    "3": menu_ecs_reiniciar,
    "4": menu_ecs_resize,
}

OPCIONES_LISTAR = {
    "1": menu_listar_grupos,
    "2": menu_listar_usuarios_grupo,
    "3": menu_listar_ecs_grupo,
    "4": menu_listar_ecs_usuario,
    "5": menu_listar_vpcs,
    "6": menu_listar_subnets,
}

OPCIONES_EXPORTAR = {
    "1": menu_exportar_csv,
    "2": menu_exportar_json,
}

# ── Bucle principal ───────────────────────────────────────────────────────────

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


OPCIONES_PRINCIPAL = {
    "1": lambda: submenu(MENU_CREAR,    OPCIONES_CREAR),
    "2": lambda: submenu(MENU_ELIMINAR, OPCIONES_ELIMINAR),
    "3": lambda: submenu(MENU_ECS,      OPCIONES_ECS),
    "4": lambda: submenu(MENU_LISTAR,   OPCIONES_LISTAR),
    "5": lambda: submenu(MENU_EXPORTAR, OPCIONES_EXPORTAR),
}

# ── CLI (argparse) ────────────────────────────────────────────────────────────

_ACTIONS = [
    "create", "enable", "disable",
    "delete-group", "delete-user", "delete-ecs", "delete-subnet", "delete-vpc",
    "start", "stop", "reboot", "resize",
    "list-groups", "list-users", "list-ecs-group", "list-ecs-user",
    "list-vpcs", "list-subnets",
    "export",
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Huawei Cloud IAM Manager — modo no interactivo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
acciones disponibles:
  create          Crear usuarios desde CSV         --csv FILE [--group NOMBRE]
  enable          Habilitar usuarios desde CSV      --csv FILE
  disable         Deshabilitar usuarios desde CSV   --csv FILE
  delete-group    Eliminar grupo y recursos         --group NOMBRE
  delete-user     Eliminar usuario                  --user NOMBRE [--group NOMBRE]
  delete-ecs      Eliminar ECS                      --ecs NOMBRE
  delete-subnet   Eliminar subnet                   --subnet NOMBRE --vpc NOMBRE
  delete-vpc      Eliminar VPC                      --vpc NOMBRE
  start           Iniciar ECS                       --group NOMBRE | --user NOMBRE
  stop            Detener ECS                       --group NOMBRE | --user NOMBRE [--force]
  reboot          Reiniciar ECS                     --group NOMBRE | --user NOMBRE [--force]
  resize          Cambiar flavor de ECS             --user NOMBRE --flavor ID
  list-groups     Listar grupos IAM
  list-users      Listar usuarios de un grupo       --group NOMBRE
  list-ecs-group  Listar ECS de un grupo            --group NOMBRE
  list-ecs-user   Listar ECS de un usuario          --user NOMBRE
  list-vpcs       Listar VPCs
  list-subnets    Listar subnets de una VPC         --vpc NOMBRE
  export          Exportar snapshot                 [--format csv|json] [--output FILE]

sin argumentos: abre el menú interactivo.
""",
    )
    parser.add_argument("--action",  choices=_ACTIONS, metavar="ACCION",
                        help="Acción a ejecutar (ver lista abajo)")
    parser.add_argument("--csv",     metavar="FILE",   help="Archivo CSV de usuarios")
    parser.add_argument("--group",   metavar="NOMBRE", help="Nombre del grupo IAM")
    parser.add_argument("--user",    metavar="NOMBRE", help="Nombre del usuario IAM")
    parser.add_argument("--ecs",     metavar="NOMBRE", help="Nombre de la ECS")
    parser.add_argument("--subnet",  metavar="NOMBRE", help="Nombre de la subnet")
    parser.add_argument("--vpc",     metavar="NOMBRE", help="Nombre de la VPC")
    parser.add_argument("--flavor",  metavar="ID",     help="ID del flavor destino (resize)")
    parser.add_argument("--force",   action="store_true",
                        help="Forzar apagado/reinicio (HARD) en stop/reboot")
    parser.add_argument("--format",  choices=["csv", "json"], default="csv",
                        help="Formato de exportación (default: csv)")
    parser.add_argument("--output",  metavar="FILE",   help="Archivo de salida para export")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Confirmar operaciones destructivas sin preguntar")
    return parser


def _need(args, *fields):
    """Aborta si algún campo requerido está ausente."""
    for f in fields:
        if not getattr(args, f, None):
            print(f"[ERROR] --{f} es requerido para '{args.action}'.")
            sys.exit(1)


def _need_target(args):
    """Aborta si no se indicó ni --group ni --user."""
    if not args.group and not args.user:
        print(f"[ERROR] Se requiere --group o --user para '{args.action}'.")
        sys.exit(1)


def _get_servers(args):
    servers = (get_servers_for_group(args.group) if args.group
               else get_servers_for_user(args.user))
    if not servers:
        print("[INFO] No se encontraron instancias.")
        sys.exit(0)
    return servers


def _ok(args, msg: str) -> bool:
    """Devuelve True si el usuario confirmó (o se pasó --yes)."""
    if args.yes:
        return True
    return confirmar(msg)


def _run_cli(args):
    action = args.action

    # ── Crear ──────────────────────────────────────────────────────────────
    if action == "create":
        _need(args, "csv")
        if not validate_csv(args.csv):
            sys.exit(1)
        create_users(args.csv, group_name=args.group or "")

    elif action == "enable":
        _need(args, "csv")
        enable_users(args.csv)

    elif action == "disable":
        _need(args, "csv")
        disable_users(args.csv)

    # ── Eliminar ───────────────────────────────────────────────────────────
    elif action == "delete-group":
        _need(args, "group")
        if not _ok(args, f"Eliminar grupo '{args.group}' y todos sus recursos?"):
            print("[AVISO] Operacion cancelada.")
            return
        delete_all(args.group)

    elif action == "delete-user":
        _need(args, "user")
        if not _ok(args, f"Eliminar usuario '{args.user}' y sus ECS?"):
            print("[AVISO] Operacion cancelada.")
            return
        delete_single_user(args.user, args.group or "")

    elif action == "delete-ecs":
        _need(args, "ecs")
        if not _ok(args, f"Eliminar ECS '{args.ecs}'?"):
            print("[AVISO] Operacion cancelada.")
            return
        delete_single_ecs(args.ecs)

    elif action == "delete-subnet":
        _need(args, "subnet", "vpc")
        if not _ok(args, f"Eliminar subnet '{args.subnet}' de VPC '{args.vpc}'?"):
            print("[AVISO] Operacion cancelada.")
            return
        delete_single_subnet(args.subnet, args.vpc)

    elif action == "delete-vpc":
        _need(args, "vpc")
        if not _ok(args, f"Eliminar VPC '{args.vpc}'?"):
            print("[AVISO] Operacion cancelada.")
            return
        delete_single_vpc(args.vpc)

    # ── ECS ────────────────────────────────────────────────────────────────
    elif action in ("start", "stop", "reboot"):
        _need_target(args)
        servers = _get_servers(args)
        modo = " (HARD)" if args.force else " (SOFT)"
        label = {"start": "Iniciar", "stop": f"Detener{modo}", "reboot": f"Reiniciar{modo}"}[action]
        if not _ok(args, f"{label} {len(servers)} instancia(s)?"):
            print("[AVISO] Operacion cancelada.")
            return
        if action == "start":
            batch_start(servers)
        elif action == "stop":
            batch_stop(servers, force=args.force)
        else:
            batch_reboot(servers, force=args.force)

    elif action == "resize":
        _need_target(args)
        _need(args, "flavor")
        servers = _get_servers(args)
        if len(servers) > 1:
            names = ", ".join(s.name for s in servers)
            print(f"[AVISO] Se encontraron {len(servers)} instancias: {names}")
            print(f"[AVISO] Se aplicara el resize solo a la primera: {servers[0].name}")
        server = servers[0]
        if not _ok(args, f"Cambiar flavor de '{server.name}' a '{args.flavor}'?"):
            print("[AVISO] Operacion cancelada.")
            return
        resize_server(server.id, args.flavor)

    # ── Listar ─────────────────────────────────────────────────────────────
    elif action == "list-groups":
        list_groups()

    elif action == "list-users":
        _need(args, "group")
        list_group_users(args.group)

    elif action == "list-ecs-group":
        _need(args, "group")
        list_ecs_for_group(args.group)

    elif action == "list-ecs-user":
        _need(args, "user")
        list_ecs_for_user(args.user)

    elif action == "list-vpcs":
        list_vpcs()

    elif action == "list-subnets":
        _need(args, "vpc")
        list_subnets_for_vpc(args.vpc)

    # ── Exportar ───────────────────────────────────────────────────────────
    elif action == "export":
        fmt = args.format.upper()
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        path = args.output or os.path.join("exports", f"snapshot_{ts}.{args.format}")
        print(f"\n[INFO] Recolectando datos del cloud...")
        snapshot = collect_snapshot()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        writer = write_csv if fmt == "CSV" else write_json
        n_groups, n_users, n_ecs = writer(snapshot, path)
        print(f"[OK] Snapshot exportado — {n_groups} grupo(s), {n_users} usuario(s), {n_ecs} ECS")
        print(f"[OK] Archivo: {os.path.abspath(path)}")


def main():
    if len(sys.argv) > 1:
        args = _build_parser().parse_args()
        if args.action is None:
            _build_parser().print_help()
            sys.exit(0)
        _run_cli(args)
        return

    # sin argumentos → menú interactivo
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
