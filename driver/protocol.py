# Original protocol realization by Sean Watson
# See: https://github.com/seanwatson/hdmi-matrix-controller/

import ipaddress
from ipaddress import IPv4Address

from .binutils import Binary, Byte, BWord, BDword, BaseStruct, hexify, Word

UDP_PORT = 30600
TCP_PORT = 8000

TCP_PACKET_LEN = 13

DISCOVERY_REQUEST = b'\x61'

_TCP_HEADER = b'\xa5\x5b'
_TCP_TAIL = b'\x00' * 4

_CRC_BASE = 0x100


class Command(object):
    Status = 0x01
    Port = 0x02
    EDID = 0x03


class Action(object):
    class Port(object):
        Query = 0x01
        Set = 0x03


def calc_crc(data) -> int:
    crc = _CRC_BASE - sum(data)
    if crc < 0:
        while crc < 0:
            crc += 0xff
        crc += 1
    return crc


class _UDPPacket(metaclass=Binary):
    size = 55           # Offset     Size         Description
    mac = Byte[6]       # 0x00 (0)   6  (byte[6]) Device MAC address
    devIP = BDword      # 0x06 (6)   4  (uint32)  Device IP address
    gwIP = BDword       # 0x0a (10)  4  (uint32)  Gateway IP address
    netMask = BDword    # 0x0e (14)  4  (uint32)  Subnet mask
    devPort = BWord     # 0x12 (18)  2  (uint16)  Device config port (?)
    const1 = BWord      # 0x14 (20)  2  (uint16)  Constant (?) 80 in big-endian
    res = Byte[32]      # 0x16 (22)  32 (???)     Placeholder (?) zero-bytes
    tail = Byte         # 0x14 (54)  1 (uint8)    Packet tail (?) constant 0x01


class UDPPacket(BaseStruct):
    _proto = _UDPPacket

    mac: bytes
    devIP: IPv4Address
    gwIP: IPv4Address
    netMask: IPv4Address
    devPort: int
    const1: int
    res: bytes

    def _fill(self, data: dict):
        super()._fill(data)
        self.devIP = ipaddress.ip_address(data['devIP'])
        self.gwIP = ipaddress.ip_address(data['gwIP'])
        self.netMask = ipaddress.ip_address(data['netMask'])

    def __repr__(self):
        mac = hexify(self.mac, ':')
        return f"MAC={mac}, IP={self.devIP}, GW={self.gwIP}," + \
            f" MASK={self.netMask}, PORT={self.devPort}"


class _TCPPacket(metaclass=Binary):
    size = 13           # Offset     Size         Description
    header = Byte[2]    # 0x00 (0)   2  (byte[2]) Packet header 0xa5, 0x5b
    cmd = Byte          # 0x02 (2)   1  (uint8)   Command group
    action = Byte       # 0x03 (3)   1  (uint8)   Command action
    arg1 = Word         # 0x04 (4)   2  (uint16)  1-st argument
    arg2 = Word         # 0x06 (6)   2  (uint16)  2-nd argument
    tail = Byte[4]      # 0x08 (8)   4  (uint32)  Always zero bytes
    crc = Byte          # 0x0c (12)  1  (uint8)   Packet CRC


class TCPPacket(BaseStruct):
    _proto = _TCPPacket

    header: bytes = _TCP_HEADER
    cmd: int
    action: int
    arg1: int
    arg2: int
    tail: bytes = _TCP_TAIL
    crc: int = 0

    def _fill(self, data: dict):
        super()._fill(data)
        crc = calc_crc(self._rawValue[:-1])
        if self.crc != crc:
            raise ValueError(f"Invalid CRC: {self.crc}, expected {crc}")

    @staticmethod
    def build(group: int, action: int,
              arg1: int = 0, arg2: int = 0):
        pkt = TCPPacket()
        pkt.cmd = group
        pkt.action = action
        pkt.arg1 = arg1
        pkt.arg2 = arg2
        pkt.crc = calc_crc(bytes(pkt)[:-1])
        return pkt

    def __repr__(self):
        return f"CMD={self.cmd}:{self.action}, " + \
            f"ARGS={self.arg1}:{self.arg2}, CRC={self.crc}"
