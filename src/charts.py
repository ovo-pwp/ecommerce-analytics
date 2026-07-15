# -*- coding: utf-8 -*-
"""
可视化图表生成
==============

每张图一个独立函数，返回 matplotlib Figure 对象。
"""

import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from math import pi

from .config import (
    SEGMENT_COLORS,
    SEGMENT_ORDER,
    COLOR_PALETTE,
    FIGURE_DPI,
    TITLE_SIZE,
    LABEL_SIZE,
    TICK_SIZE,
    OUTPUT_DIR,
    ensure_output_dir,
)

logger = logging.getLogger(__name__)


def save_fig(fig, filename):
    """统一保存图片。"""
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("[图] 已保存: figures/%s", filename)


import os


# ====================================================================
# 图 1: 用户分层分布（柱状图）
# ====================================================================
def plot_segment_distribution(rfm):
    segment_counts = rfm["Segment"].value_counts()
    total = segment_counts.sum()

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.bar(
        segment_counts.index,
        segment_counts.values,
        color=[SEGMENT_COLORS.get(s, "#888") for s in segment_counts.index],
        edgecolor="white",
        linewidth=1.5,
    )

    for bar, val in zip(bars, segment_counts.values):
        pct = val / total * 100
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 15,
            "{}\n({:.1f}%)".format(val, pct),
            ha="center",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )

    ax.set_title("客户价值分层分布", fontsize=TITLE_SIZE, fontweight="bold", pad=20)
    ax.set_xlabel("客户类型", fontsize=LABEL_SIZE)
    ax.set_ylabel("客户数量", fontsize=LABEL_SIZE)
    ax.set_ylim(0, max(segment_counts.values) * 1.15)
    ax.tick_params(labelsize=TICK_SIZE)
    plt.tight_layout()

    save_fig(fig, "01_segment_distribution.png")
    return fig


# ====================================================================
# 图 2: 各层营收贡献（环形图）
# ====================================================================
def plot_revenue_contribution(rfm):
    seg_revenue = rfm.groupby("Segment")["Monetary"].sum().sort_values(ascending=False)
    colors = [SEGMENT_COLORS.get(s, "#888") for s in seg_revenue.index]

    fig, ax = plt.subplots(figsize=(10, 7))
    wedges, texts, autotexts = ax.pie(
        seg_revenue.values,
        labels=seg_revenue.index,
        autopct=lambda pct: "{:.1f}%".format(pct),
        explode=[0.02] * len(seg_revenue),
        colors=colors,
        startangle=90,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
    )
    for text in texts:
        text.set_fontsize(12)
    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight("bold")

    ax.set_title("各客群营收贡献占比", fontsize=TITLE_SIZE, fontweight="bold", pad=20)
    plt.tight_layout()

    save_fig(fig, "02_revenue_contribution.png")
    return fig


# ====================================================================
# 图 3: 月度消费趋势
# ====================================================================
def plot_monthly_trend(df):
    df_copy = df.copy()
    df_copy["Month"] = df_copy["InvoiceDate"].dt.to_period("M")
    monthly_revenue = df_copy.groupby("Month")["TotalPrice"].sum()
    monthly_orders = df_copy.groupby("Month")["InvoiceNo"].count()

    fig, ax1 = plt.subplots(figsize=(12, 8))

    ax1.set_xlabel("月份", fontsize=LABEL_SIZE)
    ax1.set_ylabel("月度营收", fontsize=LABEL_SIZE, color="#2E86AB")
    bars = ax1.bar(
        monthly_revenue.index.astype(str),
        monthly_revenue.values,
        color="#2E86AB",
        alpha=0.7,
        width=0.6,
        label="营收",
    )
    ax1.tick_params(axis="y", labelcolor="#2E86AB")
    ax1.set_xticks(range(len(monthly_revenue)))
    ax1.set_xticklabels(monthly_revenue.index.astype(str), rotation=45, ha="right")

    ax2 = ax1.twinx()
    ax2.plot(
        monthly_orders.index.astype(str),
        monthly_orders.values,
        color="#C73E1D",
        marker="o",
        linewidth=2,
        markersize=6,
        label="订单量",
    )
    ax2.set_ylabel("订单量", fontsize=LABEL_SIZE, color="#C73E1D")
    ax2.tick_params(axis="y", labelcolor="#C73E1D")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=11)

    ax1.set_title("月度营收与订单量趋势", fontsize=TITLE_SIZE, fontweight="bold", pad=20)
    plt.tight_layout()

    save_fig(fig, "03_monthly_trend.png")
    return fig


# ====================================================================
# 图 4: RFM 二维散点图（R vs M，按分层着色）
# ====================================================================
def plot_rfm_scatter(rfm):
    fig, ax = plt.subplots(figsize=(12, 8))

    for seg in SEGMENT_ORDER:
        if seg not in rfm["Segment"].values:
            continue
        color = SEGMENT_COLORS[seg]
        subset = rfm[rfm["Segment"] == seg]
        ax.scatter(
            subset["Recency"], subset["Monetary"],
            c=color, alpha=0.5, s=25, label=seg, edgecolors="none",
        )

    ax.set_xlabel("Recency（距上次消费天数）", fontsize=LABEL_SIZE)
    ax.set_ylabel("Monetary（消费总额）", fontsize=LABEL_SIZE)
    ax.set_title("RFM 散点图（R vs M，按分层着色）", fontsize=TITLE_SIZE, fontweight="bold", pad=20)
    ax.legend(fontsize=11, loc="best", framealpha=0.9)
    plt.tight_layout()

    save_fig(fig, "04_rfm_scatter.png")
    return fig


# ====================================================================
# 图 5: 客群画像雷达图
# ====================================================================
def plot_radar_charts(rfm):
    segments = [s for s in SEGMENT_ORDER if s in rfm["Segment"].values]
    r_min, r_max = rfm["Recency"].min(), rfm["Recency"].max()
    f_min, f_max = rfm["Frequency"].min(), rfm["Frequency"].max()
    m_min, m_max = rfm["Monetary"].min(), rfm["Monetary"].max()

    fig, axes = plt.subplots(
        1, len(segments),
        figsize=(28, 7),
        subplot_kw={"polar": True},
    )
    if len(segments) == 1:
        axes = [axes]

    for idx, seg_name in enumerate(segments):
        ax = axes[idx]
        seg_data = rfm[rfm["Segment"] == seg_name]

        r_norm = 1 - (seg_data["Recency"].mean() - r_min) / (r_max - r_min + 1)
        f_norm = (seg_data["Frequency"].mean() - f_min) / (f_max - f_min + 1)
        m_norm = (seg_data["Monetary"].mean() - m_min) / (m_max - m_min + 1)

        categories = ["Recency", "Frequency", "Monetary"]
        n_cat = len(categories)
        angles = [n / float(n_cat) * 2 * pi for n in range(n_cat)]
        values = [r_norm, f_norm, m_norm] + [r_norm]
        angles_closed = angles + [angles[0]]

        color = SEGMENT_COLORS.get(seg_name, "#888888")
        ax.plot(angles_closed, values, "o-", linewidth=2.5, color=color, markersize=8)
        ax.fill(angles_closed, values, color=color, alpha=0.15)

        ax.set_xticks(angles)
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 1)
        ax.set_title(seg_name, fontsize=14, fontweight="bold", color=color, pad=20)

    plt.suptitle("各客群特征对比（归一化雷达图）", fontsize=TITLE_SIZE, fontweight="bold", y=1.02)
    plt.tight_layout()

    save_fig(fig, "05_radar_charts.png")
    return fig


# ====================================================================
# 图 6: 消费金额分布直方图 + 箱线图
# ====================================================================
def plot_monetary_analysis(rfm):
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))

    # 左侧：整体消费金额分布
    upper = rfm["Monetary"].quantile(0.95)
    axes[0].hist(rfm["Monetary"], bins=50, color="#2E86AB", alpha=0.8, edgecolor="white", linewidth=0.5)
    axes[0].axvline(
        rfm["Monetary"].median(),
        color="#C73E1D",
        linestyle="--",
        linewidth=2,
        label="中位数 {:.0f}".format(rfm["Monetary"].median()),
    )
    axes[0].set_xlabel("消费总额", fontsize=LABEL_SIZE)
    axes[0].set_ylabel("客户数量", fontsize=LABEL_SIZE)
    axes[0].set_title("客户消费金额分布", fontsize=15, fontweight="bold")
    axes[0].legend(fontsize=11)
    axes[0].set_xlim(0, upper)

    # 右侧：各分层消费金额箱线图
    segments = [s for s in SEGMENT_ORDER if s in rfm["Segment"].values]
    box_data = [rfm[rfm["Segment"] == seg]["Monetary"].dropna().values for seg in segments]
    bp = axes[1].boxplot(
        box_data,
        tick_labels=segments,
        patch_artist=True,
        medianprops=dict(color="white", linewidth=2),
    )
    for patch, color in zip(bp["boxes"], [SEGMENT_COLORS.get(s, "#888") for s in segments]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    axes[1].set_xlabel("客户类型", fontsize=LABEL_SIZE)
    axes[1].set_ylabel("消费总额", fontsize=LABEL_SIZE)
    axes[1].set_title("各客群消费金额分布", fontsize=15, fontweight="bold")
    axes[1].tick_params(labelsize=TICK_SIZE)
    axes[1].set_ylim(0, upper)

    plt.suptitle("消费金额分析", fontsize=TITLE_SIZE, fontweight="bold", y=1.02)
    plt.tight_layout()

    save_fig(fig, "06_monetary_analysis.png")
    return fig


# ====================================================================
# 图 7: 国家/地区消费分布
# ====================================================================
def plot_country_ranking(df):
    country_revenue = df.groupby("Country")["TotalPrice"].sum().nlargest(10)

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(
        country_revenue.index,
        country_revenue.values,
        color="#2E86AB",
        alpha=0.8,
        edgecolor="white",
    )
    for bar, val in zip(bars, country_revenue.values):
        ax.text(
            val + country_revenue.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            "{:,.0f}".format(val),
            va="center",
            fontsize=10,
        )

    ax.set_xlabel("总营收", fontsize=LABEL_SIZE)
    ax.set_ylabel("国家/地区", fontsize=LABEL_SIZE)
    ax.set_title("Top 10 国家/地区消费额排名", fontsize=TITLE_SIZE, fontweight="bold", pad=20)
    ax.tick_params(labelsize=TICK_SIZE)
    plt.tight_layout()

    save_fig(fig, "07_country_ranking.png")
    return fig


# ====================================================================
# 图 8: 综合仪表盘（一页汇总）
# ====================================================================
def plot_dashboard(df, rfm):
    from .segments import segment_summary, revenue_contribution

    fig = plt.figure(figsize=(20, 14))
    fig.suptitle("电商客户价值分析 - 综合看板", fontsize=24, fontweight="bold", y=0.98)

    gs = GridSpec(2, 6, figure=fig, hspace=0.3, wspace=0.25)

    total_customers = len(rfm)
    total_revenue = df["TotalPrice"].sum()
    avg_order_value = df["TotalPrice"].mean()
    top_segment = rfm["Segment"].value_counts().index[0]
    top_pct = (rfm["Segment"].value_counts().iloc[0] / total_customers) * 100

    # --- KPI 卡片 ---
    # 卡片1: 总客户数
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis("off")
    ax1.text(0.5, 0.7, "总客户数", ha="center", fontsize=13, color="#555")
    ax1.text(0.5, 0.3, "{:,}".format(total_customers), ha="center", fontsize=28, fontweight="bold", color="#2E86AB")
    ax1.text(0.5, 0.05, "名活跃客户", ha="center", fontsize=11, color="#888")

    # 卡片2: 总营收
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis("off")
    ax2.text(0.5, 0.7, "总营收", ha="center", fontsize=13, color="#555")
    ax2.text(0.5, 0.3, "{:,.0f}".format(total_revenue), ha="center", fontsize=28, fontweight="bold", color="#6A994E")
    ax2.text(0.5, 0.05, "2010-2011年度", ha="center", fontsize=11, color="#888")

    # 卡片3: 客单价
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis("off")
    ax3.text(0.5, 0.7, "客单价", ha="center", fontsize=13, color="#555")
    ax3.text(0.5, 0.3, "{:.2f}".format(avg_order_value), ha="center", fontsize=28, fontweight="bold", color="#F18F01")
    ax3.text(0.5, 0.05, "平均每单", ha="center", fontsize=11, color="#888")

    # 卡片4: 最大客群占比
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.axis("off")
    ax4.text(0.5, 0.7, "最大客群", ha="center", fontsize=13, color="#555")
    ax4.text(0.5, 0.3, "{:.1f}%".format(top_pct), ha="center", fontsize=28, fontweight="bold", color="#C73E1D")
    ax4.text(0.5, 0.05, "{}".format(top_segment), ha="center", fontsize=11, color="#888")

    # 迷你饼图
    ax5 = fig.add_subplot(gs[0, 4:6])
    segments = [s for s in SEGMENT_ORDER if s in rfm["Segment"].values]
    seg_counts = rfm["Segment"].value_counts()[segments]
    ax5.pie(
        seg_counts.values, labels=seg_counts.index, autopct="%1.0f%%",
        colors=[SEGMENT_COLORS[s] for s in seg_counts.index],
        startangle=90, textprops={"fontsize": 10},
    )
    ax5.set_title("客户分层占比", fontsize=14, fontweight="bold")

    # 月度趋势
    ax6 = fig.add_subplot(gs[1, 0:2])
    monthly = df.groupby(df["InvoiceDate"].dt.to_period("M"))["TotalPrice"].sum()
    ax6.plot(range(len(monthly)), monthly.values, color="#2E86AB", linewidth=2, marker="o", markersize=4)
    ax6.fill_between(range(len(monthly)), monthly.values, alpha=0.15, color="#2E86AB")
    ax6.set_title("月度营收趋势", fontsize=14, fontweight="bold")
    ax6.set_xticks([])
    ax6.tick_params(labelsize=9)

    # 各层平均 RFM（归一化）
    ax7 = fig.add_subplot(gs[1, 2:4])
    segment_rfm_avg = rfm.groupby("Segment")[["Recency", "Frequency", "Monetary"]].mean()
    for i, col in enumerate(["Recency", "Frequency", "Monetary"]):
        norm = (
            segment_rfm_avg[col] - segment_rfm_avg[col].min()
        ) / (segment_rfm_avg[col].max() - segment_rfm_avg[col].min() + 1)
        ax7.barh(segment_rfm_avg.index, norm.values, color=COLOR_PALETTE[i % len(COLOR_PALETTE)], alpha=0.8, label=col)
    ax7.set_title("各层平均RFM（归一化）", fontsize=14, fontweight="bold")
    ax7.legend(fontsize=9)

    # 热销产品 Top 10
    ax8 = fig.add_subplot(gs[1, 4:6])
    top_products = df.groupby("Description")["TotalPrice"].sum().nlargest(10)
    ax8.barh(range(len(top_products)), top_products.values, color="#A23B72", alpha=0.8)
    ax8.set_yticks(range(len(top_products)))
    short_names = [name[:20] + ".." if len(name) > 20 else name for name in top_products.index]
    ax8.set_yticklabels(short_names, fontsize=9)
    ax8.set_xlabel("总营收", fontsize=11)
    ax8.set_title("热销产品 Top 10", fontsize=14, fontweight="bold")
    ax8.invert_yaxis()

    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, "08_dashboard.png")
    fig.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close(fig)
    logger.info("[图] 已保存: figures/08_dashboard.png")

    return fig


# ====================================================================
# 导出结果
# ====================================================================
def export_results(rfm, df):
    """导出客户分层 CSV 和业务洞察 CSV。"""
    ensure_output_dir()

    # 客户分层结果
    rfm_export = rfm[["Recency", "Frequency", "Monetary", "R_Score", "F_Score", "M_Score", "Segment"]].copy()
    rfm_export.insert(0, "客户ID", rfm_export.index)
    rfm_export.to_csv(os.path.join(OUTPUT_DIR, "rfm_segments.csv"), index=False, encoding="utf-8-sig")
    logger.info("[导出] 客户分层结果: %d 条", len(rfm_export))

    # 业务洞察摘要
    segment_counts = rfm["Segment"].value_counts()
    total_customers = len(rfm)
    total_revenue = df["TotalPrice"].sum()
    seg_revenue = rfm.groupby("Segment")["Monetary"].sum().sort_values(ascending=False)

    insight_df = pd.DataFrame({
        "客群": seg_revenue.index,
        "客户数": [segment_counts.get(s, 0) for s in seg_revenue.index],
        "占比(%)": ([segment_counts.get(s, 0) / total_customers * 100 for s in seg_revenue.index]),
        "营收贡献": seg_revenue.values,
        "营收占比(%)": (seg_revenue.values / total_revenue * 100).round(1),
    })
    insight_df["占比(%)"] = insight_df["占比(%)"].round(1)

    insight_df.to_csv(os.path.join(OUTPUT_DIR, "segment_insights.csv"), index=False, encoding="utf-8-sig")
    logger.info("[导出] 业务洞察摘要: %d 个客群", len(insight_df))

    return insight_df
