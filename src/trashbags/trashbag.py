#!/usr/bin/env python

import sys

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound

# from minecraft.operation.move import player_move


class Trashbag:
    def __init__(self, options: object, connection=None):
        self.options = options
        self.connection = connection
        self.auth_token = None
        self.position = (0, 0, 0)
        self.rotation = (0, 0)

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
                self.options.address,
                self.options.port,
                self.auth_token,
                None,
                "1.8"
                # self.options.address,
                # self.options.port,
                # None,
                # "bob",
                # "1.8",
            )
            self.connection.connect()

        except Exception as error:
            print(f"Unable to connect, error: {error}")
            sys.exit(1)

    def print_postion(self, postion_packet):
        print(f"PositionPacket ({postion_packet}): {postion_packet}")
        self.position = (postion_packet.x, postion_packet.y, postion_packet.z)
        self.rotation = (postion_packet.yaw, postion_packet.pitch)
        print(self.rotation)

    def register_packet_listeners(self):
        # Joining the game
        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.JoinGamePacket
        )

        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.ChatMessagePacket
        )

        self.connection.register_packet_listener(
            self.print_postion, clientbound.play.PlayerPositionAndLookPacket
        )

        # Enable debug listeners
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

    def player_move(self, destination, rotation, on_ground=True):
        pos_packet = serverbound.play.PositionAndLookPacket()
        pos_packet.x = float(destination[0])
        pos_packet.feet_y = float(destination[1])
        pos_packet.z = float(destination[2])
        pos_packet.yaw = rotation[0]
        pos_packet.pitch = rotation[1]
        pos_packet.on_ground = on_ground
        self.connection.write_packet(pos_packet, force=True)
