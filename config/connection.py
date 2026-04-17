import json
from huaweicloudsdkcore.auth.credentials import BasicCredentials, GlobalCredentials
from huaweicloudsdkiam.v3 import IamClient
from huaweicloudsdkiam.v3.region.iam_region import IamRegion
from huaweicloudsdkecs.v2 import EcsClient
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion


def get_client(config_file: str = "config/config.json") -> IamClient:
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

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
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

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
