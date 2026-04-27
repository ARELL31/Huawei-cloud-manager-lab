from config.connection import get_eps_client
from huaweicloudsdkeps.v1 import (
    CreateEnterpriseProjectRequest,
    EnterpriseProject,
)
from huaweicloudsdkcore.exceptions import exceptions


def create_enterprise_project(
    name: str,
    description: str = "",
    config_file: str = "config/config.json",
) -> str | None:
    client = get_eps_client(config_file)
    try:
        req = CreateEnterpriseProjectRequest()
        req.body = EnterpriseProject(name=name, description=description)
        resp = client.create_enterprise_project(req)
        ep_id = resp.enterprise_project.id
        print(f"[OK] Enterprise project creado: {name} ({ep_id})")
        return ep_id
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] Enterprise project '{name}': {e.error_msg}")
        return None


def create_enterprise_projects(
    usernames: list[str],
    config_file: str = "config/config.json",
    on_progress=None,
) -> dict[str, str]:
    ep_ids: dict[str, str] = {}
    total = len(usernames)
    for i, username in enumerate(usernames, start=1):
        ep_id = create_enterprise_project(
            name=username,
            description=f"Proyecto de {username}",
            config_file=config_file,
        )
        if ep_id:
            ep_ids[username] = ep_id
        if on_progress:
            on_progress(i, total)
    return ep_ids
