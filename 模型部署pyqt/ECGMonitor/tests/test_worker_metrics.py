import unittest
from unittest import mock

from worker_metrics import WorkerMetrics


class WorkerMetricsTest(unittest.TestCase):
    def test_snapshot_contains_all_fields(self):
        metrics = WorkerMetrics(
            total_packets=10,
            ecg_packets=7,
            lead_events=1,
            heart_rate_events=2,
            diagnosis_count=3,
            last_inference_ms=12.5,
            elapsed_seconds=1.5,
            throughput_samples_per_sec=4.0,
        )
        snapshot = metrics.snapshot()

        self.assertEqual(snapshot["total_packets"], 10)
        self.assertEqual(snapshot["ecg_packets"], 7)
        self.assertEqual(snapshot["lead_events"], 1)
        self.assertEqual(snapshot["heart_rate_events"], 2)
        self.assertEqual(snapshot["diagnosis_count"], 3)
        self.assertEqual(snapshot["last_inference_ms"], 12.5)
        self.assertEqual(snapshot["elapsed_seconds"], 1.5)
        self.assertEqual(snapshot["throughput_samples_per_sec"], 4.0)

    @mock.patch("worker_metrics.time.perf_counter", return_value=15.0)
    def test_refresh_runtime_updates_elapsed_and_throughput(self, _mock_perf_counter):
        metrics = WorkerMetrics(ecg_packets=300)
        metrics.refresh_runtime(started_at=10.0)

        self.assertEqual(metrics.elapsed_seconds, 5.0)
        self.assertEqual(metrics.throughput_samples_per_sec, 60.0)


if __name__ == "__main__":
    unittest.main()
