# 客群统计与摘要报告生成
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
        每行一个客群，包含人数、平均 R/F/M 值、占比。
    """
    summary = df.groupby("segment").agg(
        user_count=("user_id", "count"),
        avg_recency=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
    ).reset_index()

    total = len(df)
    summary["share_pct"] = (summary["user_count"] / total * 100).round(1)

    return summary


def export_report(summary_df: pd.DataFrame, output_path: str) -> None:
    """将客群摘要导出为 CSV。"""
    summary_df.to_csv(output_path, index=False, encoding="utf-8-sig")
