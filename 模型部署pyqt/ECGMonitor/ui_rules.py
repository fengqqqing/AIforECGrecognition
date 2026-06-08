# UI 展示规则模块
# 职责：将运行时状态（诊断结果、导联状态、心率、运行指标）映射为
#       可展示的文本和样式字符串，避免 UI 控件直接依赖业务逻辑。
# 诊断标签从模型契约的 output.labels 获取，索引 0 对应"正常"类别。

from config import MODEL_CONTRACT_PATH, UI_LIMITS
from model_contract import load_model_contract
from ui_theme import ECG_MONITOR_THEME


NORMAL_RESULT_INDEX = 0  # 正常类别的诊断结果索引（来自模型契约 output.labels[0]）
_LABELS_CACHE = None     # 惰性加载的诊断标签列表缓存

_UI_STATE_COPY = {
    "idle": {
        "badge": "串口待机",
        "detail": "在线采集 / 离线回放可用",
        "hint": "辅助提示 · 等待信号输入",
        "next_action": "启动离线回放、串口采集或固定 Demo",
    },
    "demo_ready": {
        "badge": "Demo 就绪",
        "detail": "固定 Demo 场景",
        "hint": "预检通过 · 等待自动启动",
        "next_action": "等待自动启动",
    },
    "demo_starting": {
        "badge": "Demo 启动中",
        "detail": "固定 Demo 场景",
        "hint": "离线回放正在启动",
        "next_action": "等待波形开始刷新",
    },
    "replay_starting": {
        "badge": "离线回放启动中",
        "detail": "当前回放配置",
        "hint": "离线数据正在载入",
        "next_action": "等待波形开始刷新",
    },
    "serial_running": {
        "badge": "串口运行中",
        "detail": "实时采集模式",
        "hint": "先确认波形、导联和心率，再查看 AI 辅助提示",
        "next_action": "观察信号状态和辅助识别结果",
    },
    "demo_running": {
        "badge": "Demo 运行中",
        "detail": "固定 Demo 场景",
        "hint": "先确认波形、导联和心率，再查看 AI 辅助提示",
        "next_action": "等待固定窗口完成并查看辅助识别结果",
    },
    "replay_running": {
        "badge": "离线回放运行中",
        "detail": "当前回放配置",
        "hint": "先确认波形、导联和心率，再查看 AI 辅助提示",
        "next_action": "等待回放完成或查看运行指标",
    },
    "inference_done": {
        "badge": "推理完成",
        "detail": "AI 辅助识别已更新",
        "hint": "结果仅作正式判读前的辅助提示",
        "next_action": "继续观察或查看最近摘要",
    },
    "demo_completed": {
        "badge": "Demo 已完成",
        "detail": "固定 Demo 场景",
        "hint": "可查看最近运行摘要和导出文件",
        "next_action": "点击最近摘要，必要时打开导出目录",
    },
    "replay_completed": {
        "badge": "离线回放已完成",
        "detail": "当前回放配置",
        "hint": "可查看最近运行摘要和导出文件",
        "next_action": "点击最近摘要，必要时打开导出目录",
    },
    "error": {
        "badge": "状态异常",
        "detail": "资源或配置需要检查",
        "hint": "请检查模型契约、模型文件、样例数据或回放配置",
        "next_action": "按提示修复后重新启动 Demo 或回放",
    },
    "reset": {
        "badge": "显示已重置",
        "detail": "展示状态已清空",
        "hint": "辅助提示 · 等待新的信号输入",
        "next_action": "重新启动离线回放、串口采集或固定 Demo",
    },
    "unknown": {
        "badge": "状态未知",
        "detail": "当前状态未映射",
        "hint": "辅助提示 · 请确认运行状态",
        "next_action": "可重置显示后重新启动回放或 Demo",
    },
}


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
    """诊断结果样式：正常=绿色，异常=红色（带背景色和边框）。"""
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


def get_assistant_result_hint(result) -> str:
    """AI 结果卡解释文案：强调辅助提示边界，不承诺临床结论。"""
    if result is None:
        return "等待 ECG 窗口完成后显示辅助提示"
    if not isinstance(result, int):
        return "结果索引未识别，请检查模型契约或回放配置"
    if result == NORMAL_RESULT_INDEX:
        return "当前结果仅作正式判读前的辅助提示"
    return "提示需结合波形、导联状态和医生复核，仅作正式判读前参考"


def get_ui_state_copy(state: str, detail: str = "") -> dict:
    """返回顶部状态、辅助提示和下一步动作的保守展示文案。"""
    copy = dict(_UI_STATE_COPY.get(state, _UI_STATE_COPY["unknown"]))
    if detail:
        copy["detail"] = detail
    return copy


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
    """导联状态样式：连接=绿色，脱落=红色，未知=灰色。"""
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
    """将运行指标 dict 格式化为状态栏一行文本（包/ECG/诊断/推理/吞吐量）。"""
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
    """将运行指标 dict 转为底部面板五列指标的显示文本。"""
    return {
        "packets": f"{metrics.get('total_packets', 0)} / ECG {metrics.get('ecg_packets', 0)}",
        "diagnosis": str(metrics.get("diagnosis_count", 0)),
        "latency": f"{metrics.get('last_inference_ms', 0.0):.1f} ms",
        "throughput": f"{metrics.get('throughput_samples_per_sec', 0.0):.1f} 点/s",
        "events": f"导联 {metrics.get('lead_events', 0)} · 心率 {metrics.get('heart_rate_events', 0)}",
    }
