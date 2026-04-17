import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkvpc.v2 import (
    VpcClient,
    CreateSubnetRequest,
    CreateSubnetRequestBody,
    CreateSubnetOption,
)
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion


def get_vpc_client(config_file="config/config.json"):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    credentials = BasicCredentials(
        config["ak"],
        config["sk"],
        config["project_id"]
    )

    return (
        VpcClient.new_builder()
        .with_credentials(credentials)
        .with_region(VpcRegion.value_of(config["region"]))
        .build()
    )


def create_user_subnets(
    vpc_id: str,
    usernames: list[str],
    config_file: str = "config/config.json"
) -> dict:
    client = get_vpc_client(config_file)
    user_subnets = {}  # {username: subnet_id}

    for index, username in enumerate(usernames, start=1):
        subnet_cidr = f"10.0.{index}.0/24"
        gateway_ip = f"10.0.{index}.1"
        subnet_name = f"{username}_subnet"

        try:
            request = CreateSubnetRequest()
            subnetbody = CreateSubnetOption(
                name=subnet_name,
                cidr=subnet_cidr,
                vpc_id=vpc_id,
                gateway_ip=gateway_ip
            )
            request.body = CreateSubnetRequestBody(subnet=subnetbody)

            response = client.create_subnet(request)
            user_subnets[username] = response.subnet.id

            print(f"[OK] Subnet creada: {subnet_name} -> {subnet_cidr}")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] Subnet para {username}: {e.error_msg}")

    return user_subnets

