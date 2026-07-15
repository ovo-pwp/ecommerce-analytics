# -*- coding: utf-8 -*-
"""
客群统计与摘要报告生成
======================

提供客群统计摘要、营收贡献计算、ARPU 衍生指标等功能。
"""

import pandas as pd


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成各客群的统计摘要。

    Parameters
    ----------
    df : DataFrame
        必须包含 user_id, recency, frequency, monetary, segment 列。

    Returns
    -------
    DataFrame
        每行一个客群，包含人数、平均 R/F/M 值、占比、ARPU。
    """
    summary = df.groupby("segment").agg(
        user_count=("user_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
        median_monetary=("monetary", "median"),
    ).reset_index()

    total = len(df)
    summary["share_pct"] = (summary["user_count"] / total * 100).round(1)
    if total == 0:
        summary["arpu"] = 0.0
    else:
        summary["arpu"] = (summary["avg_monetary"] / summary["avg_frequency"].clip(lower=1)).round(2)

    return summary


def revenue_contribution(
    rfm_df: pd.DataFrame, transaction_df: pd.DataFrame
) -> pd.DataFrame:
    """
    基于客户级别的 Monetary 值计算各客群营收贡献，
    而非使用交易明细 merge（后者会因客户多次购买重复累加）。

    Parameters
    ----------
    rfm_df : DataFrame
        客户级 RFM 数据，需包含 segment 和 monetary 列。
    transaction_df : DataFrame
        原始交易明细（用于验证总金额一致性）。

    Returns
    -------
    DataFrame
        各客群的营收贡献摘要。
    """
    total_revenue = transaction_df["TotalPrice"].sum()

    seg_revenue = rfm_df.groupby("segment")["monetary"].sum()

    result = pd.DataFrame({
        "客群": seg_revenue.index,
        "营收贡献": seg_revenue.values,
        "营收占比(%)": (seg_revenue.values / total_revenue * 100).round(1),
    })

    return result.sort_values("营收贡献", ascending=False).reset_index(drop=True)


def export_report(summary_df: pd.DataFrame, output_path: str) -> None:
    """将客群摘要导出为 CSV。"""
    summary_df.to_csv(output_path, index=False, encoding="utf-8-sig")
