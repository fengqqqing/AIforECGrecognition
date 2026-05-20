import csv
import os
import unittest
from unittest import mock

import torch

from example import predict


class _FakeModel:
    def __init__(self):
        self.last_input = None

    def __call__(self, x):
        self.last_input = x
        out = torch.zeros((x.shape[0], 12), dtype=torch.float32)
        out[:, 5] = 1.0
        return out


def _contract(window_size=2000, min_val=1582.0, max_val=2444.0):
    return {
        "model_file": "best_acc.pt",
        "input": {
            "window_size": window_size,
            "shape": ["B", 1, window_size],
            "dtype": "float32",
        },
        "preprocessing": {
            "normalization": "min_max",
            "min_val": min_val,
            "max_val": max_val,
        },
        "output": {
            "num_classes": 12,
            "labels": [""] * 12,
        },
    }


class PredictTest(unittest.TestCase):
    @mock.patch("example._get_contract", return_value=_contract())
    @mock.patch("example._get_model", return_value=_FakeModel())
    def test_predict_output_range(self, _mock_model, _mock_contract):
        csv_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "test.csv")
        with open(csv_path, "r", encoding="utf-8") as f:
            row = next(csv.reader(f))

        values = [float(x) for x in row[:2000]]
        result = predict(values)

        self.assertIsInstance(result, int)
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 11)

    @mock.patch("example._get_contract", return_value=_contract())
    @mock.patch("example._get_model", return_value=_FakeModel())
    def test_predict_rejects_short_window_from_contract(self, _mock_model, _mock_contract):
        with self.assertRaises(ValueError):
            predict([1.0] * 1999)

    @mock.patch("example._get_contract", return_value=_contract(window_size=4, min_val=10.0, max_val=14.0))
    def test_predict_uses_contract_window_and_normalization(self, _mock_contract):
        fake_model = _FakeModel()

        with mock.patch("example._get_model", return_value=fake_model):
            result = predict([10.0, 11.0, 12.0, 13.0, 14.0])

        self.assertEqual(result, 5)
        self.assertEqual(tuple(fake_model.last_input.shape), (1, 1, 4))
        self.assertTrue(
            torch.allclose(
                fake_model.last_input,
                torch.tensor([[[0.25, 0.5, 0.75, 1.0]]], dtype=torch.float32),
            )
        )


if __name__ == "__main__":
    unittest.main()
