import pandas as pd
import numpy as np
from paths import PROCESSED_DATA_DIR

# 加载训练数据集并进行预处理
def train_loadData_():
    train = pd.read_csv(PROCESSED_DATA_DIR / 'train.csv', header=None)
    val = pd.read_csv(PROCESSED_DATA_DIR / 'test.csv', header=None)
    x_train = train.iloc[:, :-1].values
    x_train = x_train.reshape(-1, 2000, 1)
    y_train = train.iloc[:, -1].values
    x_val = val.iloc[:, :-1].values
    x_val = x_val.reshape(-1, 2000, 1)
    y_val = val.iloc[:, -1].values
    return x_train, y_train, x_val, y_val


# 加载测试数据集并进行预处理
def test_loadData_():
    test = pd.read_csv(PROCESSED_DATA_DIR / 'test.csv', header=None)
    x_test = test.iloc[:, :-1].values
    x_test = x_test.reshape(-1, 2000, 1)
    y_test = test.iloc[:, -1].values
    return x_test, y_test

