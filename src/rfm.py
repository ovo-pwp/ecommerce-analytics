# -*- coding: utf-8 -*-
"""
RFM 分层计算逻辑
================

提供用户级 RFM 原始值计算、四分位打分、以及基于总分的客群分层。

使用方式
--------
>>> df = pd.read_csv("data/online_retail.csv")
>>> rfm = calculate_rfm(df, date_col="InvoiceDate", amount_col="TotalPrice")
>>> rfm_scored = score_rfm(rfm, n_bins=4)
>>> rfm_segmented = assign_segment(rfm_scored, n_bins=4)
"""

import pandas as pd
import numpy as np


def calculate_rfm(
    df: pd.DataFrame,
    date_col: str = "order_date",
    amount_col: str = "amount",
    snapshot_date=None,
) -> pd.DataFrame:
    """
    计算每个用户的 RFM 原始值。

    Parameters
    ----------
    df : DataFrame
        交易记录表，需包含 user_id、order_date、amount 列。
    date_col : str
        订单日期列名。
    amount_col : str
        订单金额列名。
    snapshot_date : datetime-like, optional
        分析快照日。默认为数据中最大日期。

    Returns
    -------
    DataFrame
        包含 recency / frequency / monetary 三列的用户级汇总表。
    """
    if snapshot_date is None:
        snapshot_date = df[date_col].max()

    user_stats = (
        df.groupby("user_id")
        .agg(
            recency=(date_col, lambda x: (snapshot_date - x.max()).days),
            frequency=(date_col, "count"),
            monetary=(amount_col, "sum"),
        )
        .reset_index()
    )
    return user_stats


def score_rfm(df: pd.DataFrame, n_bins: int = 5) -> pd.DataFrame:
    """
    将 RFM 原始值转换为 1~n_bins 的分数。

    - recency: 越小越好 → 升序打分（得分高 = 最近）
    - frequency / monetary: 越大越好 → 降序打分（得分高 = 消费多）
    """
    df = df.copy()

    df["R_score"] = pd.qcut(
        df["recency"], q=n_bins, labels=range(n_bins, 0, -1), duplicates="drop"
    ).astype(int)
    df["F_score"] = pd.qcut(
        df["frequency"], q=n_bins, labels=range(1, n_bins + 1), duplicates="drop"
    ).astype(int)
    df["M_score"] = pd.qcut(
        df["monetary"].clip(lower=1e-9),
        q=n_bins,
        labels=range(1, n_bins + 1),
        duplicates="drop",
    ).astype(int)

    return df


def assign_segment(
    rfm_scored: pd.DataFrame, n_bins: int = 4
) -> pd.DataFrame:
    """
    基于 RFM 总分进行客群分层。

    分段阈值根据 n_bins 动态计算:
        - 高价值:   总分 >= 2/3 最大分
        - 发展:     总分 >= 1/2 最大分
        - 保持:     总分 >= 1/3 最大分
        - 挽留:     其余

    Parameters
    ----------
    rfm_scored : DataFrame
        必须包含 R_score, F_score, M_score 列。
    n_bins : int
        打分分箱数（与 score_rfm 保持一致）。

    Returns
    -------
    DataFrame
        新增 total_score 和 segment 两列。
    """
    df = rfm_scored.copy()
    df["total_score"] = df[["R_score", "F_score", "M_score"]].sum(axis=1)

    max_score = n_bins * 3  # R + F + M
    # Thresholds: use fractions of max_score, ordered from highest to lowest
    # Process from lowest threshold to highest so higher tiers overwrite lower ones
    thresholds = [
        (0, "挽留客户"),
        (max_score // 3, "保持客户"),
        (max_score // 2, "发展客户"),
        (max_score * 2 // 3, "高价值客户"),
    ]

    df["segment"] = "挽留客户"  # 默认最低段
    for threshold, label in thresholds:
        df.loc[df["total_score"] >= threshold, "segment"] = label

    return df
