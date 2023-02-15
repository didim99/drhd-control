import logging
import socket
import time
from threading import Event, Thread
from typing import Callable

import protocol
from utils import create_logger


class NetworkExplorer(object):
    _tag = 'explorer'
    _logger = None

    _retry_count = 3
    _sender_delay = 2.0

    _senderThread: Thread = None
    _finderThread: Thread = None
    _senderPaused: bool = False
    _stopEvent: Event = None

    _listener: Callable[[bytes], None] = None
    _broadcast: tuple = None
    _socket: socket = None

    def __init__(self, listener: Callable[[bytes], None]):
        self._logger = create_logger(self._tag, logging.WARNING)
        self._stopEvent = Event()
        self._listener = listener

    def _receiver_loop(self) -> None:
        self._logger.info("Receiver thread started")
        count = 1

        while True:
            try:
                if self._dispatch_stop():
                    self._logger.info("Receiver thread stopped")
                    break

                if self._socket is None:
                    raise EOFError("socket is None")
                self._logger.debug(f"Waiting for server reply ({count})")
                data, address = self._socket.recvfrom(8192)
                self._logger.debug(f"Packet received from: {address}")

                if data:
                    self._logger.debug(f"Message received: {data}")
                    self._listener(data)

                count += 1
            except (EOFError, socket.error) as e:
                self._logger.error(str(e))
                time.sleep(self._sender_delay)
                continue

    def _sender_loop(self) -> None:
        self._logger.info("Sender thread started")
        count = 1

        while True:
            try:
                if self._dispatch_stop():
                    self._logger.info("Sender thread stopped")
                    break

                if not self._senderPaused:
                    self._logger.info(f"Sending broadcast ({count}) to: {self._broadcast}")
                    self._socket.sendto(protocol.DISCOVERY_REQUEST, self._broadcast)
                    count += 1

            except socket.error as e:
                self._logger.error(str(e))
            finally:
                time.sleep(self._sender_delay)

    def start(self, ip: str) -> None:
        self.pause(False)
        self._stopEvent.clear()
        self._open_socket(ip)
        self._logger.info("Starting threads...")
        self._senderThread = Thread(
            name=self._tag + '-sender',
            target=self._sender_loop)
        self._finderThread = Thread(
            name=self._tag + '-receiver',
            target=self._receiver_loop)
        self._senderThread.start()
        self._finderThread.start()

    def pause(self, state: bool) -> None:
        self._logger.info(f"Sender thread paused: {state}")
        self._senderPaused = state

    def stop(self) -> None:
        self._logger.info("Stop event received")
        self._stopEvent.set()

    def _open_socket(self, ip: str) -> None:
        self._broadcast = ('255.255.255.255', protocol.UDP_PORT)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        if hasattr(socket, 'SO_REUSEPORT'):
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        if hasattr(socket, 'SO_BROADCAST'):
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.bind((ip, protocol.UDP_PORT))
        self._logger.info(f"Broadcast socket open at: {self._socket.getsockname()}")

    def _dispatch_stop(self) -> bool:
        if self._stopEvent.is_set():
            if self._socket is not None:
                self._socket.close()
                self._socket = None
            return True
        return False
