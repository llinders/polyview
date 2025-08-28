import logging
import os


def setup_logging():
    """
    Sets up the application-wide logging configuration.
    """
    logger = logging.getLogger()
    logger.setLevel(os.environ.get("LOG_LEVEL", logging.WARNING).upper())

    polyview_logger = logging.getLogger("polyview")
    polyview_logger.setLevel(os.environ.get("POLYVIEW_LOG_LEVEL", logging.INFO).upper())

    # Parse and apply module-specific log levels from the environment variable
    module_log_levels_str = os.environ.get("MODULE_LOG_LEVELS")
    if module_log_levels_str:
        for entry in module_log_levels_str.split(","):
            try:
                module_name, level_name = entry.strip().split(":")
                logging.getLogger(module_name).setLevel(level_name.upper())
            except ValueError:
                logger.warning(
                    f"Invalid MODULE_LOG_LEVELS entry: {entry}. Expected format 'module:LEVEL'."
                )

    # Prevent adding multiple handlers if setup_logging is called more than once
    if not logger.handlers:
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    # Library specific log levels for controlling noisiness
    logging.getLogger("langchain").setLevel(logging.INFO)
    logging.getLogger("langgraph").setLevel(logging.INFO)
    logging.getLogger("langgraph_api").setLevel(logging.INFO)


setup_logging()


def get_logger(name: str):
    return logging.getLogger(name)
