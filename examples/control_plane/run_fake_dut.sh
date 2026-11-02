#!/usr/bin/env bash
#
# run_fake_dut.sh - 本機驗證用: 在 host 端啟動一個被動 ExaBGP 當「假 DUT」。
#
# 真實環境裡這端是你的 SONiC / EC switch (DUT), 不需要這支腳本。
# 本機沒有真 DUT 時, 用它在 veth 的 host 端 (10.N.1.1) 起一個會回應的 BGP
# peer, 讓 speaker 能把 session 建到 Established, 證明整條控制平面可運作。
#
# 假 DUT 會 listen 10.N.1.1:179 (特權 port, 需 root), 被動接受 speaker 連入。
#
# 用法:
#   sudo ./run_fake_dut.sh <N>          # 前景
#   sudo ./run_fake_dut.sh <N> --bg     # 背景, log 寫 ./log/dut<N>.log
set -euo pipefail

N="${1:?用法: sudo ./run_fake_dut.sh <組號> [--bg]}"
MODE="${2:-}"

HERE="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$HERE/log"; mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/dut$N.log"
CONF_DIR="$HERE/conf"; mkdir -p "$CONF_DIR"
CONF="$CONF_DIR/dut$N.conf"

DUT_IP="10.$N.1.1"
SPK_IP="10.$N.1.2"
DUT_AS="${PEER_AS:-65001}"
SPK_AS="$((65100 + N))"    # 與 gen_conf.sh 的 speaker AS 規劃一致

USER_HOME="$(eval echo "~${SUDO_USER:-$USER}")"
SITE="$USER_HOME/.local/lib"
MAIN="$(find "$SITE" -maxdepth 3 -path '*/exabgp/application/main.py' 2>/dev/null | head -1 || true)"
PYPKG="$(find "$SITE" -maxdepth 2 -type d -name site-packages 2>/dev/null | head -1 || true)"
if [ -z "$MAIN" ] || [ -z "$PYPKG" ]; then
    echo "錯誤: 找不到 ExaBGP, 請先 python3 -m pip install --user exabgp" >&2
    exit 1
fi

# 假 DUT 設定: 單純當 peer, 被動接受連線
cat > "$CONF" <<EOF
# 自動產生 — 第 $N 組「假 DUT」(本機驗證用)
neighbor $SPK_IP {
    router-id $DUT_IP;
    local-address $DUT_IP;
    local-as $DUT_AS;
    peer-as $SPK_AS;
    hold-time 180;
}
EOF

ENV_ARR=(
    PATH="$USER_HOME/.local/bin:/usr/bin:/bin"
    PYTHONPATH="$PYPKG"
    exabgp_daemon_daemonize=false
    exabgp_log_level=INFO
    exabgp_tcp_bind="$DUT_IP"
)

echo "[*] 啟動假 DUT: listen $DUT_IP:179 (peer=$SPK_IP)"
if [ "$MODE" = "--bg" ]; then
    env "${ENV_ARR[@]}" python3 "$MAIN" "$CONF" > "$LOG" 2>&1 &
    disown || true
    echo "[*] 背景啟動, log: $LOG"
else
    env "${ENV_ARR[@]}" python3 "$MAIN" "$CONF"
fi
