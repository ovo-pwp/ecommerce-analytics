# -*- coding: utf-8 -*-
"""
在线零售合成数据生成器
======================

生成与 UCL Online Retail 数据集特征匹配的样本数据。
输出到 data/sample_retail.csv（不会覆盖真实数据）。

特征匹配:
- 54,191 条交易记录
- 7% 缺失 CustomerID
- 5% 退货（负数量）
- 15% 批量购买
- 14 个国家，UK 占 73%
- 30 种真实产品（子集）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

n = 54191  # Match original dataset size

# Product catalog (subset of real Online Retail products)
products = [
    ('SET/7 BABUSHKA NESTING BOXES', 'Children\'s toys', 5.95),
    ('KNIGHTS CREAM CERAMICAL LANTERN', 'Home', 3.39),
    ('HAND WARMER RED', 'Home', 1.85),
    ('JUMPER ROPE SKIP ROPES', 'Sports', 2.73),
    ('RECORD TIN RED RATTLE', 'Baby', 1.99),
    ('PAINTING  TEA CUP SAUCER', 'Stationery', 4.95),
    ('WOODLAND ANIMALS BIRTHDAY CARD', 'Stationery', 1.25),
    ('RETRO CAKE STANDS SET THREE', 'Kitchen', 6.95),
    ('DOORMAT NEW ENGLAND', 'Home', 3.75),
    ('STRAWBERRY CERAMIC TRINKET POT', 'Home', 2.95),
    ('GLASS JUG MILK MEASURE 500ML', 'Kitchen', 2.95),
    ('POPPINS NIGHTMARE NIGHTLIGHT', 'Baby', 3.75),
    ('MINI METAL LANTERN TINTEDE', 'Home', 1.65),
    ('PAPER CHAIN KIT RETRORED', 'Party', 1.95),
    ('VICTORIAN SEWING KIT KNIT', 'Craft', 3.75),
    ('ASSORTED COLOUR BIRD BOX 12PK', 'Garden', 3.75),
    ('HEART WARMER BROWN', 'Baby', 1.65),
    ('REGENCY TEA CUP AND SAUCER', 'Kitchen', 4.95),
    ('IVORY PINK MUG', 'Kitchen', 1.49),
    ('PINK PETAL MUG', 'Kitchen', 1.49),
    ('SMALL BABOON WOODEN BEAD', 'Baby', 0.85),
    ('BIG BABOON WOODEN BEAD', 'Baby', 1.25),
    ('CAKE STAND SET THREE VINTAGE', 'Kitchen', 5.95),
    ('RED WOOLLY HOTTIE HEARTH RUG', 'Home', 4.95),
    ('PAINTING WOODLAND ANIMALS', 'Stationery', 3.75),
    ('METAL SIGN CHILDREN HOSPITAL', 'Home', 2.95),
    ('PINEAPPLE WHEELING BARROW', 'Garden', 5.95),
    ('JIGSAW BOX OF 20 CARROTS', 'Toys', 2.95),
    ('JIGSAW BOX OF 12 APPLES', 'Toys', 2.95),
    ('WOODEN CUTTING BOARD VINTAGE', 'Kitchen', 4.95),
]

# Time range: 2010-12-01 to 2011-12-09
start_date = datetime(2010, 12, 1)
end_date = datetime(2011, 12, 9, 12, 0, 0)
total_minutes = int((end_date - start_date).total_seconds() / 60)
date_offsets = np.random.randint(0, total_minutes, n)
dates = [start_date + timedelta(minutes=int(off)) for off in date_offsets]
dates.sort()

# Customer IDs: original dataset uses 12336-16790 (4372 customers)
customer_ids = np.arange(12336, 16791)

# Countries with realistic distribution
countries = ['United Kingdom', 'Germany', 'France', 'Netherlands',
             'Australia', 'Belgium', 'Spain', 'EIRE', 'Norway',
             'Sweden', 'Italy', 'Portugal', 'Switzerland', 'Japan']
country_weights = [0.73, 0.07, 0.05, 0.03, 0.03, 0.02, 0.02, 0.02,
                   0.01, 0.01, 0.01, 0.005, 0.005, 0.005]

# Stock codes: realistic 5-digit codes from original dataset
stock_codes_pool = [f'{np.random.randint(10000, 99999)}' for _ in range(len(products))]

# Quantities: mostly positive, some negative (returns)
quantities = []
for _ in range(n):
    r = random.random()
    if r < 0.05:
        quantities.append(-random.choice([1, 2, 3]))  # ~5% returns
    elif r < 0.15:
        quantities.append(random.choice([15, 20, 25, 50, 100]))  # bulk
    else:
        quantities.append(random.choice([1, 2, 3, 4, 5, 6, 8, 10, 12]))

records = []
inv_counter = 53649

for i in range(n):
    # ~7% missing customer IDs (matches original)
    if random.random() < 0.07:
        cust_id = None
    else:
        cust_id = int(random.choice(customer_ids))

    prod_idx = np.random.randint(0, len(products))
    prod_name, prod_cat, unit_price = products[prod_idx]

    qty = quantities[i]

    # InvoiceNo: normal invoices are numeric, credits (returns) start with 'C'
    if qty < 0:
        inv_num = f'C{inv_counter:06d}'
        inv_counter += 1
    else:
        inv_num = f'{inv_counter:06d}'
        inv_counter += 1

    price = round(unit_price * qty, 2)  # naturally negative for returns

    country = str(random.choices(countries, weights=country_weights, k=1)[0])

    # Format invoice date like original
    inv_date = dates[i].strftime('%m/%d/%Y %H:%M')

    stock_code = stock_codes_pool[prod_idx]

    records.append([inv_num, stock_code, prod_name, qty, inv_date, price, cust_id, country])

df = pd.DataFrame(records, columns=[
    'InvoiceNo', 'StockCode', 'Description', 'Quantity',
    'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country'
])

# Save to a distinct filename so it doesn't overwrite real data
output_path = r'data\sample_retail.csv'
df.to_csv(output_path, index=False)

print(f'Dataset saved: {len(df)} rows')
print(f'Customers: {df.CustomerID.dropna().nunique()}')
print(f'Date range: {df.InvoiceDate.min()} to {df.InvoiceDate.max()}')
print(f'Countries: {df.Country.nunique()}')
print(f'Missing CustomerIDs: {df.CustomerID.isna().sum()}')
print(f'Negative quantities: {(df.Quantity < 0).sum()}')
total_rev = df.loc[df['Quantity'] > 0, 'UnitPrice'].multiply(
    df.loc[df['Quantity'] > 0, 'Quantity']
).sum()
print(f'Total revenue (positive qty): {total_rev:.2f}')
print(f'\n注意: 此文件为 samples_retail.csv，不会覆盖真实数据文件。')
