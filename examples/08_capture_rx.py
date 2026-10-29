#!/usr/bin/env python3
"""
範例 08: 收封包 (RX Capture) - 實際抓到封包內容並解析
--------------------------------------------------
示範 TRex 的「收」能力: 在 RX port 開啟 capture, 從 TX port 送幾個
封包, 然後把收到的封包抓回 client 端用 Scapy 解析印出。

這是驗證「對端到底收到什麼」最實用的方式 -- 真實系統互通時,
可用同樣手法把對方 (或你的 DUT) 回送的封包抓回來檢查。

重點 API:
  start_capture / stop_capture - 擷取進入某 port 的封包
  push_packets                 - 從 client 直接注入封包 (不需預設 stream)

執行: python3 08_capture_rx.py
"""
import trex_path
from trex.stl.api import STLClient, STLError
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, ICMP
from scapy.packet import Raw

TX_PORT = 0
RX_PORT = 1


def main():
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        c.reset(ports=[TX_PORT, RX_PORT])

        # 在 RX port 開啟 capture (service mode 需先開)
        c.set_service_mode(ports=[RX_PORT], enabled=True)
        cap = c.start_capture(rx_ports=[RX_PORT], limit=100)
        print("[*] 已在 port %d 開啟 capture" % RX_PORT)

        # 直接從 port 0 注入 3 個 ICMP echo 封包
        pkts = []
        for i in range(3):
            p = (Ether(src="1e:b7:94:71:36:c6", dst="12:5a:19:59:cc:ad") /
                 IP(src="10.0.0.%d" % (i + 1), dst="10.0.0.254") /
                 ICMP(type=8, seq=i) /
                 Raw(load=b"PING-%d" % i))
            pkts.append(bytes(p))
        c.push_packets(pkts, ports=[TX_PORT], force=True)
        print("[*] 從 port %d 注入 %d 個 ICMP 封包" % (TX_PORT, len(pkts)))

        import time
        time.sleep(1)

        # 把擷取到的封包抓回來
        captured = []
        c.stop_capture(cap["id"], output=captured)
        c.set_service_mode(ports=[RX_PORT], enabled=False)

        print("[結果] port %d 共擷取到 %d 個封包:" % (RX_PORT, len(captured)))
        for i, rec in enumerate(captured):
            pkt = Ether(rec["binary"])
            summary = pkt.summary()
            print("  [%d] %s" % (i, summary))

    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()
