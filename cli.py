#! /usr/bin/env python3

from argparse import ArgumentParser, FileType
from ipaddress import IPv4Address


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
    dev_sel.add_argument('-M', '--device-mac', type=str, metavar='DEV_MAC',
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
    control.add_argument('-m', '--map', type=str, nargs='+', metavar='O:I',
                         required=True,
                         help='map [I]nputs to [O]utputs, output numbers can be ' +
                              'present in both numerical and alphabetical format, ' +
                              'output 1 is A, output 2 is B, etc. To map specific ' +
                              'input to all outputs use * instead of output number, ' +
                              'in this case only one mapping group should be specified')

    return parser


def main() -> None:
    parser = create_cli()
    args = parser.parse_args()
    print(args)


if __name__ == '__main__':
    main()
