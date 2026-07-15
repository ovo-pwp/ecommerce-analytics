# -*- coding: utf-8 -*-
"""
数据加载与清洗
==============

从 CSV 读取原始交易数据，执行清洗步骤，返回干净的 DataFrame。
支持数据质量报告生成。
"""

import logging
import os
import pandas as pd
from datetime import timedelta

from .config import DATA_DIR, FONT_FAMILY
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


def setup_visualization():
    """一次性配置 matplotlib/seaborn 全局样式。"""
    matplotlib.use("Agg")
    plt.rcParams["font.family"] = FONT_FAMILY
    sns.set_style("whitegrid")
    sns.set_palette(sns.color_palette(["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#6A994E"]))
    # Re-apply font after sns.set_style (which resets font.family)
    plt.rcParams["font.sans-serif"] = [FONT_FAMILY, "Arial Unicode MS"]
    plt.rcParams["font.family"] = FONT_FAMILY


def generate_quality_report(df, output_path=None):
    """
    生成数据质量报告并打印/保存到文件。

    Parameters
    ----------
    df : DataFrame
        原始未清洗数据。
    output_path : str, optional
        报告保存路径。默认为 figures/data_quality_report.md。
    """
    lines = [
        "# 数据质量报告",
        "",
        "## 基本信息",
        f"- 总记录数: {len(df):,}",
        f"- 列数: {len(df.columns)}",
        f"- 列名: {', '.join(df.columns)}",
        "",
        "## 缺失值",
    ]

    missing = df.isnull().sum()
    missing_pct = missing / len(df) * 100
    for col in missing.index:
        if missing[col] > 0:
            lines.append(
                f"- **{col}**: {missing[col]:,} 缺失 ({missing_pct[col]:.1f}%)"
            )

    lines.extend([
        "",
        "## 数值列统计",
    ])
    num_cols = df.select_dtypes(include=[np.number if hasattr(np, 'number') else 'number']).columns
    if len(num_cols) > 0:
        stats = df[num_cols].describe()
        lines.append(stats.to_string())

    lines.extend([
        "",
        "## 异常值检测",
    ])

    if 'UnitPrice' in df.columns:
        neg_price = (df['UnitPrice'] < 0).sum()
        zero_price = (df['UnitPrice'] == 0).sum()
        lines.append(f"- 单价 < 0: {neg_price:,} 条")
        lines.append(f"- 单价 = 0: {zero_price:,} 条")

    if 'Quantity' in df.columns:
        neg_qty = (df['Quantity'] < 0).sum()
        lines.append(f"- 数量 < 0 (退货): {neg_qty:,} 条")

    if 'InvoiceDate' in df.columns:
        invalid_dates = df['InvoiceDate'].isna().sum()
        lines.append(f"- 无法解析的日期: {invalid_dates:,} 条")

    report_text = '\n'.join(lines)
    print(report_text)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info("数据质量报告已保存: %s", output_path)


import numpy as np


def load_and_clean(data_path=None, quality_report_path=None):
    """
    加载并清洗交易数据。

    Parameters
    ----------
    data_path : str, optional
        CSV 文件路径。默认为 data/online_retail.csv。
    quality_report_path : str, optional
        数据质量报告保存路径。

    Returns
    -------
    tuple
        (clean_df, snapshot_date) — 清洗后的数据和快照日
    """
    if data_path is None:
        data_path = os.path.join(DATA_DIR, "online_retail.csv")

    logger.info("加载原始数据: %s", data_path)

    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        logger.error("数据文件不存在: %s", data_path)
        raise
    except Exception as e:
        logger.error("读取数据文件失败: %s", e)
        raise

    logger.info("原始数据: %d 条记录", len(df))

    # 生成数据质量报告
    if quality_report_path is None:
        quality_report_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "figures", "data_quality_report.md"
        )
    generate_quality_report(df, quality_report_path)

    # 解析日期
    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"], format="%m/%d/%Y %H:%M", errors="coerce"
    )
    na_dates = df["InvoiceDate"].isna().sum()
    if na_dates:
        logger.warning("删除 %d 条无法解析的日期记录", na_dates)
    df = df.dropna(subset=["InvoiceDate"])

    # 删除 CustomerID 为空的记录
    before = len(df)
    df = df.dropna(subset=["CustomerID"])
    df["CustomerID"] = df["CustomerID"].astype(int)
    logger.info("删除缺失客户ID后: %d 条（移除 %d 条）", len(df), before - len(df))

    # 删除退货记录（数量为负）
    before = len(df)
    df = df[df["Quantity"] > 0]
    logger.info("删除退货记录后: %d 条（移除 %d 条）", len(df), before - len(df))

    # 删除单价为零或负的记录
    before = len(df)
    df = df[df["UnitPrice"] > 0]
    logger.info("删除异常价格后: %d 条（移除 %d 条）", len(df), before - len(df))

    # 计算每笔交易的总金额
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]
    logger.info("交易总金额: %.2f", df["TotalPrice"].sum())

    # 快照日
    snapshot_date = df["InvoiceDate"].max() + timedelta(days=1)
    logger.info("分析快照日: %s", snapshot_date.strftime("%Y-%m-%d"))

    return df, snapshot_date


def generate_rfm(df, snapshot_date, n_bins=4):
    """
    基于清洗后的数据构建 RFM 模型并打分分层。

    Parameters
    ----------
    df : DataFrame
        清洗后的交易数据。
    snapshot_date : datetime
        分析快照日。
    n_bins : int
        打分分箱数。

    Returns
    -------
    DataFrame
        客户级 RFM 数据，包含 R/F/M 原始值、分数、客群标签。
    """
    from .rfm import calculate_rfm, score_rfm

    # 使用 src/rfm.py 的新接口
    rfm_df = df.copy()
    rfm_df = rfm_df.rename(columns={"CustomerID": "user_id"})
    rfm = calculate_rfm(rfm_df, date_col="InvoiceDate", amount_col="TotalPrice", snapshot_date=snapshot_date)

    # 打分（score_rfm 期望小写列名）
    rfm = score_rfm(rfm, n_bins=n_bins)

    # 重命名为大写风格
    rfm = rfm.rename(columns={
        "recency": "Recency", "frequency": "Frequency", "monetary": "Monetary",
        "R_score": "R_Score", "F_score": "F_Score", "M_score": "M_Score",
    })
    rfm = rfm.set_index("user_id")

    # 保留旧的分层函数以保持向后兼容（visualize.py 中的命名）
    rfm = _legacy_segment(rfm)

    logger.info("活跃客户数: %d 人", len(rfm))
    logger.info("平均消费频次: %.1f 次", rfm["Frequency"].mean())
    logger.info("平均消费总额: %.2f", rfm["Monetary"].mean())
    logger.info("平均距上次消费: %.1f 天", rfm["Recency"].mean())

    return rfm


def _legacy_segment(rfm):
    """
    沿用 visualize.py 中的五分类规则（高价值/发展/保持/挽留/一般）。

    这是为了保持与现有输出一致而保留的过渡函数。
    新代码建议使用 src/rfm.py 中的 assign_segment()。
    """
    def rfm_segment(row):
        if row["R_Score"] >= 3 and row["F_Score"] >= 3 and row["M_Score"] >= 3:
            return "高价值"
        elif row["R_Score"] >= 3 and row["F_Score"] >= 2:
            return "发展"
        elif row["R_Score"] <= 2 and row["F_Score"] >= 3 and row["M_Score"] >= 3:
            return "保持"
        elif row["R_Score"] <= 2 and row["F_Score"] <= 2 and row["M_Score"] <= 2:
            return "挽留"
        else:
            return "一般"

    rfm["Segment"] = rfm.apply(rfm_segment, axis=1)
    return rfm
