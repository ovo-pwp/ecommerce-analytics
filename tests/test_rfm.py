# -*- coding: utf-8 -*-
"""src/rfm.py 单元测试"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.rfm import calculate_rfm, score_rfm, assign_segment


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture
def sample_trades():
    """最小可用交易数据集: 3 用户 × 多笔订单"""
    return pd.DataFrame({
        "user_id": ["A", "A", "A", "B", "B", "C"],
        "order_date": pd.to_datetime([
            "2024-01-01", "2024-03-01", "2024-06-01",
            "2024-02-01", "2024-04-01",
            "2024-01-15",
        ]),
        "amount": [100.0, 200.0, 300.0, 50.0, 150.0, 80.0],
    })


@pytest.fixture
def rfm_raw(sample_trades):
    """calculate_rfm 的输出"""
    return calculate_rfm(sample_trades)


# ------------------------------------------------------------------ #
# calculate_rfm
# ------------------------------------------------------------------ #
class TestCalculateRfm:
    def test_returns_correct_columns(self, rfm_raw):
        assert set(rfm_raw.columns) == {"user_id", "recency", "frequency", "monetary"}

    def test_user_a_frequency(self, rfm_raw):
        row = rfm_raw[rfm_raw["user_id"] == "A"].iloc[0]
        assert row["frequency"] == 3

    def test_user_c_frequency(self, rfm_raw):
        row = rfm_raw[rfm_raw["user_id"] == "C"].iloc[0]
        assert row["frequency"] == 1

    def test_user_a_monetary(self, rfm_raw):
        row = rfm_raw[rfm_raw["user_id"] == "A"].iloc[0]
        assert row["monetary"] == 600.0

    def test_custom_date_col(self, sample_trades):
        df = sample_trades.rename(columns={"order_date": "date"})
        result = calculate_rfm(df, date_col="date")
        assert "recency" in result.columns

    def test_custom_amount_col(self, sample_trades):
        df = sample_trades.rename(columns={"amount": "price"})
        result = calculate_rfm(df, amount_col="price")
        assert "monetary" in result.columns

    def test_snapshot_date_overrides_max(self, sample_trades):
        snap = datetime(2024, 12, 31)
        result = calculate_rfm(sample_trades, snapshot_date=snap)
        # User C's last order is 2024-01-15
        row = result[result["user_id"] == "C"].iloc[0]
        # (2024-12-31 - 2024-01-15).days = 351
        assert row["recency"] == 351

    def test_empty_input(self):
        df = pd.DataFrame({"user_id": [], "order_date": [], "amount": []})
        result = calculate_rfm(df)
        assert len(result) == 0

    def test_single_user(self, sample_trades):
        sub = sample_trades[sample_trades["user_id"] == "A"]
        result = calculate_rfm(sub)
        assert len(result) == 1
        assert result.iloc[0]["user_id"] == "A"


# ------------------------------------------------------------------ #
# score_rfm
# ------------------------------------------------------------------ #
class TestScoreRfm:
    def test_returns_score_columns(self, rfm_raw):
        scored = score_rfm(rfm_raw, n_bins=5)
        assert set(scored.columns) == {"user_id", "recency", "frequency", "monetary",
                                        "R_score", "F_score", "M_score"}

    def test_four_bins_range(self, rfm_raw):
        scored = score_rfm(rfm_raw, n_bins=4)
        for col in ("R_score", "F_score", "M_score"):
            assert scored[col].between(1, 4).all()

    def test_r_score_direction(self):
        """R 越小（越近）→ 分数越高"""
        df = pd.DataFrame({
            "user_id": ["X", "Y", "Z"],
            "recency": [10, 50, 100],
            "frequency": [5, 6, 7],
            "monetary": [100, 200, 300],
        })
        scored = score_rfm(df, n_bins=3)
        assert scored.loc[0, "R_score"] >= scored.loc[1, "R_score"]
        assert scored.loc[1, "R_score"] >= scored.loc[2, "R_score"]

    def test_f_score_direction(self):
        """F 越大 → 分数越高"""
        df = pd.DataFrame({
            "user_id": ["X", "Y", "Z"],
            "recency": [10, 20, 30],
            "frequency": [20, 10, 5],
            "monetary": [100, 200, 300],
        })
        scored = score_rfm(df, n_bins=3)
        assert scored.loc[0, "F_score"] >= scored.loc[1, "F_score"]
        assert scored.loc[1, "F_score"] >= scored.loc[2, "F_score"]

    def test_monetary_zero_handling(self):
        """monetary=0 时 clip(lower=1e-9) 不应报错"""
        df = pd.DataFrame({
            "user_id": ["X", "Y", "Z"],
            "recency": [10, 20, 30],
            "frequency": [5, 6, 7],
            "monetary": [0.0, 100.0, 200.0],
        })
        scored = score_rfm(df, n_bins=3)
        assert scored["M_score"].notna().all()


# ------------------------------------------------------------------ #
# assign_segment
# ------------------------------------------------------------------ #
class TestAssignSegment:
    def test_all_scores_high(self):
        """总分最高 → 高价值客户"""
        df = pd.DataFrame({
            "R_score": [5], "F_score": [5], "M_score": [5],
        })
        result = assign_segment(df, n_bins=5)
        assert result.iloc[0]["segment"] == "高价值客户"

    def test_all_scores_low(self):
        """总分最低 → 挽留客户"""
        df = pd.DataFrame({
            "R_score": [1], "F_score": [1], "M_score": [1],
        })
        result = assign_segment(df, n_bins=5)
        assert result.iloc[0]["segment"] == "挽留客户"

    def test_mid_score_development(self):
        """中等总分 → 发展客户"""
        df = pd.DataFrame({
            "R_score": [3], "F_score": [3], "M_score": [3],  # total=9, max=15
        })
        result = assign_segment(df, n_bins=5)
        # 9 >= 10 (2/3*15=10)? No. 9 >= 7 (1/2*15=7)? Yes → 发展
        assert result.iloc[0]["segment"] == "发展客户"

    def test_dynamic_thresholds_4bins(self):
        """n_bins=4 时阈值应自动适配（max=12）"""
        df = pd.DataFrame({
            "R_score": [4], "F_score": [4], "M_score": [4],  # total=12
        })
        result = assign_segment(df, n_bins=4)
        assert result.iloc[0]["segment"] == "高价值客户"

    def test_dynamic_thresholds_3bins(self):
        """n_bins=3 时阈值应自动适配（max=9）"""
        df = pd.DataFrame({
            "R_score": [3], "F_score": [3], "M_score": [3],  # total=9
        })
        result = assign_segment(df, n_bins=3)
        assert result.iloc[0]["segment"] == "高价值客户"

    def test_returns_total_score_column(self, rfm_raw):
        scored = score_rfm(rfm_raw, n_bins=4)
        result = assign_segment(scored, n_bins=4)
        assert "total_score" in result.columns
        assert (result["total_score"] == result[["R_score", "F_score", "M_score"]].sum(axis=1)).all()

    def test_all_segments_assigned(self, rfm_raw):
        scored = score_rfm(rfm_raw, n_bins=4)
        result = assign_segment(scored, n_bins=4)
        assert result["segment"].notna().all()
        assert result["segment"].isin(
            ["高价值客户", "发展客户", "保持客户", "挽留客户"]
        ).all()
