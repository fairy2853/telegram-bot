import os
import logging
import logging.config
from pathlib import Path
import yaml


def check_log_dir():
    """
    Ensure the logs directory exists. Create it if it doesn't exist.
    Uses pathlib for modern path handling.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.info(f"Logs directory ensured at: {log_dir.absolute()}")


def setup_logging(
    default_path="logging_config.yaml", default_level=logging.INFO, env_key="LOG_CFG"
):
    check_log_dir()

    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "rt") as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
