import logging
import sys
from typing import Union


def hexify(data, sep=' '):
    return sep.join([format(x, '02x') for x in data])


def create_logger(name: str, level: Union[int, str]):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
