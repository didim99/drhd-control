import json

from binutils import hexify
from discovery import NetworkExplorer
from protocol import UDPPacket


def on_reply(data: UDPPacket):
    print(data)
    print(data.const1, '|', hexify(data.res))


def run():
    with open('./config.json', 'r') as file:
        config = json.load(file)
    explorer = NetworkExplorer(on_reply)
    explorer.start(config.get('ip', '0.0.0.0'))


if __name__ == '__main__':
    run()
