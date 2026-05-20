import io
import os
import unittest
from unittest import mock

import example


class _FakeLoadedModel:
    def eval(self):
        return self


class _FakeOutputModel:
    def __init__(self, shape=None, output=None):
        self.shape = shape
        self.output = output

    def __call__(self, x):
        import torch

        if self.output is not None:
            return self.output
        return torch.zeros(self.shape, dtype=torch.float32)


class ExampleModelLoadingTest(unittest.TestCase):
    def tearDown(self):
        example._MODEL = None
        if hasattr(example, "_MODEL_CONTRACT"):
            example._MODEL_CONTRACT = None

    def _contract(self, model_file="best_acc.pt"):
        return {
            "model_file": model_file,
            "input": {"window_size": 2000},
            "preprocessing": {"min_val": 1582.0, "max_val": 2444.0},
            "output": {"num_classes": 12, "labels": [""] * 12},
        }

    @mock.patch("example.torch.jit.load")
    @mock.patch("example.load_model_contract")
    @mock.patch("example.os.path.exists", return_value=True)
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=b"model-bytes")
    def test_get_model_loads_from_memory_stream(self, mock_open_file, _mock_exists, mock_contract, mock_load):
        fake_model = _FakeLoadedModel()
        mock_load.return_value = fake_model
        mock_contract.return_value = self._contract("contract-model.pt")

        model = example._get_model()

        self.assertIs(model, fake_model)
        opened_path = mock_open_file.call_args.args[0]
        self.assertEqual(os.path.basename(opened_path), "contract-model.pt")
        load_arg = mock_load.call_args.args[0]
        self.assertIsInstance(load_arg, io.BytesIO)
        self.assertEqual(load_arg.getvalue(), b"model-bytes")

    @mock.patch("example.load_model_contract")
    @mock.patch("example.os.path.exists", return_value=False)
    def test_get_model_raises_when_file_missing(self, _mock_exists, mock_contract):
        mock_contract.return_value = self._contract("missing-model.pt")

        with self.assertRaises(FileNotFoundError):
            example._get_model()

    @mock.patch("example.load_model_contract")
    def test_get_model_rejects_unsafe_contract_model_path(self, mock_contract):
        mock_contract.return_value = self._contract(os.path.join("..", "outside.pt"))

        with self.assertRaises(ValueError):
            example._get_model()

    @mock.patch("example.load_model_contract", side_effect=FileNotFoundError("contract missing"))
    def test_warmup_model_raises_when_contract_missing(self, _mock_load_contract):
        with self.assertRaises(FileNotFoundError):
            example.warmup_model()

    @mock.patch("example.load_model_contract", side_effect=ValueError("label count mismatch"))
    def test_warmup_model_raises_when_contract_labels_mismatch(self, _mock_load_contract):
        with self.assertRaises(ValueError):
            example.warmup_model()

    @mock.patch("example._get_contract")
    @mock.patch("example._get_model")
    def test_warmup_model_rejects_output_class_mismatch(self, mock_get_model, mock_get_contract):
        contract = self._contract()
        contract["input"]["window_size"] = 4
        contract["output"]["num_classes"] = 12
        mock_get_contract.return_value = contract
        mock_get_model.return_value = _FakeOutputModel(shape=(1, 11))

        with self.assertRaises(ValueError):
            example.warmup_model()

    @mock.patch("example._get_contract")
    @mock.patch("example._get_model")
    def test_warmup_model_rejects_extra_output_dimensions(self, mock_get_model, mock_get_contract):
        contract = self._contract()
        contract["input"]["window_size"] = 4
        contract["output"]["num_classes"] = 12
        mock_get_contract.return_value = contract
        mock_get_model.return_value = _FakeOutputModel(shape=(1, 12, 8))

        with self.assertRaises(ValueError):
            example.warmup_model()

    @mock.patch("example._get_contract")
    @mock.patch("example._get_model")
    def test_warmup_model_rejects_non_tensor_output(self, mock_get_model, mock_get_contract):
        contract = self._contract()
        contract["input"]["window_size"] = 4
        contract["output"]["num_classes"] = 12
        mock_get_contract.return_value = contract
        mock_get_model.return_value = _FakeOutputModel(output=[[0.0] * 12])

        with self.assertRaises(ValueError):
            example.warmup_model()


if __name__ == "__main__":
    unittest.main()
