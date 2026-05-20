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
    global _MODEL_CONTRACT
    if _MODEL_CONTRACT is None:
        _MODEL_CONTRACT = load_model_contract(MODEL_CONTRACT_PATH)
    return _MODEL_CONTRACT


def _get_model_path(contract):
    return resolve_model_path(contract["model_file"], MODELS_DIR)


def _get_model():
    global _MODEL
    if _MODEL is None:
        contract = _get_contract()
        model_path = _get_model_path(contract)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        with open(model_path, "rb") as model_file:
            model_bytes = model_file.read()
        _MODEL = torch.jit.load(io.BytesIO(model_bytes), map_location="cpu")
        _MODEL.eval()
        logger.info("Inference model loaded from %s", model_path)
    return _MODEL


def warmup_model():
    contract = _get_contract()
    model = _get_model()
    _validate_model_output_shape(model, contract)


def _validate_model_output_shape(model, contract):
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
    contract = _get_contract()
    window_size = contract["input"]["window_size"]
    signal = np.asarray(data, dtype=np.float32)
    if signal.size < window_size:
        raise ValueError(f"ECG window is too short: {signal.size}, expected >= {window_size}")
    if signal.size != window_size:
        signal = signal[-window_size:]

    min_val = np.float32(contract["preprocessing"]["min_val"])
    max_val = np.float32(contract["preprocessing"]["max_val"])
    x = (signal - min_val) / (max_val - min_val)
    x_tensor = torch.from_numpy(x).view(1, 1, window_size)

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
