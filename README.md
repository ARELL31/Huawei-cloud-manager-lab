# Huawei Cloud IAM Manager

Herramienta para gestionar usuarios, grupos, VPCs, subnets e instancias ECS en Huawei Cloud mediante el SDK oficial de Python. Disponible en dos modos: interfaz gráfica (wxPython) y línea de comandos.

## Funcionalidades

- Crear usuarios IAM desde CSV, con validación previa de duplicados, correos y contraseñas débiles.
- Crear automáticamente grupo IAM, política personalizada, VPC, subnets y una ECS por usuario.
- Habilitar o deshabilitar usuarios en masa desde CSV.
- Eliminar todos los recursos de un grupo (ECS, subnets, VPC, usuarios y grupo).
- Eliminación individual de usuario, ECS, subnet o VPC.
- Listar grupos, usuarios de un grupo, ECS por grupo o usuario, VPCs y subnets.

## Requisitos

- Python 3.10+
- Credenciales de Huawei Cloud (AK/SK) con permisos sobre IAM, ECS y VPC.
- wxPython 4.2+ (solo para la interfaz gráfica).

## Instalación

```bash
pip install -r requirements.txt
pip install wxPython        # solo si vas a usar la GUI
```

## Configuración

Crea o edita `config/config.json` con tus credenciales:

```json
{
    "ak": "<access_key>",
    "sk": "<secret_key>",
    "project_id": "<project_id>",
    "domain_id": "<domain_id>",
    "region": "<region>",
    "ecs": {
        "image_ref": "<image_id>",
        "flavor_ref": "<flavor_id>",
        "root_volume_type": "SSD",
        "root_volume_size": 40
    }
}
```

> **No subas `config/config.json` al repositorio.** Está incluido en `.gitignore`.

## Formato del CSV

```csv
username,email,password,enabled
john.doe,john.doe@example.com,ExamplePass@1234!,true
jane.smith,jane@example.com,AnotherPass@99!,false
```

| Columna    | Descripción                                        |
|------------|----------------------------------------------------|
| `username` | Nombre de usuario en IAM                           |
| `email`    | Correo electrónico del usuario                     |
| `password` | Contraseña inicial (el usuario deberá cambiarla)   |
| `enabled`  | `true` para activo, `false` para inactivo          |

### Validación automática del CSV

Antes de crear usuarios, el sistema valida el archivo y reporta:

| Problema                        | Nivel      | Comportamiento              |
|---------------------------------|------------|-----------------------------|
| Username duplicado              | Error      | Bloquea la ejecución        |
| Email vacío o malformado        | Advertencia | Pide confirmación           |
| Contraseña débil (longitud, sin mayúsculas, dígitos, etc.) | Advertencia | Pide confirmación |

## Ejecución

### Interfaz gráfica (recomendada)

```bash
python gui.py
```

La GUI incluye tres pestañas — **Crear**, **Eliminar** y **Listar** — con un panel de log en tiempo real al fondo. Todas las operaciones de API corren en segundo plano para no bloquear la ventana. Compatible con Linux, macOS y Windows.

### Línea de comandos

```bash
python manage.py
```

El menú tiene tres secciones principales:

```
1. Crear
   1. Crear usuarios desde CSV
   2. Habilitar usuarios desde CSV
   3. Deshabilitar usuarios desde CSV

2. Eliminar
   1. Eliminar grupo y sus recursos
   2. Eliminar usuario individual
   3. Eliminar ECS individual
   4. Eliminar Subnet individual
   5. Eliminar VPC individual

3. Listar
   1. Listar grupos IAM
   2. Listar usuarios de un grupo
   3. Listar ECS de un grupo
   4. Listar ECS de un usuario
   5. Listar VPCs
   6. Listar Subnets de una VPC
```

## Estructura del proyecto

```
Huawei-cloud-manager-lab/
├── config/
│   ├── config.json              # Credenciales (no subir al repo)
│   └── connection.py            # load_config(), get_client(), get_ecs_client(), get_vpc_client()
├── utils/
│   ├── convert_cvs.py           # Parseo de CSV a objetos de usuario
│   ├── csv_validator.py         # Validación de CSV (duplicados, emails, contraseñas)
│   ├── list_resources.py        # Listado de grupos, usuarios, ECS, VPCs, subnets
│   ├── delete_all.py            # Eliminación masiva e individual de recursos
│   ├── iam/
│   │   ├── helpers.py           # find_user_id(), find_group_id(), read_usernames(), set_users_enabled()
│   │   ├── create_users.py      # Orquestador: usuarios → grupo → política → VPC → subnets → ECS
│   │   ├── enable_users.py      # Habilitar usuarios desde CSV
│   │   ├── disable_users.py     # Deshabilitar usuarios desde CSV
│   │   ├── create_user_group.py # Crear grupo IAM
│   │   ├── add_user_group.py    # Agregar usuarios a un grupo
│   │   ├── grant_user_group.py  # Asignar política al grupo
│   │   └── create_custom_policy.py # Política ECS_Owner_Access (acceso solo a ECS propia)
│   ├── vpc/
│   │   ├── create_vpc.py        # Crear VPC
│   │   └── create_user_subnets.py  # Crear una subnet por usuario
│   └── ecs/
│       └── create_user_ecs.py   # Crear una ECS por usuario con tag owner
├── test/
│   ├── connection_test.py       # Prueba de conectividad con la API
│   └── README.md
├── gui.py                       # Interfaz gráfica wxPython (Linux / macOS / Windows)
├── manage.py                    # Menú interactivo de línea de comandos
└── requirements.txt
```

## Política IAM personalizada

Al crear un grupo se asigna automáticamente la política `ECS_Owner_Access`, que permite a cada usuario gestionar únicamente las instancias ECS cuyo tag `owner` coincida con su nombre de usuario IAM. El resto de ECS son de solo lectura.

## Dependencias principales

| Paquete              | Uso                          |
|----------------------|------------------------------|
| `huaweicloudsdkcore` | Autenticación y cliente base |
| `huaweicloudsdkiam`  | Usuarios y grupos IAM        |
| `huaweicloudsdkecs`  | Instancias ECS               |
| `huaweicloudsdkvpc`  | VPCs y subnets               |
| `wxPython`           | Interfaz gráfica (opcional)  |

## Seguridad

- `config/config.json` está en `.gitignore`. Nunca lo subas al repositorio.
- Las contraseñas del CSV se envían con `pwd_status=True`, forzando el cambio en el primer inicio de sesión.
- La validación del CSV bloquea la ejecución si hay usernames duplicados.
