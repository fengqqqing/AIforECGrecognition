import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import offline_replay
from replay_utils import load_replay_source, parse_int_list, resolve_replay_input


class OfflineReplayTest(unittest.TestCase):
    def test_parse_int_list(self):
        self.assertEqual(parse_int_list(""), [])
        self.assertEqual(parse_int_list("1,2,3"), [1, 2, 3])
        self.assertEqual(parse_int_list(" 72, 88 , 65 "), [72, 88, 65])

    def test_load_replay_source_reads_signal_and_label(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow([1, 2, 3, 4, 7])
            temp_path = temp_file.name

        try:
            source = load_replay_source(temp_path, row_index=0, requested_samples=3)
            self.assertEqual(source["values"], [1, 2, 3])
            self.assertEqual(source["available_samples"], 4)
            self.assertEqual(source["used_samples"], 3)
            self.assertEqual(source["source_label"], 7)
            self.assertEqual(source["row_count"], 1)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_load_replay_source_supports_rows_with_nonnumeric_tail(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow(["1.0", "2.0", "3.0", "note"])
            temp_path = temp_file.name

        try:
            source = load_replay_source(temp_path, row_index=0, requested_samples=5)
            self.assertEqual(source["values"], [1, 2, 3])
            self.assertEqual(source["available_samples"], 3)
            self.assertEqual(source["used_samples"], 3)
            self.assertIsNone(source["source_label"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_resolve_replay_input_uses_explicit_path(self):
        self.assertEqual(resolve_replay_input(r"C:\temp\demo.csv", use_latest=False), r"C:\temp\demo.csv")

    def test_resolve_replay_input_selects_latest_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_dir = os.path.join(temp_dir, "20260513_100000_serial")
            second_dir = os.path.join(temp_dir, "20260513_101500_serial")
            os.makedirs(first_dir, exist_ok=True)
            os.makedirs(second_dir, exist_ok=True)

            first_file = os.path.join(first_dir, "ecg_replay.csv")
            second_file = os.path.join(second_dir, "ecg_replay.csv")
            with open(first_file, "w", encoding="utf-8", newline="") as file_obj:
                csv.writer(file_obj).writerow([1, 2, 3, 0])
            with open(second_file, "w", encoding="utf-8", newline="") as file_obj:
                csv.writer(file_obj).writerow([4, 5, 6, 1])

            os.utime(first_file, (1000, 1000))
            os.utime(second_file, (2000, 2000))

            resolved = resolve_replay_input("", use_latest=True, runs_dir=temp_dir)
            self.assertEqual(resolved, second_file)

    def test_resolve_replay_input_raises_when_latest_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(FileNotFoundError):
                resolve_replay_input("", use_latest=True, runs_dir=temp_dir)

    def test_main_replays_with_module_predict_boundary(self):
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", encoding="utf-8", suffix=".csv") as temp_file:
            writer = csv.writer(temp_file)
            writer.writerow([2000, 2000, 2000, 2])
            temp_path = temp_file.name

        try:
            output = io.StringIO()
            argv = [
                "offline_replay.py",
                "--input",
                temp_path,
                "--samples",
                "3",
                "--event-interval",
                "0",
                "--real-model",
            ]

            with mock.patch("sys.argv", argv), mock.patch(
                "offline_replay.load_model_contract", return_value={"input": {"window_size": 3}}
            ), mock.patch("offline_replay.predict", return_value=2), redirect_stdout(output):
                offline_replay.main()

            text = output.getvalue()
            self.assertIn("Inference mode: real-model", text)
            self.assertIn("Diagnosis count: 1", text)
            self.assertIn("Latest diagnosis: 2", text)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
