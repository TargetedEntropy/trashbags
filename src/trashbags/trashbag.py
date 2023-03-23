#!/usr/bin/env python

import sys

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound


def player_move(connection: Connection, destination, rotation):
    pos_packet = serverbound.play.PositionAndLookPacket()
    pos_packet.x = float(destination[0])
    pos_packet.feet_y = float(destination[1])
    pos_packet.z = float(destination[2])
    pos_packet.yaw = rotation[0]
    pos_packet.pitch = rotation[1]
    pos_packet.on_ground = True
    connection.write_packet(pos_packet, force=True)


class Trashbag:
    def __init__(self, options: object, connection=None):
        self.options = options
        self.connection = connection
        self.auth_token = None

    def login(self):
        try:
            self.auth_token = authentication.Microsoft_AuthenticationToken()
            self.auth_token.authenticate()
        except YggdrasilError as e:
            print(e)
            sys.exit()
        print(f"Logged in as {self.auth_token.username}...")

    def connect(self):
        try:
            self.connection = Connection(
                self.options.address, self.options.port, self.auth_token, None, "1.8"
            )
            self.connection.connect()

        except Exception as error:
            print(f"Unable to connect, error: {error}")
            sys.exit(1)

    def register_packet_listeners(self):
        # Joining the game
        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.JoinGamePacket
        )

        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.ChatMessagePacket
        )

        if self.options.dump_packets:
            self.connection.register_packet_listener(
                self.print_incoming, Packet, early=True
            )
            self.connection.register_packet_listener(
                self.print_outgoiang, Packet, outgoing=True
            )

    def print_packet(self, packet):
        print(f"{type(packet)}: {packet}")

    def print_debug_incoming(self, packet):
        if type(packet) is Packet:
            # This is a direct instance of the base Packet type, meaning
            # that it is a packet of unknown type, so we do not print it
            # unless explicitly requested by the user.
            if self.options.dump_unknown:
                print("--> [unknown packet] %s" % packet, file=sys.stderr)
        else:
            print("--> %s" % packet, file=sys.stderr)

    def print_debug_outgoing(self, packet):
        print("<-- %s" % packet, file=sys.stderr)

    def send_chat(self: object, text: str):
        packet = serverbound.play.ChatPacket()
        packet.message = text
        self.connection.write_packet(packet)
