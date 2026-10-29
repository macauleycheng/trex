#!/usr/bin/env python3
"""
範例 15: ICMP Echo Request / Reply (L2 ping)
--------------------------------------------------
組 ICMP echo request (ping) 與對應的 echo reply, 送出並擷取解析。
request: type=8, reply: type=0, 兩者共用相同的 id/seq 以配對。

執行: python3 15_icmp.py
"""
import proto_common
from proto_common import Ether, IP, ICMP, Raw

SRC_MAC = "6a:1b:f2:ca:02:87"
DST_MAC = "06:94:be:ef:3b:4d"
SRC_IP = "10.0.0.1"
DST_IP = "10.0.0.2"
ICMP_ID = 0x1234
PAYLOAD = b"abcdefghijklmnopqrstuvwabcdefghi"   # 典型 ping payload


def echo_request(seq):
    return (
        Ether(src=SRC_MAC, dst=DST_MAC) /
        IP(src=SRC_IP, dst=DST_IP) /
        ICMP(type=8, code=0, id=ICMP_ID, seq=seq) /
        Raw(load=PAYLOAD)
    )


def echo_reply(seq):
    # reply: src/dst 互換, type=0
    return (
        Ether(src=DST_MAC, dst=SRC_MAC) /
        IP(src=DST_IP, dst=SRC_IP) /
        ICMP(type=0, code=0, id=ICMP_ID, seq=seq) /
        Raw(load=PAYLOAD)
    )


if __name__ == "__main__":
    pkts = [
        echo_request(seq=1),
        echo_reply(seq=1),
        echo_request(seq=2),
        echo_reply(seq=2),
    ]
    proto_common.send_and_capture(
        pkts, title="ICMP Echo Request/Reply", show_detail=True)
