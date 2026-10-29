#!/usr/bin/env python3
"""
範例 14: CFM (Connectivity Fault Management, IEEE 802.1ag / ITU Y.1731)
--------------------------------------------------
CFM 用於乙太網路 OAM (連線故障管理)。EtherType = 0x8902。
本範例手刻三種 CFM PDU 並送出/擷取解析:
  - CCM (Continuity Check Message, opcode=1) : 週期性連線檢查 (心跳)
  - LBM (Loopback Message,        opcode=3) : 類似 L2 ping
  - LTM (Linktrace Message,       opcode=5) : 類似 L2 traceroute

說明: TRex 內建 scapy 2.4.3 沒有 CFM contrib 模組, 因此手刻 bytes
(跟 LLDP 範例同樣手法, 對任何冷門/自訂協定都適用)。

CFM Common Header (4 bytes):
  byte0: MD Level (bit7-5) | Version (bit4-0)
  byte1: OpCode
  byte2: Flags
  byte3: First TLV Offset

執行: python3 14_cfm.py
"""
import struct
import proto_common
from proto_common import Ether

CFM_ETHERTYPE = 0x8902
SRC_MAC = "6a:1b:f2:ca:02:87"
# CFM 群播位址: 01:80:c2:00:00:3x, x = MD level (這裡 level 0)
CFM_MCAST = "01:80:c2:00:00:30"

OP_CCM = 1
OP_LBM = 3
OP_LTM = 5

END_TLV = b"\x00"   # End TLV (type 0)


def cfm_header(md_level, opcode, flags, tlv_offset):
    b0 = ((md_level & 0x7) << 5) | (0 & 0x1f)   # version = 0
    return struct.pack("!BBBB", b0, opcode, flags, tlv_offset)


def mac_bytes(mac):
    return bytes(int(x, 16) for x in mac.split(":"))


def build_ccm():
    """CCM: 心跳。flags 低3位 = CCM interval (4 = 1s)。TLV offset = 70。"""
    hdr = cfm_header(md_level=0, opcode=OP_CCM, flags=0x04, tlv_offset=70)
    seq = struct.pack("!I", 0x00000001)          # Sequence Number
    mepid = struct.pack("!H", 100)               # MEP ID
    # Maintenance Association ID (MAID), 固定 48 bytes (這裡簡化填 0)
    maid = b"\x00" * 48
    reserved = b"\x00" * 16                      # 補到 TLV offset
    body = seq + mepid + maid + reserved
    return hdr + body + END_TLV


def build_lbm():
    """LBM: L2 ping。TLV offset = 4, 帶一個 Transaction ID。"""
    hdr = cfm_header(md_level=0, opcode=OP_LBM, flags=0x00, tlv_offset=4)
    transaction_id = struct.pack("!I", 0x12345678)
    # Data TLV (type=3): 塞一些 payload
    data = b"CFM-LBM-PING"
    data_tlv = struct.pack("!BH", 3, len(data)) + data
    return hdr + transaction_id + data_tlv + END_TLV


def build_ltm():
    """LTM: L2 traceroute。TLV offset = 17。"""
    hdr = cfm_header(md_level=0, opcode=OP_LTM, flags=0x80, tlv_offset=17)
    transaction_id = struct.pack("!I", 0x0000ABCD)
    ttl = struct.pack("!B", 64)                  # LTM TTL
    orig_mac = mac_bytes(SRC_MAC)                # Original MAC Address
    target_mac = mac_bytes("12:5a:19:59:cc:ad")  # Target MAC Address
    body = transaction_id + ttl + orig_mac + target_mac
    return hdr + body + END_TLV


def eth(dst):
    return Ether(src=SRC_MAC, dst=dst, type=CFM_ETHERTYPE)


def parse_cfm(raw):
    """手動解析 CFM common header 給人看。"""
    payload = raw[14:]   # 跳過 Ethernet header
    if len(payload) < 4:
        return "  (太短, 非 CFM)"
    b0, opcode, flags, tlv_off = struct.unpack("!BBBB", payload[:4])
    md_level = b0 >> 5
    version = b0 & 0x1f
    opnames = {1: "CCM", 2: "LBR", 3: "LBM", 4: "LTR", 5: "LTM"}
    return ("  MD_Level=%d Version=%d OpCode=%d(%s) Flags=0x%02x TLVOffset=%d"
            % (md_level, version, opcode, opnames.get(opcode, "?"),
               flags, tlv_off))


if __name__ == "__main__":
    pkts = [
        eth(CFM_MCAST) / build_ccm(),
        eth("12:5a:19:59:cc:ad") / build_lbm(),
        eth(CFM_MCAST) / build_ltm(),
    ]
    caps = proto_common.send_and_capture(
        pkts, title="CFM CCM/LBM/LTM", show_detail=False)

    print("\n--- 手動解析收到的 CFM PDU ---")
    for i, rec in enumerate(caps):
        raw = bytes(rec["binary"])
        # 只解析 EtherType 0x8902 的
        if len(raw) >= 14 and raw[12:14] == struct.pack("!H", CFM_ETHERTYPE):
            print("[%d] CFM:" % i)
            print(parse_cfm(raw))
