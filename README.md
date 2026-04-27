# Huawei Cloud Laboratory Manager

Herramienta local para administrar un **laboratorio de cómputo** hospedado en Huawei Cloud. Permite a un instructor provisionar y gestionar recursos completos por alumno — usuario IAM, enterprise project, política de acceso, VPC, subnet e instancia ECS — desde una sola operación, tanto desde interfaz gráfica como desde la línea de comandos.

Cada alumno recibe su propia máquina virtual aislada dentro de su enterprise project y solo puede acceder a ella por **VNC o SSH**. No puede encenderla, apagarla, reiniciarla, modificarla ni eliminarla.

## Funcionalidades

### Creación de laboratorio

- Importar alumnos desde CSV con validación previa (duplicados, correos, contraseñas débiles).
- Por cada alumno se crea automáticamente, en orden:
  1. Usuario IAM
  2. Enterprise project propio
  3. Grupo de permisos `perm-{usuario}` con política `ECS_VNC_SSH_Only` acotada a su enterprise project
  4. Membresía al grupo compartido del curso (para administración)
  5. VPC compartida del grupo
  6. Subnet individual dentro de esa VPC
  7. ECS asignada a su enterprise project con tag `owner`

### Gestión de usuarios

- Habilitar o deshabilitar usuarios en masa desde CSV.
- Eliminar todos los recursos de un grupo (ECS, subnets, VPC, usuarios y grupo).
- Eliminación individual de usuario, ECS, subnet o VPC.

### Gestión de ECS

- Encender, apagar y reiniciar instancias (individual o en lote).
- Cambiar el flavor (resize) de una instancia.

### Listado y exportación

- Listar grupos, usuarios de un grupo, ECS por grupo o usuario, VPCs y subnets.
- Exportar snapshot del estado del laboratorio a CSV o JSON.

## Requisitos

- Python 3.10+
- Credenciales de Huawei Cloud (AK/SK) con permisos sobre IAM, EPS, ECS y VPC.
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
| `password` | Contraseña inicial (el alumno deberá cambiarla)    |
| `enabled`  | `true` para activo, `false` para inactivo          |

### Validación automática del CSV

| Problema                                                   | Nivel       | Comportamiento           |
|------------------------------------------------------------|-------------|--------------------------|
| Username duplicado                                         | Error       | Bloquea la ejecución     |
| Email vacío o malformado                                   | Advertencia | Pide confirmación        |
| Contraseña débil (longitud, sin mayúsculas, dígitos, etc.) | Advertencia | Pide confirmación        |

## Ejecución

### Interfaz gráfica

```bash
python gui.py
```

Incluye cinco pestañas: **Crear**, **Eliminar**, **Listar**, **Gestión ECS** y **Exportar**. Todas las operaciones de API corren en segundo plano con barra de progreso en tiempo real. Compatible con Linux, macOS y Windows.

### Línea de comandos — modo interactivo

```bash
python manage.py
```

### Línea de comandos — modo no interactivo (argparse)

```bash
python manage.py --action create   --csv usuarios.csv --group Grupo-A
python manage.py --action disable  --csv usuarios.csv
python manage.py --action start    --group Grupo-A
python manage.py --action resize   --user juan --flavor c3.large.2
python manage.py --action export   --format csv --output snapshot.csv
python manage.py --action delete-group --group Grupo-A --yes
```

Usa `python manage.py --help` para ver todas las opciones disponibles. El flag `--yes / -y` omite confirmaciones para uso en scripts.

### Acciones disponibles en CLI

| Acción          | Descripción                                          |
|-----------------|------------------------------------------------------|
| `create`        | Crear usuarios, permisos, VPC y ECS desde CSV        |
| `enable`        | Habilitar usuarios desde CSV                         |
| `disable`       | Deshabilitar usuarios desde CSV                      |
| `delete-group`  | Eliminar grupo y todos sus recursos                  |
| `delete-user`   | Eliminar usuario individual                          |
| `delete-ecs`    | Eliminar ECS individual                              |
| `delete-subnet` | Eliminar subnet individual                           |
| `delete-vpc`    | Eliminar VPC individual                              |
| `start`         | Encender ECS (por grupo o usuario)                   |
| `stop`          | Apagar ECS (por grupo o usuario)                     |
| `reboot`        | Reiniciar ECS (por grupo o usuario)                  |
| `resize`        | Cambiar flavor de una ECS                            |
| `list-groups`   | Listar grupos IAM                                    |
| `list-users`    | Listar usuarios de un grupo                          |
| `list-ecs-group`| Listar ECS de un grupo                               |
| `list-ecs-user` | Listar ECS de un usuario                             |
| `list-vpcs`     | Listar VPCs                                          |
| `list-subnets`  | Listar subnets de una VPC                            |
| `export`        | Exportar snapshot del laboratorio a CSV o JSON       |

## Política de acceso de alumnos

Al crear el laboratorio se genera automáticamente la política IAM `ECS_VNC_SSH_Only` (tipo `AX`). Se asigna a un grupo individual `perm-{usuario}` acotado al enterprise project de ese alumno.

**Permisos permitidos** — solo lectura y acceso por consola:

- `ecs:servers:list`, `ecs:servers:get`
- `ecs:serverConsoles:create` (VNC)
- `ecs:serverInterfaces:get/list`
- `evs:volumes:get/list`
- `vpc:ports:get`, `vpc:publicips:get`, `vpc:subnets:get`, `vpc:networks:get`, `vpc:floatingips:get`

**Permisos denegados explícitamente:**

- Crear, modificar, eliminar servidores
- Encender, apagar, reiniciar, redimensionar
- Operaciones sobre volúmenes, keypairs, contraseñas, grupos, tags y metadata

## Estructura del proyecto

```
Huawei-cloud-manager-lab/
├── config/
│   ├── config.json                     # Credenciales (no subir al repo)
│   └── connection.py                   # Clientes SDK: IAM, ECS, VPC, EPS
├── utils/
│   ├── convert_cvs.py                  # Parseo de CSV a objetos de usuario
│   ├── csv_validator.py                # Validación de CSV
│   ├── list_resources.py               # Listado de recursos cloud
│   ├── delete_all.py                   # Eliminación masiva e individual
│   ├── export_snapshot.py              # Exportar estado del lab a CSV/JSON
│   ├── iam/
│   │   ├── helpers.py                  # find_user_id(), find_group_id(), set_users_enabled()
│   │   ├── create_users.py             # Orquestador principal de aprovisionamiento
│   │   ├── create_user_group.py        # Crear grupo IAM
│   │   ├── add_user_group.py           # Agregar usuarios a un grupo
│   │   ├── grant_enterprise_permissions.py  # Política VNC/SSH por alumno, acotada a su EP
│   │   ├── grant_user_group.py         # Asignación de política a nivel dominio (admin)
│   │   ├── create_custom_policy.py     # Definición de la política ECS_VNC_SSH_Only
│   │   ├── enable_users.py             # Habilitar usuarios desde CSV
│   │   └── disable_users.py            # Deshabilitar usuarios desde CSV
│   ├── eps/
│   │   └── create_enterprise_project.py  # Enterprise project por alumno
│   ├── vpc/
│   │   ├── create_vpc.py               # Crear VPC compartida del grupo
│   │   └── create_user_subnets.py      # Subnet individual por alumno
│   └── ecs/
│       ├── create_user_ecs.py          # ECS por alumno vinculada a su EP
│       └── manage_ecs.py               # Encender, apagar, reiniciar, redimensionar ECS
├── gui/
│   ├── app.py                          # Entrada de la GUI
│   ├── widgets.py                      # Componentes reutilizables
│   ├── mixins.py                       # ProgressMixin
│   ├── log.py                          # Panel de log en tiempo real
│   ├── constants.py
│   └── panels/
│       ├── create.py                   # Pestaña Crear
│       ├── delete.py                   # Pestaña Eliminar
│       ├── list_panel.py               # Pestaña Listar
│       ├── ecs_manage.py               # Pestaña Gestión ECS
│       ├── export.py                   # Pestaña Exportar
│       └── config.py                   # Pestaña Configuración
├── tests/
│   ├── conftest.py                     # Fixtures: make_api_error, FAKE_CONFIG
│   ├── test_connection.py              # Tests del módulo de conexión
│   ├── test_csv_validator.py           # Tests del validador de CSV
│   ├── test_iam_helpers.py             # Tests de helpers IAM
│   ├── test_manage_ecs.py              # Tests de gestión de ECS
│   ├── test_export_snapshot.py         # Tests de exportación
│   └── README.md                       # Cómo ejecutar las pruebas
├── conftest.py                         # Inyección de venv para pytest del sistema
├── pytest.ini                          # Configuración de pytest
├── gui.py                              # Punto de entrada de la GUI
├── manage.py                           # CLI interactivo y argparse
└── requirements.txt
```

## Dependencias principales

| Paquete              | Uso                                        |
|----------------------|--------------------------------------------|
| `huaweicloudsdkcore` | Autenticación y cliente base               |
| `huaweicloudsdkiam`  | Usuarios, grupos y políticas IAM           |
| `huaweicloudsdkeps`  | Enterprise projects por alumno             |
| `huaweicloudsdkecs`  | Instancias ECS                             |
| `huaweicloudsdkvpc`  | VPCs y subnets                             |
| `wxPython`           | Interfaz gráfica (opcional)                |

## Tests

```bash
~/.local/bin/pytest           # todos los tests
~/.local/bin/pytest tests/test_connection.py   # un archivo específico
```

Ver [tests/README.md](tests/README.md) para instrucciones completas.

## Seguridad

- `config/config.json` está en `.gitignore`. Nunca lo subas al repositorio.
- Las contraseñas del CSV se envían con `pwd_status=True`, forzando el cambio en el primer inicio de sesión.
- La validación del CSV bloquea la ejecución si hay usernames duplicados.
- Los permisos de cada alumno están acotados únicamente a su enterprise project mediante `AssociateRoleToGroupOnEnterpriseProject`.
