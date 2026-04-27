# Tests unitarios

Tests para la lógica de negocio del proyecto. Todos usan mocks del SDK de Huawei Cloud, por lo que **no se requiere conexión real ni credenciales** para ejecutarlos.

## Estructura

```
tests/
├── conftest.py               # Fixture make_api_error y FAKE_CONFIG compartidos
├── test_connection.py        # config/connection.py — load_config, get_client, get_ecs_client, get_vpc_client
├── test_csv_validator.py     # utils/csv_validator.py — validación de emails, contraseñas, duplicados
├── test_iam_helpers.py       # utils/iam/helpers.py — read_usernames, find_user/group_id, set_users_enabled
├── test_manage_ecs.py        # utils/ecs/manage_ecs.py — get_servers, batch_start/stop/reboot, resize
└── test_export_snapshot.py   # utils/export_snapshot.py — collect_snapshot, write_csv, write_json
```

## Requisitos

El proyecto usa un virtualenv en `../local/`. El `conftest.py` raíz lo agrega al path automáticamente, así que pytest puede correrse con el Python del sistema.

Instalar pytest una sola vez:

```bash
pip install pytest --break-system-packages
```

## Correr los tests

Desde la raíz del proyecto:

```bash
~/.local/bin/pytest
```

Correr un archivo específico:

```bash
~/.local/bin/pytest tests/test_connection.py
```

Correr un test específico:

```bash
~/.local/bin/pytest tests/test_manage_ecs.py::test_batch_stop_hard_type
```

Ver output detallado en caso de fallo:

```bash
~/.local/bin/pytest --tb=long
```
