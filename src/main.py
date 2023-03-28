#!/usr/bin/env python

import getpass
import logging
import os
import re
import sys
from optparse import OptionParser

from dotenv import load_dotenv

# from minecraft.networking.packets import serverbound
from trashbags.trashbag import Trashbag

__author__ = "Targeted Entropy"
__copyright__ = "Targeted Entropy"
__license__ = "MPL-2.0"

_logger = logging.getLogger(__name__)


def get_options():
    """
    Using Pythons OptionParser, get the sys args and the corresponding
    input parsed as required until there is enough input to proceed.

    Returns
    -------
    options
        The options to run this instance with

    """
    parser = OptionParser()

    parser.add_option(
        "-u",
        "--username",
        dest="username",
        default=None,
        help="username to log in with",
    )

    parser.add_option(
        "-p",
        "--password",
        dest="password",
        default=None,
        help="password to log in with",
    )

    parser.add_option(
        "-s",
        "--server",
        dest="server",
        default=None,
        help="server host or host:port " "(enclose IPv6 addresses in square brackets)",
    )

    parser.add_option(
        "-o",
        "--offline",
        dest="offline",
        action="store_true",
        help="connect to a server in offline mode " "(no password required)",
    )

    parser.add_option(
        "-d",
        "--dump-packets",
        dest="dump_packets",
        action="store_true",
        help="print sent and received packets to standard error",
    )

    parser.add_option(
        "-v",
        "--dump-unknown-packets",
        dest="dump_unknown",
        action="store_true",
        help="include unknown packets in --dump-packets output",
    )

    parser.add_option(
        "-m",
        "--microsoft",
        dest="microsoft",
        action="store_true",
        help="Enable Microsoft Auth",
    )

    parser.add_option(
        "-x",
        "--verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )

    (options, args) = parser.parse_args()

    if not options.microsoft:
        if not options.username:
            options.username = input("Enter your username: ")

        if not options.password and not options.offline:
            options.password = getpass.getpass(
                "Enter your password (leave " "blank for offline mode): "
            )
            options.offline = options.offline or (options.password == "")

    if not options.server:
        options.server = input(
            "Enter server host or host:port "
            "(enclose IPv6 addresses in square brackets): "
        )
    # Try to split out port and address
    match = re.match(
        r"((?P<host>[^\[\]:]+)|\[(?P<addr>[^\[\]]+)\])" r"(:(?P<port>\d+))?$",
        options.server,
    )
    if match is None:
        raise ValueError("Invalid server address: '%s'." % options.server)
    options.address = match.group("host") or match.group("addr")
    options.port = int(match.group("port") or 25565)

    # Load Env Options
    load_dotenv()
    auth_list = os.getenv("AUTH_LIST")
    if auth_list:
        options.auth_list = auth_list.split(",")

    print(options.auth_list)
    return options


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main():
    options = get_options()

    trash = Trashbag(options)

    # Perform login
    trash.login()

    # Connec to the server
    trash.connect()

    # Register the packet listeners for events
    trash.register_packet_listeners()

    while True:
        try:
            text = input()
            if text == "test":
                print("Testing...")
                print(f"Old: {trash.position}")
                new_pos = (trash.position[0] + 1, trash.position[1], trash.position[2])
                print(f"new_pos: {new_pos}")

                trash.player_move(new_pos, trash.rotation)

                new_pos = (new_pos[0] + 1, new_pos[1], new_pos[2])
                print(f"new_pos: {new_pos}")

                trash.player_move(new_pos, trash.rotation)

            # else:
            #     packet = serverbound.play.ChatPacket()
            #     packet.message = text
            #     trash.connection.write_packet(packet)
        except KeyboardInterrupt:
            _logger.info("Bye!")
            sys.exit()


if __name__ == "__main__":
    main()
