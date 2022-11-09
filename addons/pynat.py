# PyNAT: Discover external IP addresses and NAT topologies using STUN.
# Copyright (C) 2022 Ariel A. Licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# pynat.py
"""PyNAT v0.7.0

Discover external IP addresses and NAT topologies using STUN.

Copyright (C) 2022 Ariel A. Licensed under the MIT License.

Drop Python 2 support by Oreomeow, 2022-09-12.
"""
import argparse
import codecs
import ipaddress
import random
import secrets
import socket
import sys

__version__ = "0.7.0"
URL = "https://github.com/aarant/pynat"


class PynatError(Exception):
    """Raised when an error occurs during network discovery."""


# Non-NAT network topologies
BLOCKED = "Blocked"
OPEN = "Open"
UDP_FIREWALL = "UDP Firewall"
# NAT topologies
FULL_CONE = "FullCone"
RESTRICTED_CONE = "Restricted-cone"
RESTRICTED_PORT = "Restricted-port"
SYMMETRIC = "Symmetric"

# Stun message types
BIND_REQUEST_MSG = b"\x00\x01"
BIND_RESPONSE_MSG = b"\x01\x01"
MAGIC_COOKIE = b"\x21\x12\xA4\x42"

# Stun attributes
MAPPED_ADDRESS = b"\x00\x01"
RESPONSE_ADDRESS = b"\x00\x02"
CHANGE_REQUEST = b"\x00\x03"
SOURCE_ADDRESS = b"\x00\x04"
CHANGED_ADDRESS = b"\x00\x05"
XOR_MAPPED_ADDRESS = b"\x00\x20"

# List of classic STUN servers
STUN_SERVERS = [
    ("stun.ekiga.net", 3478),
    ("stun.ideasip.com", 3478),
    ("stun.voiparound.com", 3478),
    ("stun.voipbuster.com", 3478),
    ("stun.voipstunt.com", 3478),
    ("stun.voxgratia.org", 3478),
]


def randint(n):
    return secrets.randbits(n)


def ord_(ch):  # compatible to python3
    return ch if isinstance(ch, int) else ord(ch)


# Get the family of an IP address
def get_address_family(addr):
    try:
        ipaddress.IPv4Interface(addr)
        return socket.AF_INET
    except ipaddress.AddressValueError:
        try:
            ipaddress.IPv6Interface(addr)
            return socket.AF_INET6
        except ipaddress.AddressValueError as e:
            raise PynatError(f"Invalid IP address: {addr}") from e


# Send a STUN message to a server, with optional extra data
def send_stun_message(sock, addr, msg_type, trans_id=None, send_data=b""):
    if trans_id is None:
        trans_id = randint(128).to_bytes(16, byteorder="big")
    msg_len = len(send_data).to_bytes(2, byteorder="big")
    data = msg_type + msg_len + trans_id + send_data
    sock.sendto(data, addr)
    return trans_id


# Get a STUN Binding response from a server, with optional extra data
def get_stun_response(sock, addr, trans_id=None, send_data=b"", max_timeouts=6):
    timeouts = 0
    response = None
    old_timeout = sock.gettimeout()
    sock.settimeout(0.5)
    while timeouts < max_timeouts:
        try:
            trans_id = send_stun_message(
                sock, addr, BIND_REQUEST_MSG, trans_id, send_data
            )
            recv, addr = sock.recvfrom(2048)  # TODO: Why 2048
        except socket.timeout:
            timeouts += 1
            continue
        else:
            # Too short, not a valid message
            if len(recv) < 20:
                continue
            msg_type, recv_trans_id, attrs = recv[:2], recv[4:20], recv[20:]
            msg_len = int(codecs.encode(recv[2:4], "hex"), 16)
            if msg_len != len(attrs):
                continue
            if msg_type != BIND_RESPONSE_MSG:
                continue
            if recv_trans_id != trans_id:
                continue
            response = {}
            i = 0
            while i < msg_len:
                attr_type, attr_length = attrs[i: i + 2], int(
                    codecs.encode(attrs[i + 2: i + 4], "hex"), 16
                )
                attr_value = attrs[i + 4: i + 4 + attr_length]
                i += 4 + attr_length
                if (
                        attr_length % 4 != 0
                ):  # If not on a 32-bit boundary, add padding bytes
                    i += 4 - (attr_length % 4)
                if attr_type in [MAPPED_ADDRESS, SOURCE_ADDRESS, CHANGED_ADDRESS]:
                    family, port = ord_(attr_value[1]), int(
                        codecs.encode(attr_value[2:4], "hex"), 16
                    )
                    if family == 0x01:  # IPv4
                        ip = socket.inet_ntop(socket.AF_INET, attr_value[4:8])
                        if attr_type == XOR_MAPPED_ADDRESS:
                            cookie_int = int(codecs.encode(MAGIC_COOKIE, "hex"), 16)
                            port ^= cookie_int >> 16
                            ip = (
                                    int(codecs.encode(attr_value[4:8], "hex"), 16)
                                    ^ cookie_int
                            )
                            ip = socket.inet_ntoa(ip.to_bytes(4, byteorder="big"))
                            response["xor_ip"], response["xor_port"] = ip, port
                        elif attr_type == MAPPED_ADDRESS:
                            response["ext_ip"], response["ext_port"] = ip, port
                        elif attr_type == SOURCE_ADDRESS:
                            response["src_ip"], response["src_port"] = ip, port
                        elif attr_type == CHANGED_ADDRESS:
                            response["change_ip"], response["change_port"] = ip, port
                    else:  # family == 0x02:  # IPv6
                        ip = socket.inet_ntop(socket.AF_INET6, attr_value[4:20])
                        if attr_type == XOR_MAPPED_ADDRESS:
                            cookie_int = int(codecs.encode(MAGIC_COOKIE, "hex"), 16)
                            port ^= cookie_int >> 16
                            ip = int(codecs.encode(attr_value[4:20], "hex"), 16) ^ (
                                    cookie_int << 96 | trans_id
                            )
                            ip = socket.inet_ntop(
                                socket.AF_INET6, ip.to_bytes(32, byteorder="big")
                            )
                            response["xor_ip"], response["xor_port"] = ip, port
                        elif attr_type == MAPPED_ADDRESS:
                            response["ext_ip"], response["ext_port"] = ip, port
                        elif attr_type == SOURCE_ADDRESS:
                            response["src_ip"], response["src_port"] = ip, port
                        elif attr_type == CHANGED_ADDRESS:
                            response["change_ip"], response["change_port"] = ip, port
            # Prefer, when possible, to use XORed IPs and ports
            xor_ip, xor_port = response.get("xor_ip"), response.get("xor_port")
            if xor_ip is not None:
                response["ext_ip"] = xor_ip
            if xor_port is not None:
                response["ext_port"] = xor_port
            break
    sock.settimeout(old_timeout)
    return response


# Retrieve the internal working IPv4 used to access the Internet
def get_internal_ipv4(test_addr=("8.8.8.8", 80)):  # By default, queries Google's DNS
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(test_addr)
    ip = sock.getsockname()[0]
    sock.close()
    return ip


# Retrieve the internal working IPv6 used to access the Internet
def get_internal_ipv6(
        test_addr=("2001:4860:4860::8888", 80)
):  # By default, queries Google's DNS
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.connect(test_addr)
    ip = sock.getsockname()[0]
    sock.close()
    return ip


# Get a STUN binding response from a server, without any CHANGE_REQUEST flags
def stun_test_1(sock, addr):
    return get_stun_response(sock, addr)


# Get a STUN binding response from a server, asking it to change both the IP & port from which it replies
def stun_test_2(sock, addr):
    return get_stun_response(
        sock, addr, send_data=CHANGE_REQUEST + b"\x00\x04" + b"\x00\x00\x00\x06"
    )


# Get a STUN binding response from a server, asking it to change just the port from which it replies
def stun_test_3(sock, addr):
    return get_stun_response(
        sock, addr, send_data=CHANGE_REQUEST + b"\x00\x04" + b"\x00\x00\x00\x02"
    )


# Find a working classic STUN server from the list
def find_stun_server(sock):
    # Randomize the list so as to avoid using the same server twice in a row
    random.shuffle(STUN_SERVERS)
    for stun_addr in STUN_SERVERS:
        try:
            response = get_stun_response(sock, stun_addr, max_timeouts=1)
        except socket.gaierror:  # Host not found error
            continue
        else:
            if response is not None:  # Have found a working server
                return stun_addr
    return None


# Get the network topology, external IP, and external port
def get_ip_info(
        source_ip="0.0.0.0",
        source_port=54320,
        stun_host=None,
        stun_port=3478,
        include_internal=False,
        sock=None,
):
    """Get information about the network topology, external IP, and external port.

    Args:
        source_ip (str, optional): If not '0.0.0.0', the internal IP address to bind to. Defaults to '0.0.0.0'.
        source_port (int, optional): Source port to bind to. Defaults to 54320.
        stun_host (str, optional): Address of the STUN host to use. Defaults to None, in which case one is selected.
        stun_port (int, optional): Port of the STUN host to query. Defaults to 3478.
        include_internal (bool, optional): Whether to include internal IP address information. Defaults to False.
        sock (socket.socket, optional): Bound socket to connect with. If not provided, one will be created.

    Returns:
        tuple: (topology, external_ip, external_port). Topology & external_ip are strings, external_port is int.
            If `include_internal` is True, returns (topology, external_ip, external_port, internal_ip) instead.
    """
    # If no socket is passed in, create one and close it when done
    ephemeral_sock = sock is None
    if sock is None:
        family = get_address_family(source_ip)
        sock = socket.socket(family, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((source_ip, source_port))
    # Find a stun host if none was selected
    if stun_host is None:
        stun_addr = find_stun_server(sock)
        # If None was found, assume the network is blocked
        if stun_addr is None:
            if ephemeral_sock:
                sock.close()
            if include_internal:
                return BLOCKED, None, None, None
            return BLOCKED, None, None
    # If a stun host was specified, set stun_addr
    else:
        stun_addr = (stun_host, stun_port)
    # Determine the actual local, or source IP
    if source_ip == "0.0.0.0":
        # IPv4
        source_ip = get_internal_ipv4(stun_addr)
    elif source_ip == "::":
        # IPv6
        source_ip = get_internal_ipv6(stun_addr)
    # Perform Test 1, a simple STUN Request
    response = stun_test_1(sock, stun_addr)
    # If the test fails, assume the network blocked
    if response is None:
        if ephemeral_sock:
            sock.close()
        if include_internal:
            return BLOCKED, None, None, None
        return BLOCKED, None, None
    # Otherwise the network is not blocked and we can continue
    ext_ip, ext_port = response["ext_ip"], response["ext_port"]
    change_addr = response.get("change_ip"), response.get("change_port")
    # Either Open Internet or a UDP firewall, do test 2
    if ext_ip == source_ip and ext_port == source_port:
        response = stun_test_2(sock, stun_addr)
        # Open Internet or Symmetric UDP Firewall
        topology = OPEN if response is not None else UDP_FIREWALL
    # Some type of NAT, do test 2
    else:
        response = stun_test_2(sock, stun_addr)
        # Full-cone NAT
        if response is not None:
            topology = FULL_CONE
        # Some other type of NAT, do test 1 on a new ip
        else:
            response = stun_test_1(sock, change_addr)
            # This should never occur
            if response is None:
                if ephemeral_sock:
                    sock.close()
                raise PynatError("Error querying STUN server with changed address.")
            # Symmetric, restricted cone, or restricted port NAT
            recv_ext_ip, recv_ext_port = (response["ext_ip"], response["ext_port"])
            # Some type of restricted NAT, do test 3 to the change_addr with a CHANGE_REQUEST for the port
            if recv_ext_ip == ext_ip and recv_ext_port == ext_port:
                response = stun_test_3(sock, change_addr)
                # Restricted cone NAT or Restricted cone NAT
                topology = RESTRICTED_CONE if response is not None else RESTRICTED_PORT
            # Symmetric NAT
            else:
                topology = SYMMETRIC
    if ephemeral_sock:
        sock.close()
    if include_internal:
        return topology, ext_ip, ext_port, source_ip
    return topology, ext_ip, ext_port


def main():
    try:
        parser = argparse.ArgumentParser(prog="pynat", description=__doc__)
        parser.add_argument(
            "--source_ip",
            help="The source IPv4/IPv6 address to bind to.",
            type=str,
            default="0.0.0.0",
        )
        parser.add_argument(
            "--source-port", help="The source port to bind to.", type=int, default=54320
        )
        parser.add_argument(
            "--stun-host", help="The STUN host to use for queries.", type=str
        )
        parser.add_argument(
            "--stun-port",
            help="The port of the STUN host to use for queries.",
            type=int,
            default=3478,
        )
        args = parser.parse_args()
        source_ip, source_port, stun_host, stun_port = (
            args.source_ip,
            args.source_port,
            args.stun_host,
            args.stun_port,
        )
        topology, ext_ip, ext_port, source_ip = get_ip_info(
            source_ip, source_port, stun_host, stun_port, True
        )
        print(
            "Network type:",
            topology,
            f"\nInternal address: {source_ip}:{source_port}",
            f"\nExternal address: {ext_ip}:{ext_port}",
        )
    except KeyboardInterrupt:
        sys.exit()
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
