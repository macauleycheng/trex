#!/usr/bin/env python3
"""
範例 02: 送 L3 IP/UDP 封包 + 速率控制 + VM 欄位變化
--------------------------------------------------
示範:
  1. 組 Ether/IP/UDP 封包
  2. 用 Field Engine (STLVM) 讓來源 IP 每個封包遞增 (模擬多來源流量)
  3. 用 STLTXSingleBurst 送固定數量, 以及 percentage 速率控制

重點 API:
  STLVmFlowVar / STLVmWrFlowVar / STLVmFixIpv4 - 封包欄位動態變化
  STLTXSingleBurst - 送固定數量封包

執行: python3 02_l3_ip.py
"""
import trex_path
from trex.stl.api import (
    STLClient, STLStream, STLPktBuilder, STLTXSingleBurst,
    STLVmFlowVar, STLVmWrFlowVar, STLVmFixIpv4, STLScVmRaw, STLError
)
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw

TX_PORT = 0
RX_PORT = 1
BURST = 5000


def build_stream():
    base = (
        Ether(src="1e:b7:94:71:36:c6", dst="12:5a:19:59:cc:ad") /
        IP(src="16.0.0.1", dst="48.0.0.1") /
        UDP(sport=1025, dport=53) /
        Raw(load=b"L3-TREX-" + b"Y" * 40)
    )

    # Field Engine: 讓 src IP 在 16.0.0.1 ~ 16.0.0.254 之間遞增
    vm = STLScVmRaw([
        STLVmFlowVar(name="src", min_value="16.0.0.1",
                     max_value="16.0.0.254", size=4, op="inc"),
        STLVmWrFlowVar(fv_name="src", pkt_offset="IP.src"),
        STLVmFixIpv4(offset="IP"),   # 重算 IP checksum
    ])

    return STLStream(
        packet=STLPktBuilder(pkt=base, vm=vm),
        mode=STLTXSingleBurst(total_pkts=BURST, percentage=30),  # 用 30% 線速
    )


def main():
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        c.reset(ports=[TX_PORT, RX_PORT])
        c.add_streams(build_stream(), ports=[TX_PORT])

        print("[*] 送 %d 個 IP/UDP 封包 (src IP 遞增), 30%% 線速..." % BURST)
        c.clear_stats()
        c.start(ports=[TX_PORT], duration=-1)   # burst 模式送完自動停
        c.wait_on_traffic(ports=[TX_PORT])

        stats = c.get_stats()
        print("[結果] port %d 送出 = %d" % (TX_PORT, stats[TX_PORT]["opackets"]))
        print("[結果] port %d 收到 = %d" % (RX_PORT, stats[RX_PORT]["ipackets"]))
        print("[結果] 平均 tx 速率 = %.2f Mbps"
              % (stats[TX_PORT]["tx_bps"] / 1e6))

    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()
