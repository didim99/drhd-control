from .protocol import TCPPacket, Action, Command


class CmdBuilder(object):

    @staticmethod
    def query_port(port: int) -> TCPPacket:
        return TCPPacket.build(Command.Port, Action.Port.Query, port)

    @staticmethod
    def set_port(src: int, dst: int) -> TCPPacket:
        return TCPPacket.build(Command.Port, Action.Port.Set, src, dst)
