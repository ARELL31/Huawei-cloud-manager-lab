from utils.iam.helpers import set_users_enabled


def enable_users(csv_file: str, config_file: str = "config/config.json"):
    set_users_enabled(csv_file, enabled=True, config_file=config_file)
