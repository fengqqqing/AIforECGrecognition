import logging
import time

from worker_metrics import WorkerMetrics


METRICS_EMIT_INTERVAL = 200
logger = logging.getLogger(__name__)


def _noop(_value):
    return None


class EcgProcessingPipeline:
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
        self.window_size = window_size
        self.predict_func = predict_func
        self.on_ecg_sample = on_ecg_sample or _noop
        self.on_diagnosis = on_diagnosis or _noop
        self.on_lead_status = on_lead_status or _noop
        self.on_heart_rate = on_heart_rate or _noop
        self.on_metrics = on_metrics or _noop
        self.on_error = on_error or _noop
        self.metrics = WorkerMetrics()
        self._window = []
        self.started_at = 0.0

    def process_packet(self, packet):
        if len(packet) < 1:
            self._report_malformed_packet("Invalid ECG pipeline packet: missing packet type")
            return
        if packet[0] != 0x10:
            return
        if len(packet) < 2:
            self._report_malformed_packet("Invalid ECG pipeline packet: missing subtype")
            return

        self.metrics.total_packets += 1
        sub_id = packet[1]
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
        self.metrics.ecg_packets += 1
        ecg_value = (packet[2] << 8) | packet[3]
        self.on_ecg_sample(ecg_value)
        self._refresh_runtime()

        self._window.append(ecg_value)
        if len(self._window) >= self.window_size:
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
        self.metrics.lead_events += 1
        self._refresh_runtime()
        status = packet[2]
        self.on_lead_status(status)
        self.on_metrics(self.metrics.snapshot())
        if status == 1:
            self._window.clear()

    def _process_heart_rate_packet(self, packet):
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
