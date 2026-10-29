# Cisco TRex 封包收送範例 (Python)

這套範例用來學習 Cisco TRex 的封包收送能力，涵蓋 L2/L3 raw packet 與常見
協定模擬（LLDP / STP / LACP / OSPF / BGP）。全部在**軟體模式 + veth
loopback** 下驗證通過，不需要實體網卡、不碰你的管理網路。

## 環境

| 項目 | 內容 |
|------|------|
| TRex 版本 | v3.06（安裝於 `~/trex/v3.06`） |
| 執行模式 | 軟體模式（`--software`，af_packet driver） |
| 虛擬介面 | veth pair：`trex0`（port 0）↔ `trex1`（port 1） |
| port 0 MAC | `1e:b7:94:71:36:c6` |
| port 1 MAC | `12:5a:19:59:cc:ad` |
| server 位址 | `127.0.0.1`（RPC 4501 / async 4500） |

> **為什麼用軟體模式 + veth？**
> TRex 原本設計成「一個 port 送、另一個 port 收」。veth pair 等同一條虛擬
> 網線，把 port 0 送出的封包直接送到 port 1，反之亦然 —— 這就是不碰實體
> 網卡的 loopback。封包的收送邏輯與真實情境完全一致，只是走虛擬介面。
> 等要對真實設備打流量 / 測效能時，再把其中一個 port 換成實體網卡並綁
> DPDK 即可。

## 安裝 TRex

本 repo 只收範例程式，**不含 TRex 本體**（體積大、含近 100MB 的二進位，
不適合進版控）。請自行下載安裝，預設路徑 `~/trex/v3.06`（範例的
`trex_path.py` 以此為準，裝到別處請改該檔的 `TREX_ROOT`）。

```bash
mkdir -p ~/trex && cd ~/trex

# 下載 v3.06（可改成官網 release 目錄裡的其他版本）
curl -L -o v3.06.tar.gz https://trex-tgn.cisco.com/trex/release/v3.06.tar.gz

# 解壓
tar xzf v3.06.tar.gz          # 得到 ~/trex/v3.06
```

可用版本列在官網 release 目錄：<https://trex-tgn.cisco.com/trex/release/>
（檔名格式 `vX.XX.tar.gz`，例如 `v3.06.tar.gz`）。

### 若下載遇到憑證錯誤（SSL certificate problem）

某些環境下 cisco 下載站沒送完整中間憑證鏈，`curl` 會報
`unable to get local issuer certificate`。補上中間憑證即可：

```bash
cd ~/trex
# 下載簽發用的中間憑證 (HydrantID / IdenTrust) 並轉成 PEM
curl -s http://validation.identrust.com/certs/hydrantidcaO1.p7c -o hydrantid.p7c
openssl pkcs7 -inform DER -in hydrantid.p7c -print_certs -out hydrantid-chain.pem
# 組成完整 CA 鏈
cat hydrantid-chain.pem /etc/ssl/certs/ca-certificates.crt > trex-ca-bundle.pem
# 用完整鏈下載
curl --cacert ~/trex/trex-ca-bundle.pem -L \
     -o v3.06.tar.gz https://trex-tgn.cisco.com/trex/release/v3.06.tar.gz
```

### 相依套件

TRex 本體自帶 Python 直譯器與其相依（含內建 scapy），但系統仍需基本編譯/
pcap 套件；協定範例另需系統 scapy（僅在少數情況用到）：

```bash
sudo apt-get update
sudo apt-get install -y build-essential libpcap-dev python3-dev zlib1g-dev
sudo python3 -m pip install scapy
```

## 快速開始

```bash
cd ~/trex/examples

# 1. 建 veth + 啟動 TRex server（背景）
./trex_server.sh start-bg

# 2. 確認狀態
./trex_server.sh status

# 3. 跑連線測試
python3 00_connect_test.py

# 4. 跑任一範例
python3 01_l2_raw.py
```

停止 server：`./trex_server.sh stop`
刪除 veth：`./trex_server.sh teardown`

> veth 是暫時性的，機器重開機後要重新 `./trex_server.sh setup`（或
> `start-bg` 會自動建）。

## 範例清單

| 檔案 | 主題 | 示範能力 |
|------|------|----------|
| `00_connect_test.py` | 連線測試 | 連 server、取版本/port 資訊 |
| `01_l2_raw.py` | L2 raw frame | 自組 Ethernet frame、連續送（pps）、tx/rx 統計 |
| `02_l3_ip.py` | L3 IP/UDP | 組 IP/UDP、Field Engine 讓 src IP 遞增、速率控制（%）、burst |
| `03_lldp.py` | LLDP | 手刻 TLV bytes、送多播、擷取回來解析 TLV |
| `04_stp.py` | STP | 802.3/LLC/STP BPDU、scapy 完整解析 |
| `05_lacp.py` | LACP | IEEE 802.3ad slow protocol、actor/partner 狀態 |
| `06_bgp.py` | BGP | TCP/179 上的 OPEN + KEEPALIVE 訊息 |
| `07_ospf.py` | OSPF | IP proto 89、Hello 封包送多播 224.0.0.5 |
| `08_capture_rx.py` | RX capture | 注入封包、在 RX port 擷取並用 scapy 解析內容 |
| `09_multiport_select.py` | 多卡綁定 + 選 port | 一個 server 綁 4 張卡，用 port 編號指定要用哪一張 |
| `10_multicast_ipv4.py` | IPv4 multicast data | 群播 UDP 流 + 正確的 01:00:5e L2 MAC 映射 |
| `11_multicast_ipv6.py` | IPv6 multicast data | 群播 UDP 流 + 正確的 33:33 L2 MAC 映射 |
| `12_igmp.py` | IGMP v2/v3 | Query + Report（含 Router Alert option） |
| `13_mld.py` | MLD | Query / Report / Done（ICMPv6 + HBH Router Alert） |
| `14_cfm.py` | CFM (802.1ag) | CCM / LBM / LTM（手刻，EtherType 0x8902） |
| `15_icmp.py` | ICMP | Echo Request / Reply（L2 ping，id/seq 配對） |
| `16_arp.py` | ARP | Request（廣播）/ Reply（單播） |
| `17_vrrp.py` | VRRP v2/v3 | Advertisement（proto 112，群播 224.0.0.18） |
| `18_vxlan.py` | VXLAN | UDP/4789 封裝，內外層 Ether/IP 都可解析（vni） |
| `19_dhcp.py` | DHCP | DORA：Discover / Offer / Request / ACK |

輔助檔：
- `trex_path.py` — 把 TRex Python API 路徑加入 `sys.path`，設定 server 位址。
- `proto_common.py` — 協定範例共用的「送出 + 擷取 + 解析」工具。
- `trex_server.sh` — server/veth 管理腳本。

壓力測試 / 高速率流量範例在 **[`stress/`](stress/)** 子目錄（ARP flood、
DHCP starvation、multicast 壓力、SYN flood、混合線速），詳見
[`stress/README.md`](stress/README.md)。

## 兩種核心 API 用法

**(1) Stream 模式（適合效能測試 / 持續流量）**
`01`、`02` 用的方式：建 `STLStream`（封包 + 送法），`add_streams` →
`start` → `get_stats`。可指定 pps、百分比線速、burst 數量，並用 Field
Engine（`STLVM*`）讓每個封包的欄位動態變化。

**(2) push_packets 模式（適合送控制封包 / 一次性封包）**
`03`~`08` 用的方式：`push_packets()` 直接把自組的封包注入某個 port，搭配
`start_capture` / `stop_capture` 在對端擷取回來。適合 LLDP/STP/BGP 這類
keepalive / announcement，以及驗證「對端到底收到什麼」。

## 重要注意事項（踩過的坑）

1. **scapy 版本混用**：TRex client 內建自己的 scapy 2.4.3。協定範例一律
   從 `proto_common` 取 scapy 類別（它會先載入 client 鎖定 TRex 的 scapy），
   不要自己直接 `import scapy`，否則會與系統 scapy 2.8.0 衝突
   （`cannot import name 'orb'`）。

2. **LLDP 用手刻 TLV**：TRex 內建 scapy 2.4.3 的 LLDP 模組在本環境有
   `do_build` 相容性 bug，無法 build/dissect。LLDP TLV 格式單純，`03_lldp.py`
   改用手刻 bytes —— 這招對任何自訂 / 冷門協定都適用。

3. **LACP 欄位名 typo**：本版 scapy 的欄位是 `actor_port_numer` /
   `partner_port_numer`（原碼少了 b），不是 `number`。

5. **CFM 用手刻 bytes**：這版 scapy 沒有 `contrib.cfm` 模組，`14_cfm.py`
   依 IEEE 802.1ag 格式手刻 CCM/LBM/LTM。

6. **群播 / IGMP / MLD 的 L2 MAC 與 Router Alert**：
   - IPv4 群播 → `01:00:5e` + IP 後 23 bits；IPv6 群播 → `33:33` + 位址低
     32 bits。範例都內含映射函式。
   - IGMP 用 `igmpize()` 自動補 Router Alert option / TTL=1 / checksum，
     不要再手動加 `options=`（會重複）。
   - MLD 必須帶 IPv6 Hop-by-Hop + `RouterAlert(value=0)` 擴充標頭。
   - 擷取時可能看到 veth 介面自己發的 MLD/mDNS 背景封包（如 `ff02::fb`），
     那不是範例送的，屬正常。
   - 用 `push_packets` 送時，封包的 L2 目的 MAC 可能被 cfg `port_info` 的
     `dest_mac` 覆寫；協定 header 內容不受影響。真實接到 DUT 時再精確控制
     L2 目的位址即可。

4. **收封包解析要防呆**：`proto_common.send_and_capture()` 對自動解析
   （`Ether(bytes)`）包了 try/except，解析失敗就印 hex，不中斷流程。

## 從其他機器遠端連線

TRex 是 server + remote client 架構。client 可以在另一台機器上跑，透過
RPC 連到 TRex server 操作（封包仍從 server 那台的網卡進出，client 只是
遙控器）。

`trex_path.py` 支援兩個環境變數，遠端連線不必改程式碼：

| 環境變數 | 用途 | 預設 |
|----------|------|------|
| `TREX_SERVER` | TRex server 的 IP | `127.0.0.1` |
| `TREX_ROOT` | 本機 TRex 安裝路徑 | `~/trex/v3.06` |

在**遠端 client 那台**跑範例：

```bash
# 連到 TRex server (192.168.40.131)
TREX_SERVER=192.168.40.131 python3 00_connect_test.py

# server 位址 + 本機 TRex 裝在別處
TREX_SERVER=192.168.40.131 TREX_ROOT=/opt/trex/v3.06 python3 01_l2_raw.py
```

遠端連線的前置條件：

1. **client 那台要有 TRex 的 Python client 套件**。最簡單是遠端也裝一份
   TRex（`automation/trex_control_plane/interactive` 那包），用 `TREX_ROOT`
   指到它。client 端不需要跑 server、不需要網卡、不需要 DPDK。
2. **server 要監聽對外位址**（本 repo 的啟動方式已 bind `0.0.0.0:4500` 與
   `0.0.0.0:4501`，預設即可）。
3. **防火牆放行 TCP 4500 與 4501**：4501 是 RPC(命令)，4500 是 async(統計
   推播)。只開一個會「連得上但收不到統計」。
4. **同一時間預設一個 client 擁有一組 port**。多 client 要操作同組 port
   需 `force` 搶占，或各自操作不同 port。

檢查 server 監聽與防火牆：

```bash
ss -tlnp | grep -E ':4500|:4501'     # 應看到 0.0.0.0:4500 / 0.0.0.0:4501
sudo ufw status                       # 若啟用, 需 allow 4500/4501
```

## 多卡綁定與選 port（情境 A）

TRex 的網卡模型要點：

- **一個 server 啟動時，就把 cfg `interfaces:` 列的所有卡整批接管**，編號成
  port 0, 1, 2, 3...。不是「先綁一堆、用時才挑」，而是「啟動時全綁 →
  送封包時用 port 編號指定哪張」。
- DPDK 模式下被綁的卡會從 Linux kernel 消失，直到 TRex 結束才還回來。
- port 通常成對運作（0↔1、2↔3），所以綁偶數張最常見。

切換 2-port / 4-port 模式（用環境變數 `PORTS`）：

```bash
# 4-port: 建兩對 veth loopback 並用 4-port cfg 啟動
PORTS=4 ./trex_server.sh start-bg
PORTS=4 ./trex_server.sh status

# 驗證「選 port」: 從 port 0 送只有 port 1 收, 從 port 2 送只有 port 3 收
python3 09_multiport_select.py

# 收工
PORTS=4 ./trex_server.sh stop
PORTS=4 ./trex_server.sh teardown
```

4-port cfg（`cfg/trex_software_4ports.yaml`）對應：

| port | 介面 | loopback 對端 |
|------|------|--------------|
| 0 | trexA0 | trexA1 (port 1) |
| 1 | trexA1 | trexA0 (port 0) |
| 2 | trexB0 | trexB1 (port 3) |
| 3 | trexB1 | trexB0 (port 2) |

Python 裡「指定用哪張卡」就是傳 port 編號：

```python
c.start(ports=[0], duration=5)   # 只用 port 0（走第一對）
c.start(ports=[2], duration=5)   # 只用 port 2（走第二對，互不干擾）
c.push_packets(pkts, ports=[2])  # 從 port 2 送
```

> 把 veth 換成實體卡時，cfg 的 `interfaces:` 改成實體卡名（如
> `ens19`、`ens20`…）即可，Python 選 port 的用法完全不變。

## 下一步：對真實設備收送

目前是軟體 loopback。要對你的實體系統 / DUT 收送封包時：

1. 選一張閒置實體網卡（例如目前 DOWN 的 `ens19`）。
2. 用 `~/trex/v3.06/dpdk_setup_ports.py -i` 互動式產生綁 DPDK 的設定檔，
   或繼續用軟體模式把 `--iface` 指向實體網卡（效能較低但設定簡單）。
3. 把實體網卡接到你的設備，TRex port 0 送、port 1（或設備回送）收。

> ⚠️ 綁 DPDK 會讓 Linux「看不到」那張網卡（被 TRex 獨佔）。務必**不要**動到
> 管理網卡 `ens18`，否則會斷線。
