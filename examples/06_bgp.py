#!/usr/bin/env python3
"""
範例 06: BGP (Border Gateway Protocol) 模擬
--------------------------------------------------
BGP 跑在 TCP/179 上。完整 BGP session 需要 TCP 三次握手 + OPEN/KEEPALIVE/
UPDATE 等訊息交換。本範例示範「組出 BGP 控制封包並送出」的能力:
  1. BGP OPEN     - 建立 session 時交換 AS/hold-time/router-id
  2. BGP UPDATE   - 宣告一條路由 (NLRI)
  3. BGP KEEPALIVE

說明: 這裡用 push_packets 直接送出封裝好的 BGP 訊息封包 (不做真正的
TCP 狀態機)。若要對真實 BGP peer 做完整 session, 建議用 TRex 的 ASTF
模式或搭配 scapy 的 TCP 自動應答; 這裡聚焦在 "封包長相" 與送收驗證。

執行: python3 06_bgp.py
"""
import proto_common
from proto_common import Ether, IP, TCP, BGPHeader, BGPOpen

SRC_IP = "10.0.0.1"
DST_IP = "10.0.0.2"
SRC_MAC = "1e:b7:94:71:36:c6"
DST_MAC = "12:5a:19:59:cc:ad"


def eth_ip_tcp(flags="PA", seq=1000, ack=1):
    return (
        Ether(src=SRC_MAC, dst=DST_MAC) /
        IP(src=SRC_IP, dst=DST_IP) /
        TCP(sport=50000, dport=179, flags=flags, seq=seq, ack=ack)
    )


def build_bgp_open():
    # BGP OPEN: AS 65001, hold 180s, router-id 10.0.0.1
    bgp = BGPHeader(type=1) / BGPOpen(
        version=4,
        my_as=65001,
        hold_time=180,
        bgp_id=SRC_IP,
    )
    return eth_ip_tcp(seq=1000) / bgp


def build_bgp_keepalive():
    # BGP KEEPALIVE: 只有 header, type=4
    bgp = BGPHeader(type=4, len=19)
    return eth_ip_tcp(seq=1100) / bgp


if __name__ == "__main__":
    pkts = [
        build_bgp_open(),
        build_bgp_keepalive(),
    ]
    proto_common.send_and_capture(pkts, title="BGP OPEN + KEEPALIVE",
                                  show_detail=True)
