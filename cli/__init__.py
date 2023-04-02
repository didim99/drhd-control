import json
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
            self._start_explorer()
        else:
            self._run_command(self.config.device)

    def _start_explorer(self):
        self.explorer = NetworkExplorer(self._on_device_found)
        self.explorer.logging(self.config.log_udp)
        self.explorer.retry_count(self.config.num_req)
        self.explorer.start(str(self.config.bind_to))

    def _on_device_found(self, data: UDPPacket) -> None:
        if self.config.command is Command.Scan:
            if data not in self.devices:
                print(data)
            self.devices.append(data)
            return

        if self.config.device_mac is not None \
                and data.mac.lower() != self.config.device_mac.lower():
            return

        self.explorer.stop()
        self._run_command(data.devIP)

    def _run_command(self, addr: IPv4Address):
        self.device = HDMIMatrix((addr, TCP_PORT))
        self.device.logging(self.config.log_tcp)
        self.device.connect()

        if self.config.command is Command.Status:
            self._query_status()
        elif self.config.command is Command.Control:
            self._control_device()

        self.device.disconnect()

    def _query_status(self) -> None:
        mapping = self.device.get_port_mapping()
        inputs = self.device.get_inputs_status()
        outputs = self.device.get_outputs_status()

        conv = str if self.config.numeric else out_ntoa
        mapping = {conv(o): i for o, i in mapping.items()}
        inputs = {str(o): s for o, s in inputs.items()}
        outputs = {conv(o): s for o, s in outputs.items()}

        if self.config.json:
            res = {"mapping": mapping,
                   "inputs": inputs,
                   "outputs": outputs}
            print(json.dumps(res))
            return

        sconv = lambda s: "+" if s else "-"
        inputs = {o: sconv(s) for o, s in inputs.items()}
        outputs = {o: sconv(s) for o, s in outputs.items()}

        fmt_start = "{:>6s}"
        str_in = fmt_start.format("IN:")
        str_out = fmt_start.format("OUT:")
        str_name = fmt_start.format("") + " PORT MAPPING"
        for o, i in mapping.items():
            str_out += f" {o:>2s}"
            str_in += f" {i:>2d}"

        _len = max(len(str_out), len(str_in), len(str_name)) + 3
        str_name = str_name.ljust(_len)
        str_out = str_out.ljust(_len)
        str_in = str_in.ljust(_len)
        str_name += " CONNECTION STATUS"

        for o, s in outputs.items():
            str_out += f" {o:>2s}: {s}"
        for o, s in inputs.items():
            str_in += f" {o:>2s}: {s}"

        print()
        print(str_name)
        print(str_out)
        print(str_in)
        print()

    def _control_device(self) -> None:
        for mapping in self.config.map:
            if mapping.dst == config.ALL_NUM:
                self.device.map_all(mapping.src)
                return
            self.device.map_port(mapping.src, mapping.dst)


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
    network.add_argument('-r', '--num-req', type=int, metavar='NUM', default=3,
                         help='number of requests sent to network, ' +
                              'default is %(default)s')

    commands = parser.add_subparsers(dest='command', metavar='COMMAND',
                                     required=True, title='possible commands')
    scan = commands.add_parser('scan', help='scan local network for devices',
                               parents=[network])

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
