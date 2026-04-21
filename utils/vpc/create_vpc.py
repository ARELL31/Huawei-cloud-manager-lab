from config.connection import get_vpc_client
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkvpc.v2 import (
    CreateVpcRequest,
    CreateVpcRequestBody,
    CreateVpcOption,
)


def create_vpc(
    vpc_name: str,
    cidr: str = "10.0.0.0/8",
    config_file: str = "config/config.json"
):
    client = get_vpc_client(config_file)

    try:
        request = CreateVpcRequest()
        request.body = CreateVpcRequestBody(
            vpc=CreateVpcOption(name=vpc_name, cidr=cidr)
        )

        response = client.create_vpc(request)
        print(f"[OK] VPC creada: {response.vpc.name} ({response.vpc.id})")
        return response.vpc

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] VPC {vpc_name}: {e.error_msg}")
        return None
