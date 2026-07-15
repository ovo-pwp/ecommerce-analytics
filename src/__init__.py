# -*- coding: utf-8 -*-
"""
ecommerce-analytics — 基于 RFM 模型的电商用户价值分层分析

使用方式
--------
>>> from src import run_analysis
>>> run_analysis()
"""

from .config import FONT_FAMILY, SEGMENT_COLORS, OUTPUT_DIR, ensure_output_dir
from .data_loader import (
    load_and_clean,
    generate_rfm,
    setup_visualization,
    generate_quality_report,
)
from .charts import (
    plot_segment_distribution,
    plot_revenue_contribution,
    plot_monthly_trend,
    plot_rfm_scatter,
    plot_radar_charts,
    plot_monetary_analysis,
    plot_country_ranking,
    plot_dashboard,
    export_results,
)
from .rfm import calculate_rfm, score_rfm, assign_segment
from .segments import segment_summary, revenue_contribution, export_report

__all__ = [
    "FONT_FAMILY",
    "SEGMENT_COLORS",
    "OUTPUT_DIR",
    "ensure_output_dir",
    "load_and_clean",
    "generate_rfm",
    "setup_visualization",
    "generate_quality_report",
    "plot_segment_distribution",
    "plot_revenue_contribution",
    "plot_monthly_trend",
    "plot_rfm_scatter",
    "plot_radar_charts",
    "plot_monetary_analysis",
    "plot_country_ranking",
    "plot_dashboard",
    "export_results",
    "calculate_rfm",
    "score_rfm",
    "assign_segment",
    "segment_summary",
    "revenue_contribution",
    "export_report",
]
