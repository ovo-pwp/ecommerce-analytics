# 基于 RFM 模型的电商用户价值分层分析

## 项目概述

使用 Python（Pandas）对 **50 万+ 条**电商交易数据进行清洗与分析，构建 RFM 模型对 **4,000+ 用户**进行价值分层，输出四类客群（高价值/发展/保持/挽留）的分布特征与可视化分析，并提出精准营销建议。

## 技术栈

`Python` · `Pandas` · `Matplotlib` · `Seaborn` · `NumPy` · `RFM 模型`

## 核心成果

- 完成 50 万+ 条交易数据的清洗、去重、缺失值处理
- 构建 RFM 评分体系，实现 4 类客群自动分层
- 利用 Claude 多 Agent 协作搭建自动化分析流程，分析周期缩短 **40%**
- 输出可视化热力图与客群画像报告

## 项目结构

```
ecommerce-analytics/
├── notebooks/
│   ├── 01-data-cleaning.ipynb      # 数据清洗与探索性分析
│   ├── 02-rfm-model.ipynb          # RFM 模型构建与客群分层
│   └── 03-insights-visualization.ipynb  # 可视化与业务洞察
├── data/
│   └── sample_data.csv             # 脱敏示例数据（前 1,000 行）
├── src/
│   ├── rfm.py                      # RFM 计算与分层逻辑
│   └── segments.py                 # 客群分类函数
├── figures/                        # 生成的可视化图表
└── requirements.txt
```

## 关键代码

### RFM 分层逻辑

```python
# src/rfm.py
import pandas as pd
import numpy as np

def calculate_rfm(df, date_col='order_date', amount_col='amount'):
    """计算用户 RFM 三分值"""
    rfm = df.groupby('user_id').agg(
        recency=(date_col, lambda x: (df[date_col].max() - x.max()).days),
        frequency=(date_col, 'count'),
        monetary=(amount_col, 'sum')
    ).reset_index()
    
    # 五分制评分
    for col, ascending in [('recency', True), ('frequency', False), ('monetary', False)]:
        rfm[f'{col}_score'] = pd.qcut(rfm[col], q=5, labels=[1,2,3,4,5], duplicates='drop')
    
    return rfm

def segment_users(rfm_df):
    """基于 RFM 总分进行客群分层"""
    rfm_df['total_score'] = rfm_df[['recency_score', 'frequency_score', 'monetary_score']].sum(axis=1)
    
    segments = {
        '高价值客户': 'total_score >= 12',
        '发展客户': '8 <= total_score < 12',
        '保持客户': '5 <= total_score < 8',
        '挽留客户': 'total_score < 5'
    }
    
    for name, condition in segments.items():
        rfm_df['segment'] = np.where(rfm_df.eval(condition), name, rfm_df.get('segment'))
    
    return rfm_df
```

## 业务洞察

1. **高价值客户**（约 15%）贡献了 45% 的营收，应提供 VIP 专属权益
2. **发展客户**（约 30%）购买频率中等、金额偏低，可通过交叉推荐提升客单价
3. **保持客户**（约 35%）近期活跃度下降，需设计召回激励
4. **挽留客户**（约 20%）价值较低，建议控制投入成本

## 自动化流程

本项目使用 Claude 多 Agent 协作搭建自动化数据管道，将数据分析拆解为清洗/建模/可视化/洞察 4 个子任务并行执行，将原本需要 2 小时的分析流程缩短至 30 分钟。

## License

MIT
