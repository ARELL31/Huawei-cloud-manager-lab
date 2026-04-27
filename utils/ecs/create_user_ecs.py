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
    PrePaidServerExtendParam,
)
from huaweicloudsdkcore.exceptions import exceptions


def create_user_ecs(
    vpc_id: str,
    user_subnets: dict,
    ep_ids: dict | None = None,
    group_name: str = "",
    config_file: str = "config/config.json",
    on_progress=None,
) -> dict:
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

            ep_id = (ep_ids or {}).get(username)
            extendparam = PrePaidServerExtendParam(
                enterprise_project_id=ep_id
            ) if ep_id else None

            admin_pass = f"{group_name}123!" if group_name else None

            server = PrePaidServer(
                image_ref=ecs_config["image_ref"],
                flavor_ref=ecs_config["flavor_ref"],
                name=f"ecs-{username}",
                vpcid=vpc_id,
                nics=[PrePaidServerNic(subnet_id=subnet_id)],
                publicip=publicip,
                root_volume=root_volume,
                admin_pass=admin_pass,
                metadata={"owner": username},
                extendparam=extendparam,
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
