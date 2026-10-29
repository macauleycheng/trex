#!/usr/bin/env python3
"""
壓力測試: DHCP Starvation 模擬
--------------------------------------------------
以高速率送出 DHCP Discover, 每個封包用不同的 client MAC (chaddr) 與
transaction id, 模擬大量 client 同時請求位址 -- 用來測 DHCP server 的
位址池耗盡行為 (DHCP starvation 攻擊的模擬)。

可調參數 (環境變數):
  PPS       送出速率, 預設 50000
  DURATION  持續秒數, 預設 5
  NUM_CLIENT 模擬多少個不同 client, 預設 8192

執行: python3 dhcp_starvation.py
"""
import os
import stress_common
from stress_common import run_stress
import trex_path  # noqa: F401
from trex.stl.api import (
    STLStream, STLPktBuilder, STLTXCont,
    STLVmFlowVar, STLVmWrFlowVar, STLScVmRaw,
)
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.layers.dhcp import BOOTP, DHCP

PPS = int(os.environ.get("PPS", 50000))
DURATION = int(os.environ.get("DURATION", 5))
NUM_CLIENT = int(os.environ.get("NUM_CLIENT", 8192))


def build_stream():
    base = (
        Ether(src="00:00:00:00:00:00", dst="ff:ff:ff:ff:ff:ff") /
        IP(src="0.0.0.0", dst="255.255.255.255") /
        UDP(sport=68, dport=67) /
        BOOTP(op=1, chaddr=b"\x00" * 16, xid=0, flags=0x8000) /
        DHCP(options=[("message-type", "discover"), "end"])
    )
    base = base.__class__(bytes(base))   # 固定 layout 以算 offset

    # Ether.src 在 offset 6; BOOTP.chaddr 用 scapy 欄位名定位
    vm = STLScVmRaw([
        STLVmFlowVar(name="cid", min_value=1, max_value=NUM_CLIENT,
                     size=4, op="inc"),
        STLVmWrFlowVar(fv_name="cid", pkt_offset=8),            # Ether.src 低 4B
        STLVmWrFlowVar(fv_name="cid", pkt_offset="BOOTP.chaddr", offset_fixup=2),
        # transaction id 也跟著變
        STLVmFlowVar(name="xid", min_value=1, max_value=0x7fffffff,
                     size=4, op="inc"),
        STLVmWrFlowVar(fv_name="xid", pkt_offset="BOOTP.xid"),
    ])

    return STLStream(packet=STLPktBuilder(pkt=base, vm=vm),
                     mode=STLTXCont(pps=PPS))


if __name__ == "__main__":
    run_stress(build_stream(),
               title="DHCP Starvation (chaddr/xid 遞增, 模擬 %d client)" % NUM_CLIENT,
               duration=DURATION)
