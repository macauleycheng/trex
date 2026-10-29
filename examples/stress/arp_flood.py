#!/usr/bin/env python3
"""
壓力測試: ARP Flood
--------------------------------------------------
以高速率送出 ARP request, 來源 MAC 與 sender IP 每個封包遞增, 模擬大量
不同主機同時 ARP -- 常用來測交換器 MAC address table 的容量/老化行為
(MAC table 耗盡攻擊的模擬)。

可調參數 (環境變數):
  PPS       送出速率 (封包/秒), 預設 100000
  DURATION  持續秒數, 預設 5
  NUM_HOSTS 模擬多少個不同來源, 預設 4096

執行: python3 arp_flood.py
      PPS=500000 DURATION=10 python3 arp_flood.py
"""
import os
import stress_common
from stress_common import run_stress
import trex_path  # noqa: F401  (鎖定 TRex scapy)
from trex.stl.api import (
    STLStream, STLPktBuilder, STLTXCont,
    STLVmFlowVar, STLVmWrFlowVar, STLScVmRaw,
)
from scapy.layers.l2 import Ether, ARP

PPS = int(os.environ.get("PPS", 100000))
DURATION = int(os.environ.get("DURATION", 5))
NUM_HOSTS = int(os.environ.get("NUM_HOSTS", 4096))
TARGET_IP = "192.168.0.254"       # 被 ARP 查詢的目標 (例如閘道)


def build_stream():
    base = (
        Ether(src="00:00:00:00:00:00", dst="ff:ff:ff:ff:ff:ff") /
        ARP(op=1, hwsrc="00:00:00:00:00:00",
            psrc="16.0.0.0", pdst=TARGET_IP)
    )

    # Field Engine: sender MAC 低 32 bits 與 sender IP 同步遞增
    vm = STLScVmRaw([
        # MAC 低 4 bytes (Ether.src 在 offset 6, 寫後 4 bytes -> offset 8)
        STLVmFlowVar(name="host", min_value=1, max_value=NUM_HOSTS,
                     size=4, op="inc"),
        STLVmWrFlowVar(fv_name="host", pkt_offset=8),        # Ether.src 低 4B
        STLVmWrFlowVar(fv_name="host", pkt_offset="ARP.hwsrc", offset_fixup=2),
        # sender IP 同步遞增
        STLVmFlowVar(name="sip", min_value="16.0.0.1",
                     max_value="16.0.255.254", size=4, op="inc"),
        STLVmWrFlowVar(fv_name="sip", pkt_offset="ARP.psrc"),
    ])

    return STLStream(packet=STLPktBuilder(pkt=base, vm=vm),
                     mode=STLTXCont(pps=PPS))


if __name__ == "__main__":
    run_stress(build_stream(),
               title="ARP Flood (sender MAC/IP 遞增, 模擬 %d 主機)" % NUM_HOSTS,
               duration=DURATION)
