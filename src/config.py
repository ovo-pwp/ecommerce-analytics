# -*- coding: utf-8 -*-
"""
可视化配置
==========

统一管理字体、颜色、尺寸等视觉参数，支持跨平台。
"""

import platform
import os

# ------------------- 字体 -------------------
_FONT_NAMES = {
    "windows": ["Microsoft YaHei", "SimHei", "PingFang SC"],
    "darwin": ["PingFang SC", "Heiti SC", "Arial Unicode MS"],
    "linux": ["WenQuanYi Micro Hei", "Noto Sans CJK SC", "DejaVu Sans"],
}

_FONT_FAMILY = "DejaVu Sans"  # safe fallback


def _resolve_font():
    """Detect OS and find a usable Chinese-supporting font."""
    sys_name = platform.system().lower()
    candidates = _FONT_NAMES.get(sys_name, _FONT_NAMES["linux"])

    import matplotlib.font_manager as fm

    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return _FONT_FAMILY


FONT_FAMILY = _resolve_font()

# ------------------- 颜色 -------------------
SEGMENT_COLORS = {
    "高价值": "#2E86AB",
    "发展": "#6A994E",
    "保持": "#F18F01",
    "挽留": "#C73E1D",
    "一般": "#A23B72",
}

# Ordered palette for charts where segment order matters
SEGMENT_ORDER = ["高价值", "发展", "保持", "挽留", "一般"]
COLOR_PALETTE = [SEGMENT_COLORS[s] for s in SEGMENT_ORDER]

# ------------------- 尺寸 -------------------
FIGURE_DPI = 150
TITLE_SIZE = 18
LABEL_SIZE = 13
TICK_SIZE = 11

# ------------------- 路径 -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "figures")
DATA_DIR = os.path.join(BASE_DIR, "..", "data")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
