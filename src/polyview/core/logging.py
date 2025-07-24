import logging
import os


def setup_logging():
    """
    Sets up the application-wide logging configuration.
    """
    logger = logging.getLogger()
    logger.setLevel(os.environ.get("LOG_LEVEL", "WARNING").upper())
    logging.getLogger("polyview").setLevel(os.environ.get("POLYVIEW_LOG_LEVEL", "DEBUG").upper())

    # Prevent adding multiple handlers if setup_logging is called more than once
    if not logger.handlers:
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    # Library specific log levels for controlling noisiness
    logging.getLogger("langchain").setLevel(logging.INFO)
    logging.getLogger("langgraph").setLevel(logging.INFO)
    logging.getLogger("langgraph_api").setLevel(logging.INFO)


setup_logging()


def get_logger(name: str):
    return logging.getLogger(name)
