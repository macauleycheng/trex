#!/usr/bin/env python3
"""
範例 03: LLDP (Link Layer Discovery Protocol) 模擬
--------------------------------------------------
組一個標準 LLDP announcement 封包 (鄰居探索), 送出並擷取回來解析。
LLDP 送到群播位址 01:80:c2:00:00:0e, EtherType 0x88cc。

說明: TRex 內建的 scapy 2.4.3 其 LLDP contrib 模組在本環境有 do_build
相容性 bug (無法 build)。LLDP 的 TLV 格式非常單純, 因此這裡「手刻」
TLV bytes -- 這也更貼近 "送 L2 raw packet" 的精神, 你對任何自訂或冷門
協定都能用同樣手法產生封包。

TLV 格式: 每個 TLV = 2 bytes header + value
  header (16 bits) = type(7 bits) << 9 | length(9 bits)

執行: python3 03_lldp.py
"""
import struct
import proto_common
from proto_common import Ether


def tlv(tlv_type, value: bytes) -> bytes:
    """組一個 LLDP TLV。tlv_type: 0~127, value: bytes。"""
    assert len(value) < 512
    header = (tlv_type << 9) | len(value)
    return struct.pack("!H", header) + value


def mac_to_bytes(mac: str) -> bytes:
    return bytes(int(x, 16) for x in mac.split(":"))


def build_lldp():
    src_mac = "1e:b7:94:71:36:c6"

    # --- 必要 TLV ---
    # Chassis ID (type=1): subtype 4 = MAC address
    chassis = tlv(1, bytes([4]) + mac_to_bytes(src_mac))
    # Port ID (type=2): subtype 5 = interface name
    port = tlv(2, bytes([5]) + b"Gi0/1")
    # Time To Live (type=3): 2 bytes TTL
    ttl = tlv(3, struct.pack("!H", 120))
    # --- 選用 TLV ---
    # System Name (type=5)
    sysname = tlv(5, b"TREX-SIM-SWITCH")
    # System Description (type=6)
    sysdesc = tlv(6, b"TRex LLDP example")
    # End of LLDPDU (type=0, length=0)
    end = tlv(0, b"")

    payload = chassis + port + ttl + sysname + sysdesc + end

    eth = Ether(
        src=src_mac,
        dst="01:80:c2:00:00:0e",   # LLDP 多播位址
        type=0x88cc,               # LLDP EtherType
    )
    return eth / payload


if __name__ == "__main__":
    pkt = build_lldp()
    # LLDP raw payload 用 scapy summary 只會顯示 Raw, 另外解析 TLV 給人看
    caps = proto_common.send_and_capture([pkt], title="LLDP announcement",
                                         show_detail=False)
    if caps:
        print("\n--- 手動解析收到的 LLDP TLV ---")
        data = bytes(caps[0]["binary"])[14:]   # 跳過 14 bytes Ethernet header
        names = {0: "End", 1: "ChassisID", 2: "PortID", 3: "TTL",
                 4: "PortDesc", 5: "SysName", 6: "SysDesc", 7: "SysCap"}
        i = 0
        while i < len(data) - 1:
            hdr = struct.unpack("!H", data[i:i + 2])[0]
            t = hdr >> 9
            length = hdr & 0x1FF
            val = data[i + 2:i + 2 + length]
            print("  TLV type=%-2d (%-9s) len=%-3d value=%r"
                  % (t, names.get(t, "?"), length, val))
            if t == 0:
                break
            i += 2 + length
