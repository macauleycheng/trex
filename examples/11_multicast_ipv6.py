#!/usr/bin/env python3
"""
範例 11: IPv6 Multicast Data
--------------------------------------------------
送一股 IPv6 multicast UDP 資料流。
IPv6 群播的 L2 MAC 映射:
  IPv6 群播位址 -> MAC 33:33 + 位址最後 32 bits
  例: ff1e::1:2:3 -> 33:33:00:01:00:02... (取低 32 bits)

執行: python3 11_multicast_ipv6.py
"""
import proto_common
from proto_common import Ether, UDP, Raw, IPv6
from trex.stl.api import (
    STLClient, STLStream, STLPktBuilder, STLTXCont, STLError
)
import trex_path
import socket

TX_PORT = 0
RX_PORT = 1
MCAST_IP6 = "ff1e::1:2:3"    # global scope (ff1e) 群播位址


def ipv6_mcast_mac(ip6):
    """IPv6 群播位址 -> L2 多播 MAC (33:33 + 位址低 32 bits)。"""
    packed = socket.inet_pton(socket.AF_INET6, ip6)
    last4 = packed[-4:]
    return "33:33:%02x:%02x:%02x:%02x" % (last4[0], last4[1], last4[2], last4[3])


def build_stream():
    dmac = ipv6_mcast_mac(MCAST_IP6)
    pkt = (
        Ether(src="6a:1b:f2:ca:02:87", dst=dmac) /
        IPv6(src="2001:db8::1", dst=MCAST_IP6, hlim=32) /
        UDP(sport=5004, dport=5004) /
        Raw(load=b"MCAST6-STREAM-" + b"D" * 60)
    )
    print("[*] IPv6 multicast: dst_ip=%s -> dst_mac=%s" % (MCAST_IP6, dmac))
    return STLStream(packet=STLPktBuilder(pkt=pkt), mode=STLTXCont(pps=2000))


def main():
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        c.reset(ports=[TX_PORT, RX_PORT])
        c.add_streams(build_stream(), ports=[TX_PORT])
        c.clear_stats()
        c.start(ports=[TX_PORT], duration=2)
        c.wait_on_traffic(ports=[TX_PORT])
        s = c.get_stats()
        print("[結果] port %d 送出=%d, port %d 收到=%d"
              % (TX_PORT, s[TX_PORT]["opackets"], RX_PORT, s[RX_PORT]["ipackets"]))
    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()
