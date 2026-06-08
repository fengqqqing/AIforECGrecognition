# 模型推理入口模块
# 职责：加载 TorchScript 模型、执行 min-max 归一化、调用模型返回分类结果。
# 关键设计：
#   - 使用内存流加载模型（先 read() 再 BytesIO），规避 Windows 中文路径导致
#     torch.jit.load 直接传路径时的编码错误。
#   - 模型和契约通过全局变量惰性加载（单例），避免重复 I/O。
#   - predict() 接受 ECG 采样点序列，返回 int 分类标签编号。
#   - warmup_model() 在启动时做 dummy input 推理，验证模型输出类别数与契约一致。

import io
import logging
import os
from typing import Sequence

import numpy as np
import pandas as pd
import torch

from config import MODEL_CONTRACT_PATH, MODELS_DIR, SAMPLE_DATA_DIR
from model_contract import load_model_contract, resolve_model_path

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_CONTRACT = None


def _get_contract():
    """惰性加载模型契约，返回契约 dict。"""
    global _MODEL_CONTRACT
    if _MODEL_CONTRACT is None:
        _MODEL_CONTRACT = load_model_contract(MODEL_CONTRACT_PATH)
    return _MODEL_CONTRACT


def _get_model_path(contract):
    """从契约中解析模型文件的绝对路径。"""
    return resolve_model_path(contract["model_file"], MODELS_DIR)


def _get_model():
    """惰性加载 TorchScript 模型（CPU 模式，eval 状态）。"""
    global _MODEL
    if _MODEL is None:
        contract = _get_contract()
        model_path = _get_model_path(contract)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        # 先读取二进制到内存，再通过 BytesIO 交给 torch.jit.load，
        # 规避 Windows 中文路径下直接传路径的编码问题。
        with open(model_path, "rb") as model_file:
            model_bytes = model_file.read()
        _MODEL = torch.jit.load(io.BytesIO(model_bytes), map_location="cpu")
        _MODEL.eval()
        logger.info("Inference model loaded from %s", model_path)
    return _MODEL


def warmup_model():
    """启动时调用：加载契约和模型，用 dummy input 验证输出类别数与契约一致。"""
    contract = _get_contract()
    model = _get_model()
    _validate_model_output_shape(model, contract)


def _validate_model_output_shape(model, contract):
    """用全零 dummy input 做推理，检查输出 shape 是否为 (1, num_classes)。"""
    window_size = contract["input"]["window_size"]
    num_classes = contract["output"]["num_classes"]
    dummy_input = torch.zeros((1, 1, window_size), dtype=torch.float32)
    try:
        with torch.no_grad():
            outputs = model(dummy_input)
    except Exception as exc:
        raise RuntimeError("模型契约 warmup 推理失败，请检查输入 shape 与模型文件是否匹配") from exc

    actual_shape = tuple(outputs.shape) if isinstance(outputs, torch.Tensor) else type(outputs).__name__
    if not isinstance(outputs, torch.Tensor) or tuple(outputs.shape) != (1, num_classes):
        raise ValueError(
            "模型输出类别数与契约不一致: "
            f"actual={actual_shape}, expected_shape={(1, num_classes)}"
        )


def predict(data: Sequence[float]) -> int:
    """对 ECG 采样点序列执行推理：min-max 归一化 -> reshape -> 模型前向 -> argmax 返回标签编号。"""
    contract = _get_contract()
    window_size = contract["input"]["window_size"]
    signal = np.asarray(data, dtype=np.float32)
    if signal.size < window_size:
        raise ValueError(f"ECG window is too short: {signal.size}, expected >= {window_size}")
    if signal.size != window_size:
        signal = signal[-window_size:]

    min_val = np.float32(contract["preprocessing"]["min_val"])  # 归一化下界（来自模型契约）
    max_val = np.float32(contract["preprocessing"]["max_val"])  # 归一化上界（来自模型契约）
    x = (signal - min_val) / (max_val - min_val)  # min-max 归一化到 [0, 1]
    x_tensor = torch.from_numpy(x).view(1, 1, window_size)  # reshape 为 (1, 1, window_size)

    model = _get_model()
    with torch.no_grad():
        outputs = model(x_tensor)
        pred = torch.argmax(outputs, dim=1)
        return int(pred.item())


if __name__ == "__main__":
    data = pd.read_csv(os.path.join(SAMPLE_DATA_DIR, "test.csv"), header=None)
    data = data.iloc[0, :-1].values.tolist()
    result = predict(data)
    print(result)
