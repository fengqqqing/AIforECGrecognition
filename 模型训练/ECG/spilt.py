# 数据集划分脚本
# 职责：读取 generate_data.py 生成的 data.csv，随机打乱后按 7:1:2 比例
#       划分为训练集、验证集和测试集，保存为 train.csv / val.csv / test.csv。
# 数据来源：artifacts/training/ecg/processed_data/data.csv
# 注意：保存语句已注释，需手动取消注释后运行。

#     # 打乱数据集并划分训练集、验证集和测试集


# 导入必要的科学计算和数据处理库
import numpy as np
import pandas as pd
from paths import PROCESSED_DATA_DIR

# 1. 读取原始数据集
# header=None 表示该CSV文件没有列名，数据从第一行开始
data = pd.read_csv(PROCESSED_DATA_DIR / 'data.csv', header=None)

# 2. 数据集随机打乱 (关键步骤)
# frac=1 表示抽取100%的数据，即对所有数据进行随机重排
# 这一步是为了打破数据可能存在的顺序相关性，保证划分的子集分布均匀
data = data.sample(frac=1)

# 3. 计算数据的全局最大值和最小值 (用于检查数据范围或后续归一化)
# iloc[:, :-1] 表示选取除最后一列(通常是标签)之外的所有特征列
# axis=(0, 1) 表示在整个矩阵范围内寻找极值
min_val = np.min(data.iloc[:, :-1].values, axis=(0, 1))
max_val = np.max(data.iloc[:, :-1].values, axis=(0, 1))
print(f"数据最小值: {min_val}, 数据最大值: {max_val}")

# 4. 数据集切分 (Split)
# 按照 7:1:2 的比例进行切分

# 训练集: 取前 70% 的数据
train = data.iloc[:int(len(data) * 0.7)]

# 验证集: 取 70% 到 80% 之间的数据 (共 10%)
val = data.iloc[int(len(data) * 0.7): int(len(data) * 0.8)]

# 测试集: 取 80% 之后的所有数据 (共 20%)
test = data.iloc[int(len(data) * 0.8):]

# 5. 保存划分后的数据集
# train.to_csv(PROCESSED_DATA_DIR / 'train.csv', index=False, header=False)
# val.to_csv(PROCESSED_DATA_DIR / 'val.csv', index=False, header=False)
# test.to_csv(PROCESSED_DATA_DIR / 'test.csv', index=False, header=False)

