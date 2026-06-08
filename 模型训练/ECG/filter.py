# ECG 小波去噪模块
# 职责：对 ECG 信号进行 9 层 db5 小波分解，用通用阈值去噪，
#       清除第 1-2 层高频系数（噪声为主），对其他层做软阈值处理。
# 调用方：dataset.py 中的 getDataSet()。

import numpy as np
import pywt


# 小波去噪预处理
def denoise(data):
    """db5 小波 9 层分解去噪：通用阈值 + 清除高频系数。"""
    # 小波变换：9 层分解，得到 [cA9, cD9, cD8, ..., cD1]
    coeffs = pywt.wavedec(data=data, wavelet='db5', level=9)
    cA9, cD9, cD8, cD7, cD6, cD5, cD4, cD3, cD2, cD1 = coeffs
    # 通用阈值（VisuShrink）：基于噪声标准差估计（MAD / 0.6745）
    threshold = (np.median(np.abs(cD1)) / 0.6745) * (np.sqrt(2 * np.log(len(cD1))))
    threshold = (np.median(np.abs(cD1)) / 0.6745) * (np.sqrt(2 * np.log(len(cD1))))
    cD1.fill(0)
    cD2.fill(0)
    for i in range(1, len(coeffs) - 2):
        coeffs[i] = pywt.threshold(coeffs[i], threshold)
    # 小波反变换,获取去噪后的信号
    rdata = pywt.waverec(coeffs=coeffs, wavelet='db5')
    return rdata
