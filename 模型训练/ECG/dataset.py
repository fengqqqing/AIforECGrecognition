import numpy as np
import wfdb
from draw import plot_signal
from filter import denoise
from collections import Counter
from paths import RAW_DATA_DIR


# 读取心电数据和对应标签,并对数据进行小波去噪
def getDataSet(number, X_data, Y_data):
    ecgClassSet = ['N', 'A', 'V', 'L', 'R']                                     # 五种心电类型
    print("正在读取 " + number + " 号心电数据...")

    # 绘制数字信号前1000个数据点
    # record = wfdb.rdrecord(str(RAW_DATA_DIR / number), sampfrom=0, sampto=1000, physical=False, channel_names=['MLII'])
    # signal = record.d_signal[0:1000]
    # plot_signal(signal)

    record = wfdb.rdrecord(str(RAW_DATA_DIR / number), channel_names=['MLII'])  # 读取数据
    data = record.p_signal.flatten()                                            # 获取原始信号(650000个数据点)
    # plot_signal(data[0:1000])                                                 # 绘制原始信号前1000个数据点
    rdata = denoise(data=data)                                                  # 小波去噪

    annotation = wfdb.rdann(str(RAW_DATA_DIR / number), 'atr')                  # 读取标签
    Rlocation = annotation.sample                                               # R波位置
    Rclass = annotation.symbol                                                  # R波标签
    # counter = Counter(Rclass)                                                   # 统计心电类型数量
    # print(counter)

    start = 10
    end = 5
    i = start
    j = len(annotation.symbol) - end                                            # 去掉前后的不稳定数据
    while i < j:
        try:
            lable = ecgClassSet.index(Rclass[i])                                # 选取NAVLR五种心电类型，转换为01234
            x_train = rdata[Rlocation[i] - 100:Rlocation[i] + 200]              # 截取R波前100个数据点，后200个数据点
            X_data.append(x_train)
            Y_data.append(lable)
            i += 1
        except ValueError:
            i += 1
    return


# 加载训练数据集并进行预处理
def train_loadData():
    numberSet = ['100', '101', '103', '106', '107', '108', '109', '111', '112', '113', '114', '115',
                 '116', '117', '119', '122', '123', '124', '200', '201', '203', '205', '210', '212',
                 '213', '214', '215', '217', '219', '221', '222', '223', '228', '231', '232', '233']
    dataSet = []
    lableSet = []
    for n in numberSet:
        getDataSet(n, dataSet, lableSet)                                # 读取心电数据和对应标签
    dataSet = np.array(dataSet).reshape(-1, 300)                        # 数据集
    lableSet = np.array(lableSet).reshape(-1, 1)                        # 标签集
    train_ds = np.hstack((dataSet, lableSet))                           # 数据集和标签集合并
    np.random.shuffle(train_ds)                                         # 打乱顺序

    X = train_ds[:, :300].reshape(-1, 300, 1)                           # 全部数据集数据
    Y = train_ds[:, 300]                                                # 全部数据标签
    shuffle_index = np.random.permutation(len(X))                       # 打乱顺序
    val_length = int(0.1 * len(shuffle_index))                          # 验证集数量
    val_index = shuffle_index[:val_length]
    train_index = shuffle_index[val_length:]
    X_val, Y_val = X[val_index], Y[val_index]                           # 验证集数据和标签
    X_train, Y_train = X[train_index], Y[train_index]                   # 训练集数据和标签
    return X_train, Y_train, X_val, Y_val


# 加载测试数据集并进行预处理
def test_loadData():
    numberSet = ['105', '121', '202', '208', '220', '230', '234']
    dataSet = []
    lableSet = []
    for n in numberSet:
        getDataSet(n, dataSet, lableSet)                                # 读取心电数据和对应标签
    dataSet = np.array(dataSet).reshape(-1, 300)                        # 数据集
    lableSet = np.array(lableSet).reshape(-1, 1)                        # 标签集
    train_ds = np.hstack((dataSet, lableSet))                           # 数据集和标签集合并

    X = train_ds[:, :300].reshape(-1, 300, 1)                           # 全部数据集数据
    Y = train_ds[:, 300]                                                # 全部数据标签
    return X, Y
