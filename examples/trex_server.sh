#!/usr/bin/env bash
###############################################################################
# TRex 軟體模式 server 管理腳本 (veth loopback)
#
# 用法:
#   ./trex_server.sh setup     # 建立 veth pair (trex0 <-> trex1)
#   ./trex_server.sh start     # 啟動 TRex server (軟體模式, 前景)
#   ./trex_server.sh start-bg  # 啟動 TRex server (背景, log 寫到 /tmp)
#   ./trex_server.sh stop      # 停止 TRex server
#   ./trex_server.sh status    # 檢查狀態
#   ./trex_server.sh teardown  # 刪除 veth pair
#
# 注意: veth 是暫時性的, 機器重開機後要重新 setup。
###############################################################################
set -euo pipefail

TREX_DIR="$HOME/trex/v3.06"
LOG="/tmp/trex_server.log"

# 模式: 由環境變數 PORTS 控制 (2 或 4), 預設 2
#   PORTS=2 ./trex_server.sh start-bg   -> 2-port loopback (trex0/trex1)
#   PORTS=4 ./trex_server.sh start-bg   -> 4-port, 兩對 loopback
PORTS="${PORTS:-2}"
if [ "$PORTS" = "4" ]; then
    CFG="$TREX_DIR/cfg/trex_software_4ports.yaml"
    VETHS="trexA0 trexA1 trexB0 trexB1"
    PAIRS="trexA0:trexA1 trexB0:trexB1"
else
    CFG="$TREX_DIR/cfg/trex_software_loopback.yaml"
    VETHS="trex0 trex1"
    PAIRS="trex0:trex1"
fi

setup_veth() {
    echo "[*] 模式: ${PORTS}-port"
    for pair in $PAIRS; do
        a="${pair%%:*}"
        b="${pair##*:}"
        if ip link show "$a" &>/dev/null; then
            echo "[=] veth $a/$b 已存在"
            continue
        fi
        echo "[*] 建立 veth pair $a <-> $b"
        sudo ip link add "$a" type veth peer name "$b"
        for i in "$a" "$b"; do
            sudo ethtool -K "$i" rx off tx off tso off gso off gro off lro off 2>/dev/null || true
            sudo ip link set "$i" up
            sudo ip link set "$i" promisc on
        done
    done
    echo "[OK] veth 建立完成, MAC 對照:"
    local idx=0
    for i in $VETHS; do
        echo "    port $idx = $i  MAC=$(cat /sys/class/net/$i/address)"
        idx=$((idx + 1))
    done
    echo "[!] 若 MAC 與 cfg 不符, 請更新 $CFG。"
}

teardown_veth() {
    for pair in $PAIRS; do
        a="${pair%%:*}"
        if ip link show "$a" &>/dev/null; then
            sudo ip link del "$a"
            echo "[OK] 已刪除 veth pair ${pair/:/ <-> }"
        fi
    done
}

start_fg() {
    setup_veth
    echo "[*] 啟動 TRex server (前景, Ctrl-C 停止)..."
    cd "$TREX_DIR"
    sudo ./t-rex-64 -i --software --cfg "$CFG"
}

start_bg() {
    setup_veth
    if pgrep -f "t-rex-64 -i --software" &>/dev/null; then
        echo "[=] TRex server 已在執行"
        return
    fi
    echo "[*] 啟動 TRex server (背景), log: $LOG"
    cd "$TREX_DIR"
    sudo nohup ./t-rex-64 -i --software --cfg "$CFG" >"$LOG" 2>&1 &
    sleep 10
    if pgrep -f "t-rex-64 -i --software" &>/dev/null; then
        echo "[OK] TRex server 已啟動 (RPC: 127.0.0.1:4501)"
    else
        echo "[ERROR] 啟動失敗, 請看 $LOG"
        tail -20 "$LOG"
        exit 1
    fi
}

stop_srv() {
    if pgrep -f "t-rex-64" &>/dev/null; then
        sudo pkill -f "t-rex-64" || true
        sleep 2
        echo "[OK] 已停止 TRex server"
    else
        echo "[=] TRex server 未執行"
    fi
}

status_srv() {
    if pgrep -f "t-rex-64 -i --software" &>/dev/null; then
        echo "[+] TRex server: 執行中"
        pgrep -af "t-rex-64 -i --software" | head -1
    else
        echo "[-] TRex server: 未執行"
    fi
    echo "veth (${PORTS}-port 模式):"
    ip -br link show 2>/dev/null | grep -E "$(echo $VETHS | tr ' ' '|')" || echo "  (無 veth)"
}

case "${1:-}" in
    setup)    setup_veth ;;
    teardown) teardown_veth ;;
    start)    start_fg ;;
    start-bg) start_bg ;;
    stop)     stop_srv ;;
    status)   status_srv ;;
    *)
        echo "用法: $0 {setup|start|start-bg|stop|status|teardown}"
        exit 1
        ;;
esac
