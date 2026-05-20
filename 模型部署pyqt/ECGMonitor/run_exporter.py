import csv
import json
import os
from datetime import datetime

from config import EXPORT_POLICY


class RunExporter:
    def __init__(self, mode: str, policy=None):
        self._policy = dict(EXPORT_POLICY if policy is None else policy)
        self._enabled = self._policy.get("enabled", True)
        self._mode = mode
        self._metrics_path = None
        self._diagnosis_path = None
        self._replay_path = None
        self._diagnosis_header_written = False
        self._replay_written = False
        self._samples = []
        self._latest_result = -1
        self._latest_label = ""
        self._latest_diagnosis_count = 0
        self._latest_inference_ms = 0.0
        self._latest_throughput = 0.0
        if not self._enabled:
            return

        runs_dir = self._policy["runs_dir"]
        os.makedirs(runs_dir, exist_ok=True)
        timestamp = datetime.now().strftime(self._policy["timestamp_format"])
        self._base_dir = os.path.join(runs_dir, f"{timestamp}_{mode}")
        os.makedirs(self._base_dir, exist_ok=True)
        self._metrics_path = os.path.join(self._base_dir, "metrics.jsonl")
        self._diagnosis_path = os.path.join(self._base_dir, "diagnosis.csv")
        self._replay_path = os.path.join(self._base_dir, "ecg_replay.csv")

    @property
    def base_dir(self):
        return getattr(self, "_base_dir", None)

    @property
    def replay_path(self):
        return self._replay_path

    def append_metrics(self, metrics: dict):
        if not self._enabled or self._metrics_path is None:
            return
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mode": self._mode,
            "metrics": metrics,
        }
        with open(self._metrics_path, "a", encoding="utf-8") as file_obj:
            file_obj.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def append_ecg_sample(self, value: int):
        if not self._enabled:
            return
        self._samples.append(int(value))

    def append_diagnosis(self, result: int, label: str, metrics: dict):
        if not self._enabled or self._diagnosis_path is None:
            return
        self._latest_result = int(result)
        self._latest_label = label
        self._latest_diagnosis_count = int(metrics.get("diagnosis_count", 0))
        self._latest_inference_ms = float(metrics.get("last_inference_ms", 0.0))
        self._latest_throughput = float(metrics.get("throughput_samples_per_sec", 0.0))
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mode": self._mode,
            "result": result,
            "label": label,
            "diagnosis_count": metrics.get("diagnosis_count", 0),
            "last_inference_ms": metrics.get("last_inference_ms", 0.0),
            "throughput_samples_per_sec": metrics.get("throughput_samples_per_sec", 0.0),
        }
        file_exists = os.path.exists(self._diagnosis_path)
        with open(self._diagnosis_path, "a", encoding="utf-8", newline="") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=list(row.keys()))
            if not file_exists and not self._diagnosis_header_written:
                writer.writeheader()
                self._diagnosis_header_written = True
            writer.writerow(row)

    def finalize(self):
        if not self._enabled or self._replay_written or self._replay_path is None:
            return
        if not self._samples:
            return
        row = list(self._samples)
        row.append(self._latest_result)
        with open(self._replay_path, "w", encoding="utf-8", newline="") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerow(row)
        self._replay_written = True

    def latest_summary(self):
        if not self._enabled:
            return "导出未启用"
        latest_diagnosis = (
            f"{self._latest_label} ({self._latest_result})"
            if self._latest_label
            else "未产生"
        )
        return (
            f"运行模式: {self._mode}\n"
            f"导出目录: {self.base_dir or '未创建'}\n"
            f"诊断次数: {self._latest_diagnosis_count}\n"
            f"最近诊断: {latest_diagnosis}\n"
            f"单次推理: {self._latest_inference_ms:.1f} ms\n"
            f"吞吐量: {self._latest_throughput:.1f} 点/s\n"
            f"采样点数: {len(self._samples)}\n"
            f"指标文件: {self._metrics_path or '未创建'}\n"
            f"诊断文件: {self._diagnosis_path or '未创建'}\n"
            f"回放文件: {self._replay_path or '未创建'}"
        )
