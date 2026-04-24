from config.connection import get_client, get_ecs_client
from utils.iam.helpers import find_group_id
from huaweicloudsdkiam.v3 import KeystoneListUsersForGroupByAdminRequest
from huaweicloudsdkecs.v2 import (
    ListServersDetailsRequest,
    BatchStartServersRequest, BatchStartServersRequestBody, BatchStartServersOption,
    BatchStopServersRequest, BatchStopServersRequestBody, BatchStopServersOption,
    BatchRebootServersRequest, BatchRebootServersRequestBody, BatchRebootSeversOption,
    ListResizeFlavorsRequest,
    ResizeServerRequest, ResizeServerRequestBody, ResizePrePaidServerOption,
    ServerId,
)
from huaweicloudsdkcore.exceptions import exceptions


def get_servers_for_user(username: str, config_file: str = "config/config.json") -> list:
    ecs_client = get_ecs_client(config_file)
    try:
        servers = ecs_client.list_servers_details(ListServersDetailsRequest()).servers or []
        return [s for s in servers if (s.metadata or {}).get("owner", "") == username]
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar ECS: {e.error_msg}")
        return []


def get_servers_for_group(group_name: str, config_file: str = "config/config.json") -> list:
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
        print(f"[ERROR] No se pudieron listar usuarios: {e.error_msg}")
        return []

    try:
        servers = ecs_client.list_servers_details(ListServersDetailsRequest()).servers or []
        return [s for s in servers if (s.metadata or {}).get("owner", "") in usernames]
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar ECS: {e.error_msg}")
        return []


def _server_ids(servers: list) -> list[ServerId]:
    return [ServerId(id=s.id) for s in servers]


def batch_start(servers: list, config_file: str = "config/config.json") -> str | None:
    """Inicia las instancias. Retorna job_id o None si falla."""
    ecs_client = get_ecs_client(config_file)
    try:
        req = BatchStartServersRequest()
        req.body = BatchStartServersRequestBody(
            os_start=BatchStartServersOption(servers=_server_ids(servers))
        )
        resp = ecs_client.batch_start_servers(req)
        print(f"[OK] Inicio enviado — {len(servers)} ECS · job_id: {resp.job_id}")
        return resp.job_id
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo iniciar ECS: {e.error_msg}")
        return None


def batch_stop(servers: list, force: bool = False,
               config_file: str = "config/config.json") -> str | None:
    """Detiene las instancias. force=True usa HARD (corte inmediato)."""
    ecs_client = get_ecs_client(config_file)
    stop_type = "HARD" if force else "SOFT"
    try:
        req = BatchStopServersRequest()
        req.body = BatchStopServersRequestBody(
            os_stop=BatchStopServersOption(servers=_server_ids(servers), type=stop_type)
        )
        resp = ecs_client.batch_stop_servers(req)
        print(f"[OK] Detención enviada ({stop_type}) — {len(servers)} ECS · job_id: {resp.job_id}")
        return resp.job_id
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo detener ECS: {e.error_msg}")
        return None


def batch_reboot(servers: list, force: bool = False,
                 config_file: str = "config/config.json") -> str | None:
    """Reinicia las instancias. force=True usa HARD (reinicio forzado)."""
    ecs_client = get_ecs_client(config_file)
    reboot_type = "HARD" if force else "SOFT"
    try:
        req = BatchRebootServersRequest()
        req.body = BatchRebootServersRequestBody(
            reboot=BatchRebootSeversOption(servers=_server_ids(servers), type=reboot_type)
        )
        resp = ecs_client.batch_reboot_servers(req)
        print(f"[OK] Reinicio enviado ({reboot_type}) — {len(servers)} ECS · job_id: {resp.job_id}")
        return resp.job_id
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo reiniciar ECS: {e.error_msg}")
        return None


def list_resize_flavors(server_id: str, config_file: str = "config/config.json") -> list:
    """Retorna los flavors disponibles para cambiar en la instancia dada."""
    ecs_client = get_ecs_client(config_file)
    try:
        resp = ecs_client.list_resize_flavors(
            ListResizeFlavorsRequest(instance_uuid=server_id)
        )
        return resp.flavors or []
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudieron listar flavors: {e.error_msg}")
        return []


def resize_server(server_id: str, flavor_ref: str,
                  config_file: str = "config/config.json") -> bool:
    """Cambia el flavor (vCPUs/RAM) de la instancia. Retorna True si la petición fue aceptada."""
    ecs_client = get_ecs_client(config_file)
    try:
        req = ResizeServerRequest(server_id=server_id)
        req.body = ResizeServerRequestBody(
            resize=ResizePrePaidServerOption(flavor_ref=flavor_ref)
        )
        ecs_client.resize_server(req)
        print(f"[OK] Cambio de flavor enviado → {flavor_ref} · server_id: {server_id}")
        return True
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo cambiar el flavor: {e.error_msg}")
        return False
