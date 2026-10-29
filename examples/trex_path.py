"""
共用模組: 把 TRex Python API (STL client) 的路徑加入 sys.path。
所有範例 import 這個模組即可使用 trex.stl.api / trex.astf.api。

兩個設定都可用環境變數覆寫, 遠端連線 / 不同安裝路徑時不必改程式碼:

  TREX_SERVER  TRex server 的連線位址 (預設 127.0.0.1 本機)
  TREX_ROOT    TRex 安裝路徑 (預設 ~/trex/v3.06)

範例:
  # 本機 (預設)
  python3 00_connect_test.py

  # 連到另一台 server
  TREX_SERVER=192.168.40.131 python3 00_connect_test.py

  # server 連遠端, 且本機 TRex 裝在別處
  TREX_SERVER=192.168.40.131 TREX_ROOT=/opt/trex/v3.06 python3 00_connect_test.py
"""
import sys
import os

# TRex 安裝路徑 (可用環境變數 TREX_ROOT 覆寫)
TREX_ROOT = os.path.expanduser(
    os.environ.get("TREX_ROOT", "~/trex/v3.06")
)
# 互動式 client (STLClient / ASTFClient) 所在套件路徑
TREX_STL_PATH = os.path.join(
    TREX_ROOT, "automation", "trex_control_plane", "interactive"
)

if not os.path.isdir(TREX_STL_PATH):
    sys.stderr.write(
        "[trex_path] 找不到 TRex client 套件路徑:\n"
        "    %s\n"
        "請確認 TRex 已安裝, 或用 TREX_ROOT 指定正確路徑, 例如:\n"
        "    TREX_ROOT=/opt/trex/v3.06 python3 <script>.py\n"
        % TREX_STL_PATH
    )

if TREX_STL_PATH not in sys.path:
    sys.path.insert(0, TREX_STL_PATH)

# TRex server 連線位址 (可用環境變數 TREX_SERVER 覆寫; 預設本機)
TREX_SERVER = os.environ.get("TREX_SERVER", "127.0.0.1")
