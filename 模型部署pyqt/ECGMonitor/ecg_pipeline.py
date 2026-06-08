# ECG 处理管线模块
# 职责：接收原始数据包（0x10 包头），按子类型分发到 ECG/导联/心率处理逻辑；
#       累计 ECG 采样点到固定窗口，达到窗口长度后调用注入的 predict_func 触发推理；
#       通过回调函数将 ECG 采样、诊断结果、导联状态、心率事件和运行指标转发给调用方。
# 边界：本模块不依赖 Qt 信号、不直接操作串口、不持有模型对象；
#       SerialInferenceWorker 和 OfflineReplayWorker 共用同一条管线实例。

import logging
import time

from worker_metrics import WorkerMetrics


# 每隔 N 个 ECG 包发出一次 metrics_updated 快照（即使未触发推理）
METRICS_EMIT_INTERVAL = 200
logger = logging.getLogger(__name__)


def _noop(_value):
    return None


class EcgProcessingPipeline:
    """ECG 处理管线：包分发 -> 窗口累计 -> 推理触发 -> 回调转发。"""
    def __init__(
        self,
        window_size,
        predict_func,
        on_ecg_sample=None,
        on_diagnosis=None,
        on_lead_status=None,
        on_heart_rate=None,
        on_metrics=None,
        on_error=None,
    ):
        self.window_size = window_size  # 模型输入窗口长度，来自契约 input.window_size
        self.predict_func = predict_func  # 推理函数，接收 ECG 采样点列表，返回分类标签编号
        self.on_ecg_sample = on_ecg_sample or _noop
        self.on_diagnosis = on_diagnosis or _noop
        self.on_lead_status = on_lead_status or _noop
        self.on_heart_rate = on_heart_rate or _noop
        self.on_metrics = on_metrics or _noop
        self.on_error = on_error or _noop
        self.metrics = WorkerMetrics()  # 运行时指标累积器
        self._window = []  # ECG 诊断窗口缓冲区，累计到 window_size 后触发推理
        self.started_at = 0.0  # 管线启动时间戳，用于计算运行时长和吞吐量

    def process_packet(self, packet):
        """处理单个数据包：仅处理 0x10 包头，按子类型分发到 ECG/导联/心率处理。"""
        if len(packet) < 1:
            self._report_malformed_packet("Invalid ECG pipeline packet: missing packet type")
            return
        if packet[0] != 0x10:
            return
        if len(packet) < 2:
            self._report_malformed_packet("Invalid ECG pipeline packet: missing subtype")
            return

        self.metrics.total_packets += 1  # 每个 0x10 包计入总包数
        sub_id = packet[1]  # 子类型：0x02=ECG, 0x03=导联, 0x04=心率
        if sub_id == 0x02:
            if not self._has_min_length(packet, 4, "ECG"):
                return
            self._process_ecg_packet(packet)
        elif sub_id == 0x03:
            if not self._has_min_length(packet, 3, "lead"):
                return
            self._process_lead_packet(packet)
        elif sub_id == 0x04:
            if not self._has_min_length(packet, 4, "heart rate"):
                return
            self._process_heart_rate_packet(packet)

    def _process_ecg_packet(self, packet):
        """处理 ECG 数据包：提取 16 位采样值，累计到诊断窗口，达到窗口长度后触发推理。"""
        self.metrics.ecg_packets += 1
        ecg_value = (packet[2] << 8) | packet[3]  # 高 8 位 + 低 8 位合成 16 位采样值
        self.on_ecg_sample(ecg_value)
        self._refresh_runtime()

        self._window.append(ecg_value)  # 追加到诊断窗口缓冲区
        if len(self._window) >= self.window_size:
            # 窗口已满，触发推理（无论成功或失败都会清空窗口）
            try:
                start = time.perf_counter()
                result = self.predict_func(self._window)
                self.metrics.last_inference_ms = (time.perf_counter() - start) * 1000.0
                self.metrics.diagnosis_count += 1
                self._refresh_runtime()
                logger.info(
                    "Inference completed: result=%s window=%s duration_ms=%.2f count=%s",
                    result,
                    self.window_size,
                    self.metrics.last_inference_ms,
                    self.metrics.diagnosis_count,
                )
                self.on_diagnosis(result)
                self.on_metrics(self.metrics.snapshot())
            except Exception as exc:
                logger.exception("Inference failed in ECG pipeline")
                self.on_error(f"AI推理失败: {exc}")
            self._window.clear()
        elif self.metrics.ecg_packets % METRICS_EMIT_INTERVAL == 0:
            self.on_metrics(self.metrics.snapshot())

    def _process_lead_packet(self, packet):
        """处理导联状态包：status=1 表示导联脱落，会清空当前诊断窗口。"""
        self.metrics.lead_events += 1
        self._refresh_runtime()
        status = packet[2]
        self.on_lead_status(status)
        self.on_metrics(self.metrics.snapshot())
        if status == 1:
            self._window.clear()

    def _process_heart_rate_packet(self, packet):
        """处理心率数据包：仅 hr > 0 时发出 heart_rate 信号。"""
        self.metrics.heart_rate_events += 1
        self._refresh_runtime()
        heart_rate = (packet[2] << 8) | packet[3]
        if heart_rate > 0:
            self.on_heart_rate(heart_rate)
            self.on_metrics(self.metrics.snapshot())

    def _refresh_runtime(self):
        if self.started_at > 0:
            self.metrics.refresh_runtime(self.started_at)

    def _has_min_length(self, packet, expected_length, packet_name):
        if len(packet) >= expected_length:
            return True
        self._report_malformed_packet(
            f"Invalid {packet_name} packet: expected at least {expected_length} bytes, got {len(packet)}"
        )
        return False

    def _report_malformed_packet(self, message):
        logger.warning(message)
        self.on_error(message)
