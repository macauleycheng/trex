#!/usr/bin/env python3
"""
壓力測試: TCP SYN Flood
--------------------------------------------------
以高速率送出 TCP SYN, 來源 IP 與來源 port 每個封包遞增, 模擬大量半開
連線 -- 經典的 SYN flood 壓測, 用來測防火牆/伺服器的 SYN 防護與連線表
容量。

可調參數 (環境變數):
  PPS       送出速率, 預設 300000
  DURATION  持續秒數, 預設 5
  DST_IP    被攻擊目標 IP, 預設 48.0.0.1
  DST_PORT  被攻擊目標 port, 預設 80

執行: python3 syn_flood.py
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
from scapy.layers.inet import IP, TCP

PPS = int(os.environ.get("PPS", 300000))
DURATION = int(os.environ.get("DURATION", 5))
DST_IP = os.environ.get("DST_IP", "48.0.0.1")
DST_PORT = int(os.environ.get("DST_PORT", 80))


def build_stream():
    base = (
        Ether(src="6a:1b:f2:ca:02:87", dst="06:94:be:ef:3b:4d") /
        IP(src="16.0.0.1", dst=DST_IP) /
        TCP(sport=1024, dport=DST_PORT, flags="S", seq=0)
    )

    vm = STLScVmRaw([
        # 來源 IP 遞增 (大量不同來源)
        STLVmFlowVar(name="sip", min_value="16.0.0.1",
                     max_value="16.0.255.254", size=4, op="inc"),
        STLVmWrFlowVar(fv_name="sip", pkt_offset="IP.src"),
        # 來源 port 遞增
        STLVmFlowVar(name="sport", min_value=1024, max_value=65535,
                     size=2, op="inc"),
        STLVmWrFlowVar(fv_name="sport", pkt_offset="TCP.sport"),
        STLVmFixIpv4(offset="IP"),
    ])

    return STLStream(packet=STLPktBuilder(pkt=base, vm=vm),
                     mode=STLTXCont(pps=PPS))


if __name__ == "__main__":
    run_stress(build_stream(),
               title="TCP SYN Flood (src IP/port 遞增 -> %s:%d)"
                     % (DST_IP, DST_PORT),
               duration=DURATION)
