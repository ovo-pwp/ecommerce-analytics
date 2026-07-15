# -*- coding: utf-8 -*-
"""src/segments.py 单元测试"""

import pytest
import pandas as pd
import numpy as np

from src.segments import segment_summary, revenue_contribution, export_report


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture
def sample_rfm():
    """模拟 RFM 客户数据"""
    return pd.DataFrame({
        "user_id": [1, 2, 3, 4, 5, 6],
        "recency": [5, 20, 100, 3, 50, 150],
        "frequency": [10, 5, 2, 15, 8, 1],
        "monetary": [5000, 2000, 300, 8000, 1500, 100],
        "segment": ["高价值", "发展", "挽留", "高价值", "一般", "挽留"],
    })


@pytest.fixture
def sample_transactions():
    """模拟交易明细"""
    return pd.DataFrame({
        "CustomerID": [1, 1, 2, 3, 4, 4, 5, 6],
        "TotalPrice": [2000, 3000, 2000, 300, 4000, 4000, 1500, 100],
    })


# ------------------------------------------------------------------ #
# segment_summary
# ------------------------------------------------------------------ #
class TestSegmentSummary:
    def test_returns_correct_columns(self, sample_rfm):
        result = segment_summary(sample_rfm)
        expected = {"segment", "user_count", "avg_recency", "avg_frequency",
                     "avg_monetary", "median_monetary", "share_pct", "arpu"}
        assert set(result.columns) == expected

    def test_user_count(self, sample_rfm):
        result = segment_summary(sample_rfm)
        counts = result.set_index("segment")["user_count"]
        assert counts["高价值"] == 2
        assert counts["挽留"] == 2
        assert counts["发展"] == 1
        assert counts["一般"] == 1

    def test_share_pct_sum(self, sample_rfm):
        result = segment_summary(sample_rfm)
        assert abs(result["share_pct"].sum() - 100.0) < 0.2  # rounding

    def test_arpu_positive(self, sample_rfm):
        result = segment_summary(sample_rfm)
        assert (result["arpu"] > 0).all()

    def test_empty_input(self):
        df = pd.DataFrame(columns=["user_id", "recency", "frequency", "monetary", "segment"])
        result = segment_summary(df)
        assert len(result) == 0


# ------------------------------------------------------------------ #
# revenue_contribution
# ------------------------------------------------------------------ #
class TestRevenueContribution:
    def test_returns_correct_columns(self, sample_rfm, sample_transactions):
        result = revenue_contribution(sample_rfm, sample_transactions)
        expected = {"客群", "营收贡献", "营收占比(%)"}
        assert set(result.columns) == expected

    def test_total_matches_monetary_sum(self, sample_rfm, sample_transactions):
        result = revenue_contribution(sample_rfm, sample_transactions)
        total = result["营收贡献"].sum()
        expected = sample_rfm["monetary"].sum()
        assert abs(total - expected) < 0.01

    def test_pct_sum_near_100(self, sample_rfm, sample_transactions):
        result = revenue_contribution(sample_rfm, sample_transactions)
        assert abs(result["营收占比(%)"].sum() - 100.0) < 0.2

    def test_sorted_descending(self, sample_rfm, sample_transactions):
        result = revenue_contribution(sample_rfm, sample_transactions)
        assert (result["营收贡献"].diff().dropna() <= 0).all()

    def test_high_value_has_highest_revenue(self, sample_rfm, sample_transactions):
        result = revenue_contribution(sample_rfm, sample_transactions)
        hv = result[result["客群"] == "高价值"]["营收贡献"].iloc[0]
        ret = result[result["客群"] == "挽留"]["营收贡献"].iloc[0]
        assert hv > ret  # 高价值客户应该比挽留客户贡献更多营收


# ------------------------------------------------------------------ #
# export_report
# ------------------------------------------------------------------ #
class TestExportReport:
    def test_writes_file(self, tmp_path, sample_rfm):
        result = segment_summary(sample_rfm)
        path = tmp_path / "test_output.csv"
        export_report(result, str(path))
        assert path.exists()

    def test_content_matches_input(self, tmp_path, sample_rfm):
        result = segment_summary(sample_rfm)
        path = tmp_path / "test_output.csv"
        export_report(result, str(path))
        loaded = pd.read_csv(path, encoding="utf-8-sig")
        pd.testing.assert_frame_equal(loaded, result, check_dtype=False)
