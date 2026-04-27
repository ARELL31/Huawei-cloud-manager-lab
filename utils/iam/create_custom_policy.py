import json
from config.connection import get_client
from huaweicloudsdkiam.v3 import (
    CreateCloudServiceCustomPolicyRequest,
    CreateCloudServiceCustomPolicyRequestBody,
    ServicePolicyRoleOption,
    KeystoneListPermissionsRequest,
)
from huaweicloudsdkcore.exceptions import exceptions

POLICY_NAME = "ECS_VNC_SSH_Only"


def build_policy_document():
    return {
        "Version": "1.1",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecs:servers:list",
                    "ecs:servers:get",
                    "ecs:serverConsoles:create",
                    "ecs:serverInterfaces:get",
                    "ecs:serverInterfaces:list",
                    "evs:volumes:get",
                    "evs:volumes:list",
                    "vpc:ports:get",
                    "vpc:publicips:get",
                    "vpc:subnets:get",
                    "vpc:networks:get",
                    "vpc:floatingips:get",
                ]
            },
            {
                "Effect": "Deny",
                "Action": [
                    "ecs:servers:create",
                    "ecs:servers:delete",
                    "ecs:servers:update",
                    "ecs:servers:start",
                    "ecs:servers:stop",
                    "ecs:servers:reboot",
                    "ecs:servers:resize",
                    "ecs:serverVolumes:use",
                    "ecs:serverVolumes:delete",
                    "ecs:serverKeypairs:create",
                    "ecs:serverPasswords:update",
                    "ecs:serverGroups:manage",
                    "ecs:serverTags:create",
                    "ecs:serverTags:delete",
                    "ecs:serverMetadata:set",
                    "ecs:serverMetadata:delete",
                ]
            }
        ]
    }


def find_existing_policy(client, policy_name: str):
    try:
        request = KeystoneListPermissionsRequest()
        response = client.keystone_list_permissions(request)
        for role in response.roles:
            if role.name == policy_name:
                print(f"[OK] Politica custom ya existe: {policy_name} ({role.id})")
                return role.id
    except exceptions.ClientRequestException as e:
        print(f"[WARN] No se pudo verificar existencia de politica: {e.error_msg}")
    return None


def create_custom_policy(config_file: str = "config/config.json") -> str | None:
    client = get_client(config_file)

    existing_id = find_existing_policy(client, POLICY_NAME)
    if existing_id:
        return existing_id

    try:
        role_option = ServicePolicyRoleOption(
            display_name="ECS VNC/SSH Only",
            type="AX",
            description="Solo acceso por VNC y SSH. Sin permisos de encendido, apagado, reinicio, borrado ni modificacion.",
            policy=build_policy_document()
        )

        request = CreateCloudServiceCustomPolicyRequest()
        request.body = CreateCloudServiceCustomPolicyRequestBody(role=role_option)

        response = client.create_cloud_service_custom_policy(request)
        role_id = response.role.id
        print(f"[OK] Politica custom creada: {POLICY_NAME} ({role_id})")
        return role_id

    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo crear la politica custom: {e.error_msg}")
        return None
