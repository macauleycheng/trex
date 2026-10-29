#!/usr/bin/env python3
"""
範例 00: 連線測試
連到本機 TRex server, 取得版本/port 資訊, 確認環境正常。
執行: python3 00_connect_test.py
"""
import trex_path
from trex.stl.api import STLClient, STLError


def main():
    c = STLClient(server=trex_path.TREX_SERVER)
    try:
        c.connect()
        print("[OK] 已連線到 TRex server:", trex_path.TREX_SERVER)

        ver = c.get_server_version()
        print("  版本        :", ver.get("version"))
        print("  build       :", ver.get("build_date"), ver.get("build_time"))
        print("  mode        :", ver.get("mode"))

        ports = c.get_all_ports()
        print("  可用 ports  :", ports)

        # 取得並顯示每個 port 的屬性
        info = c.get_port_info(ports)
        for p in info:
            print("  port %s: driver=%s src_mac=%s dst_mac=%s link=%s"
                  % (p["index"], p.get("driver"), p.get("src_mac"),
                     p.get("dest"), p.get("link")))

    except STLError as e:
        print("[ERROR]", e)
    finally:
        c.disconnect()
        print("[OK] 已斷線")


if __name__ == "__main__":
    main()
