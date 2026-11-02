# 控制平面模擬：多組 BGP speaker（netns + ExaBGP）

這套範例示範「真正的控制平面模擬」——用 **ExaBGP** 跟 DUT 建立**真實的
BGP neighbor**（完成 TCP 三次握手 + OPEN/KEEPALIVE/UPDATE 交換，到
Established），並用 **Linux network namespace (netns)** 讓**多組 speaker 在
同一台 server 上並行、互不干擾**（供多人 / 多條測試路徑同時使用）。

> **為什麼不是用 TRex 做？**
> TRex（含本 repo 其他範例）擅長**資料平面**高速打流。它原生沒有 BGP 狀態機：
> EMU 模擬的是 host-side 協定（ARP / ND / DHCP / IGMP…），**不含 BGP**；
> `examples/06_bgp.py` 也只手組 BGP 封包、不建真 session。要真正建立 BGP
> neighbor、灌路由，業界標準做法是用專門的 BGP speaker（ExaBGP / GoBGP /
> FRR）。本範例用 ExaBGP 負責**控制平面**，TRex 仍負責**資料平面**，兩者在
> 同一條（經 fanout + VLAN 隔離的）邏輯路徑上分工。

## 為什麼用 network namespace 而不是 Docker？

多組 BGP speaker 同台共存，真正的衝突點是 **TCP/179 這個 port 與來源 IP**，
不是 process 隔離。每組需要自己獨立的 L3 身分（IP / routing table / 179）。

- **netns** 直接提供獨立網路堆疊（介面、IP、routing table、179），輕量、不需
  額外 runtime。**Docker 的網路隔離底層本來就是 netns**，所以若只要網路隔離，
  netns 就夠。
- 需要「環境一致 / 即起即丟 / 資源限制 / 編排」等**管理面**好處時，再在外面
  包 Docker 不遲（底層仍是 netns）。

本範例採 netns（已實測兩組並行 session 同時 Established、互不干擾）。

## 檔案

| 檔案 | 用途 |
|------|------|
| `setup_netns.sh` | 建立 / 拆除 N 組隔離環境（netns + veth + IP） |
| `gen_conf.sh` | 依組號產生該組 speaker 的 ExaBGP 設定（`conf/speakerN.conf`） |
| `announce.py` | ExaBGP API process：session 起來後宣告一批路由並常駐 |
| `run_speaker.sh` | 在指定 netns 內啟動 speaker ExaBGP |
| `run_fake_dut.sh` | 本機驗證用：在 host 端起被動 ExaBGP 當「假 DUT」（真實環境不需要） |
| `verify.sh` | 檢查各組 session 狀態 / 路由宣告 / 是否有連線中斷 |

## 前置：安裝 ExaBGP

```bash
python3 -m pip install --user exabgp
python3 -m exabgp version      # 確認可跑（本範例實測 5.0.15 / Python 3.8）
```

> 本範例腳本已處理幾個實測踩過的坑：
> - **TCP/179 是特權 port**，需 root → 腳本用 `sudo`（netns 操作本就需 root）。
> - **多版 Python 的 site-packages 混雜** → 腳本會自動定位真正裝了 exabgp 的
>   site-packages，避免 `No module named 'exabgp'`。
> - **speaker 是主動連線端**，不 listen → 設 `exabgp_tcp_bind=""`。

## 位址與 AS 規劃

| 組 N | netns | speaker IP | DUT IP | speaker AS | DUT AS |
|------|-------|-----------|--------|-----------|--------|
| 1 | bgpspk1 | 10.1.1.2/30 | 10.1.1.1/30 | 65101 | 65001 |
| 2 | bgpspk2 | 10.2.1.2/30 | 10.2.1.1/30 | 65102 | 65001 |
| N | bgpspk{N} | 10.N.1.2/30 | 10.N.1.1/30 | 65100+N | 65001 |

每組一個 `/30`、各組不同 AS（eBGP），完全隔離。

## 本機快速驗證（無需真實 DUT）

本機沒有 DUT 時，用 `run_fake_dut.sh` 在 veth 的 host 端起一個被動 ExaBGP
當對端，讓 session 真的建到 Established。

```bash
cd ~/trex/examples/control_plane

# 1. 建兩組隔離環境
sudo ./setup_netns.sh start 2

# 2. 產生兩組 speaker 設定
./gen_conf.sh 1
./gen_conf.sh 2

# 3. 起「假 DUT」(每組一個, 背景)
sudo ./run_fake_dut.sh 1 --bg
sudo ./run_fake_dut.sh 2 --bg

# 4. 起 speaker (每組一個, 背景)
./run_speaker.sh 1 --bg
./run_speaker.sh 2 --bg

# 5. 驗證: 兩組都應 ESTABLISHED、各宣告 3 筆路由、churn=0
sudo ./verify.sh 2

# 收工
sudo pkill -f exabgp
sudo ./setup_netns.sh stop
```

預期 `verify.sh` 輸出每組 `[OK] BGP session ESTABLISHED` 且 `宣告路由 3 筆`。

> **實測已驗證**：兩組 speaker 在各自 netns 同時 Established、各宣告路由、
> churn=0，且 group1 的 speaker IP 不會出現在 group2 的 netns（隔離成立）。

## 自訂宣告的路由

`announce.py` 讀環境變數（在 speaker 那端的 process 環境）：

| 變數 | 預設 | 說明 |
|------|------|------|
| `BGP_ROUTES` | `192.0.2.0/24,198.51.100.0/24,203.0.113.0/24` | 逗號分隔的 prefix |
| `BGP_NEXTHOP` | `self` | next-hop（self = speaker 的 local-address） |
| `BGP_ANNOUNCE_DELAY` | `3` | session 起來後延遲幾秒再宣告 |

需要撤路由 / 動態改變，可擴充 `announce.py` 從 stdin 讀指令後
`withdraw route <prefix>`（ExaBGP API 支援）。

## 對接真實 DUT（SONiC / EC switch）

本機驗證把對端放在 veth 的 host 端。對真實 DUT 時，差別只在**把 netns 的
對外介面換成「掛了對應 VLAN 的實體子介面」**：

1. 在實體網卡上建 VLAN 子介面（對應 topo-manager 分配的 VLAN）：
   ```bash
   sudo ip link add link <實體卡> name <卡>.<vlan> type vlan id <vlan>
   ```
2. 把該子介面移進該組 netns，設 speaker IP（與 DUT 在同一 /30）：
   ```bash
   sudo ip link set <卡>.<vlan> netns bgpspk<N>
   sudo ip netns exec bgpspk<N> ip addr add 10.N.1.2/30 dev <卡>.<vlan>
   sudo ip netns exec bgpspk<N> ip link set <卡>.<vlan> up
   ```
3. 把 `gen_conf.sh` 產生設定裡的 `neighbor` 改成 DUT 在該 VLAN 的介面 IP、
   `peer-as` 改成 DUT 實際 AS。
4. 不需要 `run_fake_dut.sh`（DUT 本身就是對端）。

控制平面（BGP session）走這條 VLAN 路徑；資料平面打流由 TRex 在**同一條
VLAN 路徑**上進行。兩者共用同一 L3 鄰接。

## 與 topo-manager 的對應

本範例的「組」正好對應 `topo-manager` 設計裡的**一條測試路徑 / 一個 VLAN
分配**：

```
一位使用者 / 一條測試 = 一個 VLAN = 一個 netns + 一份 ExaBGP speaker
                                      └ 綁該 VLAN 子介面 + 獨立 local IP
```

未來 topo-manager 自動化時，可由系統在分配 VLAN 的同時：建 netns、把對應
VLAN 子介面移進去、產生 speaker 設定、起 ExaBGP。本範例的腳本即是該自動化
的手動版雛形。

## 疑難排解

| 現象 | 原因 / 解法 |
|------|-------------|
| `No module named 'exabgp'` | 多版 Python site-packages 混雜；腳本已自動定位，若仍失敗確認 `pip install --user exabgp` 裝在哪個 python |
| `binding below port 1024 requires root` | 179 是特權 port；用 `sudo` 跑（假 DUT 端） |
| `verify.sh` 顯示 churn > 0 | 對端未就緒、AS/IP 不符、或 router-id 衝突；確認 DUT 已 listen 且 AS 對應正確 |
| session 一直 Active 不 Established | 對端沒在 179 listen，或路徑不通（先 `ip netns exec bgspk<N> ping <DUT>`） |
| 無 CLI named pipe 警告 | 可忽略，不影響 session（僅 exabgp-cli 互動功能） |
