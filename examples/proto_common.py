"""
協定範例共用工具。

重要: 本模組「先」載入 TRex STL client, 這會把 TRex 內建的 scapy 2.4.3
鎖進 sys.modules。之後所有 scapy import 都會用這一份, 避免與系統 scapy
2.8.0 混用造成 `cannot import name 'orb'` 之類的版本衝突。

因此各協定範例請「只」從本模組取得 scapy 類別 (例如 from proto_common
import Ether, LLDPDUChassisID ...), 不要自己直接 import scapy。

功能: send_and_capture() 送出一組自組封包, 並在 RX port 擷取回來解析。
"""
import time
import trex_path                      # noqa: F401  (加入 sys.path)
from trex.stl.api import STLClient    # 先載入 -> 鎖定 TRex 內建 scapy

# --- 以下 scapy import 必定使用 TRex 內建 2.4.3 ---
from scapy.layers.l2 import Ether, Dot3, LLC, STP, Dot1Q          # noqa: E402
from scapy.layers.inet import IP, UDP, TCP, ICMP                  # noqa: E402
from scapy.packet import Raw                                      # noqa: E402
from scapy.contrib.lldp import (                                  # noqa: E402
    LLDPDUChassisID, LLDPDUPortID, LLDPDUTimeToLive,
    LLDPDUSystemName, LLDPDUEndOfLLDPDU,
)
from scapy.contrib.lacp import SlowProtocol, LACP                 # noqa: E402
from scapy.contrib.ospf import OSPF_Hdr, OSPF_Hello               # noqa: E402
from scapy.contrib.bgp import BGPHeader, BGPOpen                  # noqa: E402
from scapy.contrib.igmp import IGMP                               # noqa: E402
from scapy.contrib.igmpv3 import (                                # noqa: E402
    IGMPv3, IGMPv3mq, IGMPv3mr, IGMPv3gr,
)
from scapy.layers.inet6 import (                                  # noqa: E402
    IPv6, IPv6ExtHdrHopByHop, RouterAlert,
    ICMPv6MLQuery, ICMPv6MLReport, ICMPv6MLDone,
)
from scapy.layers.l2 import ARP                                  # noqa: E402
from scapy.layers.vrrp import VRRP, VRRPv3                       # noqa: E402
from scapy.layers.vxlan import VXLAN                             # noqa: E402
from scapy.layers.dhcp import DHCP, BOOTP                        # noqa: E402

TX_PORT = 0
RX_PORT = 1


def send_and_capture(scapy_pkts, title="", show_detail=True):
    """送出 scapy 封包清單, 從對端擷取回來並印出解析結果。

    scapy_pkts  : list of scapy packet
    title       : 這批封包的說明文字
    show_detail : 是否印出 scapy 完整欄位解析 (show2)
    """
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        c.reset(ports=[TX_PORT, RX_PORT])
        c.set_service_mode(ports=[RX_PORT], enabled=True)

        cap = c.start_capture(rx_ports=[RX_PORT], limit=100)

        raw = [bytes(p) for p in scapy_pkts]
        c.push_packets(raw, ports=[TX_PORT], force=True)
        print("[*] %s: 從 port %d 送出 %d 個封包"
              % (title, TX_PORT, len(raw)))

        time.sleep(1)

        captured = []
        c.stop_capture(cap["id"], output=captured)
        c.set_service_mode(ports=[RX_PORT], enabled=False)

        print("[結果] port %d 擷取到 %d 個封包:" % (RX_PORT, len(captured)))
        for i, rec in enumerate(captured):
            raw_bytes = bytes(rec["binary"])
            # 註: TRex 內建 scapy 2.4.3 的 LLDP 模組 dissect 有 bug, 自動解析
            #     某些封包會丟例外。這裡用 try/except 保護, 解析失敗就印 hex,
            #     不影響 "送/收" 本身已成功的事實。
            try:
                pkt = Ether(raw_bytes)
                print("  [%d] len=%d  %s"
                      % (i, len(raw_bytes), pkt.summary()))
                if show_detail:
                    pkt.show2()
            except Exception as e:
                print("  [%d] len=%d  (scapy 自動解析失敗: %s)"
                      % (i, len(raw_bytes), type(e).__name__))
                print("       hex: %s" % raw_bytes.hex())
        return captured
    finally:
        c.disconnect()
