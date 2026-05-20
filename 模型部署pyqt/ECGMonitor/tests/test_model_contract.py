import json
import os
import tempfile
import unittest

from model_contract import load_model_contract


def _valid_contract(model_file="best_acc.pt"):
    return {
        "contract_version": 1,
        "model_name": "best_acc",
        "model_file": model_file,
        "framework": "torchscript",
        "device": "cpu",
        "input": {
            "window_size": 2000,
            "shape": ["B", 1, 2000],
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


class ModelContractTest(unittest.TestCase):
    def _write_contract(self, tmpdir, contract):
        contract_path = os.path.join(tmpdir, "best_acc.contract.json")
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(contract, f, ensure_ascii=False)
        return contract_path

    def _write_model_file(self, tmpdir):
        model_path = os.path.join(tmpdir, "best_acc.pt")
        with open(model_path, "wb") as f:
            f.write(b"fake-model")
        return model_path

    def test_load_model_contract_accepts_valid_contract(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model_file(tmpdir)
            contract_path = self._write_contract(tmpdir, _valid_contract())

            contract = load_model_contract(contract_path)

        self.assertEqual(contract["model_file"], "best_acc.pt")
        self.assertEqual(contract["input"]["window_size"], 2000)

    def test_load_model_contract_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model_file(tmpdir)
            contract = _valid_contract()
            del contract["preprocessing"]["min_val"]
            contract_path = self._write_contract(tmpdir, contract)

            with self.assertRaises(ValueError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_non_positive_window_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model_file(tmpdir)
            contract = _valid_contract()
            contract["input"]["window_size"] = 0
            contract_path = self._write_contract(tmpdir, contract)

            with self.assertRaises(ValueError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_invalid_normalization_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model_file(tmpdir)
            contract = _valid_contract()
            contract["preprocessing"]["min_val"] = 2444.0
            contract["preprocessing"]["max_val"] = 1582.0
            contract_path = self._write_contract(tmpdir, contract)

            with self.assertRaises(ValueError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_label_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._write_model_file(tmpdir)
            contract = _valid_contract()
            contract["output"]["labels"] = contract["output"]["labels"][:-1]
            contract_path = self._write_contract(tmpdir, contract)

            with self.assertRaises(ValueError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_missing_model_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = self._write_contract(tmpdir, _valid_contract())

            with self.assertRaises(FileNotFoundError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_absolute_model_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract = _valid_contract(os.path.join(tmpdir, "best_acc.pt"))
            contract_path = self._write_contract(tmpdir, contract)

            with self.assertRaises(ValueError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_parent_directory_model_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract = _valid_contract(os.path.join("..", "best_acc.pt"))
            contract_path = self._write_contract(tmpdir, contract)

            with self.assertRaises(ValueError):
                load_model_contract(contract_path)

    def test_load_model_contract_rejects_unsupported_runtime_contract_values(self):
        invalid_cases = [
            (("contract_version",), 2),
            (("framework",), "onnx"),
            (("device",), "cuda"),
            (("input", "dtype"), "float64"),
            (("preprocessing", "normalization"), "z_score"),
            (("input", "shape"), ["B", 1, 1000]),
        ]

        for field_path, value in invalid_cases:
            with self.subTest(field=".".join(field_path)):
                with tempfile.TemporaryDirectory() as tmpdir:
                    self._write_model_file(tmpdir)
                    contract = _valid_contract()
                    current = contract
                    for field_name in field_path[:-1]:
                        current = current[field_name]
                    current[field_path[-1]] = value
                    contract_path = self._write_contract(tmpdir, contract)

                    with self.assertRaises(ValueError):
                        load_model_contract(contract_path)


if __name__ == "__main__":
    unittest.main()
