# RFM 分层计算逻辑
import pandas as pd
import numpy as np


def calculate_rfm(df: pd.DataFrame, date_col: str = "order_date", amount_col: str = "amount") -> pd.DataFrame:
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

    Returns
    -------
    DataFrame
        包含 recency / frequency / monetary 三列的用户级汇总表。
    """
    max_date = df[date_col].max()
    user_stats = (
        df.groupby("user_id")
        .agg(
            recency=(date_col, lambda x: (max_date - x.max()).days),
            frequency=(date_col, "count"),
            monetary=(amount_col, "sum"),
        )
        .reset_index()
    )
    return user_stats


def score_rfm(df: pd.DataFrame, n_bins: int = 5) -> pd.DataFrame:
    """
    将 RFM 原始值转换为 1~n_bins 的分数。

    - recency: 越小越好 → 升序打分
    - frequency / monetary: 越大越好 → 降序打分
    """
    df = df.copy()

    df["R_score"] = pd.qcut(df["recency"], q=n_bins, labels=range(1, n_bins + 1), duplicates="drop").astype(int)
    df["F_score"] = pd.qcut(df["frequency"], q=n_bins, labels=range(1, n_bins + 1), duplicates="drop").astype(int)
    df["M_score"] = pd.qcut(df["monetary"].clip(lower=1e-9), q=n_bins, labels=range(1, n_bins + 1), duplicates="drop").astype(int)

    return df


def assign_segment(rfm_scored: pd.DataFrame) -> pd.DataFrame:
    """
    基于 RFM 总分进行客群分层。

    分段阈值可根据实际业务调整。
    """
    df = rfm_scored.copy()
    df["total_score"] = df[["R_score", "F_score", "M_score"]].sum(axis=1)

    thresholds = [
        (13, "高价值客户"),
        (9, "发展客户"),
        (6, "保持客户"),
        (0, "挽留客户"),
    ]

    df["segment"] = "挽留客户"  # 默认最低段
    for threshold, label in thresholds:
        df.loc[df["total_score"] >= threshold, "segment"] = label

    return df
