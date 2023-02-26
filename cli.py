#! /usr/bin/env python3

from argparse import ArgumentParser


def create_cli() -> ArgumentParser:
    parser = ArgumentParser(prog='drhd-cli', allow_abbrev=False)

    commands = parser.add_argument_group('commands')
    cmds = commands.add_mutually_exclusive_group(required=True)
    cmds.add_argument('--scan', action='store_true', required=False,
                      help="scan local network for devices")
    cmds.add_argument('--status', action='store_true', required=False,
                      help="query device status")
    cmds.add_argument('--control', action='store_true', required=False,
                      help="manage device")

    scan = parser.add_argument_group('scan options')
    scan.add_argument('-n', '--num-req', type=int, metavar='NUM', default=3,
                      help='number of requests sent to network, ' +
                      'default is %(default)s')

    control = parser.add_argument_group('control options')
    control.add_argument('-m', '--map', type=str, nargs='*', metavar='O:I',
                         help='map [I]nputs to [O]utputs, output numbers can be ' +
                              'present in both numerical and alphabetical format, ' +
                              'output 1 is A, output 2 is B, etc. To map specific ' +
                              'input to all outputs use * instead of output number, ' +
                              'in this case only one mapping group should be specified')

    options = parser.add_argument_group('general options')
    options.add_argument('-b', '--bind-to', type=str, metavar='BIND_IP', default='0.0.0.0',
                         help='bind to specific IP address instead of %(default)s ' +
                              'when scanning for devices, useful when you want ' +
                              'to scan only specific network interface')
    options.add_argument('-d', '--device', type=str, metavar='DEV_IP',
                         help='device IP address, if not specified we will try ' +
                              'to automatically find device in local network. ' +
                              'Note that if you have multiple active devices and ' +
                              'no device MAC specified we will connect to first ' +
                              'responded device, what can be totally random due' +
                              'to UDP networking specifics')
    options.add_argument('-M', '--device-mac', type=str, metavar='DEV_MAC',
                         help='device MAC address, if specified we will try ' +
                              'to find device with this MAC in local network')
    options.add_argument('-l', '--logging', type=str, metavar='LEVEL', default='warning',
                         choices=['debug', 'info', 'warning', 'error'],
                         help='set logging level, one of [%(choices)s], ' +
                              'default is %(default)s')
    options.add_argument('-c', '--config', type=str, metavar='CONFIG',
                         help='path to config file in JSON format, ' +
                              'if specified, options --bind-to, --device, ' +
                              '--device-mac and --logging will be ignored ' +
                              'and loaded from config')

    return parser


def main() -> None:
    parser = create_cli()
    args = parser.parse_args()
    print(args)


if __name__ == '__main__':
    main()
