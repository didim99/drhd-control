import json
import random
from ipaddress import IPv4Address

from driver import HDMIMatrix
from driver.discovery import NetworkExplorer
from driver.protocol import UDPPacket, TCP_PORT


class MatrixTester(object):
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
        self.start_test(data.devIP)

    def start_test(self, ip: IPv4Address):
        self.device = HDMIMatrix((ip, TCP_PORT))
        self.device.logging(self.config.get("log_tcp", "warning"))
        self.device.connect()
        if self.explorer is not None:
            self.explorer.stop()
        self.test_matrix()
        self.device.disconnect()

    def test_matrix(self):
        for i in range(self.device.num_out):
            src = self.device.get_source_for(i + 1)
        for i in range(self.device.num_out):
            src = random.randint(1, 4)
            self.device.set_port(src, i + 1)
        mapping = self.device.get_port_mapping()


def run():
    with open('./config.json', 'r') as file:
        config = json.load(file)
    controller = MatrixTester(config)
    if "dev_ip" not in config:
        controller.find()
    else:
        ip = IPv4Address(config['dev_ip'])
        controller.start_test(ip)


if __name__ == '__main__':
    run()
