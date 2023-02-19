import logging
import sys
from typing import Union


def create_logger(name: str, level: Union[int, str]):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


class SupportsLogging(object):
    _tag: str = "root"
    _logger = None

    def __init__(self, level: int):
        self._logger = create_logger(self._tag, level)

    def logging(self, level: str):
        self._logger.setLevel(level.upper())
