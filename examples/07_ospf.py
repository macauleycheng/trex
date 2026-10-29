#!/usr/bin/env python3
"""
範例 07: OSPF (Open Shortest Path First) 模擬
--------------------------------------------------
OSPF 直接跑在 IP 上 (protocol number 89), Hello 封包送到群播 224.0.0.5
(AllSPFRouters)。本範例組一個 OSPF Hello 封包並送出/擷取解析。

OSPF Hello 用來發現鄰居、建立 adjacency; 內含 network mask、hello/dead
interval、router priority、鄰居清單等。

執行: python3 07_ospf.py
"""
import proto_common
from proto_common import Ether, IP, OSPF_Hdr, OSPF_Hello

ROUTER_ID = "10.0.0.1"
SRC_MAC = "1e:b7:94:71:36:c6"


def build_ospf_hello():
    eth = Ether(
        src=SRC_MAC,
        dst="01:00:5e:00:00:05",      # 224.0.0.5 對應的多播 MAC
    )
    ip = IP(
        src="10.0.0.1",
        dst="224.0.0.5",              # AllSPFRouters
        proto=89,                     # OSPF
        ttl=1,
    )
    ospf = OSPF_Hdr(
        version=2,
        src=ROUTER_ID,                # router id
        area="0.0.0.0",               # backbone area
    ) / OSPF_Hello(
        mask="255.255.255.0",
        hellointerval=10,
        prio=1,
        deadinterval=40,
        router="10.0.0.1",            # designated router
        backup="0.0.0.0",
        neighbors=[],                 # 尚無已知鄰居
    )
    return eth / ip / ospf


if __name__ == "__main__":
    pkt = build_ospf_hello()
    proto_common.send_and_capture([pkt], title="OSPF Hello",
                                  show_detail=True)
