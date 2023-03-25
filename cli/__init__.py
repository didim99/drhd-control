from argparse import ArgumentParser, FileType
from ipaddress import IPv4Address
from typing import List

from driver import HDMIMatrix
from driver.discovery import NetworkExplorer
from driver.protocol import UDPPacket, TCP_PORT
from .config import validate_mac, validate_mapping, \
    validate_args, CliConfig, __ALL, Command, out_ntoa


class MatrixController(object):
    config: CliConfig = None
    explorer: NetworkExplorer = None
    devices: List[UDPPacket] = None
    device: HDMIMatrix = None

    def __init__(self, cfg: CliConfig):
        self.config = cfg
        self.devices = []

    def start(self):
        if self.config.command is Command.Scan \
                or self.config.device is None:
            self.start_explorer()
        else:
            self.run_command(self.config.device)

    def start_explorer(self):
        self.explorer = NetworkExplorer(self.on_device_found)
        self.explorer.logging(self.config.log_udp)
        self.explorer.retry_count(self.config.num_req)
        self.explorer.start(str(self.config.bind_to))

    def on_device_found(self, data: UDPPacket) -> None:
        if self.config.command is Command.Scan:
            if data not in self.devices:
                print(data)
            self.devices.append(data)
            return

        if self.config.device_mac is not None \
                and data.mac.lower() != self.config.device_mac.lower():
            return

        self.explorer.stop()
        self.run_command(data.devIP)

    def run_command(self, addr: IPv4Address):
        self.device = HDMIMatrix((addr, TCP_PORT))
        self.device.logging(self.config.log_tcp)
        self.device.connect()

        if self.config.command is Command.Status:
            self.query_status()
        elif self.config.command is Command.Control:
            self.setup_device()

        self.device.disconnect()

    def query_status(self):
        mapping = self.device.get_port_mapping()
        outputs = [out_ntoa(o) for o in mapping.keys()]
        inputs = list(mapping.values())

        print(outputs)
        print(inputs)

    def setup_device(self):
        pass


def create_cli() -> ArgumentParser:
    parser = ArgumentParser(prog='drhd-cli', allow_abbrev=False, add_help=False,
                            description='Utility to control Dr.HD HDMI ' +
                                        'matrix over TCP/IP',
                            epilog='to get help for specific COMMAND ' +
                                   'type: %(prog)s COMMAND -h')

    options = parser.add_argument_group('general options')
    options.add_argument('-h', '--help', action='help',
                         help='show this help message and exit')
    options.add_argument('-l', '--logging', type=str, metavar='LEVEL', default='warning',
                         choices=['debug', 'info', 'warning', 'error'],
                         help='set logging level, one of [%(choices)s], ' +
                              'default is %(default)s')
    options.add_argument('-c', '--config', type=FileType('r'), metavar='CONFIG',
                         help='path to config file in JSON format, ' +
                              'if specified, options --bind-to, --device, ' +
                              '--device-mac and --logging will be ignored ' +
                              'and loaded from config')

    connect = ArgumentParser(add_help=False, allow_abbrev=False)
    dev_sel = connect.add_mutually_exclusive_group(required=True)
    dev_sel.add_argument('-d', '--device', type=IPv4Address, metavar='DEV_IP',
                         help='device IP address, if not specified we will try ' +
                              'to automatically find device in local network. ' +
                              'Note that if you have multiple active devices and ' +
                              'no device MAC specified we will connect to first ' +
                              'responded device, what can be totally random due' +
                              'to UDP networking specifics')
    dev_sel.add_argument('-M', '--device-mac', type=validate_mac, metavar='DEV_MAC',
                         help='device MAC address, if specified we will try ' +
                              'to find device with this MAC in local network')

    network = ArgumentParser(add_help=False, allow_abbrev=False)
    network.add_argument('-b', '--bind-to', type=IPv4Address,
                         metavar='BIND_IP', default='0.0.0.0',
                         help='bind to specific IP address instead of %(default)s ' +
                              'when scanning for devices, useful when you want ' +
                              'to scan only specific network interface')

    commands = parser.add_subparsers(dest='command', metavar='COMMAND',
                                     required=True, title='possible commands')
    scan = commands.add_parser('scan', help='scan local network for devices',
                               parents=[network])
    scan.add_argument('-n', '--num-req', type=int, metavar='NUM', default=3,
                      help='number of requests sent to network, ' +
                      'default is %(default)s')

    status = commands.add_parser('status', help='query device status',
                                 parents=[network, connect])
    status.add_argument('-n', '--numeric', action='store_true',
                        help='use numeric notation for outputs instead of ' +
                             'alphabetical: output A is 1, output B is 2, etc')
    status.add_argument('-j', '--json', action='store_true',
                        help='format output as JSON')

    control = commands.add_parser('control', help='manage device',
                                  parents=[network, connect])
    control.add_argument('-m', '--map', type=validate_mapping, metavar='O:I',
                         required=True, nargs='+',
                         help='map [O]utputs to [I]nputs, output numbers can be ' +
                              'present in both numerical and alphabetical format, ' +
                              'output 1 is A, output 2 is B, etc. To map specific input ' +
                              f'to all outputs use {__ALL} instead of output number, ' +
                              'in this case only one mapping group should be specified')

    return parser


def main() -> None:
    parser = create_cli()
    args = parser.parse_args()
    validate_args(args, parser)
    try:
        cfg = CliConfig(args)
    except Exception as e:
        parser.error(str(e))
        exit()

    controller = MatrixController(cfg)
    controller.start()
