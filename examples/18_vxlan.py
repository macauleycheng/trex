#!/usr/bin/env python3
"""
範例 18: VXLAN (Virtual eXtensible LAN) 封裝
--------------------------------------------------
VXLAN 把 L2 frame 封裝在 UDP 裡 (overlay 網路), 用 24-bit VNI 區隔租戶。
封裝結構:
  Outer Ether / Outer IP / UDP(dport=4789) / VXLAN(vni) / Inner Ether / Inner IP ...

本範例組一個帶內層 ICMP 的 VXLAN 封包, 送出並擷取, 驗證內外層都能解析。

執行: python3 18_vxlan.py
"""
import proto_common
from proto_common import Ether, IP, UDP, ICMP, VXLAN, Raw

# 外層 (underlay / VTEP 之間)
OUTER_SMAC = "6a:1b:f2:ca:02:87"
OUTER_DMAC = "06:94:be:ef:3b:4d"
OUTER_SIP = "192.168.1.1"         # VTEP A
OUTER_DIP = "192.168.1.2"         # VTEP B
VNI = 5000                        # 租戶識別

# 內層 (overlay / 租戶的真實封包)
INNER_SMAC = "aa:bb:cc:00:00:01"
INNER_DMAC = "aa:bb:cc:00:00:02"
INNER_SIP = "172.16.0.1"
INNER_DIP = "172.16.0.2"


def build_vxlan():
    inner = (
        Ether(src=INNER_SMAC, dst=INNER_DMAC) /
        IP(src=INNER_SIP, dst=INNER_DIP) /
        ICMP(type=8, id=0x1, seq=1) /
        Raw(load=b"INNER-TENANT-PING")
    )
    outer = (
        Ether(src=OUTER_SMAC, dst=OUTER_DMAC) /
        IP(src=OUTER_SIP, dst=OUTER_DIP) /
        UDP(sport=50000, dport=4789) /       # 4789 = VXLAN 標準 port
        VXLAN(vni=VNI, flags=0x08)           # flags 0x08 = VNI valid
    )
    return outer / inner


if __name__ == "__main__":
    proto_common.send_and_capture(
        [build_vxlan()], title="VXLAN (inner ICMP, vni=%d)" % VNI,
        show_detail=True)
