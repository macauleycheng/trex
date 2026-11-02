#!/usr/bin/env bash
#
# setup_netns.sh - 建立 / 拆除多組隔離的 BGP speaker 網路環境 (network namespace)
# -----------------------------------------------------------------------------
# 每一組 (group) 代表「一位使用者 / 一條測試路徑」, 彼此用 Linux network
# namespace 完全隔離: 各自獨立的網路堆疊、IP、routing table、以及 TCP/179。
# 因此多組 ExaBGP speaker 可以在同一台 server 上同時跑, 互不搶 port、互不干擾。
#
# 本機驗證模式 (loopback):
#   每組建一對 veth, 一端在 netns 內 (speaker), 一端留在 host (模擬 DUT 對端)。
#   netns 端跑 speaker ExaBGP, host 端可跑一個被動 ExaBGP 當假 DUT。
#
# 對接真實 DUT 時:
#   把 host 端 veth 換成「掛了對應 VLAN 的實體子介面」移進 netns 即可 (見 README)。
#
# 位址規劃 (每組一個 /30):
#   group N:  host(DUT) = 10.<N>.1.1/30   speaker = 10.<N>.1.2/30
#   netns 名 = bgpspk<N>   veth = veth-h<N> (host) / veth-s<N> (speaker)
#
# 用法:
#   sudo ./setup_netns.sh start 3      # 建 3 組
#   sudo ./setup_netns.sh status
#   sudo ./setup_netns.sh stop         # 拆除全部 (預設掃 1..16)
#   sudo ./setup_netns.sh stop 3       # 拆除 3 組
# -----------------------------------------------------------------------------
set -euo pipefail

NS_PREFIX="bgpspk"
MAX_SCAN=16          # stop 未指定組數時, 掃描到此上限

need_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "錯誤: 需要 root (netns 操作), 請用 sudo 執行。" >&2
        exit 1
    fi
}

grp_ns()   { echo "${NS_PREFIX}$1"; }
grp_vh()   { echo "veth-h$1"; }       # host 端 (DUT)
grp_vs()   { echo "veth-s$1"; }       # speaker 端 (進 netns)
grp_dut()  { echo "10.$1.1.1"; }      # host / 假 DUT IP
grp_spk()  { echo "10.$1.1.2"; }      # speaker IP

create_group() {
    local n="$1"
    local ns vh vs dut spk
    ns="$(grp_ns "$n")"; vh="$(grp_vh "$n")"; vs="$(grp_vs "$n")"
    dut="$(grp_dut "$n")"; spk="$(grp_spk "$n")"

    # 冪等: 先清掉同名殘留
    ip netns del "$ns" 2>/dev/null || true
    ip link del "$vh" 2>/dev/null || true

    ip netns add "$ns"
    ip link add "$vh" type veth peer name "$vs"
    ip link set "$vs" netns "$ns"

    # host 端 (假 DUT)
    ip addr add "${dut}/30" dev "$vh"
    ip link set "$vh" up

    # netns 端 (speaker)
    ip netns exec "$ns" ip addr add "${spk}/30" dev "$vs"
    ip netns exec "$ns" ip link set "$vs" up
    ip netns exec "$ns" ip link set lo up

    echo "[+] group $n : ns=$ns  speaker=$spk  dut(host)=$dut"
}

delete_group() {
    local n="$1"
    local ns vh
    ns="$(grp_ns "$n")"; vh="$(grp_vh "$n")"
    if ip netns list 2>/dev/null | grep -q "^${ns}\b" || ip link show "$vh" >/dev/null 2>&1; then
        ip netns del "$ns" 2>/dev/null || true
        ip link del "$vh" 2>/dev/null || true
        echo "[-] group $n : removed ($ns)"
    fi
}

cmd_start() {
    local count="${1:-1}"
    need_root
    local i
    for ((i=1; i<=count; i++)); do
        create_group "$i"
    done
    echo "完成: 已建立 $count 組。用 './run_speaker.sh <N>' 在某組內啟動 ExaBGP。"
}

cmd_stop() {
    need_root
    local count="${1:-$MAX_SCAN}"
    local i
    for ((i=1; i<=count; i++)); do
        delete_group "$i"
    done
    echo "完成: 已拆除 (掃描 1..$count)。"
}

cmd_status() {
    need_root
    echo "=== network namespaces ($NS_PREFIX*) ==="
    local found=0 ns
    for ns in $(ip netns list 2>/dev/null | awk '{print $1}' | grep "^${NS_PREFIX}" || true); do
        found=1
        local n="${ns#$NS_PREFIX}"
        local spk dut
        spk="$(grp_spk "$n")"; dut="$(grp_dut "$n")"
        echo "--- $ns (speaker=$spk, dut=$dut) ---"
        ip netns exec "$ns" ip -brief addr show 2>/dev/null | grep -v '^lo' || true
        # 有無已建立的 BGP session
        if ip netns exec "$ns" ss -tn 2>/dev/null | grep -q ':179'; then
            echo "    BGP: $(ip netns exec "$ns" ss -tn 2>/dev/null | grep ':179' | awk '{print $1" "$4" -> "$5}')"
        else
            echo "    BGP: (no session on 179)"
        fi
    done
    [ "$found" -eq 0 ] && echo "(目前沒有 ${NS_PREFIX}* namespace)"
}

usage() {
    cat >&2 <<EOF
用法: sudo $0 <start|stop|status> [N]
  start N    建立 N 組隔離環境 (預設 1)
  stop  [N]  拆除 (指定 N 組, 或預設掃描 1..$MAX_SCAN 全拆)
  status     列出各組狀態與 BGP session
EOF
    exit 1
}

case "${1:-}" in
    start)  cmd_start "${2:-1}" ;;
    stop)   cmd_stop "${2:-}" ;;
    status) cmd_status ;;
    *)      usage ;;
esac
