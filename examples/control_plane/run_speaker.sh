#!/usr/bin/env bash
#
# run_speaker.sh - 在第 N 組的 netns 內啟動 ExaBGP speaker。
#
# 處理掉本環境的幾個眉角 (都是實測踩過的坑):
#   1. ExaBGP 以 --user 安裝在 ~/.local, 用其 application/main.py 進入點。
#   2. BGP 的 TCP/179 是特權 port, 需 root; netns exec 本來就需 root, 故用 sudo。
#   3. 透過 env 傳 ExaBGP 設定 (exabgp_* 環境變數), 不依賴 ~/.local/etc 設定檔。
#   4. speaker 是「主動連線」端, 不 listen, 故 exabgp_tcp_bind 設空字串。
#   5. 前景不 daemonize, log 導到 ./log/speaker<N>.log 方便觀察。
#
# 用法:
#   ./run_speaker.sh <N>            # 前景啟動 (Ctrl-C 結束)
#   ./run_speaker.sh <N> --bg       # 背景啟動, log 寫入 ./log/speaker<N>.log
#
# 先決條件: 已 './setup_netns.sh start N' 建好該組 netns, 且已 './gen_conf.sh N'。
set -euo pipefail

N="${1:?用法: ./run_speaker.sh <組號> [--bg]}"
MODE="${2:-}"

HERE="$(cd "$(dirname "$0")" && pwd)"
NS="bgpspk$N"
CONF="$HERE/conf/speaker$N.conf"
LOG_DIR="$HERE/log"
LOG="$LOG_DIR/speaker$N.log"
mkdir -p "$LOG_DIR"

# --- 找 ExaBGP 安裝路徑 (--user 安裝) ---
USER_HOME="$(eval echo "~${SUDO_USER:-$USER}")"
SITE="$USER_HOME/.local/lib"
MAIN="$(find "$SITE" -maxdepth 3 -path '*/exabgp/application/main.py' 2>/dev/null | head -1 || true)"
PYPKG="$(find "$SITE" -maxdepth 2 -type d -name site-packages 2>/dev/null | head -1 || true)"

if [ -z "$MAIN" ] || [ -z "$PYPKG" ]; then
    echo "錯誤: 找不到 ExaBGP (預期在 $SITE/pythonX.Y/site-packages/exabgp)。" >&2
    echo "      請先: python3 -m pip install --user exabgp" >&2
    exit 1
fi
if [ ! -f "$CONF" ]; then
    echo "錯誤: 找不到設定 $CONF, 請先: ./gen_conf.sh $N" >&2
    exit 1
fi
if ! ip netns list 2>/dev/null | grep -q "^$NS\b"; then
    echo "錯誤: netns $NS 不存在, 請先: sudo ./setup_netns.sh start $N" >&2
    exit 1
fi

EXABGP_ENV=(
    PATH="$USER_HOME/.local/bin:/usr/bin:/bin"
    PYTHONPATH="$PYPKG"
    exabgp_daemon_daemonize=false
    exabgp_log_level=INFO
    exabgp_tcp_bind=""
)

echo "[*] 在 netns $NS 內啟動 speaker (conf=$CONF)"
if [ "$MODE" = "--bg" ]; then
    sudo ip netns exec "$NS" env "${EXABGP_ENV[@]}" \
        python3 "$MAIN" "$CONF" > "$LOG" 2>&1 &
    disown || true
    echo "[*] 背景啟動, log: $LOG  (用 ./verify.sh 檢查 session)"
else
    sudo ip netns exec "$NS" env "${EXABGP_ENV[@]}" \
        python3 "$MAIN" "$CONF"
fi
