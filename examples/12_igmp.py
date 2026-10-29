#!/usr/bin/env python3
"""
範例 12: IGMP Query 與 Report (v2 + v3)
--------------------------------------------------
IGMP 用於 IPv4 群播成員管理:
  - Query  : router 問「誰還在收這個群組」(送到 224.0.0.1 all-hosts)
  - Report : host 回「我要加入/我還在這個群組」(送到該群組位址)

本範例組 4 種封包並送出/擷取解析:
  1. IGMPv2 General Query
  2. IGMPv2 Membership Report (join 239.1.2.3)
  3. IGMPv3 General Query
  4. IGMPv3 Membership Report (join 239.1.2.3, mode=CHANGE_TO_EXCLUDE)

重點: IGMP 封包 IP TTL=1, 並帶 IP Router Alert option (0x94040000)。

執行: python3 12_igmp.py
"""
import proto_common
from proto_common import (
    Ether, IP, IGMP, IGMPv3, IGMPv3mq, IGMPv3mr, IGMPv3gr,
)

SRC_MAC = "6a:1b:f2:ca:02:87"
SRC_IP = "10.0.0.2"
GROUP = "239.1.2.3"

# IP Router Alert option (RFC 2113), IGMP 封包需帶
ROUTER_ALERT = b"\x94\x04\x00\x00"


def ipv4_mcast_mac(ip):
    o = [int(x) for x in ip.split(".")]
    return "01:00:5e:%02x:%02x:%02x" % (o[1] & 0x7f, o[2], o[3])


def igmpv2_query():
    # General Query: type=0x11, gaddr=0.0.0.0, 送到 224.0.0.1
    # 註: igmpize() 會自動補上 Router Alert option/TTL/checksum/MAC,
    #     故這裡不手動加 options, 以免重複。
    eth = Ether(src=SRC_MAC, dst=ipv4_mcast_mac("224.0.0.1"))
    ip = IP(src=SRC_IP, dst="224.0.0.1")
    igmp = IGMP(type=0x11, mrcode=100, gaddr="0.0.0.0")
    p = eth / ip / igmp
    p[IGMP].igmpize()   # 自動修正 checksum/TTL/MAC/option
    return p


def igmpv2_report():
    # v2 Membership Report: type=0x16, gaddr=群組, 送到群組位址
    eth = Ether(src=SRC_MAC, dst=ipv4_mcast_mac(GROUP))
    ip = IP(src=SRC_IP, dst=GROUP)
    igmp = IGMP(type=0x16, gaddr=GROUP)
    p = eth / ip / igmp
    p[IGMP].igmpize()
    return p


def igmpv3_query():
    # v3 General Query: type=0x11, 送到 224.0.0.1
    eth = Ether(src=SRC_MAC, dst=ipv4_mcast_mac("224.0.0.1"))
    ip = IP(src=SRC_IP, dst="224.0.0.1", ttl=1, options=ROUTER_ALERT)
    igmp = IGMPv3(type=0x11, mrcode=100) / IGMPv3mq(
        gaddr="0.0.0.0", qrv=2, qqic=125, srcaddrs=[])
    return eth / ip / igmp


def igmpv3_report():
    # v3 Membership Report: type=0x22, 送到 224.0.0.22 (all IGMPv3 routers)
    eth = Ether(src=SRC_MAC, dst=ipv4_mcast_mac("224.0.0.22"))
    ip = IP(src=SRC_IP, dst="224.0.0.22", ttl=1, options=ROUTER_ALERT)
    # rtype 4 = CHANGE_TO_EXCLUDE_MODE (等同 join, 不指定來源)
    grec = IGMPv3gr(rtype=4, maddr=GROUP, srcaddrs=[])
    igmp = IGMPv3(type=0x22) / IGMPv3mr(records=[grec])
    return eth / ip / igmp


if __name__ == "__main__":
    pkts = [igmpv2_query(), igmpv2_report(), igmpv3_query(), igmpv3_report()]
    proto_common.send_and_capture(
        pkts, title="IGMP v2/v3 Query+Report", show_detail=True)
