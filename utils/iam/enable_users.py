from utils.iam.helpers import set_users_enabled


def enable_users(csv_file: str, config_file: str = "config/config.json", on_progress=None):
    set_users_enabled(csv_file, enabled=True, config_file=config_file, on_progress=on_progress)
