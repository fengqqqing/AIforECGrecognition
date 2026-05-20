from config import MODEL_CONTRACT_PATH, UI_LIMITS
from model_contract import load_model_contract
from ui_theme import ECG_MONITOR_THEME


NORMAL_RESULT_INDEX = 0
_LABELS_CACHE = None


def _get_diagnosis_labels():
    global _LABELS_CACHE
    if _LABELS_CACHE is None:
        contract = load_model_contract(MODEL_CONTRACT_PATH)
        _LABELS_CACHE = contract["output"]["labels"]
    return _LABELS_CACHE


def get_diagnosis_label(result: int) -> str:
    labels = _get_diagnosis_labels()
    if 0 <= result < len(labels):
        return labels[result]
    return ""


def get_diagnosis_style(result: int) -> str:
    colors = ECG_MONITOR_THEME["colors"]
    radius = ECG_MONITOR_THEME["radius"]["medium"]
    if result == NORMAL_RESULT_INDEX:
        color = colors["normal"]
        background = "#0d2619"
    else:
        color = colors["warning"]
        background = "#2a1518"
    return (
        f"background-color: {background}; "
        f"color: {color}; "
        f"border: 1px solid {color}; "
        f"border-radius: {radius}px; "
        "font-weight: 700; "
        "padding: 3px 8px;"
    )


def _status_text_style(color: str, background: str) -> str:
    radius = ECG_MONITOR_THEME["radius"]["small"]
    return (
        f"background-color: {background}; "
        f"color: {color}; "
        f"border: 1px solid {color}; "
        f"border-radius: {radius}px; "
        "font-weight: 700; "
        "padding: 2px 8px;"
    )


def get_lead_status_text(status: int) -> str:
    if status == 0:
        return "导联连接"
    if status == 1:
        return "导联脱落"
    return "导联未知"


def get_lead_status_style(status: int) -> str:
    colors = ECG_MONITOR_THEME["colors"]
    if status == 0:
        return _status_text_style(colors["normal"], "#0d2619")
    if status == 1:
        return _status_text_style(colors["warning"], "#2a1518")
    return _status_text_style(colors["unknown"], "#151d25")


def get_heart_rate_style(hr: int) -> str:
    colors = ECG_MONITOR_THEME["colors"]
    if should_display_heart_rate(hr):
        color = colors["normal"]
    else:
        color = colors["unknown"]
    return (
        f"color: {color}; "
        "font-weight: 700;"
    )


def is_lead_connected(status: int) -> bool:
    return status == 0


def should_display_heart_rate(hr: int) -> bool:
    return 0 < hr < UI_LIMITS["heart_rate_max"]


def format_worker_metrics(metrics: dict) -> str:
    if not metrics:
        return "运行指标: 未开始"
    return (
        "运行指标: "
        f"包={metrics.get('total_packets', 0)} "
        f"ECG={metrics.get('ecg_packets', 0)} "
        f"诊断={metrics.get('diagnosis_count', 0)} "
        f"导联={metrics.get('lead_events', 0)} "
        f"心率={metrics.get('heart_rate_events', 0)} "
        f"单次推理={metrics.get('last_inference_ms', 0.0):.1f}ms "
        f"吞吐量={metrics.get('throughput_samples_per_sec', 0.0):.1f}点/s"
    )


def format_metrics_panel_values(metrics: dict) -> dict:
    return {
        "packets": f"{metrics.get('total_packets', 0)} / ECG {metrics.get('ecg_packets', 0)}",
        "diagnosis": str(metrics.get("diagnosis_count", 0)),
        "latency": f"{metrics.get('last_inference_ms', 0.0):.1f} ms",
        "throughput": f"{metrics.get('throughput_samples_per_sec', 0.0):.1f} 点/s",
        "events": f"导联 {metrics.get('lead_events', 0)} · 心率 {metrics.get('heart_rate_events', 0)}",
    }
