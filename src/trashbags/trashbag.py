#!/usr/bin/env python

import json
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
        self.user_list = {}

    def login(self):
        try:
            self.auth_token = authentication.Microsoft_AuthenticationToken()
            if self.options.username:
                if not self.auth_token.PersistenceLogoin_r(self.options.username):
                    print("Login to {} failed".format(self.options.username))
                    sys.exit(1)
            else:
                if not self.auth_token.authenticate():
                    sys.exit(2)
        except YggdrasilError as e:
            print(e)
            sys.exit()
        print(f"Logged in as {self.auth_token.username}...")

    def connect(self):
        try:
            self.connection = Connection(
                self.options.address, self.options.port, self.auth_token, None, "1.12.2"
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
            self.chat_handler, clientbound.play.ChatMessagePacket
        )

        self.connection.register_packet_listener(
            self.print_postion, clientbound.play.PlayerPositionAndLookPacket
        )

        self.connection.register_packet_listener(
            self.user_handler, clientbound.play.PlayerListItemPacket
        )

        # Enable debug listeners
        if self.options.dump_packets:
            self.connection.register_packet_listener(
                self.print_debug_incoming, Packet, early=True
            )
            self.connection.register_packet_listener(
                self.print_debug_outgoing, Packet, outgoing=True
            )

    def print_packet(self, packet):
        print(f"{type(packet)}: {packet}")

    def print_debug_incoming(self, packet):
        if type(packet) is Packet:
            # This is a direct instance of the base Packet type, meaning
            # that it is a packet of unknown type, so we do not print it
            # unless explicitly requested by the user.
            if self.options.dump_unknown:
                print("--> [unknown packet] %s" % packet)  # , file=sys.stderr)
        else:
            print("--> %s" % packet, file=sys.stderr)

    def print_debug_outgoing(self, packet):
        print("<-- %s" % packet, file=sys.stderr)

    def get_msg_sender(self, packet):
        json_data = json.loads(packet.json_data)
        if "extra" in json_data:
            for reponse_iter in json_data["extra"]:
                if reponse_iter["color"] == "light_purple":
                    return reponse_iter["text"]

    def is_whisper(self, packet) -> bool:
        json_data = json.loads(packet.json_data)
        if "color" in json_data:
            return True
        else:
            return False

    def is_authorized(self, sender):
        if sender in self.options.auth_list:
            return True
        else:
            return False

    def user_handler(self, packet):
        if packet.action_type.__name__ == "AddPlayerAction":
            self.user_list[packet.actions[0].name] = packet.actions[0].uuid
        if packet.action_type.__name__ == "RemovePlayerAction":
            self.user_list = {
                k: v for k, v in self.user_list.items() if v != packet.actions[0].uuid
            }

    def chat_handler(self, packet):
        if self.is_whisper(packet):
            sender_name = self.get_msg_sender(packet)
            sender_uuid = self.user_list[sender_name]
            if not self.is_authorized(sender_uuid):
                return
            print(f"Received authorized whisper from {sender_name}")

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
