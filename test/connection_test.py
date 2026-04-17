import json
from pathlib import Path
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkiam.v3.region.iam_region import IamRegion
from huaweicloudsdkiam.v3 import *

class HuaweiCloudClient:

    def __init__(self, config_file="config.json"):
        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.ak = data["ak"]
        self.sk = data["sk"]
        self.project_id = data["project_id"]
        self.domain_id = data["domain_id"]
        self.user_id = data["user_id"]
        self.region = data["region"]

        credentials = BasicCredentials(self.ak, self.sk, self.project_id)

        self.client = IamClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(IamRegion.value_of(self.region)) \
            .build()

    def verify(self):
        try:
            request = KeystoneShowUserRequest(user_id=self.user_id)
            response = self.client.keystone_show_user(request)
            print("Conexion valida")
            print("Usuario:", response.user.name)
            print("Dominio:", response.user.domain_id)
        except exceptions.ClientRequestException as e:
            print("Credenciales invalidas")
            print(e.error_msg)

if __name__ == "__main__":
    cliente = HuaweiCloudClient()
    cliente.verify()
