import logging
import socket
from ipaddress import IPv4Address
from threading import Event
from typing import Tuple, Dict

from binutils import hexify
from command import CmdBuilder
from protocol import TCP_PACKET_LEN, TCPPacket
from utils import SupportsLogging


class HDMIMatrix(SupportsLogging):
    _tag = 'matrix'

    num_out: int = 4
    num_in: int = 4

    endpoint: Tuple[str, int] = None

    _connected: Event = None
    _socket: socket = None
    _buffer: bytearray = None

    def __init__(self, endpoint: Tuple[IPv4Address, int]):
        super().__init__(logging.WARNING)
        self.endpoint = (str(endpoint[0]), endpoint[1])
        self._connected = Event()
        self._buffer = bytearray()

    def connect(self) -> None:
        self._logger.info(f"Connecting to: {self.endpoint}")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect(self.endpoint)
        self._connected.set()
        self._logger.info(f"Connected to: {self.endpoint}")

    def disconnect(self):
        self._logger.info(f"Disconnecting from: {self.endpoint}")
        self._check_connection()
        self._socket.close()
        self._connected.clear()
        self._logger.info("Disconnected")

    def get_port_mapping(self) -> Dict[int, int]:
        mapping = {}
        for i in range(self.num_out):
            self._send_packet(CmdBuilder.query_port(i+1))
            reply = self._read_packet()
            mapping[reply.arg1] = reply.arg2
        return mapping

    def _check_connection(self) -> None:
        if not self._connected.is_set():
            raise socket.error("Not connected!")

    def _send_packet(self, data: TCPPacket) -> None:
        data = bytes(data)
        self._logger.debug(f"SEND >> {hexify(data)}")
        self._socket.send(data)

    def _read_packet(self) -> TCPPacket:
        while len(self._buffer) < TCP_PACKET_LEN:
            data = self._socket.recv(1024)
            self._buffer += data
        data = self._buffer[:TCP_PACKET_LEN]
        self._buffer = self._buffer[TCP_PACKET_LEN:]
        self._logger.debug(f"RECV << {hexify(data)}")
        return TCPPacket(data)
