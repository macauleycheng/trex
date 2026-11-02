#!/usr/bin/env bash
#
# verify.sh - 驗證各組 BGP session 狀態與路由宣告情形。
#
# 檢查項目 (每組):
#   1. netns 是否存在
#   2. netns 內 TCP/179 是否有 ESTAB session (speaker <-> DUT)
#   3. speaker log 是否有成功宣告路由 (route added)
#   4. 是否有連線反覆中斷 (closing connection = churn, 不健康)
#
# 用法:
#   sudo ./verify.sh          # 掃描 1..16
#   sudo ./verify.sh 3        # 只看第 1..3 組
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$HERE/log"
MAX="${1:-16}"

if [ "$(id -u)" -ne 0 ]; then
    echo "提示: 建議用 sudo 執行 (讀 netns 狀態需 root)。" >&2
fi

overall_ok=1
any=0
for ((n=1; n<=MAX; n++)); do
    NS="bgpspk$n"
    ip netns list 2>/dev/null | grep -q "^$NS\b" || continue
    any=1
    SPK_IP="10.$n.1.2"; DUT_IP="10.$n.1.1"
    LOG="$LOG_DIR/speaker$n.log"

    estab="$(ip netns exec "$NS" ss -tn 2>/dev/null | grep ':179' | grep -c ESTAB || true)"
    routes="$(grep -ac 'route added' "$LOG" 2>/dev/null || echo 0)"
    churn="$(grep -ac 'closing connection' "$LOG" 2>/dev/null || echo 0)"

    printf '=== group %d (ns=%s  speaker=%s  dut=%s) ===\n' "$n" "$NS" "$SPK_IP" "$DUT_IP"
    if [ "$estab" -ge 1 ]; then
        printf '  [OK ] BGP session ESTABLISHED (%s)\n' \
            "$(ip netns exec "$NS" ss -tn 2>/dev/null | grep ':179' | awk '{print $4" -> "$5}' | head -1)"
    else
        printf '  [FAIL] 沒有 ESTAB session on 179\n'
        overall_ok=0
    fi
    printf '  [i  ] 宣告路由筆數 (route added): %s\n' "$routes"
    if [ "$churn" -gt 0 ]; then
        printf '  [WARN] 偵測到 %s 次連線中斷 (churn), 可能 DUT 未就緒或 AS/IP 設定不符\n' "$churn"
    fi
done

[ "$any" -eq 0 ] && { echo "(沒有任何 bgpspk* netns, 請先 setup_netns.sh start)"; exit 0; }
echo
if [ "$overall_ok" -eq 1 ]; then
    echo "結果: 全部檢查通過。"
else
    echo "結果: 有組未建立 session, 見上方 [FAIL] / [WARN]。"
    exit 1
fi
