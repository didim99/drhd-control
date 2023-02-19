import json

from discovery import NetworkExplorer
from matrix import HDMIMatrix
from protocol import UDPPacket, TCP_PORT


class MatrixController(object):
    config: dict = None
    explorer: NetworkExplorer = None
    device: HDMIMatrix = None

    def __init__(self, config: dict):
        self.config = config

    def find(self):
        self.explorer = NetworkExplorer(self.on_device_found)
        self.explorer.logging(self.config.get("log_udp", "warning"))
        self.explorer.start(self.config.get('ip', '0.0.0.0'))

    def on_device_found(self, data: UDPPacket):
        self.explorer.pause(True)
        self.device = HDMIMatrix((data.devIP, TCP_PORT))
        self.device.logging(self.config.get("log_tcp", "warning"))
        self.device.connect()
        self.explorer.stop()
        self.test_matrix()
        self.device.disconnect()

    def test_matrix(self):
        mapping = self.device.get_port_mapping()
        print(f"--- Port mapping: {mapping} ---")


def run():
    with open('./config.json', 'r') as file:
        config = json.load(file)
    controller = MatrixController(config)
    controller.find()


if __name__ == '__main__':
    run()
