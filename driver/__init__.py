import logging
import socket
from enum import Enum
from ipaddress import IPv4Address
from threading import Event
from typing import Tuple, Dict

from .binutils import hexify
from .command import CmdBuilder
from .protocol import TCP_PACKET_LEN, PORT_CONNECTED, TCPPacket
from .utils import SupportsLogging


class ProtocolError(Exception):
    pass


class PortType(Enum):
    Input = "input"
    Output = "output"


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

    def disconnect(self) -> None:
        self._check_connection()
        self._logger.info(f"Disconnecting from: {self.endpoint}")
        self._socket.close()
        self._connected.clear()
        self._logger.info("Disconnected")

    def get_source_for(self, out_port: int) -> int:
        self._check_connection()
        self._send_packet(CmdBuilder.query_port(out_port))
        reply = self._read_packet()
        self._logger.info(f"Port mapping: {reply.arg1} -> {reply.arg2}")
        return reply.arg1

    def get_input_status(self, in_port: int) -> bool:
        """:returns True if port is connected, otherwise false"""
        return self.get_port_status(in_port, PortType.Input)

    def get_output_status(self, out_port: int) -> bool:
        """:returns True if port is connected (HPD signal present), otherwise false"""
        return self.get_port_status(out_port, PortType.Output)

    def get_port_status(self, port: int, _type: PortType) -> bool:
        self._check_connection()
        cmd = CmdBuilder.input_status if _type is PortType.Input \
            else CmdBuilder.output_status
        self._send_packet(cmd(port))
        reply = self._read_packet()
        connected = reply.arg2 == PORT_CONNECTED
        status = "connected" if connected else "not connected"
        self._logger.info(f"{_type.value.capitalize()} {reply.arg1} is {status}")
        return connected

    def get_inputs_status(self) -> Dict[int, bool]:
        return self.get_ports_status(PortType.Input)

    def get_outputs_status(self) -> Dict[int, bool]:
        return self.get_ports_status(PortType.Output)

    def get_ports_status(self, _type: PortType) -> Dict[int, bool]:
        count = self.num_in if _type is PortType.Input else self.num_out
        res = {}
        for i in range(count):
            res[i + 1] = self.get_port_status(i + 1, _type)
        return res

    def get_port_mapping(self) -> Dict[int, int]:
        """
        :returns dictionary that contains mapping between inputs and outputs
                 where keys represents output numbers (starting from 1) and
                 values represents corresponding input numbers.
        """
        self._check_connection()
        mapping = {}
        for i in range(self.num_out):
            self._send_packet(CmdBuilder.query_port(i + 1))
            reply = self._read_packet()
            mapping[reply.arg1] = reply.arg2
        self._logger.info(f"Port mapping: {mapping}")
        return mapping

    def map_port(self, in_port: int, out_port: int):
        self._send_packet(CmdBuilder.map_port(in_port, out_port))
        reply = self._read_packet()
        if reply.arg2 != out_port:
            raise ProtocolError(f"Invalid response, expected {out_port}, got {reply.arg2}")
        self._logger.info(f"Set port mapping: {in_port} -> {out_port}")

    def map_all(self, in_port: int):
        for i in range(self.num_out):
            self.map_port(in_port, i + 1)

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
