import csv
import json
import os
import tempfile
import unittest

from demo_readiness import DemoReadinessError, check_demo_readiness


def _valid_contract(model_file="best_acc.pt", window_size=4):
    return {
        "contract_version": 1,
        "model_name": "best_acc",
        "model_file": model_file,
        "framework": "torchscript",
        "device": "cpu",
        "input": {
            "window_size": window_size,
            "shape": ["B", 1, window_size],
            "dtype": "float32",
        },
        "preprocessing": {
            "normalization": "min_max",
            "min_val": 1582.0,
            "max_val": 2444.0,
        },
        "output": {
            "num_classes": 12,
            "labels": [
                "正常",
                "RT室早",
                "ST上移",
                "ST下移",
                "窦性房颤",
                "窦性室颤",
                "单发室早",
                "窦性静止",
                "二联律",
                "房扑",
                "房早",
                "双重起搏",
            ],
        },
    }


class DemoReadinessTest(unittest.TestCase):
    def _write_contract(self, tmpdir, contract=None):
        contract_path = os.path.join(tmpdir, "best_acc.contract.json")
        with open(contract_path, "w", encoding="utf-8") as file_obj:
            json.dump(contract or _valid_contract(), file_obj, ensure_ascii=False)
        return contract_path

    def _write_model(self, tmpdir, filename="best_acc.pt"):
        model_path = os.path.join(tmpdir, filename)
        with open(model_path, "wb") as file_obj:
            file_obj.write(b"fake-model")
        return model_path

    def _write_csv(self, tmpdir, rows):
        csv_path = os.path.join(tmpdir, "test.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as file_obj:
            writer = csv.writer(file_obj)
            writer.writerows(rows)
        return csv_path

    def _policy(self, csv_path, contract_path, **overrides):
        policy = {
            "input_csv": csv_path,
            "source_type": "test_csv",
            "row": 0,
            "samples": 4,
            "event_interval": 2,
            "lead_events": [0, 0],
            "hr_events": [72, 84],
            "model_contract_path": contract_path,
        }
        policy.update(overrides)
        return policy

    def test_check_demo_readiness_accepts_valid_assets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model(tmpdir)
            contract_path = self._write_contract(tmpdir)
            csv_path = self._write_csv(tmpdir, [[2000, 2001, 2002, 2003, 0]])

            result = check_demo_readiness(self._policy(csv_path, contract_path))

        self.assertEqual(result["window_size"], 4)
        self.assertEqual(result["source"]["used_samples"], 4)
        self.assertEqual(result["source"]["source_label"], 0)

    def test_check_demo_readiness_reports_missing_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = self._write_csv(tmpdir, [[2000, 2001, 2002, 2003, 0]])
            missing_contract = os.path.join(tmpdir, "missing.contract.json")

            with self.assertRaises(DemoReadinessError) as ctx:
                check_demo_readiness(self._policy(csv_path, missing_contract))

        self.assertIn("模型契约不存在", str(ctx.exception))

    def test_check_demo_readiness_reports_missing_model_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = self._write_contract(tmpdir)
            csv_path = self._write_csv(tmpdir, [[2000, 2001, 2002, 2003, 0]])

            with self.assertRaises(DemoReadinessError) as ctx:
                check_demo_readiness(self._policy(csv_path, contract_path))

        self.assertIn("模型文件不存在", str(ctx.exception))

    def test_check_demo_readiness_reports_missing_sample_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model(tmpdir)
            contract_path = self._write_contract(tmpdir)
            missing_csv = os.path.join(tmpdir, "missing.csv")

            with self.assertRaises(DemoReadinessError) as ctx:
                check_demo_readiness(self._policy(missing_csv, contract_path))

        self.assertIn("样例数据不存在", str(ctx.exception))

    def test_check_demo_readiness_reports_invalid_row(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model(tmpdir)
            contract_path = self._write_contract(tmpdir)
            csv_path = self._write_csv(tmpdir, [[2000, 2001, 2002, 2003, 0]])

            with self.assertRaises(DemoReadinessError) as ctx:
                check_demo_readiness(self._policy(csv_path, contract_path, row=3))

        self.assertIn("demo row 无效", str(ctx.exception))

    def test_check_demo_readiness_reports_short_sample_row(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model(tmpdir)
            contract_path = self._write_contract(tmpdir)
            csv_path = self._write_csv(tmpdir, [[2000, 2001, 0]])

            with self.assertRaises(DemoReadinessError) as ctx:
                check_demo_readiness(self._policy(csv_path, contract_path, samples=4))

        self.assertIn("样例数据不足", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
