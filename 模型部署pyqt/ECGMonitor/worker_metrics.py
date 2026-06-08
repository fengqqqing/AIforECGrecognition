# 运行时指标数据模块
# 职责：以 dataclass 形式累积运行指标（总包数、ECG 包数、导联/心率事件数、
#       诊断次数、推理耗时、运行时长、吞吐量），并支持快照导出为 dict。

from dataclasses import asdict, dataclass
import time


@dataclass
class WorkerMetrics:
    total_packets: int = 0
    ecg_packets: int = 0
    lead_events: int = 0
    heart_rate_events: int = 0
    diagnosis_count: int = 0
    last_inference_ms: float = 0.0
    elapsed_seconds: float = 0.0
    throughput_samples_per_sec: float = 0.0

    def refresh_runtime(self, started_at: float):
        """刷新运行时长和吞吐量（ECG 包数 / 运行时长）。"""
        elapsed = max(time.perf_counter() - started_at, 0.0)
        self.elapsed_seconds = elapsed
        if elapsed > 0:
            self.throughput_samples_per_sec = self.ecg_packets / elapsed
        else:
            self.throughput_samples_per_sec = 0.0

    def snapshot(self):
        """返回当前指标的 dict 快照，用于信号传递和 JSONL 导出。"""
        return asdict(self)
