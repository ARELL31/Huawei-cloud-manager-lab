import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkvpc.v2 import (
    VpcClient,
    CreateVpcRequest,
    CreateVpcRequestBody,
    CreateVpcOption,
)
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion


def create_vpc(
    vpc_name: str,
    cidr: str = "10.0.0.0/8",
    config_file: str = "config/config.json"
):
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    credentials = BasicCredentials(
        config["ak"],
        config["sk"],
        config.get("project_id")
    )

    client = VpcClient.new_builder() \
        .with_credentials(credentials) \
        .with_region(VpcRegion.value_of(config["region"])) \
        .build()

    try:
        request = CreateVpcRequest()
        body = CreateVpcRequestBody(
            vpc=CreateVpcOption(
                name=vpc_name,
                cidr=cidr
            )
        )
        request.body = body

        response = client.create_vpc(request)
        print(f"[OK] VPC creada: {response.vpc.name} ({response.vpc.id})")
        return response.vpc

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] VPC {vpc_name}: {e.error_msg}")
        return None
