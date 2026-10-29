#!/usr/bin/env python3
"""
範例 05: LACP (Link Aggregation Control Protocol) 模擬
--------------------------------------------------
組一個 LACPDU (slow protocol), 送出並擷取解析。
LACP 是 IEEE 802.3ad slow protocol, EtherType 0x8809,
送到群播 01:80:c2:00:00:02。

注意: scapy 類別一律從 proto_common 取得 (使用 TRex 內建 scapy)。

執行: python3 05_lacp.py
"""
import proto_common
from proto_common import Ether, SlowProtocol, LACP


def build_lacp():
    eth = Ether(
        src="1e:b7:94:71:36:c6",
        dst="01:80:c2:00:00:02",   # Slow protocol 多播位址
        type=0x8809,               # Slow Protocol EtherType
    )
    slow = SlowProtocol(subtype=0x01)   # 0x01 = LACP
    lacp = LACP(
        version=1,
        actor_system="1e:b7:94:71:36:c6",
        actor_system_priority=32768,
        actor_key=1,
        actor_port_priority=32768,
        actor_port_numer=1,         # 註: 本版 scapy 欄位名為 numer (原碼 typo)
        actor_state=0x3d,           # active/aggregation/sync/collecting/distributing
        partner_system="12:5a:19:59:cc:ad",
        partner_system_priority=32768,
        partner_key=1,
        partner_port_priority=32768,
        partner_port_numer=1,       # 註: 本版 scapy 欄位名為 numer (原碼 typo)
        partner_state=0x3d,
    )
    return eth / slow / lacp


if __name__ == "__main__":
    pkt = build_lacp()
    proto_common.send_and_capture([pkt], title="LACPDU")
