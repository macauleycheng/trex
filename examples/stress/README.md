# 壓力測試 / 高速率流量範例

以 TRex stateless 的連續流量（`STLTXCont`）+ Field Engine（封包欄位逐包
變化）產生高速率壓力流量，用來測設備的表容量、轉發效能與防護機制。

> 前置：先啟動 TRex server（見上層 `../README.md`）。這些範例會 import
> 上層的 `trex_path.py`，所以直接在本目錄執行即可。

## 範例清單

| 檔案 | 模擬情境 | 逐包變化的欄位 |
|------|----------|----------------|
| `arp_flood.py` | ARP 洪水（測 MAC table 容量/老化） | sender MAC + sender IP 遞增 |
| `dhcp_starvation.py` | DHCP 位址池耗盡 | client MAC(chaddr) + xid 遞增 |
| `multicast_stress.py` | 大量群播群組（測 IGMP snooping 表） | 群組 IP + L2 多播 MAC 同步遞增 |
| `syn_flood.py` | TCP SYN flood | 來源 IP + 來源 port 遞增 |
| `mixed_line_rate.py` | 混合封包大小/協定打線速 | 多 stream（64B+1500B UDP + ARP） |

## 用法

所有範例都用環境變數調參數，預設跑短時間（避免佔滿）：

```bash
cd examples/stress

# 預設
python3 arp_flood.py

# 調速率與時間
PPS=500000 DURATION=10 python3 arp_flood.py

# DHCP starvation 模擬 2 萬 client
NUM_CLIENT=20000 PPS=100000 python3 dhcp_starvation.py

# multicast 壓力: 4096 群組, 1500B 大封包
NUM_GROUPS=4096 PKT_SIZE=1500 python3 multicast_stress.py

# SYN flood 打特定目標
DST_IP=10.1.1.1 DST_PORT=443 PPS=500000 python3 syn_flood.py

# 混合流量打 100% 線速
PERCENT=100 DURATION=10 python3 mixed_line_rate.py
```

共用參數：
- `PPS` — 送出速率（封包/秒），pps-based 範例用
- `PERCENT` — 線速百分比，percentage-based 範例用（mixed_line_rate）
- `DURATION` — 持續秒數

執行時會每秒印即時 TX/RX 速率，結束印總結（送出/收到/drop）。

## 注意事項

1. **軟體模式速率有限**：veth + af_packet 大約到十幾萬～數十萬 pps。真正
   要打線速（10G/40G/100G）需要實體網卡 + DPDK 模式。這些範例的邏輯完全
   相同，換成 DPDK port 即可衝到線速。

2. **percentage + duration 的陷阱**：多條 stream 各用低 `percentage` 時，
   TRex 的 `start(duration=N)` 會把時間按線速比例放大（實測 3s 變 65s）。
   因此 `stress_common.run_stress()` 不依賴 start 的 duration，改成自己
   計時、到點主動 `stop()`，對任何速率模式都可靠。

3. **這些是測試流量產生器**：ARP flood / DHCP starvation / SYN flood 在
   真實網路上屬攻擊行為，只可在你自己的測試環境 / 封閉 lab 對自己的 DUT
   使用。
