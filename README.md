# trex

Cisco TRex 封包收送範例集（Python）。

涵蓋 L2/L3 raw packet 與常見協定模擬：LLDP、STP、LACP、OSPF、BGP、
IPv4/IPv6 multicast、IGMP、MLD、CFM、ICMP、ARP、VRRP、VXLAN、DHCP，
以及多卡綁定 + 選 port、RX capture。全部在軟體模式（af_packet）+ veth
loopback 下驗證通過，不需要實體網卡。

## 目錄結構

```
trex/
├── README.md          # 本檔
└── examples/          # 所有範例與說明
    ├── README.md      # 詳細說明：安裝、啟動、每個範例的用法與注意事項
    ├── trex_path.py   # TRex Python API 路徑設定
    ├── proto_common.py# 協定範例共用工具（送出 + 擷取 + 解析）
    ├── trex_server.sh # server / veth 管理腳本
    └── NN_*.py        # 20 個範例（00~19）
```

> TRex 本體（`v3.06/`）與下載檔（`*.tar.gz`）體積大、含近 100MB 二進位，
> 不進版控。安裝方式見 [`examples/README.md`](examples/README.md) 的
> 「安裝 TRex」章節。

## 開始

詳見 **[`examples/README.md`](examples/README.md)**。快速版：

```bash
cd examples
./trex_server.sh start-bg     # 建 veth + 啟動 TRex server
python3 00_connect_test.py    # 連線測試
python3 01_l2_raw.py          # 跑範例
```
