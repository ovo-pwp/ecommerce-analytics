# 电商用户价值分层分析 — RFM 模型

基于 RFM（Recency, Frequency, Monetary）模型对电商交易数据进行客户价值分层，输出多维度可视化分析报表。

## 项目概述

使用 Python（Pandas、Matplotlib、Seaborn）对 Online Retail 数据集进行清洗、建模与可视化，将客户分为 **高价值 / 发展 / 保持 / 挽留 / 一般** 五个客群，并通过 8 张图表呈现分析结果。

## 技术栈

`Python 3.9+` · `Pandas` · `NumPy` · `Matplotlib` · `Seaborn` · `RFM 模型`

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 生成样本数据（如尚无真实数据）
python generate_sample_data.py

# 运行完整分析流程
python visualize.py

# 自定义数据路径和分箱数
python visualize.py --data data/my_data.csv --n-bins 5
```

## 项目结构

```
ecommerce-analytics/
├── visualize.py                  # 主入口（命令行）
├── generate_sample_data.py       # 合成数据生成器
├── requirements.txt              # Python 依赖
├── src/
│   ├── __init__.py               # 包初始化
│   ├── config.py                 # 配置（字体、颜色、路径）
│   ├── data_loader.py            # 数据加载、清洗、RFM 构建
│   ├── charts.py                 # 8 张可视化图表
│   ├── rfm.py                    # RFM 核心计算（通用库）
│   └── segments.py               # 客群统计与营收贡献
├── data/
│   └── sample_retail.csv         # 样本数据（generate_sample_data.py 生成）
├── figures/                      # 输出图表与 CSV
│   ├── 01_segment_distribution.png
│   ├── 02_revenue_contribution.png
│   ├── 03_monthly_trend.png
│   ├── 04_rfm_scatter.png
│   ├── 05_radar_charts.png
│   ├── 06_monetary_analysis.png
│   ├── 07_country_ranking.png
│   ├── 08_dashboard.png
│   ├── rfm_segments.csv          # 客户分层明细
│   ├── segment_insights.csv      # 客群统计摘要
│   └── data_quality_report.md    # 数据质量报告
└── notebooks/                    # 探索性分析 Jupyter 笔记本
    ├── 01-data-cleaning.ipynb
    ├── 02-rfm-model.ipynb
    └── 03-insights-visualization.ipynb
```

## 分析方法

### RFM 模型

| 维度 | 含义 | 计算方式 |
|------|------|----------|
| **R (Recency)** | 最近一次消费距今天数 | `快照日 - 最后下单日` |
| **F (Frequency)** | 消费频次 | 订单数量 |
| **M (Monetary)** | 消费总额 | 所有订单金额之和 |

每个维度按四分位（quartile）打分 1-4 分：
- R 越小越好（越近分数越高）
- F / M 越大越好（消费越多分数越高）

### 客群分层规则

| 客群 | 条件 | 业务含义 |
|------|------|----------|
| **高价值** | R≥3 且 F≥3 且 M≥3 | 近期活跃、高频、高消费的优质客户 |
| **发展** | R≥3 且 F≥2 | 近期活跃且有一定频次，有上升空间 |
| **保持** | R≤2 且 F≥3 且 M≥3 | 曾经的高频高消费客户，近期不活跃 |
| **挽留** | R≤2 且 F≤2 且 M≤2 | 各方面表现均不佳，需关注流失风险 |
| **一般** | 其他 | 特征不突出的混合客群 |

### 营收贡献计算

营收贡献基于客户级别的 **Monetary 值** 计算，而非原始交易明细的累加，确保每个客户的贡献只计算一次。

## 输出结果

运行 `python visualize.py` 后会在 `figures/` 目录生成：

- **8 张 PNG 图表**（150 DPI）
- **rfm_segments.csv** — 每位客户的 RFM 指标、打分和客群标签
- **segment_insights.csv** — 各客群的客户数、占比、营收贡献
- **data_quality_report.md** — 数据质量诊断报告

## 依赖

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.12
scipy>=1.10
```

## License

MIT
