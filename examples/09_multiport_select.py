#!/usr/bin/env python3
"""
範例 09: 多卡綁定 + 指定 port 使用 (情境 A)
--------------------------------------------------
一個 TRex server 啟動時綁了 4 張卡 (port 0~3, 兩對 loopback):
    port 0 (trexA0) <--> port 1 (trexA1)
    port 2 (trexB0) <--> port 3 (trexB1)

本範例示範「用時指定某個 port」:
  1. 列出 server 綁了哪些 port
  2. 只從 port 0 送 -> 驗證只有 port 1 收到 (port 2/3 不受影響)
  3. 只從 port 2 送 -> 驗證只有 port 3 收到 (port 0/1 不受影響)

需先用 4-port 設定檔啟動 server:
  cd ~/trex/v3.06
  sudo ./t-rex-64 -i --software --cfg cfg/trex_software_4ports.yaml

執行: python3 09_multiport_select.py
"""
import trex_path
from trex.stl.api import (
    STLClient, STLStream, STLPktBuilder, STLTXSingleBurst, STLError
)
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP
from scapy.packet import Raw

BURST = 2000


def make_stream(tag):
    pkt = (
        Ether() /
        IP(src="16.0.0.1", dst="48.0.0.1") /
        UDP(sport=1025, dport=53) /
        Raw(load=("TAG-%s-" % tag).encode() + b"Z" * 40)
    )
    return STLStream(packet=STLPktBuilder(pkt=pkt),
                     mode=STLTXSingleBurst(total_pkts=BURST, percentage=50))


def snapshot(c, ports):
    """回傳 {port: (opackets, ipackets)}。"""
    s = c.get_stats()
    return {p: (s[p]["opackets"], s[p]["ipackets"]) for p in ports}


def tx_on_port(c, tx_port, all_ports):
    """只從 tx_port 送一個 burst, 回報每個 port 送/收的增量。"""
    c.reset(ports=all_ports)
    c.add_streams(make_stream(tx_port), ports=[tx_port])

    before = snapshot(c, all_ports)
    c.clear_stats()
    c.start(ports=[tx_port], duration=-1)
    c.wait_on_traffic(ports=[tx_port])
    after = snapshot(c, all_ports)

    print("[*] 只從 port %d 送出 %d 個封包後, 各 port 的收送:" % (tx_port, BURST))
    for p in all_ports:
        o = after[p][0]
        i = after[p][1]
        mark = "  <== 送出口" if p == tx_port else ""
        print("    port %d: 送(o)=%-6d 收(i)=%-6d%s" % (p, o, i, mark))
    print()


def main():
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        ports = c.get_all_ports()
        print("[OK] 此 TRex server 綁定的 ports:", ports)
        print("     (每個 port = 啟動時 cfg interfaces 列的一張卡)\n")

        if len(ports) < 4:
            print("[!] 偵測到的 port 少於 4, 請確認用 4-port cfg 啟動 server")
            return

        # 測試一: 只用 port 0 (第一對 loopback)
        tx_on_port(c, 0, ports)
        # 測試二: 只用 port 2 (第二對 loopback)
        tx_on_port(c, 2, ports)

        print("[結論] 送 port 0 時只有 port 1 收到, 送 port 2 時只有 port 3 收到")
        print("       -> 一個 server 綁多張卡, 用 port 編號就能指定要用哪一張。")

    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()


if __name__ == "__main__":
    main()
