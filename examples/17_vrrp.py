#!/usr/bin/env python3
"""
範例 17: VRRP (Virtual Router Redundancy Protocol) Advertisement
--------------------------------------------------
VRRP 讓多台 router 共用一個虛擬 IP 做閘道冗餘。master 週期送
advertisement 宣告自己還活著。
  - 直接跑在 IP 上 (protocol number 112)
  - 送到群播 224.0.0.18, L2 MAC 01:00:5e:00:00:12
  - 虛擬 MAC 慣例: 00:00:5e:00:01:<VRID>

本範例組 VRRPv2 與 VRRPv3 advertisement 各一。

執行: python3 17_vrrp.py
"""
import proto_common
from proto_common import Ether, IP, IPv6, VRRP, VRRPv3

VRID = 10
PRIORITY = 100
VIRTUAL_IP = "10.0.0.254"         # 虛擬閘道 IP
VRRP_MCAST_MAC = "01:00:5e:00:00:12"   # 對應 224.0.0.18
# VRRP 慣例來源 MAC = 虛擬 MAC
VRRP_VMAC = "00:00:5e:00:01:%02x" % VRID


def vrrpv2_adv():
    return (
        Ether(src=VRRP_VMAC, dst=VRRP_MCAST_MAC) /
        IP(src="10.0.0.1", dst="224.0.0.18", ttl=255, proto=112) /
        VRRP(version=2, type=1, vrid=VRID, priority=PRIORITY,
             ipcount=1, authtype=0, adv=1, addrlist=[VIRTUAL_IP])
    )


def vrrpv3_adv():
    return (
        Ether(src=VRRP_VMAC, dst=VRRP_MCAST_MAC) /
        IP(src="10.0.0.1", dst="224.0.0.18", ttl=255, proto=112) /
        VRRPv3(version=3, type=1, vrid=VRID, priority=PRIORITY,
               ipcount=1, adv=100, addrlist=[VIRTUAL_IP])
    )


if __name__ == "__main__":
    pkts = [vrrpv2_adv(), vrrpv3_adv()]
    proto_common.send_and_capture(
        pkts, title="VRRP v2/v3 Advertisement", show_detail=True)
