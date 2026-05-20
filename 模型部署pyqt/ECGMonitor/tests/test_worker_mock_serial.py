import threading
import time
import unittest
from unittest import mock

from PyQt5 import QtCore

from PackUnpack import PackUnpack
from serial_worker import SerialInferenceWorker


def build_packet(raw):
    pkt = list(raw)
    ok = PackUnpack().packData(pkt)
    if not ok:
        raise RuntimeError("pack failed")
    return bytes(pkt)


class FakeSerial:
    stream = []

    def __init__(self, *args, **kwargs):
        self.is_open = True
        self._chunks = list(self.stream)
        self.written = []

    @property
    def in_waiting(self):
        return len(self._chunks[0]) if self._chunks else 0

    def read(self, _n):
        if self._chunks:
            return self._chunks.pop(0)
        time.sleep(0.005)
        return b""

    def write(self, data):
        self.written.append(bytes(data))

    def close(self):
        self.is_open = False


class WorkerTest(unittest.TestCase):
    @mock.patch("serial_worker.serial.Serial", new=FakeSerial)
    def test_worker_processes_stream(self):
        FakeSerial.stream = [
            build_packet([0x10, 0x02, 0x07, 0xD0]),
            build_packet([0x10, 0x03, 0x00]),
            build_packet([0x10, 0x04, 0x00, 0x48]),
        ]

        worker = SerialInferenceWorker("COM1", 115200, 8, 1, "N")
        ecg_samples = []
        lead_states = []
        heart_rates = []

        worker.ecg_sample.connect(ecg_samples.append, type=QtCore.Qt.DirectConnection)
        worker.lead_status.connect(lead_states.append, type=QtCore.Qt.DirectConnection)
        worker.heart_rate.connect(heart_rates.append, type=QtCore.Qt.DirectConnection)

        t = threading.Thread(target=worker.run, daemon=True)
        t.start()
        time.sleep(0.08)
        worker.stop()
        t.join(timeout=1.0)

        self.assertIn(2000, ecg_samples)
        self.assertIn(0, lead_states)
        self.assertIn(72, heart_rates)

    @mock.patch("serial_worker.load_model_contract", return_value={"input": {"window_size": 3}})
    @mock.patch("serial_worker.serial.Serial", new=FakeSerial)
    def test_worker_stream_emits_diagnosis_and_metrics(self, _mock_contract):
        FakeSerial.stream = [
            build_packet([0x10, 0x02, 0x07, 0xD0]),
            build_packet([0x10, 0x02, 0x07, 0xD0]),
            build_packet([0x10, 0x02, 0x07, 0xD0]),
        ]

        worker = SerialInferenceWorker("COM1", 115200, 8, 1, "N")
        diagnosis = []
        metrics = []
        worker.diagnosis.connect(diagnosis.append, type=QtCore.Qt.DirectConnection)
        worker.metrics_updated.connect(metrics.append, type=QtCore.Qt.DirectConnection)

        with mock.patch("serial_worker.predict", return_value=7):
            t = threading.Thread(target=worker.run, daemon=True)
            t.start()
            time.sleep(0.08)
            worker.stop()
            t.join(timeout=1.0)

        self.assertEqual(diagnosis, [7])
        self.assertTrue(metrics)
        self.assertEqual(metrics[-1]["ecg_packets"], 3)
        self.assertEqual(metrics[-1]["diagnosis_count"], 1)


if __name__ == "__main__":
    unittest.main()
