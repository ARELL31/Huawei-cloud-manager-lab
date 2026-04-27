from config.connection import get_client
from huaweicloudsdkiam.v3 import (
    CreateCloudServiceCustomPolicyRequest,
    CreateCloudServiceCustomPolicyRequestBody,
    UpdateCloudServiceCustomPolicyRequest,
    UpdateCloudServiceCustomPolicyRequestBody,
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
                    "ecs:*:get",
                    "ecs:*:get*",
                    "ecs:*:list",
                    "ecs:*:list*",
                    "ecs:*:show*",
                    "ecs:servers:createConsole",
                    "ecs:cloudServers:vnc",
                    "evs:*:get",
                    "evs:*:get*",
                    "evs:*:list",
                    "evs:*:list*",
                    "vpc:*:get",
                    "vpc:*:get*",
                    "vpc:*:list",
                    "vpc:*:list*",
                ]
            },
            {
                "Effect": "Deny",
                "Action": [
                    "ecs:servers:start",
                    "ecs:servers:stop",
                    "ecs:servers:delete",
                    "ecs:servers:setMetadata",
                    "ecs:servers:setTags",
                    "ecs:serverPasswords:manage",
                    "ecs:serverGroups:manage",
                    "ecs:serverVolumeAttachments:create",
                    "ecs:serverVolumeAttachments:delete",
                    "ecs:serverVolumes:use",
                ]
            }
        ]
    }


def find_existing_policy(client, policy_name: str):
    try:
        response = client.keystone_list_permissions(KeystoneListPermissionsRequest())
        for role in response.roles:
            if role.name == policy_name:
                return role.id
    except exceptions.ClientRequestException as e:
        print(f"[WARN] No se pudo verificar existencia de politica: {e.error_msg}")
    return None


def create_custom_policy(config_file: str = "config/config.json") -> str | None:
    client = get_client(config_file)

    existing_id = find_existing_policy(client, POLICY_NAME)

    role_option = ServicePolicyRoleOption(
        display_name="ECS VNC SSH Only",
        type="AX",
        description="Solo acceso por VNC y SSH. Sin permisos de encendido, apagado, reinicio, borrado ni modificacion.",
        policy=build_policy_document()
    )

    if existing_id:
        try:
            request = UpdateCloudServiceCustomPolicyRequest(role_id=existing_id)
            request.body = UpdateCloudServiceCustomPolicyRequestBody(role=role_option)
            client.update_cloud_service_custom_policy(request)
            print(f"[OK] Politica custom actualizada: {POLICY_NAME} ({existing_id})")
            return existing_id
        except exceptions.ClientRequestException as e:
            print(f"[ERROR] No se pudo actualizar la politica custom: {e.error_msg}")
            return None

    try:
        request = CreateCloudServiceCustomPolicyRequest()
        request.body = CreateCloudServiceCustomPolicyRequestBody(role=role_option)
        response = client.create_cloud_service_custom_policy(request)
        role_id = response.role.id
        print(f"[OK] Politica custom creada: {POLICY_NAME} ({role_id})")
        return role_id
    except exceptions.ClientRequestException as e:
        print(f"[ERROR] No se pudo crear la politica custom: {e.error_msg}")
        return None
