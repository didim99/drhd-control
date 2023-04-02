from __future__ import annotations

import json
import re
from argparse import Namespace, ArgumentTypeError, ArgumentParser
from collections import namedtuple
from enum import Enum
from ipaddress import IPv4Address
from typing import Callable, List


__mapping = namedtuple('mapping', ['src', 'dst'])

__ALL = '*'
__FIRST_OUT = 'A'
ALL_NUM = -1


def out_aton(symbol: str) -> int:
    return ord(symbol) - ord(__FIRST_OUT) + 1


def out_ntoa(num: int) -> str:
    return chr(ord(__FIRST_OUT) + num - 1)


def validate_mac(value: str) -> str:
    value = value.lower()
    if not re.match("^[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", value):
        raise ArgumentTypeError(f'Invalid MAC address string: {value}')
    return value.replace('-', ':')


def validate_mapping(value: str) -> __mapping:
    value = value.upper()
    if not re.match(f"^([A-Z{__ALL}]|[0-9]{{1,2}}):[0-9]{{1,2}}$", value):
        raise ArgumentTypeError(f'Invalid mapping format: {value}')
    dst, src = value.split(':')
    if dst == __ALL:
        dst = ALL_NUM
    elif dst.isalpha():
        dst = out_aton(dst)
    return __mapping(int(src), int(dst))


def validate_args(args: Namespace, parser: ArgumentParser) -> None:
    if 'map' not in args:
        return

    outputs = []
    group: __mapping
    for group in args.map:
        if group.dst == ALL_NUM and len(args.map) > 1:
            parser.error('Only one mapping group must be ' +
                         f'specified when using {__ALL} as out number')
        if group.dst in outputs:
            dst = out_ntoa(group.dst)
            parser.error(f'Duplicated mapping for output {dst} ({group.dst})')
        outputs.append(group.dst)


class Command(Enum):
    Scan = "scan"
    Status = "status"
    Control = "control"


class CliConfig(object):
    log_udp: str = None
    log_tcp: str = None
    command: Command = None
    num_req: int = None
    bind_to: IPv4Address = None
    device: IPv4Address = None
    device_mac: str = None
    numeric: bool = None
    json: bool = None
    map: List[__mapping] = None

    def __init__(self, args: Namespace):
        args = vars(args)
        self._fill_from(args)
        self.log_tcp = args['logging']
        self.log_udp = args['logging']
        self.command = Command(self.command)

        if 'config' in args and args['config'] is not None:
            self._read_config(args['config'])

    def _read_config(self, data) -> None:
        data = json.load(data)
        self._fill_from(data)
        self._check_ip(data, 'bind_to')
        self._check_ip(data, 'device')
        if 'device_mac' in data:
            self.device_mac = validate_mac(data['device_mac'])

    def _check_ip(self, data: dict, key: str) -> None:
        if key not in data:
            return
        try:
            ip = IPv4Address(data[key])
            setattr(self, key, ip)
        except Exception as e:
            raise ValueError("Invalid IP address value from "
                             + f"config for '{key}': {data[key]}") from e

    def _fill_from(self, data: dict):
        for key, val in data.items():
            if hasattr(self, key):
                setattr(self, key, val)

    def __iter__(self):
        for key in dir(self):
            if key.startswith('__'):
                continue
            item = getattr(self, key)
            if isinstance(item, Callable):
                continue
            yield key, item

    def __repr__(self):
        return str(dict(self))
