# Original protocol realization by Sean Watson
# See: https://github.com/seanwatson/hdmi-matrix-controller/

import ipaddress
import struct
from ipaddress import IPv4Address

from .binutils import Binary, Byte, BWord, BDword, BaseStruct, hexify, Word

UDP_PORT = 30600
TCP_PORT = 8000

TCP_PACKET_LEN = 13

DISCOVERY_REQUEST = b'\x61'

_TCP_HEADER = b'\xa5\x5b'
_TCP_TAIL = b'\x00' * 4

_CRC_BASE = 0x100

ALL_PORTS = 0x00
PORT_CONNECTED = 0x00


class Command(object):
    Status = 0x01
    Port = 0x02
    EDID = 0x03
    Setup = 0x06


class Action(object):
    class Status(object):
        Input = 0x04
        Output = 0x05
        Beeper = 0x0b

    class Port(object):
        Query = 0x01
        Set = 0x03

    class EDID(object):
        Set = 0x02
        SetAll = 0x01
        Copy = 0x04
        CopyAll = 0x03

    class Setup(object):
        Beeper = 0x01


class EDID(object):
    V1080I_A20 = 0x01
    V1080I_A51 = 0x02
    V1080I_A71 = 0x03
    V1080P_A20 = 0x04
    V1080P_A51 = 0x05
    V1080P_A71 = 0x06
    V3D_A20 = 0x07
    V3D_A51 = 0x08
    V3D_A71 = 0x09
    V4K2K_A20 = 0x0A
    V4K2K_A51 = 0x0B
    V4K2K_A71 = 0x0C
    DVI_1024_768 = 0x0D
    DVI_1920_1080 = 0x0E
    DVI_1920_1200 = 0x0F


class BeepState(object):
    Off = 0xf0
    On = 0x0f


def calc_crc(data) -> int:
    data = struct.unpack(f"{len(data)}b", data)
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

    mac: str = None
    devIP: IPv4Address = None
    gwIP: IPv4Address = None
    netMask: IPv4Address = None
    devPort: int = None
    const1: int = None
    res: bytes = None

    def _fill(self, data: dict):
        super()._fill(data)
        self.mac = hexify(self.mac, ':')
        self.devIP = ipaddress.ip_address(data['devIP'])
        self.gwIP = ipaddress.ip_address(data['gwIP'])
        self.netMask = ipaddress.ip_address(data['netMask'])

    def __eq__(self, other):
        if type(other) is not UDPPacket:
            raise NotImplemented
        other: UDPPacket
        return other.mac == self.mac \
            and other.devIP == self.devIP \
            and other.devPort == self.devPort

    def __repr__(self):
        return f"MAC={self.mac}, IP={self.devIP}, GW={self.gwIP}," + \
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
