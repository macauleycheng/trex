#!/usr/bin/env bash
#
# gen_conf.sh - 依組號產生該組的 ExaBGP speaker 設定檔。
#
# 位址規劃與 setup_netns.sh 一致:
#   group N:  speaker(local) = 10.N.1.2   peer(DUT)  = 10.N.1.1
#   local-as = 65000+N (本端)             peer-as    = 65001 (DUT, 可改)
#
# 產出檔: ./conf/speaker<N>.conf
#
# 用法: ./gen_conf.sh <N>
set -euo pipefail

N="${1:?用法: ./gen_conf.sh <組號>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$HERE/conf"
mkdir -p "$OUT_DIR"

SPEAKER_IP="10.$N.1.2"
PEER_IP="10.$N.1.1"
# AS 規劃: DUT 固定 65001; 每組 speaker = 65100+N (互不相同, 且與 DUT 不同 = eBGP)
LOCAL_AS="$((65100 + N))"
PEER_AS="${PEER_AS:-65001}"
OUT="$OUT_DIR/speaker$N.conf"

cat > "$OUT" <<EOF
# 自動產生 (gen_conf.sh $N) — 第 $N 組 BGP speaker
# speaker=$SPEAKER_IP  peer(DUT)=$PEER_IP  local-as=$LOCAL_AS  peer-as=$PEER_AS

process announce-routes-$N {
    run /usr/bin/env python3 $HERE/announce.py;
    encoder text;
}

neighbor $PEER_IP {
    router-id $SPEAKER_IP;
    local-address $SPEAKER_IP;
    local-as $LOCAL_AS;
    peer-as $PEER_AS;
    hold-time 180;

    api {
        processes [ announce-routes-$N ];
    }
}
EOF

echo "產生: $OUT"
