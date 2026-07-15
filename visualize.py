# -*- coding: utf-8 -*-
"""
电商用户价值分层分析 - 可视化报告
====================================
基于 RFM 模型对交易数据中的客户进行价值分层，
输出多维度可视化图表，用于客户汇报展示。

数据源: Online Retail (UCL) - 2010年12月 ~ 2011年12月

用法
----
    python visualize.py                     # 完整流程
    python visualize.py --data data/foo.csv # 自定义数据路径
"""

import argparse
import logging
import sys
import os

# 确保项目根目录在 sys.path 中
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.config import ensure_output_dir
from src.data_loader import setup_visualization, load_and_clean, generate_rfm
from src.charts import (
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

# ------------------- 日志配置 -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="RFM 电商用户价值分层分析")
    parser.add_argument("--data", type=str, default=None, help="CSV 数据文件路径")
    parser.add_argument("--n-bins", type=int, default=4, help="RFM 打分分箱数 (默认 4)")
    parser.add_argument("--quiet", action="store_true", help="仅输出最终结果，不打印中间日志")
    args = parser.parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    print("=" * 60)
    print("电商用户价值分层分析 — 开始")
    print("=" * 60)

    # 步骤 1: 加载与清洗
    print("\n第一步：加载与清洗数据")
    df, snapshot_date = load_and_clean(args.data)

    # 步骤 2: 构建 RFM
    print("\n第二步：构建 RFM 模型")
    rfm = generate_rfm(df, snapshot_date, n_bins=args.n_bins)

    # 步骤 3: 可视化
    print("\n第三步：生成可视化图表")
    setup_visualization()
    ensure_output_dir()

    plot_segment_distribution(rfm)
    plot_revenue_contribution(rfm)
    plot_monthly_trend(df)
    plot_rfm_scatter(rfm)
    plot_radar_charts(rfm)
    plot_monetary_analysis(rfm)
    plot_country_ranking(df)
    plot_dashboard(df, rfm)

    # 步骤 4: 导出
    print("\n第四步：导出结果")
    insight_df = export_results(rfm, df)

    print("\n" + "=" * 60)
    print("全部完成！")
    print("=" * 60)
    print("\n共生成 8 张可视化图表，保存在 figures/ 目录")
    print("数据导出: figures/rfm_segments.csv, figures/segment_insights.csv")

    # 打印摘要
    print("\n客群分布摘要:")
    for _, row in insight_df.iterrows():
        print(
            "  {}: {:>4} 人 ({:>5.1f}%), 营收贡献 {:>6.1f}%".format(
                row["客群"], row["客户数"], row["占比(%)"], row["营收占比(%)"]
            )
        )


if __name__ == "__main__":
    main()
