"""
壓力測試共用工具。

把 stream 以指定速率/時間送出, 期間印出即時 tx/rx 速率, 結束後印總結。
所有壓力範例共用 run_stress()。

注意: scapy 類別請從本模組 (或各範例自行 import trex_path 後) 取得, 一律
使用 TRex 內建 scapy, 避免與系統 scapy 版本衝突。
"""
import os
import sys
import time

# 讓 stress/ 下的範例能 import 上層的 trex_path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import trex_path                                      # noqa: E402,F401
from trex.stl.api import STLClient, STLError          # noqa: E402

TX_PORT = 0
RX_PORT = 1


def run_stress(streams, title="", duration=5, tx_port=TX_PORT,
               rx_port=RX_PORT, poll=1.0):
    """送出 stream(s) 做壓力測試, 期間印即時速率。

    streams  : 單一 STLStream 或 list
    duration : 送出秒數
    poll     : 每隔幾秒印一次即時統計
    """
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        c.reset(ports=[tx_port, rx_port])
        c.add_streams(streams, ports=[tx_port])

        print("=" * 60)
        print("壓力測試: %s" % title)
        print("  送出 port=%d, 收 port=%d, 持續=%ds" % (tx_port, rx_port, duration))
        print("=" * 60)

        c.clear_stats()
        # 註: 不依賴 start(duration=...) -- 在多條 stream 用 percentage 速率時,
        #     TRex 的 duration 會被按線速比例放大 (例如 3s 變 65s)。改成自己
        #     計時, 時間到主動 stop, 對任何速率模式都可靠。
        c.start(ports=[tx_port])

        # 即時統計, 到時間就主動停
        t0 = time.time()
        while time.time() - t0 < duration and c.is_traffic_active(ports=[tx_port]):
            time.sleep(poll)
            s = c.get_stats()
            tx_pps = s[tx_port]["tx_pps"]
            tx_bps = s[tx_port]["tx_bps"]
            rx_pps = s[rx_port]["rx_pps"]
            print("  t=%4.1fs | TX %10.0f pps / %7.1f Mbps | RX %10.0f pps"
                  % (time.time() - t0, tx_pps, tx_bps / 1e6, rx_pps))

        c.stop(ports=[tx_port])
        c.wait_on_traffic(ports=[tx_port])

        s = c.get_stats()
        print("-" * 60)
        print("總結:")
        print("  TX 封包總數 : %d" % s[tx_port]["opackets"])
        print("  RX 封包總數 : %d" % s[rx_port]["ipackets"])
        print("  TX 位元組   : %d" % s[tx_port]["obytes"])
        drop = s[tx_port]["opackets"] - s[rx_port]["ipackets"]
        print("  收送差 (drop/背景) : %d" % drop)
        return s

    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()
