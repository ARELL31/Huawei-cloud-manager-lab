HUAWEI_REGIONS = [
    "ae-ad-1",
    "af-north-1",
    "af-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-southeast-3",
    "ap-southeast-4",
    "ap-southeast-5",
    "cn-east-2",
    "cn-east-3",
    "cn-east-4",
    "cn-east-5",
    "cn-north-1",
    "cn-north-2",
    "cn-north-4",
    "cn-north-9",
    "cn-north-11",
    "cn-north-12",
    "cn-south-1",
    "cn-south-2",
    "cn-south-4",
    "cn-southwest-2",
    "cn-southwest-3",
    "eu-west-0",
    "eu-west-101",
    "la-north-2",
    "la-south-2",
    "me-east-1",
    "my-kualalumpur-1",
    "na-mexico-1",
    "ru-moscow-1",
    "sa-brazil-1",
    "tr-west-1",
]

RESOURCE_TYPES = ["Usuario", "ECS", "Subnet", "VPC"]

LIST_OPTIONS = [
    "Grupos IAM",
    "Usuarios de un grupo",
    "ECS de un grupo",
    "ECS de un usuario",
    "VPCs",
    "Subnets de una VPC",
]

LIST_COLUMNS = {
    "Grupos IAM":           [("Nombre", 200), ("ID", 300), ("Descripcion", 220)],
    "Usuarios de un grupo": [("Nombre", 200), ("ID", 300), ("Estado", 120)],
    "ECS de un grupo":      [("Nombre", 200), ("Propietario", 150), ("ID", 280), ("Estado", 110)],
    "ECS de un usuario":    [("Nombre", 200), ("ID", 300), ("Estado", 120)],
    "VPCs":                 [("Nombre", 200), ("ID", 300), ("CIDR", 140), ("Estado", 110)],
    "Subnets de una VPC":   [("Nombre", 200), ("ID", 300), ("CIDR", 140), ("Estado", 110)],
}

NEEDS_FILTER = {
    "Usuarios de un grupo": "Nombre del grupo",
    "ECS de un grupo":      "Nombre del grupo",
    "ECS de un usuario":    "Nombre del usuario",
    "Subnets de una VPC":   "Nombre de la VPC",
}
