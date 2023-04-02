from .protocol import TCPPacket, Action, Command, BeepState, ALL_PORTS


class CmdBuilder(object):

    @staticmethod
    def query_port(out_port: int) -> TCPPacket:
        return TCPPacket.build(Command.Port, Action.Port.Query, out_port)

    @staticmethod
    def map_port(in_port: int, out_port: int) -> TCPPacket:
        return TCPPacket.build(Command.Port, Action.Port.Set, in_port, out_port)

    @staticmethod
    def set_edid(in_port: int, value: int) -> TCPPacket:
        action = Action.EDID.SetAll if in_port == ALL_PORTS else Action.EDID.Set
        return TCPPacket.build(Command.EDID, action, value, in_port)

    @staticmethod
    def copy_edid(out_port: int, in_port: int) -> TCPPacket:
        action = Action.EDID.CopyAll if in_port == ALL_PORTS else Action.EDID.Copy
        return TCPPacket.build(Command.EDID, action, out_port, in_port)

    @staticmethod
    def output_status(out_port: int) -> TCPPacket:
        return TCPPacket.build(Command.Status, Action.Status.Output, out_port)

    @staticmethod
    def input_status(in_port: int) -> TCPPacket:
        return TCPPacket.build(Command.Status, Action.Status.Input, in_port)

    @staticmethod
    def set_peep(enable: bool) -> TCPPacket:
        state = BeepState.On if enable else BeepState.Off
        return TCPPacket.build(Command.Setup, Action.Setup.Beeper, state)

    @staticmethod
    def query_beep() -> TCPPacket:
        return TCPPacket.build(Command.Status, Action.Status.Beeper)
