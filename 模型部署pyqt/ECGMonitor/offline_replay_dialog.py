# 离线回放设置对话框模块
# 职责：提供 GUI 表单让用户配置离线回放参数（数据源、样本数、事件节奏、
#       模拟标签、帧间隔、导联/心率事件列表等），确认后返回更新后的 policy dict。

from PyQt5 import QtWidgets

from replay_utils import SOURCE_TYPE_LATEST_REPLAY, SOURCE_TYPE_TEST_CSV, parse_int_list


def _format_event_list(values):
    return ",".join(str(v) for v in values)


class OfflineReplayDialog(QtWidgets.QDialog):
    """离线回放设置对话框：表单输入 -> 确认后返回 policy dict。"""

    def __init__(self, policy: dict, parent=None):
        """policy: 当前回放策略 dict，对话框初始化时从其中加载默认值。"""
        super().__init__(parent)
        self._policy = dict(policy)
        self.setWindowTitle("离线回放设置")
        self.resize(460, 360)
        self._build_ui()
        self._load_policy()

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.sourceTypeCombo = QtWidgets.QComboBox(self)
        self.sourceTypeCombo.addItem("测试文件 test.csv", SOURCE_TYPE_TEST_CSV)
        self.sourceTypeCombo.addItem("最新回放文件 ecg_replay.csv", SOURCE_TYPE_LATEST_REPLAY)

        self.inputEdit = QtWidgets.QLineEdit(self)
        self.realModelCheck = QtWidgets.QCheckBox("使用真实模型推理", self)

        self.rowSpin = QtWidgets.QSpinBox(self)
        self.rowSpin.setMinimum(0)
        self.rowSpin.setMaximum(999999)

        self.samplesSpin = QtWidgets.QSpinBox(self)
        self.samplesSpin.setMinimum(1)
        self.samplesSpin.setMaximum(999999)

        self.eventIntervalSpin = QtWidgets.QSpinBox(self)
        self.eventIntervalSpin.setMinimum(0)
        self.eventIntervalSpin.setMaximum(999999)

        self.mockLabelSpin = QtWidgets.QSpinBox(self)
        self.mockLabelSpin.setMinimum(0)
        self.mockLabelSpin.setMaximum(99)

        self.frameSleepSpin = QtWidgets.QSpinBox(self)
        self.frameSleepSpin.setMinimum(0)
        self.frameSleepSpin.setMaximum(10000)

        self.leadEventsEdit = QtWidgets.QLineEdit(self)
        self.hrEventsEdit = QtWidgets.QLineEdit(self)

        layout.addRow("数据源", self.sourceTypeCombo)
        layout.addRow("输入 CSV", self.inputEdit)
        layout.addRow("", self.realModelCheck)
        layout.addRow("数据行号", self.rowSpin)
        layout.addRow("回放样本数", self.samplesSpin)
        layout.addRow("事件间隔", self.eventIntervalSpin)
        layout.addRow("模拟标签", self.mockLabelSpin)
        layout.addRow("帧间隔(ms)", self.frameSleepSpin)
        layout.addRow("导联事件", self.leadEventsEdit)
        layout.addRow("心率事件", self.hrEventsEdit)

        self.sourceTypeCombo.currentIndexChanged.connect(self._sync_source_mode)
        self.realModelCheck.toggled.connect(self._sync_model_mode)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _load_policy(self):
        source_type = self._policy.get("source_type", SOURCE_TYPE_TEST_CSV)
        self._set_combo_data(self.sourceTypeCombo, source_type)
        self.inputEdit.setText(self._policy.get("input_csv", ""))
        self.realModelCheck.setChecked(bool(self._policy.get("use_real_model", False)))
        self.rowSpin.setValue(int(self._policy.get("row", 0)))
        self.samplesSpin.setValue(int(self._policy.get("samples", 2000)))
        self.eventIntervalSpin.setValue(int(self._policy.get("event_interval", 500)))
        self.mockLabelSpin.setValue(int(self._policy.get("mock_label", 0)))
        self.frameSleepSpin.setValue(int(self._policy.get("frame_sleep_ms", 1)))
        self.leadEventsEdit.setText(_format_event_list(self._policy.get("lead_events", [])))
        self.hrEventsEdit.setText(_format_event_list(self._policy.get("hr_events", [])))
        self._sync_source_mode()
        self._sync_model_mode()

    @staticmethod
    def _set_combo_data(combo: QtWidgets.QComboBox, value: str):
        for index in range(combo.count()):
            if combo.itemData(index) == value:
                combo.setCurrentIndex(index)
                return

    def _sync_source_mode(self):
        source_type = self.sourceTypeCombo.currentData()
        use_test_file = source_type == SOURCE_TYPE_TEST_CSV
        self.inputEdit.setEnabled(use_test_file)
        if not use_test_file:
            self.inputEdit.setPlaceholderText("将自动使用 runs 目录下最新的 ecg_replay.csv")
        else:
            self.inputEdit.setPlaceholderText("")

    def _sync_model_mode(self):
        self.mockLabelSpin.setEnabled(not self.realModelCheck.isChecked())

    def get_policy(self):
        """返回用户配置后的回放策略 dict，供 ParamMonitor 启动回放使用。"""
        return {
            "source_type": self.sourceTypeCombo.currentData(),
            "input_csv": self.inputEdit.text().strip(),
            "use_real_model": self.realModelCheck.isChecked(),
            "row": self.rowSpin.value(),
            "samples": self.samplesSpin.value(),
            "event_interval": self.eventIntervalSpin.value(),
            "lead_events": parse_int_list(self.leadEventsEdit.text()),
            "hr_events": parse_int_list(self.hrEventsEdit.text()),
            "mock_label": self.mockLabelSpin.value(),
            "frame_sleep_ms": self.frameSleepSpin.value(),
        }
