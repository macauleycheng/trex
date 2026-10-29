#!/usr/bin/env python3
"""
範例 04: STP (Spanning Tree Protocol) BPDU 模擬
--------------------------------------------------
組一個 STP Configuration BPDU (橋接協定資料單元), 送出並擷取解析。
STP 用 802.3 (Dot3) + LLC 封裝, 送到群播 01:80:c2:00:00:00。

注意: scapy 類別一律從 proto_common 取得 (使用 TRex 內建 scapy)。

執行: python3 04_stp.py
"""
import proto_common
from proto_common import Dot3, LLC, STP


def build_stp():
    # STP 走 802.3 (Dot3), dst 為 STP 多播位址
    eth = Dot3(
        src="1e:b7:94:71:36:c6",
        dst="01:80:c2:00:00:00",
    )
    llc = LLC(dsap=0x42, ssap=0x42, ctrl=0x03)   # STP 的 LLC 標準值
    stp = STP(
        proto=0,
        version=0,                 # 0 = 傳統 STP
        bpdutype=0,                # Configuration BPDU
        bpduflags=0,
        rootid=32768,
        rootmac="1e:b7:94:71:36:c6",
        pathcost=0,
        bridgeid=32768,
        bridgemac="1e:b7:94:71:36:c6",
        portid=0x8001,
        age=0, maxage=20, hellotime=2, fwddelay=15,
    )
    return eth / llc / stp


if __name__ == "__main__":
    pkt = build_stp()
    proto_common.send_and_capture([pkt], title="STP Configuration BPDU")
