# 集中配置模块
# 职责：定义项目路径常量、串口默认参数、UI 限制、重连策略、离线回放策略、
#       Demo 回放策略和导出策略。所有模块通过 from config import ... 引用。
# 注意：模型文件、窗口长度、归一化参数和标签顺序由模型契约（contract JSON）提供，
#       本模块不再承载模型语义配置，避免双源漂移。

import os


BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, "models")
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")
MODEL_CONTRACT_PATH = os.path.join(MODELS_DIR, "best_acc.contract.json")
RUNS_DIR = os.path.join(BASE_DIR, "runs")

SERIAL_DEFAULTS = {
    "baud_rate": 115200,
    "data_bits": 8,
    "stop_bits": 1,
    "parity": "N",
}

UI_LIMITS = {
    "heart_rate_max": 350,       # 心率显示上限，超过则显示 "--"
    "wave_draw_threshold": 10,   # 波形缓冲区积攒到此数量才触发绘制，减少 UI 刷新频率
}

RECONNECT_POLICY = {
    "enabled": True,
    "interval_ms": 2000,         # 断连后重连间隔（毫秒）
    "max_attempts": 3,           # 最大自动重连次数
}

# 离线回放默认策略（可通过 GUI "回放设置" 对话框修改）
OFFLINE_REPLAY_POLICY = {
    "input_csv": os.path.join(SAMPLE_DATA_DIR, "test.csv"),
    "source_type": "test_csv",
    "use_real_model": False,
    "row": 0,
    "samples": 2000,
    "event_interval": 500,
    "lead_events": [0, 1, 0],
    "hr_events": [72, 88, 65],
    "mock_label": 0,
    "frame_sleep_ms": 1,
}

# Demo 回放策略：启动 --demo 时自动执行的固定场景回放（使用真实模型推理）
DEMO_REPLAY_POLICY = {
    "input_csv": os.path.join(SAMPLE_DATA_DIR, "test.csv"),
    "source_type": "test_csv",
    "use_real_model": True,
    "row": 3,
    "samples": 2000,
    "event_interval": 500,
    "lead_events": [0, 0, 0, 0],
    "hr_events": [72, 84, 78, 90],
    "mock_label": 0,
    "frame_sleep_ms": 1,
    "model_contract_path": MODEL_CONTRACT_PATH,
    "expected_source_label": 0,
    "expected_real_diagnosis": 0,
    "manual_mock_replay": {
        "row": 3,
        "samples": 2000,
        "event_interval": 500,
        "lead_events": [0, 0, 0, 0],
        "hr_events": [72, 84, 78, 90],
        "mock_label": 0,
    },
    "display_strategy": {
        "primary_mode": "real-model",
        "result_wording": "AI 辅助识别结果，仅用于实验演示。",
    },
}

# 运行导出策略：指标、诊断和回放文件的输出目录和时间戳格式
EXPORT_POLICY = {
    "enabled": True,
    "runs_dir": RUNS_DIR,
    "timestamp_format": "%Y%m%d_%H%M%S",
}
