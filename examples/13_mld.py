#!/usr/bin/env python3
"""
範例 13: MLD (Multicast Listener Discovery) Query 與 Report
--------------------------------------------------
MLD 是 IPv6 版的 IGMP, 用 ICMPv6 承載:
  - Query  (type 130): router 問「誰還在聽這個群組」
  - Report (type 131): host 回報「我要聽這個群組」
  - Done   (type 132): host 離開群組 (等同 IGMP leave)

重點:
  1. MLD 封包要帶 IPv6 Hop-by-Hop Extension Header + Router Alert (MLD=0)
  2. 來源用 link-local (fe80::), hop limit = 1
  3. L2 MAC = 33:33 + 目的位址低 32 bits

本範例組 General Query / Report / Done 並送出擷取解析。

執行: python3 13_mld.py
"""
import socket
import proto_common
from proto_common import (
    Ether, IPv6, IPv6ExtHdrHopByHop, RouterAlert,
    ICMPv6MLQuery, ICMPv6MLReport, ICMPv6MLDone,
)

SRC_MAC = "6a:1b:f2:ca:02:87"
SRC_IP6 = "fe80::1"                 # link-local 來源
GROUP6 = "ff1e::1:2:3"              # 要聽的群播群組
ALL_NODES = "ff02::1"              # General Query 送到 all-nodes
ALL_ROUTERS = "ff02::2"           # Report/Done 送到 all-routers


def ipv6_mcast_mac(ip6):
    last4 = socket.inet_pton(socket.AF_INET6, ip6)[-4:]
    return "33:33:%02x:%02x:%02x:%02x" % tuple(last4)


def hbh():
    # Hop-by-Hop + Router Alert (value 0 = MLD)
    return IPv6ExtHdrHopByHop(options=[RouterAlert(value=0)])


def mld_query():
    # General Query: mladdr=:: (問所有群組), 送到 ff02::1
    eth = Ether(src=SRC_MAC, dst=ipv6_mcast_mac(ALL_NODES))
    ip6 = IPv6(src=SRC_IP6, dst=ALL_NODES, hlim=1)
    mld = ICMPv6MLQuery(mrd=10000, mladdr="::")
    return eth / ip6 / hbh() / mld


def mld_report():
    # Listener Report: mladdr=群組, 送到 all-routers ff02::2
    eth = Ether(src=SRC_MAC, dst=ipv6_mcast_mac(ALL_ROUTERS))
    ip6 = IPv6(src=SRC_IP6, dst=ALL_ROUTERS, hlim=1)
    mld = ICMPv6MLReport(mladdr=GROUP6)
    return eth / ip6 / hbh() / mld


def mld_done():
    # Listener Done (leave): 送到 all-routers ff02::2
    eth = Ether(src=SRC_MAC, dst=ipv6_mcast_mac(ALL_ROUTERS))
    ip6 = IPv6(src=SRC_IP6, dst=ALL_ROUTERS, hlim=1)
    mld = ICMPv6MLDone(mladdr=GROUP6)
    return eth / ip6 / hbh() / mld


if __name__ == "__main__":
    pkts = [mld_query(), mld_report(), mld_done()]
    proto_common.send_and_capture(
        pkts, title="MLD Query/Report/Done", show_detail=True)
