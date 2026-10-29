#!/usr/bin/env python3
"""
壓力測試: Multicast 高速率壓力
--------------------------------------------------
以高速率送出 IPv4 multicast UDP 流, 群組位址 (dst IP) 與對應的 L2 多播
MAC 同步遞增, 模擬大量不同群播群組同時傳輸 -- 用來測交換器的群播轉發
表 (IGMP snooping table) 容量與轉發效能。

可調參數 (環境變數):
  PPS        送出速率, 預設 200000
  DURATION   持續秒數, 預設 5
  NUM_GROUPS 模擬多少個不同群組, 預設 1024
  PKT_SIZE   每個封包大小 (bytes), 預設 512

執行: python3 multicast_stress.py
"""
import os
import stress_common
from stress_common import run_stress
import trex_path  # noqa: F401
from trex.stl.api import (
    STLStream, STLPktBuilder, STLTXCont,
    STLVmFlowVar, STLVmWrFlowVar, STLVmFixIpv4, STLScVmRaw,
)
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw

PPS = int(os.environ.get("PPS", 200000))
DURATION = int(os.environ.get("DURATION", 5))
NUM_GROUPS = int(os.environ.get("NUM_GROUPS", 1024))
PKT_SIZE = int(os.environ.get("PKT_SIZE", 512))


def build_stream():
    # 基底群組 239.1.0.0, L2 MAC 01:00:5e:01:00:00
    pad = max(0, PKT_SIZE - 42)
    base = (
        Ether(src="6a:1b:f2:ca:02:87", dst="01:00:5e:01:00:00") /
        IP(src="10.0.0.1", dst="239.1.0.0", ttl=32) /
        UDP(sport=5004, dport=5004) /
        Raw(load=b"M" * pad)
    )

    # 群組 (IP 低 16 bits) 與 L2 MAC 低 16 bits 同步遞增
    vm = STLScVmRaw([
        STLVmFlowVar(name="grp", min_value=0, max_value=NUM_GROUPS - 1,
                     size=2, op="inc"),
        # 寫 IP dst 低 2 bytes (239.1.x.y 的 x.y)
        STLVmWrFlowVar(fv_name="grp", pkt_offset="IP.dst", offset_fixup=2),
        # 寫 L2 多播 MAC 低 2 bytes (01:00:5e:01:x:y 的 x:y -> Ether.dst offset 4)
        STLVmWrFlowVar(fv_name="grp", pkt_offset=4),
        STLVmFixIpv4(offset="IP"),
    ])

    return STLStream(packet=STLPktBuilder(pkt=base, vm=vm),
                     mode=STLTXCont(pps=PPS))


if __name__ == "__main__":
    run_stress(build_stream(),
               title="Multicast Stress (%d 群組, %dB, 群組位址遞增)"
                     % (NUM_GROUPS, PKT_SIZE),
               duration=DURATION)
