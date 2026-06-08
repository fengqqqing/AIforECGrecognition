# CSV 快速训练数据加载模块（2000 点窗口，12 分类）
# 职责：从已处理的 CSV 文件中读取训练/测试数据，reshape 为 (N, 2000, 1) 格式。
# 数据来源：artifacts/training/ecg/processed_data/ 下的 train.csv / test.csv。
# 注意：此模块与部署侧模型契约的窗口长度（2000 点）一致，
#       是当前部署模型训练所使用的数据加载方式。

import pandas as pd
import numpy as np
from paths import PROCESSED_DATA_DIR

# 加载训练数据集并进行预处理
def train_loadData_():
    """加载训练和验证数据：train.csv 用于训练，test.csv 用于验证。返回 (x_train, y_train, x_val, y_val)。"""
    train = pd.read_csv(PROCESSED_DATA_DIR / 'train.csv', header=None)
    val = pd.read_csv(PROCESSED_DATA_DIR / 'test.csv', header=None)  # 注意：此处用 test.csv 做验证
    x_train = train.iloc[:, :-1].values
    x_train = x_train.reshape(-1, 2000, 1)
    y_train = train.iloc[:, -1].values
    x_val = val.iloc[:, :-1].values
    x_val = x_val.reshape(-1, 2000, 1)
    y_val = val.iloc[:, -1].values
    return x_train, y_train, x_val, y_val


# 加载测试数据集并进行预处理
def test_loadData_():
    """加载测试数据：从 test.csv 读取，返回 (x_test, y_test)。"""
    test = pd.read_csv(PROCESSED_DATA_DIR / 'test.csv', header=None)
    x_test = test.iloc[:, :-1].values
    x_test = x_test.reshape(-1, 2000, 1)
    y_test = test.iloc[:, -1].values
    return x_test, y_test

