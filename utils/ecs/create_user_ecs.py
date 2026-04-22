from config.connection import get_ecs_client, load_config
from huaweicloudsdkecs.v2 import (
    CreateServersRequest,
    CreateServersRequestBody,
    PrePaidServer,
    PrePaidServerRootVolume,
    PrePaidServerNic,
    PrePaidServerPublicip,
    PrePaidServerEip,
    PrePaidServerEipBandwidth,
)
from huaweicloudsdkcore.exceptions import exceptions


def create_user_ecs(
    vpc_id: str,
    user_subnets: dict,
    config_file: str = "config/config.json",
    on_progress=None,           # on_progress(current: int, total: int)
) -> dict:
    """
    Crea una ECS por usuario.
    Retorna {'created': [username, ...], 'failed': [username, ...]}.
    """
    client = get_ecs_client(config_file)
    ecs_config = load_config(config_file)["ecs"]

    created = []
    failed = []
    total = len(user_subnets)

    for i, (username, subnet_id) in enumerate(user_subnets.items(), start=1):
        try:
            root_volume = PrePaidServerRootVolume(
                volumetype=ecs_config.get("root_volume_type", "SSD"),
                size=ecs_config.get("root_volume_size", 40)
            )

            bandwidth = PrePaidServerEipBandwidth(
                size=5,
                sharetype="PER",
                chargemode="traffic"
            )
            publicip = PrePaidServerPublicip(
                eip=PrePaidServerEip(iptype="5_bgp", bandwidth=bandwidth)
            )

            server = PrePaidServer(
                image_ref=ecs_config["image_ref"],
                flavor_ref=ecs_config["flavor_ref"],
                name=f"ecs-{username}",
                vpcid=vpc_id,
                nics=[PrePaidServerNic(subnet_id=subnet_id)],
                publicip=publicip,
                root_volume=root_volume,
                metadata={"owner": username},
            )

            request = CreateServersRequest()
            request.body = CreateServersRequestBody(server=server)

            response = client.create_servers(request)
            print(f"[OK] ECS creada para {username}: {response.server_ids}")
            created.append(username)

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] ECS para {username}: {e.error_msg} (código: {e.status_code})")
            failed.append(username)

        if on_progress:
            on_progress(i, total)

    return {"created": created, "failed": failed}
