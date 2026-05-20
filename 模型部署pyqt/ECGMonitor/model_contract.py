import json
import os
from pathlib import Path


_REQUIRED_FIELDS = [
    ("contract_version",),
    ("model_name",),
    ("model_file",),
    ("framework",),
    ("device",),
    ("input", "window_size"),
    ("input", "shape"),
    ("input", "dtype"),
    ("preprocessing", "normalization"),
    ("preprocessing", "min_val"),
    ("preprocessing", "max_val"),
    ("output", "num_classes"),
    ("output", "labels"),
]


def load_model_contract(path):
    with open(path, "r", encoding="utf-8") as f:
        contract = json.load(f)
    _validate_required_fields(contract)
    _validate_contract_values(contract, path)
    return contract


def resolve_model_path(model_file, models_dir):
    model_file_path = Path(model_file)
    if model_file_path.is_absolute():
        raise ValueError("模型契约字段 model_file 必须是相对 models/ 的路径")
    if any(part == ".." for part in model_file_path.parts):
        raise ValueError("模型契约字段 model_file 不能包含父目录引用")

    models_root = Path(models_dir).resolve()
    resolved_path = (models_root / model_file_path).resolve()
    try:
        resolved_path.relative_to(models_root)
    except ValueError as exc:
        raise ValueError("模型契约字段 model_file 必须位于 models/ 目录内") from exc
    return str(resolved_path)


def _validate_required_fields(contract):
    for field_path in _REQUIRED_FIELDS:
        current = contract
        for field_name in field_path:
            if not isinstance(current, dict) or field_name not in current:
                dotted_name = ".".join(field_path)
                raise ValueError(f"模型契约缺少必填字段: {dotted_name}")
            current = current[field_name]


def _validate_contract_values(contract, contract_path):
    if contract["contract_version"] != 1:
        raise ValueError("模型契约字段 contract_version 必须为 1")
    if contract["framework"] != "torchscript":
        raise ValueError("模型契约字段 framework 必须为 torchscript")
    if contract["device"] != "cpu":
        raise ValueError("模型契约字段 device 必须为 cpu")
    if contract["input"]["dtype"] != "float32":
        raise ValueError("模型契约字段 input.dtype 必须为 float32")
    if contract["preprocessing"]["normalization"] != "min_max":
        raise ValueError("模型契约字段 preprocessing.normalization 必须为 min_max")

    window_size = contract["input"]["window_size"]
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValueError("模型契约字段 input.window_size 必须是正整数")
    if contract["input"]["shape"] != ["B", 1, window_size]:
        raise ValueError("模型契约字段 input.shape 必须与 window_size 一致")

    min_val = contract["preprocessing"]["min_val"]
    max_val = contract["preprocessing"]["max_val"]
    if min_val >= max_val:
        raise ValueError("模型契约字段 preprocessing.min_val 必须小于 max_val")

    num_classes = contract["output"]["num_classes"]
    labels = contract["output"]["labels"]
    if not isinstance(labels, list):
        raise ValueError("模型契约字段 output.labels 必须是数组")
    if num_classes != len(labels):
        raise ValueError("模型契约字段 output.num_classes 必须等于 labels 数量")

    model_path = resolve_model_path(contract["model_file"], os.path.dirname(os.path.abspath(contract_path)))
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型契约指向的模型文件不存在: {model_path}")
