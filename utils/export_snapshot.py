import csv
import json
from datetime import datetime

from config.connection import get_client, get_ecs_client
from huaweicloudsdkiam.v3 import (
    KeystoneListGroupsRequest,
    KeystoneListUsersForGroupByAdminRequest,
)
from huaweicloudsdkecs.v2 import ListServersDetailsRequest
from huaweicloudsdkcore.exceptions import exceptions


def _extract_ips(server) -> list[str]:
    ips = []
    if not server.addresses:
        return ips
    for addrs in server.addresses.values():
        for addr in (addrs or []):
            if hasattr(addr, "addr") and addr.addr:
                ips.append(addr.addr)
    return ips


def collect_snapshot(
    config_file: str = "config/config.json",
    on_progress=None,
) -> list[dict]:
    """
    Retorna lista de grupos con sus usuarios y ECS.

    on_progress(current, total) se llama por cada grupo procesado.

    Estructura de cada elemento:
    {
        "nombre": str, "id": str,
        "usuarios": [
            {
                "nombre": str, "id": str, "estado": "habilitado"|"deshabilitado",
                "ecs": [{"nombre": str, "id": str, "estado": str, "ips": [str]}]
            }
        ]
    }
    """
    iam_client = get_client(config_file)
    ecs_client = get_ecs_client(config_file)

    groups_raw = iam_client.keystone_list_groups(
        KeystoneListGroupsRequest()
    ).groups or []

    all_servers = ecs_client.list_servers_details(
        ListServersDetailsRequest()
    ).servers or []

    servers_by_owner: dict[str, list] = {}
    for s in all_servers:
        owner = (s.metadata or {}).get("owner", "")
        if owner:
            servers_by_owner.setdefault(owner, []).append(s)

    total = len(groups_raw)
    snapshot = []

    for i, group in enumerate(groups_raw, 1):
        try:
            users_raw = iam_client.keystone_list_users_for_group_by_admin(
                KeystoneListUsersForGroupByAdminRequest(group_id=group.id)
            ).users or []
        except exceptions.ClientRequestException as e:
            print(f"[WARN] No se pudieron listar usuarios del grupo '{group.name}': {e.error_msg}")
            users_raw = []

        usuarios = []
        for user in users_raw:
            ecs_list = [
                {
                    "nombre": s.name,
                    "id":     s.id,
                    "estado": s.status,
                    "ips":    _extract_ips(s),
                }
                for s in servers_by_owner.get(user.name, [])
            ]
            usuarios.append({
                "nombre": user.name,
                "id":     user.id,
                "estado": "habilitado" if user.enabled else "deshabilitado",
                "ecs":    ecs_list,
            })

        snapshot.append({
            "nombre":   group.name,
            "id":       group.id,
            "usuarios": usuarios,
        })

        if on_progress:
            on_progress(i, total)

    return snapshot


_CSV_FIELDS = [
    "grupo_nombre", "grupo_id",
    "usuario_nombre", "usuario_id", "usuario_estado",
    "ecs_nombre", "ecs_id", "ecs_estado", "ecs_ips",
]


def write_csv(snapshot: list[dict], path: str) -> tuple[int, int, int]:
    """Escribe snapshot en CSV. Retorna (grupos, usuarios, ecs)."""
    n_groups = n_users = n_ecs = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for group in snapshot:
            n_groups += 1
            for user in group["usuarios"]:
                n_users += 1
                if user["ecs"]:
                    for ecs in user["ecs"]:
                        n_ecs += 1
                        writer.writerow({
                            "grupo_nombre":   group["nombre"],
                            "grupo_id":       group["id"],
                            "usuario_nombre": user["nombre"],
                            "usuario_id":     user["id"],
                            "usuario_estado": user["estado"],
                            "ecs_nombre":     ecs["nombre"],
                            "ecs_id":         ecs["id"],
                            "ecs_estado":     ecs["estado"],
                            "ecs_ips":        ", ".join(ecs["ips"]),
                        })
                else:
                    writer.writerow({
                        "grupo_nombre":   group["nombre"],
                        "grupo_id":       group["id"],
                        "usuario_nombre": user["nombre"],
                        "usuario_id":     user["id"],
                        "usuario_estado": user["estado"],
                        "ecs_nombre": "", "ecs_id": "",
                        "ecs_estado": "", "ecs_ips": "",
                    })
    return n_groups, n_users, n_ecs


def write_json(snapshot: list[dict], path: str) -> tuple[int, int, int]:
    """Escribe snapshot en JSON. Retorna (grupos, usuarios, ecs)."""
    n_groups = len(snapshot)
    n_users  = sum(len(g["usuarios"]) for g in snapshot)
    n_ecs    = sum(len(u["ecs"]) for g in snapshot for u in g["usuarios"])
    data = {
        "snapshot_at": datetime.now().isoformat(timespec="seconds"),
        "totales": {"grupos": n_groups, "usuarios": n_users, "ecs": n_ecs},
        "grupos": snapshot,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return n_groups, n_users, n_ecs
