import copy
import logging
import time
from typing import Optional, Sequence

from PyQt5 import QtCore
import serial

from ecg_pipeline import EcgProcessingPipeline
from PackUnpack import PackUnpack
from config import MODEL_CONTRACT_PATH
from example import predict
from model_contract import load_model_contract

logger = logging.getLogger(__name__)


class SerialInferenceWorker(QtCore.QObject):
    opened = QtCore.pyqtSignal(str)
    closed = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)
    ecg_sample = QtCore.pyqtSignal(int)
    diagnosis = QtCore.pyqtSignal(int)
    lead_status = QtCore.pyqtSignal(int)
    heart_rate = QtCore.pyqtSignal(int)
    metrics_updated = QtCore.pyqtSignal(dict)

    def __init__(self, port: str, baud_rate: int, data_bits: int, stop_bits: int, parity: str):
        super().__init__()
        self._port = port
        self._baud_rate = baud_rate
        self._data_bits = data_bits
        self._stop_bits = stop_bits
        self._parity = parity

        self._running = False
        self._serial: Optional[serial.Serial] = None
        self._unpacker = PackUnpack()
        self._window_size = load_model_contract(MODEL_CONTRACT_PATH)["input"]["window_size"]
        self._pipeline = EcgProcessingPipeline(
            window_size=self._window_size,
            predict_func=lambda values: predict(values),
            on_ecg_sample=self.ecg_sample.emit,
            on_diagnosis=self.diagnosis.emit,
            on_lead_status=self.lead_status.emit,
            on_heart_rate=self.heart_rate.emit,
            on_metrics=self.metrics_updated.emit,
            on_error=self.error.emit,
        )
        self._metrics = self._pipeline.metrics
        self._started_at = 0.0

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baud_rate,
                bytesize=self._data_bits,
                stopbits=self._stop_bits,
                parity=self._parity,
                timeout=0.05,
            )
            self._running = True
            self._started_at = time.perf_counter()
            self._pipeline.started_at = self._started_at
            self.opened.emit(self._port)
        except Exception as exc:
            logger.exception("Failed to open serial port")
            self.error.emit(f"串口打开失败: {exc}")
            self.closed.emit()
            return

        try:
            while self._running:
                data = self._serial.read(self._serial.in_waiting or 1)
                if not data:
                    continue

                for byte in data:
                    if self._unpacker.unpackData(byte):
                        packet = copy.deepcopy(self._unpacker.getUnpackRslt())
                        self._process_packet(packet)
        except Exception as exc:
            logger.exception("Serial worker loop error")
            self.error.emit(f"串口读取异常: {exc}")
        finally:
            self._refresh_runtime()
            self._close_serial()
            logger.info("Serial worker stopped with metrics: %s", self._metrics.snapshot())
            self.metrics_updated.emit(self._metrics.snapshot())
            self.closed.emit()

    @QtCore.pyqtSlot(object)
    def send_data(self, data: Sequence[int]):
        if not self._serial or not self._serial.is_open:
            return
        try:
            self._serial.write(bytes(data))
        except Exception as exc:
            logger.exception("Failed to send serial data")
            self.error.emit(f"串口发送失败: {exc}")

    def stop(self):
        self._running = False

    def _close_serial(self):
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                logger.exception("Failed to close serial port")

    def _process_packet(self, packet):
        self._pipeline.process_packet(packet)

    def _refresh_runtime(self):
        if self._started_at > 0:
            self._metrics.refresh_runtime(self._started_at)
