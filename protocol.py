import ipaddress
from ipaddress import IPv4Address

from binutils import Binary, Byte, BWord, BDword, BaseStruct, hexify

UDP_PORT = 30600
TCP_PORT = 8000

DISCOVERY_REQUEST = b'\x61'


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
        return f"MAC: {mac}, IP: {self.devIP}, GW: {self.gwIP}," + \
            f" MASK: {self.netMask}, PORT: {self.devPort}"
