#!/usr/bin/env python3
"""
announce.py - ExaBGP API process: session 建立後宣告一批路由, 之後常駐。

ExaBGP 會以此腳本為子行程啟動, 本腳本把 "announce route ..." 指令寫到
stdout, ExaBGP 讀取後轉成真正的 BGP UPDATE 送給 peer (DUT)。

路由清單可用環境變數 BGP_ROUTES 覆寫 (逗號分隔的 prefix)。next-hop 用
BGP_NEXTHOP (預設 self = 用 speaker 的 local-address)。

重點 (ExaBGP API 規則):
  - 每條指令結尾一定要 "\n"
  - 每次 write 後一定要 flush(), 否則 ExaBGP 收不到
  - 本行程必須常駐 (持續存活), 結束等於停止這些路由的維護
"""
import os
import sys
import time


def send(cmd):
    sys.stdout.write(cmd + "\n")
    sys.stdout.flush()


def main():
    # 等 BGP session 進入 Established 再宣告 (給握手 + OPEN/KEEPALIVE 一點時間)
    time.sleep(float(os.environ.get("BGP_ANNOUNCE_DELAY", "3")))

    routes = os.environ.get(
        "BGP_ROUTES",
        "192.0.2.0/24,198.51.100.0/24,203.0.113.0/24",
    ).split(",")
    next_hop = os.environ.get("BGP_NEXTHOP", "self")

    for prefix in routes:
        prefix = prefix.strip()
        if not prefix:
            continue
        send("announce route %s next-hop %s" % (prefix, next_hop))
        sys.stderr.write("[announce] %s next-hop %s\n" % (prefix, next_hop))
        sys.stderr.flush()

    # 常駐: 保持路由被宣告的狀態。收到 SIGTERM (ExaBGP 關閉) 時一併結束。
    while True:
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        pass
