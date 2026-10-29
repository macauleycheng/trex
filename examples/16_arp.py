#!/usr/bin/env python3
"""
範例 16: ARP Request / Reply
--------------------------------------------------
ARP 用於 IPv4 -> MAC 位址解析。
  Request (op=1): 廣播問「誰是 10.0.0.2? 告訴 10.0.0.1」
  Reply   (op=2): 單播回「10.0.0.2 在 <MAC>」

ARP request 的 L2 目的是廣播 ff:ff:ff:ff:ff:ff。

執行: python3 16_arp.py
"""
import proto_common
from proto_common import Ether, ARP

REQ_MAC = "6a:1b:f2:ca:02:87"     # 發問者 MAC
REQ_IP = "10.0.0.1"               # 發問者 IP
TGT_MAC = "06:94:be:ef:3b:4d"     # 被問者 MAC
TGT_IP = "10.0.0.2"               # 被問者 IP


def arp_request():
    # 廣播, hwdst 填 00:00:00:00:00:00 (未知)
    return (
        Ether(src=REQ_MAC, dst="ff:ff:ff:ff:ff:ff") /
        ARP(op=1,
            hwsrc=REQ_MAC, psrc=REQ_IP,
            hwdst="00:00:00:00:00:00", pdst=TGT_IP)
    )


def arp_reply():
    # 單播回給發問者
    return (
        Ether(src=TGT_MAC, dst=REQ_MAC) /
        ARP(op=2,
            hwsrc=TGT_MAC, psrc=TGT_IP,
            hwdst=REQ_MAC, pdst=REQ_IP)
    )


if __name__ == "__main__":
    pkts = [arp_request(), arp_reply()]
    proto_common.send_and_capture(
        pkts, title="ARP Request/Reply", show_detail=True)
