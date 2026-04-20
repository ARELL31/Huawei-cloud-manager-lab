import json
from config.connection import get_ecs_client
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
    config_file: str = "config/config.json"
):
    client = get_ecs_client(config_file)

    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    ecs_config = config["ecs"]

    for username, subnet_id in user_subnets.items():
        try:
            root_volume = PrePaidServerRootVolume(
                volumetype=ecs_config.get("root_volume_type", "SSD"),
                size=ecs_config.get("root_volume_size", 40)
            )

            nic = PrePaidServerNic(subnet_id=subnet_id)

            bandwidth = PrePaidServerEipBandwidth(
                size=5,
                sharetype="PER",
                chargemode="traffic"
            )
            eip = PrePaidServerEip(
                iptype="5_bgp",
                bandwidth=bandwidth
            )
            publicip = PrePaidServerPublicip(eip=eip)

            server = PrePaidServer(
            image_ref=ecs_config["image_ref"],
            flavor_ref=ecs_config["flavor_ref"],
            name=f"ecs-{username}",
            vpcid=vpc_id,
            nics=[nic],
            publicip=publicip,
            root_volume=root_volume,
            metadata={"owner": username},
           )

            request = CreateServersRequest()
            request.body = CreateServersRequestBody(server=server)

            response = client.create_servers(request)
            print(f"[OK] ECS creada para {username}: {response.server_ids}")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] ECS para {username}: {e.error_msg} (código: {e.status_code})")
