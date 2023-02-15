import ipaddress
import json

from discovery import NetworkExplorer
from utils import hexify


def on_reply(data: bytes):
    mac = hexify(data[0:6], ":")
    ip = ipaddress.ip_address(data[6:10])
    gw = ipaddress.ip_address(data[10:14])
    mask = ipaddress.ip_address(data[14:18])
    port = int.from_bytes(data[18:20], 'big')
    print(f"MAC: {mac}, IP: {ip}, GW: {gw}, MASK: {mask}, PORT: {port}")

    data = data[20:]
    print('tail:', len(data), '->', hexify(data))


def run():
    with open('./config.json', 'r') as file:
        config = json.load(file)
    explorer = NetworkExplorer(on_reply)
    explorer.start(config.get('ip', '0.0.0.0'))


if __name__ == '__main__':
    run()
