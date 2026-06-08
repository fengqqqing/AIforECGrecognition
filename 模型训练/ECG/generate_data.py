# 数据增强与生成脚本
# 职责：从 processed_data/ 下的各分类 CSV 文件中，对每个文件随机截取 2000 点窗口，
#       并通过时域噪声增强（高斯噪声 std=10/30）和频域增强（随机增益 80%-120%）
#       生成增强样本，最终合并为 data.csv。
# 输出：artifacts/training/ecg/processed_data/data.csv（每行 = 2000 点 + 标签）

# 生成数据

import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from paths import PROCESSED_DATA_DIR

path = PROCESSED_DATA_DIR
path_dir = os.listdir(path)
final_data = pd.DataFrame()
with tqdm(total=path_dir.__len__()) as pbar:
    for i in path_dir:
        # 1. 先拼接完整路径
        file_full_path = os.path.join(path, i)

        # 2. 过滤逻辑
        name_part = i.split('.')[0]
        if not os.path.isfile(file_full_path) or i[-3:] != 'csv' or not name_part.isdigit():
            pbar.update(1)  # 记得更新进度条，否则跳过时进度条不动
            continue

        # 3. 这里的变量名要和下面 read_csv 保持一致
        # 如果你下面用的是 data_path，这里就叫 data_path
        data_path = file_full_path

        name = int(name_part)
        if name > 11:
            name = 0  # 超出 12 分类范围的文件归为类别 0（正常）

        data = pd.read_csv(data_path, header=None)  # 现在 data_path 肯定定义过了
        data = data.values.flatten()


        for j in range(0, 200):
            start_index = np.random.randint(0, 8001)  # 随机起始位置
            data_ = data[start_index: start_index + 2000]  # 截取 2000 点窗口
            data_list = list(data_)
            data_list.append(name)
            data_frame = pd.DataFrame(data_list).T
            final_data = pd.concat([final_data, data_frame], axis=0)

            for k in [10, 30]:
                # 时域增强：添加高斯噪声（std=10 和 std=30 两种强度）
                data__ = data_ + np.random.normal(0, k, data_.shape)
                data__ = data__.astype(int)
                data_list = list(data__)
                data_list.append(name)
                data_frame = pd.DataFrame(data_list).T
                final_data = pd.concat([final_data, data_frame], axis=0)

            # --- 增加的频域增强代码 ---
            # 频域增强：对频谱各频率分量随机增减 20% 幅度
            fft_vals = np.fft.rfft(data_)
            gain = np.random.uniform(0.8, 1.2, len(fft_vals))  # 随机 80%-120% 的增益
            fft_vals = fft_vals * gain
            data_freq = np.fft.irfft(fft_vals, n=len(data_))
            data_freq = data_freq.astype(int)

            # 封装并写入 final_data
            data_list_freq = list(data_freq)
            data_list_freq.append(name)
            data_frame_freq = pd.DataFrame(data_list_freq).T
            final_data = pd.concat([final_data, data_frame_freq], axis=0)

        pbar.update(1)

final_data.to_csv(PROCESSED_DATA_DIR / 'data.csv', index=False, header=False)
