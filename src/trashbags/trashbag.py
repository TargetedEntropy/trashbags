#!/usr/bin/env python

import json
import sys

from minecraft import authentication
from minecraft.exceptions import YggdrasilError
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, clientbound, serverbound

from .discord_logging import MyLittleDiscord

# from minecraft.operation.move import player_move


class Trashbag:
    def __init__(self, options: object, connection=None):
        self.options = options
        self.connection = connection
        self.auth_token = None
        self.position = (0, 0, 0)
        self.rotation = (0, 0)

        # Health
        self.health = 0.0
        self.food = 0
        self.food_saturation = 0.0

        self.user_list = {}
        self.entity_list = {}
        self.discord = MyLittleDiscord(self.options)

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

    def update_postion(self, postion_packet):
        self.position = (postion_packet.x, postion_packet.y, postion_packet.z)
        self.rotation = (postion_packet.yaw, postion_packet.pitch)

    def update_users(self, packet):
        if packet.action_type.__name__ == "AddPlayerAction":
            self.user_list[packet.actions[0].name] = packet.actions[0].uuid
        if packet.action_type.__name__ == "RemovePlayerAction":
            self.user_list = {
                k: v for k, v in self.user_list.items() if v != packet.actions[0].uuid
            }

    def update_health(self, packet: object):
        self.food = packet.food
        self.health = packet.health
        self.food_saturation = packet.food_saturation

    def register_packet_listeners(self):
        # Joining the game
        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.JoinGamePacket
        )

        self.connection.register_packet_listener(
            self.chat_handler, clientbound.play.ChatMessagePacket
        )

        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.RespawnPacket
        )

        # self.connection.register_packet_listener(
        #     self.print_packet, clientbound.play.UnknownPacket
        # )

        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.PlayerPositionAndLookPacket
        )

        self.connection.register_packet_listener(
            self.update_postion, clientbound.play.PlayerPositionAndLookPacket
        )

        self.connection.register_packet_listener(
            self.update_users, clientbound.play.PlayerListItemPacket
        )

        self.connection.register_packet_listener(
            self.update_health, clientbound.play.UpdateHealthPacket
        )

        self.connection.register_packet_listener(
            self.print_packet, clientbound.play.NBTQueryPacket
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

    def get_chat_sender(self, packet):
        json_data = json.loads(packet.json_data)
        if "extra" in json_data:
            for extra_data in json_data["extra"]:
                if "color" not in extra_data:
                    continue
                return extra_data["text"]

    def is_whisper(self, packet) -> bool:
        json_data = json.loads(packet.json_data)
        if "color" in json_data:
            return True
        else:
            return False

    def is_chat(self, packet) -> bool:
        json_data = json.loads(packet.json_data)
        if "extra" in json_data:
            if len(json_data["extra"]) > 0:
                if json_data["extra"][0]["text"] == "<":
                    return True

    def is_authorized(self, sender):
        if sender in self.options.auth_list:
            return True
        else:
            return False

    def get_chat_message(self, packet) -> str:
        json_data = json.loads(packet.json_data)
        if "extra" in json_data:
            if len(json_data["extra"]) == 4:
                return json_data["extra"][3]["text"]
            elif len(json_data["extra"]) == 3:
                return json_data["extra"][2]["text"]

    def chat_handler(self, packet):
        # Skip chat if we're still loading
        if self.user_list is None:
            return

        if self.is_whisper(packet):
            sender_name = self.get_msg_sender(packet)
            sender_uuid = self.user_list[sender_name]

            # Sekurity
            if not self.is_authorized(sender_uuid):
                return

            print(f"Received authorized whisper from {sender_name}")
            self.discord.send_channel_message(
                f"Received authorized whisper from {sender_name}"
            )

            whisper_msg = self.get_chat_message(packet)

            self.whisper_handler(sender_name, sender_uuid, whisper_msg)

        elif self.is_chat(packet):
            sender_name = self.get_chat_sender(packet)
            sender_uuid = self.user_list[sender_name]

            # sekuritay
            if sender_uuid is None:
                return

            chat_msg = self.get_chat_message(packet)
            print(f"{sender_name} > {chat_msg}")

            self.public_handler(sender_name, sender_uuid, chat_msg)

    def whisper_handler(
        self, sender_name: str, sender_uuid: str, whisper_msg: str
    ) -> None:
        if not self.is_authorized(sender_uuid):
            return

        if whisper_msg == "hi":
            print(f"GotWhisper: {whisper_msg}")

    def public_handler(self, sender_name: str, sender_uuid: str, chat_msg: str) -> None:
        # Admin Commands
        if self.is_authorized(sender_uuid):
            print(f"Received authorized chat from {sender_name}, msg: {chat_msg}")
            if chat_msg == "purge":
                self.send_chat("initiating purge...")
            elif chat_msg == "hrmm":
                print("Got a HRMM")

        pass

    def send_chat(self: object, text: str):
        packet = serverbound.play.ChatPacket()
        packet.message = text
        self.connection.write_packet(packet)

    def player_move(self, destination, on_ground=True):
        print(f"postition: {destination}, onground: {on_ground}")

        pos_packet = serverbound.play.PlayerPositionPacket()
        pos_packet.x = float(destination[0])
        pos_packet.feet_y = float(destination[1])
        pos_packet.z = float(destination[2])
        # pos_packet.yaw = rotation[0]
        # pos_packet.pitch = rotation[1]
        pos_packet.on_ground = on_ground
        self.connection.write_packet(pos_packet, force=True)

    def respawn(self):
        packet = serverbound.play.ClientStatusPacket()
        packet.action_id = 0
        self.connection.write_packet(packet, force=True)
