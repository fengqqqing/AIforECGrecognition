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
        elapsed = max(time.perf_counter() - started_at, 0.0)
        self.elapsed_seconds = elapsed
        if elapsed > 0:
            self.throughput_samples_per_sec = self.ecg_packets / elapsed
        else:
            self.throughput_samples_per_sec = 0.0

    def snapshot(self):
        return asdict(self)
