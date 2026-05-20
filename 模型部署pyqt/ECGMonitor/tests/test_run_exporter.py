import csv
import json
import os
import tempfile
import unittest

from run_exporter import RunExporter


class RunExporterTest(unittest.TestCase):
    def test_exporter_writes_metrics_diagnosis_and_replay(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = RunExporter(
                "offline",
                {
                    "enabled": True,
                    "runs_dir": temp_dir,
                    "timestamp_format": "%Y%m%d_%H%M%S",
                },
            )
            metrics = {
                "total_packets": 10,
                "ecg_packets": 8,
                "diagnosis_count": 1,
                "lead_events": 1,
                "heart_rate_events": 1,
                "last_inference_ms": 9.5,
                "throughput_samples_per_sec": 160.0,
            }
            for value in [1, 2, 3, 4]:
                exporter.append_ecg_sample(value)
            exporter.append_metrics(metrics)
            exporter.append_diagnosis(0, "正常", metrics)
            exporter.finalize()

            metrics_path = os.path.join(exporter.base_dir, "metrics.jsonl")
            diagnosis_path = os.path.join(exporter.base_dir, "diagnosis.csv")
            replay_path = os.path.join(exporter.base_dir, "ecg_replay.csv")

            self.assertTrue(os.path.exists(metrics_path))
            self.assertTrue(os.path.exists(diagnosis_path))
            self.assertTrue(os.path.exists(replay_path))

            with open(metrics_path, "r", encoding="utf-8") as file_obj:
                payload = json.loads(file_obj.readline())
            self.assertEqual(payload["mode"], "offline")
            self.assertEqual(payload["metrics"]["diagnosis_count"], 1)

            with open(diagnosis_path, "r", encoding="utf-8") as file_obj:
                text = file_obj.read()
            self.assertIn("正常", text)
            self.assertIn("throughput_samples_per_sec", text)

            with open(replay_path, "r", encoding="utf-8") as file_obj:
                row = next(csv.reader(file_obj))
            self.assertEqual(row, ["1", "2", "3", "4", "0"])

    def test_latest_summary_contains_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = RunExporter(
                "serial",
                {
                    "enabled": True,
                    "runs_dir": temp_dir,
                    "timestamp_format": "%Y%m%d_%H%M%S",
                },
            )
            exporter.append_ecg_sample(100)
            exporter.finalize()
            summary = exporter.latest_summary()
            self.assertIn("模式: serial", summary)
            self.assertIn("metrics.jsonl", summary)
            self.assertIn("diagnosis.csv", summary)
            self.assertIn("ecg_replay.csv", summary)

    def test_latest_summary_highlights_run_result_and_engineering_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = RunExporter(
                "offline",
                {
                    "enabled": True,
                    "runs_dir": temp_dir,
                    "timestamp_format": "%Y%m%d_%H%M%S",
                },
            )
            metrics = {
                "diagnosis_count": 1,
                "last_inference_ms": 9.5,
                "throughput_samples_per_sec": 160.0,
            }

            exporter.append_diagnosis(0, "正常", metrics)
            summary = exporter.latest_summary()

            self.assertIn("运行模式: offline", summary)
            self.assertIn("导出目录:", summary)
            self.assertIn("诊断次数: 1", summary)
            self.assertIn("最近诊断: 正常 (0)", summary)
            self.assertIn("单次推理: 9.5 ms", summary)
            self.assertIn("吞吐量: 160.0 点/s", summary)

    def test_latest_summary_when_disabled(self):
        exporter = RunExporter(
            "serial",
            {
                "enabled": False,
                "runs_dir": "",
                "timestamp_format": "%Y%m%d_%H%M%S",
            },
        )
        self.assertEqual(exporter.latest_summary(), "导出未启用")


if __name__ == "__main__":
    unittest.main()
