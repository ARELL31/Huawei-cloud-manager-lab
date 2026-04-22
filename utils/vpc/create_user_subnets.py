from config.connection import get_vpc_client
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkvpc.v2 import (
    CreateSubnetRequest,
    CreateSubnetRequestBody,
    CreateSubnetOption,
)


def create_user_subnets(
    vpc_id: str,
    usernames: list[str],
    config_file: str = "config/config.json",
    on_progress=None,           # on_progress(current: int, total: int)
) -> dict:
    client = get_vpc_client(config_file)
    user_subnets = {}
    total = len(usernames)

    for index, username in enumerate(usernames, start=1):
        subnet_cidr = f"10.0.{index}.0/24"
        gateway_ip = f"10.0.{index}.1"
        subnet_name = f"{username}_subnet"

        try:
            request = CreateSubnetRequest()
            request.body = CreateSubnetRequestBody(
                subnet=CreateSubnetOption(
                    name=subnet_name,
                    cidr=subnet_cidr,
                    vpc_id=vpc_id,
                    gateway_ip=gateway_ip
                )
            )

            response = client.create_subnet(request)
            user_subnets[username] = response.subnet.id
            print(f"[OK] Subnet creada: {subnet_name} -> {subnet_cidr}")

        except exceptions.ClientRequestException as e:
            print(f"[ERROR] Subnet para {username}: {e.error_msg}")

        if on_progress:
            on_progress(index, total)

    return user_subnets
