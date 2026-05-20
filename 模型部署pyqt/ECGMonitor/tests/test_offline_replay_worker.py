import csv
import os
import tempfile
import unittest
from unittest import mock

from PyQt5 import QtCore

from offline_replay_worker import OfflineReplayWorker
from replay_utils import SOURCE_TYPE_TEST_CSV


class OfflineReplayWorkerTest(unittest.TestCase):
    def test_load_values_from_csv(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow([1, 2, 3, 4, 0])
            temp_path = temp_file.name

        try:
            worker = OfflineReplayWorker(
                {
                    "source_type": SOURCE_TYPE_TEST_CSV,
                    "input_csv": temp_path,
                    "row": 0,
                    "samples": 3,
                    "event_interval": 0,
                    "lead_events": [],
                    "hr_events": [],
                    "mock_label": 0,
                    "use_real_model": False,
                    "frame_sleep_ms": 0,
                }
            )
            source = worker._policy["input_csv"]
            self.assertEqual(source, temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_run_emits_ai_diagnosis_metrics_and_summary(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(([2000] * 2000) + [0])
            temp_path = temp_file.name

        try:
            worker = OfflineReplayWorker(
                {
                    "source_type": SOURCE_TYPE_TEST_CSV,
                    "input_csv": temp_path,
                    "row": 0,
                    "samples": 2000,
                    "event_interval": 0,
                    "lead_events": [],
                    "hr_events": [],
                    "mock_label": 4,
                    "use_real_model": False,
                    "frame_sleep_ms": 0,
                }
            )
            diagnosis = []
            metrics = []
            summaries = []

            worker.diagnosis.connect(diagnosis.append, type=QtCore.Qt.DirectConnection)
            worker.metrics_updated.connect(metrics.append, type=QtCore.Qt.DirectConnection)
            worker.replay_summary.connect(summaries.append, type=QtCore.Qt.DirectConnection)

            worker.run()

            self.assertEqual(diagnosis, [4])
            self.assertTrue(metrics)
            self.assertEqual(metrics[-1]["diagnosis_count"], 1)
            self.assertEqual(metrics[-1]["ecg_packets"], 2000)
            self.assertTrue(summaries)
            self.assertEqual(summaries[-1]["source_label"], 0)
            self.assertEqual(summaries[-1]["latest_diagnosis"], 4)
            self.assertFalse(summaries[-1]["used_real_model"])
            self.assertFalse(summaries[-1]["matched"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_run_emits_lead_and_heart_rate_events(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(([2000] * 10) + [0])
            temp_path = temp_file.name

        try:
            worker = OfflineReplayWorker(
                {
                    "source_type": SOURCE_TYPE_TEST_CSV,
                    "input_csv": temp_path,
                    "row": 0,
                    "samples": 10,
                    "event_interval": 5,
                    "lead_events": [0, 1],
                    "hr_events": [72, 88],
                    "mock_label": 0,
                    "use_real_model": False,
                    "frame_sleep_ms": 0,
                }
            )
            lead_states = []
            heart_rates = []
            metrics = []

            worker.lead_status.connect(lead_states.append, type=QtCore.Qt.DirectConnection)
            worker.heart_rate.connect(heart_rates.append, type=QtCore.Qt.DirectConnection)
            worker.metrics_updated.connect(metrics.append, type=QtCore.Qt.DirectConnection)

            worker.run()

            self.assertEqual(lead_states, [0, 1])
            self.assertEqual(heart_rates, [72, 88])
            self.assertTrue(metrics)
            self.assertEqual(metrics[-1]["lead_events"], 2)
            self.assertEqual(metrics[-1]["heart_rate_events"], 2)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_run_emits_summary_for_real_model_compare(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(([2000] * 2000) + [3])
            temp_path = temp_file.name

        try:
            worker = OfflineReplayWorker(
                {
                    "source_type": SOURCE_TYPE_TEST_CSV,
                    "input_csv": temp_path,
                    "row": 0,
                    "samples": 2000,
                    "event_interval": 0,
                    "lead_events": [],
                    "hr_events": [],
                    "mock_label": 0,
                    "use_real_model": True,
                    "frame_sleep_ms": 0,
                }
            )
            summaries = []
            worker.replay_summary.connect(summaries.append, type=QtCore.Qt.DirectConnection)

            with mock.patch("offline_replay_worker.predict", return_value=3):
                worker.run()

            self.assertTrue(summaries)
            self.assertEqual(summaries[-1]["source_label"], 3)
            self.assertEqual(summaries[-1]["latest_diagnosis"], 3)
            self.assertTrue(summaries[-1]["used_real_model"])
            self.assertTrue(summaries[-1]["matched"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_run_emits_error_and_closed_when_pipeline_initialization_fails(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(([2000] * 3) + [0])
            temp_path = temp_file.name

        try:
            worker = OfflineReplayWorker(
                {
                    "source_type": SOURCE_TYPE_TEST_CSV,
                    "input_csv": temp_path,
                    "row": 0,
                    "samples": 3,
                    "event_interval": 0,
                    "lead_events": [],
                    "hr_events": [],
                    "mock_label": 0,
                    "use_real_model": False,
                    "frame_sleep_ms": 0,
                }
            )
            errors = []
            closed = []
            worker.error.connect(errors.append, type=QtCore.Qt.DirectConnection)
            worker.closed.connect(lambda: closed.append(True), type=QtCore.Qt.DirectConnection)

            with self.assertLogs("offline_replay_worker", level="ERROR"), mock.patch(
                "offline_replay_worker.load_model_contract", side_effect=RuntimeError("bad contract")
            ):
                worker.run()

            self.assertEqual(len(closed), 1)
            self.assertEqual(len(errors), 1)
            self.assertIn("离线回放初始化失败", errors[0])
            self.assertIn("bad contract", errors[0])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
