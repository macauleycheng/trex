#!/usr/bin/env python3
"""
壓力測試: 多 Stream 混合流量打線速
--------------------------------------------------
同時掛多條不同協定的 stream (ARP / IP-UDP 小封包 / IP-UDP 大封包), 以
百分比線速一起送出, 模擬真實混合流量 -- 用來測設備在混合封包大小/協定
下的整體轉發效能。

每條 stream 的來源 IP 都會遞增以產生多條 flow。

可調參數 (環境變數):
  PERCENT   目標線速百分比, 預設 80
  DURATION  持續秒數, 預設 5

執行: python3 mixed_line_rate.py
      PERCENT=100 DURATION=10 python3 mixed_line_rate.py
"""
import os
import stress_common
from stress_common import run_stress
import trex_path  # noqa: F401
from trex.stl.api import (
    STLStream, STLPktBuilder, STLTXCont,
    STLVmFlowVar, STLVmWrFlowVar, STLVmFixIpv4, STLScVmRaw,
)
from scapy.layers.l2 import Ether, ARP
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw

PERCENT = int(os.environ.get("PERCENT", 80))
DURATION = int(os.environ.get("DURATION", 5))

SMAC = "6a:1b:f2:ca:02:87"
DMAC = "06:94:be:ef:3b:4d"


def ip_flow_vm():
    return STLScVmRaw([
        STLVmFlowVar(name="sip", min_value="16.0.0.1",
                     max_value="16.0.255.254", size=4, op="inc"),
        STLVmWrFlowVar(fv_name="sip", pkt_offset="IP.src"),
        STLVmFixIpv4(offset="IP"),
    ])


def udp_stream(size, name_prefix, weight):
    pad = max(0, size - 42)
    pkt = (Ether(src=SMAC, dst=DMAC) /
           IP(src="16.0.0.1", dst="48.0.0.1") /
           UDP(sport=1025, dport=53) /
           Raw(load=b"X" * pad))
    # 用 percentage 分配該 stream 的線速佔比
    return STLStream(packet=STLPktBuilder(pkt=pkt, vm=ip_flow_vm()),
                     mode=STLTXCont(percentage=weight), name=name_prefix)


def arp_stream(weight):
    pkt = (Ether(src="00:00:00:00:00:01", dst="ff:ff:ff:ff:ff:ff") /
           ARP(op=1, hwsrc="00:00:00:00:00:01", psrc="16.0.0.1",
               pdst="192.168.0.254"))
    return STLStream(packet=STLPktBuilder(pkt=pkt),
                     mode=STLTXCont(percentage=weight), name="arp")


def build_streams():
    # 三條 stream 各分配一部分線速 (總和 = PERCENT)
    w = PERCENT / 3.0
    return [
        udp_stream(64, "udp_small", w),    # 小封包 (考驗 pps)
        udp_stream(1500, "udp_large", w),  # 大封包 (考驗 bps)
        arp_stream(w),                     # ARP 混入
    ]


if __name__ == "__main__":
    run_stress(build_streams(),
               title="Mixed Line-Rate (64B+1500B UDP + ARP, 共 %d%% 線速)"
                     % PERCENT,
               duration=DURATION)
