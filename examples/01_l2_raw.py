#!/usr/bin/env python3
"""
範例 01: 送 L2 Raw Ethernet Frame
--------------------------------------------------
示範最基本的能力: 自己用 Scapy 組一個 L2 frame, 從 port 0 送出,
並在 port 1 用計數器確認收到。

重點 API:
  STLPktBuilder  - 把 Scapy 封包包成 TRex packet
  STLStream      - 一條 stream (要送的封包 + 送法)
  STLTXCont      - 連續送出模式 (指定 pps)
  add_streams / start / stop / get_stats

執行: python3 01_l2_raw.py
"""
import trex_path
from trex.stl.api import (
    STLClient, STLStream, STLPktBuilder, STLTXCont, STLError
)
from scapy.layers.l2 import Ether
from scapy.packet import Raw

TX_PORT = 0
RX_PORT = 1


def build_stream():
    # 自組一個 L2 frame: 指定來源/目的 MAC + 自訂 payload
    pkt = Ether(
        src="1e:b7:94:71:36:c6",
        dst="12:5a:19:59:cc:ad",
        type=0x9000,          # 自訂 EtherType (loopback/測試用)
    ) / Raw(load=b"HELLO-TREX-L2-" + b"X" * 50)

    return STLStream(
        packet=STLPktBuilder(pkt=pkt),
        mode=STLTXCont(pps=1000),   # 以 1000 pps 連續送
    )


def main():
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        c.reset(ports=[TX_PORT, RX_PORT])     # 清空既有設定與統計

        c.add_streams(build_stream(), ports=[TX_PORT])
        print("[*] 以 1000 pps 從 port %d 送 L2 frame, 持續 3 秒..." % TX_PORT)

        c.clear_stats()
        c.start(ports=[TX_PORT], duration=3)
        c.wait_on_traffic(ports=[TX_PORT])    # 等送完

        stats = c.get_stats()
        tx = stats[TX_PORT]["opackets"]
        rx = stats[RX_PORT]["ipackets"]
        print("[結果] port %d 送出 = %d packets" % (TX_PORT, tx))
        print("[結果] port %d 收到 = %d packets" % (RX_PORT, rx))
        print("[結論] L2 loopback", "OK" if rx > 0 else "沒收到 (檢查設定)")

    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()
