import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials, GlobalCredentials
from huaweicloudsdkiam.v3 import IamClient
from huaweicloudsdkiam.v3.region.iam_region import IamRegion
from huaweicloudsdkecs.v2 import EcsClient
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkvpc.v2 import VpcClient
from huaweicloudsdkvpc.v2.region.vpc_region import VpcRegion
from huaweicloudsdkeps.v1 import EpsClient


def load_config(config_file: str = "config/config.json") -> dict:
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_client(config_file: str = "config/config.json") -> IamClient:
    config = load_config(config_file)
    credentials = GlobalCredentials(
        ak=config["ak"],
        sk=config["sk"],
    )
    return (
        IamClient.new_builder()
        .with_credentials(credentials)
        .with_region(IamRegion.value_of("la-north-2"))
        .build()
    )


def get_ecs_client(config_file: str = "config/config.json") -> EcsClient:
    config = load_config(config_file)
    credentials = BasicCredentials(
        ak=config["ak"],
        sk=config["sk"],
        project_id=config["project_id"]
    )
    return (
        EcsClient.new_builder()
        .with_credentials(credentials)
        .with_region(EcsRegion.value_of(config["region"]))
        .build()
    )


def get_vpc_client(config_file: str = "config/config.json") -> VpcClient:
    config = load_config(config_file)
    credentials = BasicCredentials(
        ak=config["ak"],
        sk=config["sk"],
        project_id=config["project_id"]
    )
    return (
        VpcClient.new_builder()
        .with_credentials(credentials)
        .with_region(VpcRegion.value_of(config["region"]))
        .build()
    )


def get_eps_client(config_file: str = "config/config.json") -> EpsClient:
    config = load_config(config_file)
    credentials = GlobalCredentials(
        ak=config["ak"],
        sk=config["sk"],
    )
    return (
        EpsClient.new_builder()
        .with_credentials(credentials)
        .with_endpoint("https://eps.myhuaweicloud.com")
        .build()
    )
