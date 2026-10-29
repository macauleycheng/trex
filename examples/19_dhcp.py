#!/usr/bin/env python3
"""
範例 19: DHCP DORA 四步握手 (Discover / Offer / Request / ACK)
--------------------------------------------------
DHCP 用 BOOTP + DHCP options 承載, 走 UDP (client:68 -> server:67,
server:67 -> client:68)。標準租約流程 DORA:
  1. Discover : client 廣播「有沒有 DHCP server?」
  2. Offer    : server 回「我可以給你 192.168.1.100」
  3. Request  : client 廣播「我要用 192.168.1.100」
  4. ACK      : server 確認「好, 租給你」(即 reply)

本範例組這四個封包並送出/擷取解析。

執行: python3 19_dhcp.py
"""
import proto_common
from proto_common import Ether, IP, UDP, BOOTP, DHCP

CLIENT_MAC = "6a:1b:f2:ca:02:87"
SERVER_MAC = "06:94:be:ef:3b:4d"
CLIENT_MAC_RAW = bytes(int(x, 16) for x in CLIENT_MAC.split(":"))
XID = 0x12345678                  # transaction id, 整個 DORA 共用
OFFERED_IP = "192.168.1.100"
SERVER_IP = "192.168.1.1"


def dhcp_discover():
    # client -> broadcast
    return (
        Ether(src=CLIENT_MAC, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(op=1, chaddr=CLIENT_MAC_RAW, xid=XID, flags=0x8000) /
        DHCP(options=[
            ("message-type", "discover"),
            ("param_req_list", [1, 3, 6, 15]),   # subnet/router/dns/domain
            "end",
        ])
    )


def dhcp_offer():
    # server -> client (這裡用廣播, 真實可單播)
    return (
        Ether(src=SERVER_MAC, dst=CLIENT_MAC) /
        IP(src=SERVER_IP, dst="255.255.255.255") /
        UDP(sport=67, dport=68) /
        BOOTP(op=2, chaddr=CLIENT_MAC_RAW, xid=XID,
              yiaddr=OFFERED_IP, siaddr=SERVER_IP) /
        DHCP(options=[
            ("message-type", "offer"),
            ("server_id", SERVER_IP),
            ("lease_time", 86400),
            ("subnet_mask", "255.255.255.0"),
            ("router", "192.168.1.1"),
            "end",
        ])
    )


def dhcp_request():
    # client -> broadcast, 指明要哪個 IP / 哪台 server
    return (
        Ether(src=CLIENT_MAC, dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(op=1, chaddr=CLIENT_MAC_RAW, xid=XID, flags=0x8000) /
        DHCP(options=[
            ("message-type", "request"),
            ("requested_addr", OFFERED_IP),
            ("server_id", SERVER_IP),
            "end",
        ])
    )


def dhcp_ack():
    # server -> client, 確認租約 (reply)
    return (
        Ether(src=SERVER_MAC, dst=CLIENT_MAC) /
        IP(src=SERVER_IP, dst="255.255.255.255") /
        UDP(sport=67, dport=68) /
        BOOTP(op=2, chaddr=CLIENT_MAC_RAW, xid=XID,
              yiaddr=OFFERED_IP, siaddr=SERVER_IP) /
        DHCP(options=[
            ("message-type", "ack"),
            ("server_id", SERVER_IP),
            ("lease_time", 86400),
            ("subnet_mask", "255.255.255.0"),
            ("router", "192.168.1.1"),
            "end",
        ])
    )


if __name__ == "__main__":
    pkts = [dhcp_discover(), dhcp_offer(), dhcp_request(), dhcp_ack()]
    proto_common.send_and_capture(
        pkts, title="DHCP DORA (Discover/Offer/Request/ACK)",
        show_detail=True)
