"""
共用模組: 把 TRex Python API (STL client) 的路徑加入 sys.path。
所有範例 import 這個模組即可使用 trex.stl.api / trex.astf.api。
"""
import sys
import os

# TRex 安裝路徑
TREX_ROOT = os.path.expanduser("~/trex/v3.06")
# 互動式 client (STLClient / ASTFClient) 所在套件路徑
TREX_STL_PATH = os.path.join(
    TREX_ROOT, "automation", "trex_control_plane", "interactive"
)

if TREX_STL_PATH not in sys.path:
    sys.path.insert(0, TREX_STL_PATH)

# TRex server 連線位址 (本機軟體模式)
TREX_SERVER = "127.0.0.1"
