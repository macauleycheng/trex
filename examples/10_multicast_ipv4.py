#!/usr/bin/env python3
"""
範例 10: IPv4 Multicast Data
--------------------------------------------------
送一股 IPv4 multicast UDP 資料流 (模擬影音串流這類群播資料)。
重點在正確的 L2 多播 MAC 映射:
  IPv4 群播位址 239.1.2.3 -> MAC 01:00:5e:01:02:03
  (規則: 01:00:5e + IP 後 23 bits)

執行: python3 10_multicast_ipv4.py
"""
import proto_common
from proto_common import Ether, IP, UDP, Raw
from trex.stl.api import (
    STLClient, STLStream, STLPktBuilder, STLTXCont, STLError
)
import trex_path

TX_PORT = 0
RX_PORT = 1
MCAST_IP = "239.1.2.3"       # 管理性 scope 的 IPv4 群播位址


def ipv4_mcast_mac(ip):
    """IPv4 群播位址 -> L2 多播 MAC (01:00:5e + IP 後 23 bits)。"""
    octets = [int(x) for x in ip.split(".")]
    return "01:00:5e:%02x:%02x:%02x" % (octets[1] & 0x7f, octets[2], octets[3])


def build_stream():
    dmac = ipv4_mcast_mac(MCAST_IP)
    pkt = (
        Ether(src="6a:1b:f2:ca:02:87", dst=dmac) /
        IP(src="10.0.0.1", dst=MCAST_IP, ttl=32) /   # 群播 TTL 常設小值
        UDP(sport=5004, dport=5004) /                # 5004 = RTP 典型 port
        Raw(load=b"MCAST-STREAM-" + b"D" * 60)
    )
    print("[*] IPv4 multicast: dst_ip=%s -> dst_mac=%s" % (MCAST_IP, dmac))
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
