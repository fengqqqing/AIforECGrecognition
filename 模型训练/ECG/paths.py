# 训练侧路径常量模块
# 职责：定义训练侧所有目录路径，避免在各模块中硬编码路径。
# 所有路径基于 artifacts/training/ecg/ 目录。

from pathlib import Path


TRAINING_DIR = Path(__file__).resolve().parent        # 模型训练/ECG/ 目录
PROJECT_ROOT = TRAINING_DIR.parents[1]                 # 项目根目录

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "training" / "ecg"  # 训练产物根目录
RAW_DATA_DIR = ARTIFACTS_DIR / "raw_data"                        # MIT-BIH 原始数据
PROCESSED_DATA_DIR = ARTIFACTS_DIR / "processed_data"            # 处理后的 CSV 数据
MODEL_ARTIFACTS_DIR = ARTIFACTS_DIR / "models"                  # 模型 checkpoint 和导出文件
FIGURES_DIR = ARTIFACTS_DIR / "figures"                         # 训练曲线等可视化结果
