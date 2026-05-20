import logging
import time

from PyQt5 import QtCore

from config import MODEL_CONTRACT_PATH, OFFLINE_REPLAY_POLICY
from ecg_pipeline import EcgProcessingPipeline
from example import predict
from model_contract import load_model_contract
from replay_utils import load_replay_source, resolve_replay_path_from_policy

logger = logging.getLogger(__name__)


def make_ecg_packet(value):
    value = int(value)
    return [0x10, 0x02, (value >> 8) & 0xFF, value & 0xFF]


def make_lead_packet(status):
    return [0x10, 0x03, int(status) & 0xFF]


def make_hr_packet(hr):
    hr = int(hr)
    return [0x10, 0x04, (hr >> 8) & 0xFF, hr & 0xFF]


class OfflineReplayWorker(QtCore.QObject):
    opened = QtCore.pyqtSignal(str)
    closed = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    ecg_sample = QtCore.pyqtSignal(int)
    diagnosis = QtCore.pyqtSignal(int)
    lead_status = QtCore.pyqtSignal(int)
    heart_rate = QtCore.pyqtSignal(int)
    metrics_updated = QtCore.pyqtSignal(dict)
    replay_summary = QtCore.pyqtSignal(dict)

    def __init__(self, policy=None):
        super().__init__()
        self._policy = dict(OFFLINE_REPLAY_POLICY if policy is None else policy)
        self._running = False

    @QtCore.pyqtSlot()
    def run(self):
        diagnosis_values = []

        try:
            source_path = self._policy.get("resolved_input_csv") or resolve_replay_path_from_policy(self._policy)
            source = load_replay_source(source_path, self._policy["row"], self._policy["samples"])
            values = source["values"]
        except Exception as exc:
            logger.exception("Failed to load offline replay data")
            self.error.emit(f"离线回放加载失败: {exc}")
            self.closed.emit()
            return

        try:
            use_real_model = bool(self._policy.get("use_real_model", False))
            if use_real_model:
                predict_func = lambda values: predict(values)
            else:
                predict_func = lambda values: self._policy["mock_label"]

            def emit_diagnosis(value):
                diagnosis_values.append(value)
                self.diagnosis.emit(value)

            pipeline = EcgProcessingPipeline(
                window_size=load_model_contract(MODEL_CONTRACT_PATH)["input"]["window_size"],
                predict_func=predict_func,
                on_ecg_sample=self.ecg_sample.emit,
                on_diagnosis=emit_diagnosis,
                on_lead_status=self.lead_status.emit,
                on_heart_rate=self.heart_rate.emit,
                on_metrics=self.metrics_updated.emit,
                on_error=self.error.emit,
            )
        except Exception as exc:
            logger.exception("Failed to initialize offline replay")
            self.error.emit(f"离线回放初始化失败: {exc}")
            self.closed.emit()
            return

        self._running = True
        self.opened.emit("OFFLINE_REPLAY")

        try:
            lead_idx = 0
            hr_idx = 0
            interval = self._policy["event_interval"]
            for index, value in enumerate(values, start=1):
                if not self._running:
                    break

                pipeline.process_packet(make_ecg_packet(value))

                if interval > 0 and index % interval == 0:
                    if lead_idx < len(self._policy["lead_events"]):
                        pipeline.process_packet(make_lead_packet(self._policy["lead_events"][lead_idx]))
                        lead_idx += 1
                    if hr_idx < len(self._policy["hr_events"]):
                        pipeline.process_packet(make_hr_packet(self._policy["hr_events"][hr_idx]))
                        hr_idx += 1

                time.sleep(self._policy["frame_sleep_ms"] / 1000.0)
        except Exception as exc:
            logger.exception("Offline replay failed")
            self.error.emit(f"离线回放运行失败: {exc}")
        finally:
            self.replay_summary.emit(
                {
                    "source_path": source["source_path"],
                    "source_label": source["source_label"],
                    "used_real_model": use_real_model,
                    "latest_diagnosis": diagnosis_values[-1] if diagnosis_values else None,
                    "diagnosis_count": len(diagnosis_values),
                    "matched": (
                        source["source_label"] == diagnosis_values[-1]
                        if diagnosis_values and source["source_label"] is not None
                        else None
                    ),
                }
            )
            self.closed.emit()

    def stop(self):
        self._running = False
