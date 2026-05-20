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
    "heart_rate_max": 350,
    "wave_draw_threshold": 10,
}

RECONNECT_POLICY = {
    "enabled": True,
    "interval_ms": 2000,
    "max_attempts": 3,
}

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

EXPORT_POLICY = {
    "enabled": True,
    "runs_dir": RUNS_DIR,
    "timestamp_format": "%Y%m%d_%H%M%S",
}
