import logging
from pathlib import Path


_log_format = f"%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
_project_root = Path(__file__).resolve().parent
_log_file = _project_root / "telegram.loger"


def get_file_handler(level):
    file_handler = logging.FileHandler(_log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_log_format))
    return file_handler


def get_stream_handler(level):
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter(_log_format))
    return stream_handler


def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = logging.DEBUG
    logger.setLevel(level)
    logger.propagate = False
    logger.addHandler(get_file_handler(level))
    logger.addHandler(get_stream_handler(level))
    return logger
