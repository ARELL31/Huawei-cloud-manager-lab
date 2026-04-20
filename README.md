# Huawei Cloud IAM Manager

Herramienta de línea de comandos para gestionar usuarios, grupos, VPCs, subnets e instancias ECS en Huawei Cloud a través de su SDK oficial de Python.

## Funcionalidades

- Crear usuarios IAM desde un archivo CSV, junto con grupo, política, VPC, subnets y una instancia ECS por usuario.
- Habilitar o deshabilitar usuarios en masa desde CSV.
- Eliminar todos los recursos asociados a un grupo (ECS, subnets, VPC, usuarios y el grupo mismo).

## Requisitos

- Python 3.10+
- Credenciales de Huawei Cloud (AK/SK) con permisos sobre IAM, ECS y VPC.

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

Edita `config/config.json` con tus credenciales y parámetros de proyecto:

```json
{
    "ak": "<access_key>",
    "sk": "<secret_key>",
    "project_id": "<project_id>",
    "domain_id": "<domain_id>",
    "region": "<region>",
    "user_id": "<admin_user_id>",
    "ecs": {
        "image_ref": "<image_id>",
        "flavor_ref": "<flavor_id>",
        "root_volume_type": "SSD",
        "root_volume_size": 40
    }
}
```

## Formato del CSV

El archivo CSV debe tener las siguientes columnas:

```csv
username,email,password,enabled
john.doe,john.doe@example.com,ExamplePass@1234!,true
```

| Columna    | Descripción                              |
|------------|------------------------------------------|
| `username` | Nombre de usuario en IAM                 |
| `email`    | Correo electrónico del usuario           |
| `password` | Contraseña inicial (se requiere cambio)  |
| `enabled`  | `true` para activo, `false` para inactivo |

## Uso

Ejecuta el menú interactivo con:

```bash
python manage.py
```

### Opciones del menú

| Opción | Acción                                                                                               |
|--------|------------------------------------------------------------------------------------------------------|
| `1`    | **Crear usuarios desde CSV** — crea usuarios IAM; opcionalmente crea grupo, VPC, subnets y ECS.     |
| `2`    | **Habilitar usuarios desde CSV** — reactiva cuentas deshabilitadas.                                  |
| `3`    | **Deshabilitar usuarios desde CSV** — suspende cuentas sin eliminarlas.                              |
| `4`    | **Eliminar grupo y sus recursos** — elimina ECS, subnets, VPC, usuarios y el grupo (irreversible).   |
| `0`    | Salir.                                                                                               |

## Estructura del proyecto

```
Huawei-cloud-manager-lab/
├── config/
│   ├── config.json          # Credenciales y parámetros (no subir al repo)
│   └── connection.py        # Fábricas de clientes IAM, ECS y VPC
├── utils/
│   ├── convert_cvs.py       # Parseo del CSV a objetos de usuario
│   ├── create_users.py      # Creación completa de usuarios y recursos
│   ├── enable_users.py      # Habilitación de usuarios
│   ├── disable_users.py     # Deshabilitación de usuarios
│   ├── create_user_group.py # Creación de grupo IAM
│   ├── add_user_group.py    # Asignación de usuarios a grupo
│   ├── grant_user_group.py  # Asignación de política al grupo
│   ├── create_custom_policy.py # Creación de política personalizada
│   ├── create_vpc.py        # Creación de VPC
│   ├── create_user_subnets.py  # Creación de subnets por usuario
│   ├── create_user_ecs.py   # Creación de instancias ECS por usuario
│   └── delete_all.py # Eliminación completa de recursos del grupo
├── test/
│   ├── connection_test.py   # Prueba de conectividad con la API
│   └── README.md
├── usuarios.csv             # Ejemplo de CSV de usuarios
├── manage.py                # Punto de entrada (menú interactivo)
└── requirements.txt
```

## Dependencias principales

| Paquete                  | Uso                        |
|--------------------------|----------------------------|
| `huaweicloudsdkcore`     | Autenticación y cliente base |
| `huaweicloudsdkiam`      | Gestión de usuarios y grupos |
| `huaweicloudsdkecs`      | Gestión de instancias ECS  |
| `huaweicloudsdkvpc`      | Gestión de VPCs y subnets  |

## Seguridad

- **No subas `config/config.json` al repositorio.** Contiene credenciales sensibles. Está incluido en `.gitignore`.
- Las contraseñas del CSV se marcan con `pwd_status=True`, forzando al usuario a cambiarlas en el primer inicio de sesión.

## Licencia

Consulta el archivo [LICENSE](LICENSE) para más información.
