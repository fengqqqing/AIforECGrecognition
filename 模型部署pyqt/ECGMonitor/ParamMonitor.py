# *_* coding : UTF-8 *_*
# ECG Monitor 主窗口模块
# 职责：作为 PyQt 上位机的 UI 协调层，负责：
#   - 串口采集 Worker 和离线回放 Worker 的生命周期管理（启动/停止/重连）
#   - ECG 实时波形绘制（QPainter 滚动式绘制）
#   - 诊断结果、心率、导联状态、运行指标的 UI 展示
#   - 导出目录管理、最近运行摘要展示
#   - Demo 模式自动启动
# 边界：不直接承担协议解析、模型加载和导出细节，这些由各自的模块负责。

import logging
import os
import sys
from statistics import median

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint
from PyQt5.QtGui import QColor, QStatusTipEvent, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QAction, QLabel, QMessageBox, QPushButton
from PyQt5 import QtGui

from ParamMonitor_ui import Ui_MainWindow
from config import DEMO_REPLAY_POLICY, EXPORT_POLICY, OFFLINE_REPLAY_POLICY, RECONNECT_POLICY, UI_LIMITS
from demo_readiness import DemoReadinessError, check_demo_readiness
from form_setuart import UartSet
from example import warmup_model
from offline_replay_dialog import OfflineReplayDialog
from offline_replay_worker import OfflineReplayWorker
from replay_utils import SOURCE_TYPE_LATEST_REPLAY, resolve_replay_path_from_policy
from run_exporter import RunExporter
from serial_worker import SerialInferenceWorker
from ui_theme import (
    ECG_MONITOR_THEME,
    apply_main_window_theme,
    get_metric_caption_style,
    get_metric_card_style,
    get_metric_value_style,
    get_metrics_label_style,
    get_mode_badge_style,
)
from ui_rules import (
    format_metrics_panel_values,
    get_assistant_result_hint,
    get_diagnosis_label,
    get_diagnosis_style,
    get_heart_rate_style,
    get_lead_status_style,
    get_lead_status_text,
    get_ui_state_copy,
    format_worker_metrics,
    is_lead_connected,
    should_display_heart_rate,
)

logger = logging.getLogger(__name__)

THREAD_STOP_TIMEOUT_MS = 3000     # Worker 线程停止等待超时（毫秒），超时后强制 terminate
WAVE_GRID_MINOR_PX = 10           # 波形背景小网格间距（像素）
WAVE_GRID_MAJOR_PX = 40           # 波形背景大网格间距（像素）
WAVE_DEFAULT_BASELINE = 2048      # ECG 波形默认基线值（ADC 中间值）
WAVE_DISPLAY_SCALE = 7            # ECG 采样值到像素的缩放因子
WAVE_BASELINE_SMOOTHING = 0.25    # 基线平滑系数（EMA），避免波形上下跳动


def resource_path(*parts):
    """获取资源文件路径，兼容 PyInstaller 打包后的 _MEIPASS 临时目录。"""
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, *parts)


class ParamMonitor(QtWidgets.QMainWindow, Ui_MainWindow):
    """ECG Monitor 主窗口：UI 事件调度、Worker 生命周期管理、波形绘制、状态展示。"""
    sendSerialData = QtCore.pyqtSignal(object)

    def __init__(self, demo_mode=False):
        super(ParamMonitor, self).__init__()
        self.setupUi(self)
        self.init()

        # --- 波形绘制状态 ---
        self.mECG1WaveList = []  # ECG 采样点缓冲区，定时器取出并绘制
        self.mECG1XStep = 0      # 波形绘制的 X 轴游标位置，到达右边界后归零（环形绘制）
        self.waveDisplayBaseline = None  # 波形显示基线（EMA 平滑后的中位数）
        self.maxECG1Length = self.ecg1WaveLabel.width()
        self.maxECG1Height = self.ecg1WaveLabel.height()
        self.pixmapECG1 = QPixmap(self.ecg1WaveLabel.width(), self.ecg1WaveLabel.height())
        self.painterEcg1 = QPainter(self.pixmapECG1)
        self.draw_wave_background()
        self.ecg1WaveLabel.setPixmap(self.pixmapECG1)
        self.ecg1WaveLabel.installEventFilter(self)

        # --- Worker 生命周期状态 ---
        self.serial_thread = None
        self.serial_worker = None
        self.serial_running = False
        self.offline_thread = None
        self.offline_worker = None
        self.offline_running = False
        self.offline_policy = dict(OFFLINE_REPLAY_POLICY)
        self.last_serial_config = None       # 上次串口配置，用于自动重连
        self.manual_disconnect = False       # 用户手动断开时设为 True，阻止自动重连
        self.reconnect_pending = False       # 标记是否需要自动重连
        self.reconnect_attempts = 0          # 当前重连尝试次数
        self.last_error_message = ""         # 最近一次错误信息
        self.current_metrics = {}            # 当前运行指标快照
        self.run_exporter = None             # 当前运行的导出器
        self.last_run_exporter = None        # 上一次运行的导出器（用于"最近摘要"）
        self.last_offline_summary = None     # 离线回放完成后的结果对照摘要
        self.model_ready = False             # 模型契约检查是否通过
        self.demo_ready = False              # Demo 预检是否通过
        self.demo_readiness = None           # Demo 预检结果
        self.demo_readiness_error = ""       # Demo 预检失败原因
        self.demo_mode = bool(demo_mode)     # 是否以 Demo 模式启动
        self.demo_replay_active = False      # Demo 回放是否正在运行

        try:
            warmup_model()
            self.model_ready = True
        except Exception as exc:
            message = f"模型契约检查失败: {exc}"
            logger.exception(message)
            self.last_error_message = message
            self.statusStr = message
            self.statusBar().showMessage(message)
            QMessageBox.warning(self, "模型契约检查失败", message)

        if self.demo_mode:
            self.check_demo_readiness_at_startup()
            if self.demo_ready:
                QTimer.singleShot(0, self.start_demo_mode)

    def init(self):
        """初始化 UI 交互：菜单栏、定时器、布局、主题、模式横幅。"""
        self.menu1 = QAction(self)
        self.menu1.setText('串口设置')
        self.menubar.addAction(self.menu1)
        self.menu1.triggered.connect(self.slot_serialSet)

        self.menu2 = QAction(self)
        self.menu2.setText('退出')
        self.menubar.addAction(self.menu2)
        self.menu2.triggered.connect(self.slot_quit)

        self.statusStr = '串口未打开'
        self.statusBar().showMessage(self.statusStr)
        self.helpButton = QPushButton("说明", self)
        self.helpButton.setObjectName("helpButton")
        self.helpButton.clicked.connect(self.slot_showHelp)
        self.statusBar().addPermanentWidget(self.helpButton)
        self.setup_top_actions()
        self.setup_runtime_icons()
        self.setup_responsive_layout()
        self.setup_right_info_panel()
        self.setup_metrics_panel()
        apply_main_window_theme(self)
        self.apply_ui_state("idle")
        self.update_metrics_display({})
        self.heartRateLabel.setStyleSheet(get_heart_rate_style(0))
        self.heartRateTextLabel_2.setStyleSheet(get_lead_status_style(-1))

        self.waveDrawTimer = QTimer(self)
        self.waveDrawTimer.timeout.connect(self.on_draw_wave)
        self.waveDrawTimer.start(16)

        self.reconnectTimer = QTimer(self)
        self.reconnectTimer.setSingleShot(True)
        self.reconnectTimer.timeout.connect(self.try_reconnect)

        self.heartShapeTimer = QTimer(self)
        self.heartShapeTimer.timeout.connect(self.heartShapeFlash)
        self.heartShapeTimer.start(500)
        self.heartLabel_3.setVisible(False)

    def setup_runtime_icons(self):
        icon_map = (
            (self.heartLabel, "24gf-heartPulse.png"),
            (self.heartLabel_3, "24gf-heartPulse.png"),
            (self.connectStateLabel_5, "connected.png"),
            (self.connectStateLabel, "未连接.png"),
        )
        for label, filename in icon_map:
            pixmap = QPixmap(resource_path("image", filename))
            if pixmap.isNull():
                logger.warning("UI icon not found: %s", filename)
            label.setPixmap(pixmap)

    def demo_policy_summary(self):
        return f"固定场景 row={DEMO_REPLAY_POLICY['row']} · {DEMO_REPLAY_POLICY['samples']} 点"

    def setup_top_actions(self):
        self.topActionFrame = QtWidgets.QFrame(self.topBarFrame)
        self.topActionFrame.setObjectName("topActionFrame")
        self.topActionLayout = QtWidgets.QHBoxLayout(self.topActionFrame)
        self.topActionLayout.setContentsMargins(0, 0, 0, 0)
        self.topActionLayout.setSpacing(6)

        actions = (
            ("replayActionButton", "离线回放", "1. 启动离线回放，模拟一次 ECG 采集与初筛流程", lambda: self.slot_offlineReplay()),
            ("configActionButton", "回放设置", "调整样本数、事件节奏和模型模式", lambda: self.slot_offlineReplayConfig()),
            ("summaryActionButton", "最近摘要", "查看最近一次运行的摘要和结果对照", lambda: self.slot_showLatestSummary()),
            ("exportActionButton", "导出目录", "打开 metrics、diagnosis 和 replay 导出目录", lambda: self.slot_openExportDir()),
            ("resetActionButton", "重置显示", "清空当前展示，准备重新运行", lambda: self.slot_resetDisplay()),
        )
        for name, text, tooltip, handler in actions:
            button = QPushButton(text, self.topActionFrame)
            button.setObjectName(name)
            button.setFixedHeight(28)
            button.setToolTip(tooltip)
            button.setStatusTip(tooltip)
            button.clicked.connect(handler)
            self.topActionLayout.addWidget(button)
            setattr(self, name, button)

        self.topBarLayout.insertWidget(3, self.topActionFrame)

    def setup_responsive_layout(self):
        self.setMinimumSize(QtCore.QSize(1024, 560))

        self.rootLayout.setContentsMargins(8, 6, 8, 6)
        self.rootLayout.setSpacing(6)
        self.rootLayout.setStretch(0, 0)
        self.rootLayout.setStretch(1, 1)
        self.rootLayout.setStretch(2, 0)

        self.topBarFrame.setMinimumHeight(82)
        self.topBarFrame.setMaximumHeight(112)
        self.topBarFrame.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.topBarLayout.setContentsMargins(12, 6, 12, 6)
        self.topBarLayout.setSpacing(8)
        self.topActionFrame.setFixedHeight(28)
        self.modeBadgeLabel.setFixedHeight(28)
        self.modeBadgeLabel.setMinimumWidth(118)
        mode_font = self.modeBadgeLabel.font()
        mode_font.setPointSize(10)
        self.modeBadgeLabel.setFont(mode_font)

        self.mainContentFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.waveformCard.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.waveformLayout.setContentsMargins(10, 8, 10, 10)
        self.waveformLayout.setSpacing(6)
        self.waveformLayout.setStretch(0, 0)
        self.waveformLayout.setStretch(1, 1)
        self.ecg1WaveLabel.setMinimumSize(QtCore.QSize(460, 180))
        self.ecg1WaveLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setup_right_scroll_area()

        self.metricsPanel.setMinimumHeight(64)
        self.metricsPanel.setMaximumHeight(80)
        self.metricsPanel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.metricsPanelLayout.setContentsMargins(10, 5, 10, 5)
        self.metricsPanelLayout.setSpacing(6)

    def setup_right_scroll_area(self):
        if hasattr(self, "rightInfoScrollArea"):
            return

        self.rightInfoScrollArea = QtWidgets.QScrollArea(self.mainContentFrame)
        self.rightInfoScrollArea.setObjectName("rightInfoScrollArea")
        self.rightInfoScrollArea.setWidgetResizable(True)
        self.rightInfoScrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.rightInfoScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rightInfoScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.rightInfoScrollArea.setMinimumWidth(280)
        self.rightInfoScrollArea.setMaximumWidth(340)
        self.rightInfoScrollArea.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        index = self.mainContentLayout.indexOf(self.rightInfoPanel)
        self.mainContentLayout.removeWidget(self.rightInfoPanel)
        self.rightInfoScrollArea.setWidget(self.rightInfoPanel)
        self.mainContentLayout.insertWidget(index, self.rightInfoScrollArea)

    def setup_right_info_panel(self):
        for layout in (self.aiResultLayout, self.heartRateLayout, self.leadStatusLayout):
            layout.setContentsMargins(8, 5, 8, 5)
            layout.setSpacing(3)

        self.rightInfoLayout.setSpacing(5)
        self.aiResultCard.setMinimumHeight(84)
        self.aiResultCard.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
        self.aiResultCard.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.heartRateCard.setMinimumHeight(70)
        self.heartRateCard.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
        self.heartRateCard.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.leadStatusCard.setMinimumHeight(96)
        self.leadStatusCard.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
        self.leadStatusCard.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.heartRateLayout.setContentsMargins(8, 4, 8, 4)
        self.leadStatusLayout.setContentsMargins(8, 4, 8, 4)

        self.connectStateLabel_2.setMinimumSize(QtCore.QSize(80, 28))
        self.connectStateLabel_2.setMaximumSize(QtCore.QSize(180, QtWidgets.QWIDGETSIZE_MAX))
        self.connectStateLabel_2.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        self.aiResultLayout.setAlignment(self.connectStateLabel_2, Qt.AlignHCenter)
        result_font = self.connectStateLabel_2.font()
        result_font.setPointSize(20)
        self.connectStateLabel_2.setFont(result_font)
        self.assistantHintLabel.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)

        self.heartLabel.setMaximumSize(QtCore.QSize(26, 26))
        self.heartLabel.setMinimumSize(QtCore.QSize(26, 26))
        self.heartLabel_3.setMaximumSize(QtCore.QSize(24, 24))
        self.heartLabel_3.setMinimumSize(QtCore.QSize(24, 24))
        self.heartRateValueLayout.setSpacing(6)
        heart_font = self.heartRateLabel.font()
        heart_font.setPointSize(18)
        self.heartRateLabel.setFont(heart_font)
        unit_font = self.heartRateUnitLabel.font()
        unit_font.setPointSize(18)
        self.heartRateUnitLabel.setFont(unit_font)
        heart_value_height = self.heartRateLabel.fontMetrics().height() + 4
        self.heartRateLabel.setMinimumSize(QtCore.QSize(54, heart_value_height))
        self.heartRateLabel.setMaximumSize(QtCore.QSize(76, QtWidgets.QWIDGETSIZE_MAX))
        self.heartRateLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.heartRateUnitLabel.setMinimumSize(QtCore.QSize(48, heart_value_height))
        self.heartRateUnitLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        self.connectStateLabel_5.setMaximumSize(QtCore.QSize(24, 24))
        self.connectStateLabel_5.setMinimumSize(QtCore.QSize(24, 24))
        self.connectStateLabel.setMaximumSize(QtCore.QSize(24, 24))
        self.connectStateLabel.setMinimumSize(QtCore.QSize(24, 24))
        self.leadStatusTitleLabel.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
        self.leadStatusTitleLabel.setMinimumHeight(self.leadStatusTitleLabel.fontMetrics().height() + 2)
        self.leadStatusTitleLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.leadStatusLayout.setSpacing(4)
        self.leadStatusLayout.setAlignment(Qt.AlignTop)
        self.leadStatusLayout.insertSpacing(2, 4)
        self.leadStatusValueLayout.setContentsMargins(0, 0, 0, 0)
        self.leadStatusValueLayout.setSpacing(6)
        self.leadStatusValueLayout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        lead_font = self.heartRateTextLabel_2.font()
        lead_font.setPointSize(13)
        self.heartRateTextLabel_2.setFont(lead_font)
        lead_badge_height = self.heartRateTextLabel_2.fontMetrics().height() + 6
        self.heartRateTextLabel_2.setMinimumSize(QtCore.QSize(76, lead_badge_height))
        self.heartRateTextLabel_2.setMaximumSize(QtCore.QSize(122, QtWidgets.QWIDGETSIZE_MAX))
        self.heartRateTextLabel_2.setAlignment(Qt.AlignCenter)
        self.heartRateTextLabel_2.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.leadStatusValueLayout.setAlignment(self.heartRateTextLabel_2, Qt.AlignVCenter)
        self.leadStructureLabel.setText("三导联单通道 · 脱落监测")
        self.leadStructureLabel.setMaximumHeight(QtWidgets.QWIDGETSIZE_MAX)
        self.leadStructureLabel.setMinimumHeight(self.leadStructureLabel.fontMetrics().height() * 2 + 4)
        self.leadStructureLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.leadStructureLabel.setWordWrap(True)
        self.leadStructureLabel.setAlignment(Qt.AlignCenter)

    def update_mode_banner(self, badge_text, detail_text, hint_text):
        self.modeBadgeLabel.setText(badge_text)
        self.demoPolicyLabel.setText(detail_text)
        self.modeHintLabel.setText(hint_text)
        if "不可用" in badge_text or "失败" in hint_text:
            state = "warning"
        elif "待机" in badge_text:
            state = "unknown"
        else:
            state = "normal"
        self.modeBadgeLabel.setStyleSheet(get_mode_badge_style(state))

    def apply_ui_state(self, state, detail=""):
        copy = get_ui_state_copy(state, detail=detail)
        self.update_mode_banner(copy["badge"], copy["detail"], copy["hint"])
        return copy

    def setup_metrics_panel(self):
        self.metric_value_labels = {}
        self.metricsSummaryLabel.setStyleSheet(get_metrics_label_style())
        self.metricsSummaryLabel.setText(format_worker_metrics({}))
        self.metricsSummaryLabel.setVisible(False)

        metrics = (
            ("metricPacket", "包计数", "packets"),
            ("metricDiagnosis", "诊断次数", "diagnosis"),
            ("metricInference", "单次推理", "latency"),
            ("metricThroughput", "吞吐量", "throughput"),
            ("metricEvent", "事件计数", "events"),
        )
        for index, (prefix, title, value_key) in enumerate(metrics, start=1):
            card = QtWidgets.QFrame(self.metricsPanel)
            card.setObjectName(f"{prefix}Card")
            card.setStyleSheet(get_metric_card_style())
            card.setMinimumWidth(100)

            layout = QtWidgets.QVBoxLayout(card)
            layout.setContentsMargins(10, 4, 10, 4)
            layout.setSpacing(1)

            caption = QLabel(title, card)
            caption.setObjectName(f"{prefix}CaptionLabel")
            caption.setStyleSheet(get_metric_caption_style())

            value = QLabel("--", card)
            value.setObjectName(f"{prefix}ValueLabel")
            value.setStyleSheet(get_metric_value_style())
            value.setMinimumHeight(22)
            value.setMaximumHeight(24)
            value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            layout.addWidget(caption)
            layout.addWidget(value)
            self.metricsPanelLayout.insertWidget(index, card)

            setattr(self, f"{prefix}Card", card)
            setattr(self, f"{prefix}CaptionLabel", caption)
            setattr(self, f"{prefix}ValueLabel", value)
            self.metric_value_labels[value_key] = value

    def update_metrics_display(self, metrics):
        text = format_worker_metrics(metrics)
        self.metricsSummaryLabel.setText(text)
        values = format_metrics_panel_values(metrics)
        for key, label in self.metric_value_labels.items():
            label.setText(values[key])

    def slot_serialSet(self):
        if self.offline_running:
            self.stop_offline_worker()
        self.uartset = UartSet(self.serial_running)
        self.uartset.serialSignal.connect(self.slot_serial)
        self.uartset.show()

    def slot_serial(self, portNum, baudRate, dataBits, stopBits, parity):
        if self.serial_running:
            self.stop_serial_worker(manual=True)
            self.statusStr = "串口已关闭"
            self.statusBar().showMessage(self.statusStr)
            return

        self.start_serial_worker(portNum, baudRate, dataBits, stopBits, parity)

    def start_serial_worker(self, portNum, baudRate, dataBits, stopBits, parity):
        """启动串口采集 Worker：创建 QThread + SerialInferenceWorker，连接信号。"""
        if not self.model_ready:
            self.show_model_not_ready("无法启动串口真实推理")
            return

        self.stop_serial_worker(manual=False)
        self.stop_offline_worker()
        self.manual_disconnect = False
        self.reconnect_pending = False
        self.last_error_message = ""
        self.current_metrics = {}
        self.run_exporter = RunExporter("serial")
        self.last_serial_config = {
            "portNum": portNum,
            "baudRate": baudRate,
            "dataBits": dataBits,
            "stopBits": stopBits,
            "parity": parity,
        }

        self.serial_thread = QtCore.QThread(self)
        self.serial_worker = SerialInferenceWorker(
            port=portNum,
            baud_rate=int(baudRate),
            data_bits=int(dataBits),
            stop_bits=int(stopBits),
            parity=parity,
        )
        self.serial_worker.moveToThread(self.serial_thread)

        self.serial_thread.started.connect(self.serial_worker.run)
        self.serial_worker.opened.connect(self.on_serial_opened)
        self.serial_worker.closed.connect(self.on_serial_closed)
        self.serial_worker.error.connect(self.on_serial_error)
        self.serial_worker.ecg_sample.connect(self.on_ecg_sample)
        self.serial_worker.diagnosis.connect(self.on_diagnosis)
        self.serial_worker.lead_status.connect(self.on_lead_status)
        self.serial_worker.heart_rate.connect(self.on_heart_rate)
        self.serial_worker.metrics_updated.connect(self.on_metrics_updated)
        self.serial_worker.closed.connect(self.serial_thread.quit)
        self.serial_thread.finished.connect(self.on_serial_thread_finished)
        self.sendSerialData.connect(self.serial_worker.send_data)

        self.serial_thread.start()
        self.statusStr = "串口连接中..."
        self.statusBar().showMessage(self.statusStr)
        self.update_mode_banner("串口连接中", f"{portNum} · {baudRate}bps", "等待设备数据")

    def slot_offlineReplay(self):
        if self.offline_running:
            self.stop_offline_worker()
            self.statusStr = "离线回放已停止"
            self.statusBar().showMessage(self.statusStr)
            return

        self.start_offline_worker()

    def slot_offlineReplayConfig(self):
        dialog = OfflineReplayDialog(self.offline_policy, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.offline_policy = dialog.get_policy()
            self.statusStr = "离线回放参数已更新"
            self.statusBar().showMessage(self.statusStr)

    def slot_openExportDir(self):
        runs_dir = EXPORT_POLICY["runs_dir"]
        os.makedirs(runs_dir, exist_ok=True)
        os.startfile(runs_dir)

    def latest_summary_text(self):
        exporter = self.run_exporter or self.last_run_exporter
        if exporter is None:
            return "当前还没有可展示的运行摘要。"

        summary = exporter.latest_summary()
        if not self.last_offline_summary:
            return summary

        matched = self.last_offline_summary.get("matched")
        if matched is True:
            matched_text = "是"
        elif matched is False:
            matched_text = "否"
        else:
            matched_text = "未对照"

        return (
            f"{summary}\n"
            "\n"
            "回放对照:\n"
            f"来源文件: {self.last_offline_summary.get('source_path', '')}\n"
            f"源标签: {self.last_offline_summary.get('source_label', '未知')}\n"
            f"本次诊断: {self.last_offline_summary.get('latest_diagnosis', '未产生')}\n"
            f"诊断次数: {self.last_offline_summary.get('diagnosis_count', 0)}\n"
            f"真实模型: {'是' if self.last_offline_summary.get('used_real_model') else '否'}\n"
            f"是否一致: {matched_text}"
        )

    def slot_showLatestSummary(self):
        exporter = self.run_exporter or self.last_run_exporter
        if exporter is None:
            QMessageBox.information(self, "最近运行摘要", "当前还没有可展示的运行摘要。")
            return
        dialog = QMessageBox(self)
        dialog.setWindowTitle("最近运行摘要")
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(self.latest_summary_text())
        open_replay_button = None
        if exporter.replay_path and os.path.exists(exporter.replay_path):
            open_replay_button = dialog.addButton("打开回放文件", QMessageBox.ActionRole)
        open_dir_button = dialog.addButton("打开导出目录", QMessageBox.ActionRole)
        dialog.addButton(QMessageBox.Ok)
        dialog.exec_()

        clicked = dialog.clickedButton()
        if open_replay_button is not None and clicked == open_replay_button:
            os.startfile(exporter.replay_path)
        elif clicked == open_dir_button and exporter.base_dir:
            os.startfile(exporter.base_dir)

    def slot_showHelp(self):
        message = (
            "界面功能说明\n"
            "\n"
            "1. 串口设置：连接或断开在线串口设备。\n"
            "2. 离线回放：使用 CSV 心电数据进行无设备回放测试。\n"
            "3. 回放设置：配置离线回放样本数、事件节奏等参数。\n"
            "4. 打开导出目录：查看本次或历史运行导出的指标、诊断和回放文件。\n"
            "5. 最近运行摘要：显示当前最近一次运行的导出路径和关键结果。\n"
            "6. 重置显示：清空波形缓存、诊断标签和心率/导联显示。\n"
            "\n"
            "运行指标说明\n"
            "\n"
            "- 包：已处理的数据包总数。\n"
            "- ECG：已接收的心电采样点数。\n"
            "- 诊断：已完成的 AI 推理次数。\n"
            "- 导联：收到的导联状态事件次数。\n"
            "- 心率：收到的心率事件次数。\n"
            "- 单次推理：最近一次 AI 推理的耗时。\n"
            "- 吞吐量：从本次运行开始到当前为止，平均每秒处理的 ECG 采样点数。\n"
            "\n"
            "导出文件说明\n"
            "\n"
            "- metrics.jsonl：运行过程中的指标快照。\n"
            "- diagnosis.csv：每次 AI 诊断的结果记录。\n"
            "- ecg_replay.csv：本次采集的 ECG 波形，可作为后续离线回放输入。"
        )
        QMessageBox.information(self, "界面说明", message)

    def slot_resetDisplay(self):
        self.reset_display_state()
        self.statusStr = "显示已重置"
        self.statusBar().showMessage(self.statusStr)
        self.apply_ui_state("reset")

    def start_offline_worker(self):
        """启动离线回放 Worker：创建 QThread + OfflineReplayWorker，连接信号。"""
        if self.offline_policy.get("use_real_model") and not self.model_ready:
            self.show_model_not_ready("无法启动真实模型回放")
            return

        self.stop_serial_worker(manual=False)
        self.stop_offline_worker()
        try:
            resolved_path = resolve_replay_path_from_policy(self.offline_policy)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "离线回放", str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "离线回放", f"离线回放配置无效: {exc}")
            return

        self.last_offline_summary = None
        self.current_metrics = {}
        self.run_exporter = RunExporter("offline")

        self.offline_thread = QtCore.QThread(self)
        replay_policy = dict(self.offline_policy)
        replay_policy["resolved_input_csv"] = resolved_path
        self.offline_worker = OfflineReplayWorker(replay_policy)
        self.offline_worker.moveToThread(self.offline_thread)

        self.offline_thread.started.connect(self.offline_worker.run)
        self.offline_worker.opened.connect(self.on_offline_opened)
        self.offline_worker.closed.connect(self.on_offline_closed)
        self.offline_worker.error.connect(self.on_serial_error)
        self.offline_worker.ecg_sample.connect(self.on_ecg_sample)
        self.offline_worker.diagnosis.connect(self.on_diagnosis)
        self.offline_worker.lead_status.connect(self.on_lead_status)
        self.offline_worker.heart_rate.connect(self.on_heart_rate)
        self.offline_worker.metrics_updated.connect(self.on_metrics_updated)
        self.offline_worker.replay_summary.connect(self.on_offline_replay_summary)
        self.offline_worker.closed.connect(self.offline_thread.quit)
        self.offline_thread.finished.connect(self.on_offline_thread_finished)

        self.offline_thread.start()
        self.statusStr = "Demo 演示启动中..." if self.demo_replay_active else "离线回放启动中..."
        self.statusBar().showMessage(self.statusStr)
        if self.demo_replay_active:
            self.apply_ui_state("demo_starting", self.demo_policy_summary())
        else:
            self.apply_ui_state("replay_starting")

    def start_demo_mode(self):
        if not self.demo_ready:
            self.show_demo_not_ready("无法启动 Demo 演示")
            return
        if DEMO_REPLAY_POLICY.get("use_real_model") and not self.model_ready:
            self.show_model_not_ready("无法启动 Demo 真实模型演示")
            return

        self.offline_policy = dict(DEMO_REPLAY_POLICY)
        self.demo_replay_active = True
        self.statusStr = "Demo 演示启动中..."
        self.statusBar().showMessage(self.statusStr)
        self.apply_ui_state("demo_starting", self.demo_policy_summary())
        self.start_offline_worker()

    def check_demo_readiness_at_startup(self):
        try:
            self.demo_readiness = check_demo_readiness()
            self.demo_ready = True
            self.demo_readiness_error = ""
            self.apply_ui_state("demo_ready", self.demo_policy_summary())
        except DemoReadinessError as exc:
            self.demo_ready = False
            self.demo_readiness = None
            self.demo_readiness_error = str(exc)
            self.statusStr = self.demo_readiness_error
            self.statusBar().showMessage(self.statusStr)
            self.apply_ui_state("error", "Demo 预检未通过")
            QMessageBox.warning(self, "Demo 预检失败", self.demo_readiness_error)
        except Exception as exc:
            self.demo_ready = False
            self.demo_readiness = None
            self.demo_readiness_error = f"Demo 预检失败: {exc}"
            self.statusStr = self.demo_readiness_error
            self.statusBar().showMessage(self.statusStr)
            self.apply_ui_state("error", "Demo 预检未通过")
            QMessageBox.warning(self, "Demo 预检失败", self.demo_readiness_error)

    def show_demo_not_ready(self, action):
        detail = self.demo_readiness_error or "Demo 预检未通过"
        message = f"{action}：{detail}"
        self.statusStr = message
        self.statusBar().showMessage(message)
        self.apply_ui_state("error", "Demo 预检未通过")
        QMessageBox.warning(self, "Demo 未就绪", message)

    def show_model_not_ready(self, action):
        detail = self.last_error_message or "模型契约检查未通过"
        message = f"{action}：{detail}"
        self.statusStr = message
        self.statusBar().showMessage(message)
        self.apply_ui_state("error", "模型契约检查未通过")
        QMessageBox.warning(self, "模型未就绪", message)

    def stop_serial_worker(self, manual=True):
        """停止串口采集 Worker：停止 worker -> 等待线程退出 -> 断开信号 -> finalize 导出。"""
        if manual:
            self.manual_disconnect = True
            self.reconnect_pending = False
            self.reconnect_attempts = 0
            self.last_error_message = ""
            self.reconnectTimer.stop()

        if self.serial_worker is not None:
            self.serial_worker.stop()

        if self.serial_thread is not None:
            self.serial_thread.quit()
            if not self.serial_thread.wait(THREAD_STOP_TIMEOUT_MS):
                logger.warning("Serial thread did not stop in time; terminating thread")
                self.serial_thread.terminate()
                self.serial_thread.wait(THREAD_STOP_TIMEOUT_MS)

        if self.serial_worker is not None:
            try:
                self.sendSerialData.disconnect(self.serial_worker.send_data)
            except Exception:
                pass

        if self.serial_thread is not None and not self.serial_thread.isRunning():
            self.serial_worker = None
            self.serial_thread = None

        self.serial_running = False
        if self.run_exporter is not None:
            self.run_exporter.finalize()
            self.last_run_exporter = self.run_exporter
            self.run_exporter = None
        self.update_metrics_display({})
        if not self.offline_running:
            self.apply_ui_state("idle")

    def stop_offline_worker(self):
        """停止离线回放 Worker：停止 worker -> 等待线程退出 -> finalize 导出。"""
        if self.offline_worker is not None:
            self.offline_worker.stop()

        if self.offline_thread is not None:
            self.offline_thread.quit()
            if not self.offline_thread.wait(THREAD_STOP_TIMEOUT_MS):
                logger.warning("Offline thread did not stop in time; terminating thread")
                self.offline_thread.terminate()
                self.offline_thread.wait(THREAD_STOP_TIMEOUT_MS)

        if self.offline_thread is not None and not self.offline_thread.isRunning():
            self.offline_worker = None
            self.offline_thread = None

        self.offline_running = False
        if self.run_exporter is not None:
            self.run_exporter.finalize()
        self.last_run_exporter = self.run_exporter
        self.run_exporter = None
        self.update_metrics_display({})
        if not self.serial_running and not self.demo_replay_active:
            self.apply_ui_state("idle")

    @QtCore.pyqtSlot(str)
    def on_serial_opened(self, port_name):
        self.serial_running = True
        self.reconnect_pending = False
        self.reconnect_attempts = 0
        self.statusStr = f"串口已打开: {port_name}"
        self.statusBar().showMessage(self.statusStr)
        self.apply_ui_state("serial_running", port_name)

    @QtCore.pyqtSlot(str)
    def on_offline_opened(self, _source_name):
        self.offline_running = True
        self.statusStr = "Demo 演示进行中..." if self.demo_replay_active else "离线回放进行中..."
        self.statusBar().showMessage(self.statusStr)
        if self.demo_replay_active:
            self.apply_ui_state("demo_running", self.demo_policy_summary())
        else:
            self.apply_ui_state("replay_running")

    @QtCore.pyqtSlot()
    def on_serial_closed(self):
        self.serial_running = False

    @QtCore.pyqtSlot()
    def on_offline_closed(self):
        self.offline_running = False

    @QtCore.pyqtSlot()
    def on_serial_thread_finished(self):
        self.serial_running = False
        self.serial_worker = None
        self.serial_thread = None
        if self.reconnect_pending and not self.manual_disconnect:
            self.schedule_reconnect()

    @QtCore.pyqtSlot()
    def on_offline_thread_finished(self):
        demo_was_active = self.demo_replay_active
        self.offline_running = False
        self.offline_worker = None
        self.offline_thread = None
        if self.run_exporter is not None:
            self.run_exporter.finalize()
            self.last_run_exporter = self.run_exporter
            self.run_exporter = None
        if not self.serial_running:
            if demo_was_active:
                self.statusStr = "Demo 演示已完成，可通过“最近运行摘要”查看导出结果"
                self.apply_ui_state("demo_completed", self.demo_policy_summary())
            else:
                self.statusStr = "离线回放已完成"
                self.apply_ui_state("replay_completed")
            self.statusBar().showMessage(self.statusStr)
        self.demo_replay_active = False
        if self.last_offline_summary and self.last_offline_summary.get("used_real_model"):
            source_label = self.last_offline_summary.get("source_label")
            latest_diagnosis = self.last_offline_summary.get("latest_diagnosis")
            if source_label is not None and latest_diagnosis is not None:
                matched = self.last_offline_summary.get("matched")
                QMessageBox.information(
                    self,
                    "离线回放结果对照",
                    (
                        f"来源文件: {self.last_offline_summary.get('source_path', '')}\n"
                        f"源标签: {source_label}\n"
                        f"本次诊断: {latest_diagnosis}\n"
                        f"是否一致: {'是' if matched else '否'}"
                    ),
                )

    @QtCore.pyqtSlot(str)
    def on_serial_error(self, message):
        logger.error(message)
        self.last_error_message = message
        self.statusStr = message
        self.statusBar().showMessage(self.statusStr)
        if not self.manual_disconnect:
            self.reconnect_pending = True

    @QtCore.pyqtSlot(dict)
    def on_metrics_updated(self, metrics):
        self.current_metrics = dict(metrics)
        self.update_metrics_display(metrics)
        if self.run_exporter is not None:
            self.run_exporter.append_metrics(metrics)

    @QtCore.pyqtSlot(dict)
    def on_offline_replay_summary(self, summary):
        self.last_offline_summary = dict(summary)

    def schedule_reconnect(self):
        if not RECONNECT_POLICY["enabled"] or self.last_serial_config is None:
            return
        if self.reconnect_attempts >= RECONNECT_POLICY["max_attempts"]:
            self.reconnect_pending = False
            self.statusStr = f"{self.last_error_message}，已停止自动重连"
            self.statusBar().showMessage(self.statusStr)
            return
        if self.reconnectTimer.isActive():
            return
        self.reconnect_attempts += 1
        self.statusStr = (
            f"{self.last_error_message}，"
            f"{RECONNECT_POLICY['interval_ms'] // 1000}秒后尝试重连"
            f"（第{self.reconnect_attempts}/{RECONNECT_POLICY['max_attempts']}次）"
        )
        self.statusBar().showMessage(self.statusStr)
        self.reconnectTimer.start(RECONNECT_POLICY["interval_ms"])

    def try_reconnect(self):
        if self.manual_disconnect or not self.reconnect_pending or self.last_serial_config is None:
            return
        logger.info("Attempting serial reconnect #%s", self.reconnect_attempts)
        self.start_serial_worker(**self.last_serial_config)

    @QtCore.pyqtSlot(int)
    def on_ecg_sample(self, ecg_value):
        self.mECG1WaveList.append(ecg_value)
        if self.run_exporter is not None:
            self.run_exporter.append_ecg_sample(ecg_value)

    @QtCore.pyqtSlot(int)
    def on_diagnosis(self, result):
        label = get_diagnosis_label(result)
        if not label:
            return

        self.connectStateLabel_2.setText(label)
        self.connectStateLabel_2.setAlignment(Qt.AlignCenter)
        self.connectStateLabel_2.setStyleSheet(get_diagnosis_style(result))
        self.assistantHintLabel.setText(get_assistant_result_hint(result))
        if self.run_exporter is not None:
            self.run_exporter.append_diagnosis(result, label, self.current_metrics)

    @QtCore.pyqtSlot(int)
    def on_lead_status(self, status):
        self.heartRateTextLabel_2.setText(get_lead_status_text(status))
        self.heartRateTextLabel_2.setStyleSheet(get_lead_status_style(status))
        if is_lead_connected(status):
            self.connectStateLabel_5.setVisible(True)
            self.connectStateLabel.setVisible(False)
        else:
            self.connectStateLabel_5.setVisible(False)
            self.connectStateLabel.setVisible(True)

    @QtCore.pyqtSlot(int)
    def on_heart_rate(self, hr):
        if should_display_heart_rate(hr):
            self.heartRateLabel.setText(str(hr))
            self.heartRateLabel.setAlignment(Qt.AlignRight)
        else:
            self.heartRateLabel.setText("--")
        self.heartRateLabel.setStyleSheet(get_heart_rate_style(hr))

    def on_draw_wave(self):
        """定时器回调（16ms）：缓冲区有足够数据时触发波形绘制。"""
        if len(self.mECG1WaveList) > UI_LIMITS["wave_draw_threshold"]:
            self.drawECG1Wave()

    def reset_display_state(self):
        self.mECG1WaveList.clear()
        self.mECG1XStep = 0
        self.waveDisplayBaseline = None
        self.draw_wave_background()
        self.ecg1WaveLabel.setPixmap(self.pixmapECG1)
        self.connectStateLabel_2.setText("")
        self.assistantHintLabel.setText(get_assistant_result_hint(None))
        self.heartRateLabel.setText("--")
        self.heartRateLabel.setStyleSheet(get_heart_rate_style(0))
        self.heartRateTextLabel_2.setText("导联未知")
        self.heartRateTextLabel_2.setStyleSheet(get_lead_status_style(-1))
        self.connectStateLabel_5.setVisible(False)
        self.connectStateLabel.setVisible(True)
        self.current_metrics = {}
        self.update_metrics_display({})

    def data_send(self, data):
        if self.serial_running and self.serial_worker is not None:
            self.sendSerialData.emit(data)

    def draw_wave_background(self, rect=None):
        if rect is None:
            rect = QRect(0, 0, self.maxECG1Length, self.maxECG1Height)

        colors = ECG_MONITOR_THEME["colors"]
        self.painterEcg1.save()
        self.painterEcg1.setClipRect(rect)
        self.painterEcg1.fillRect(rect, QColor(colors["wave_background"]))

        self.painterEcg1.setPen(QPen(QColor(colors["wave_grid_minor"]), 1, Qt.SolidLine))
        start_x = rect.left() - (rect.left() % WAVE_GRID_MINOR_PX)
        for x in range(start_x, rect.right() + 1, WAVE_GRID_MINOR_PX):
            self.painterEcg1.drawLine(x, rect.top(), x, rect.bottom())
        start_y = rect.top() - (rect.top() % WAVE_GRID_MINOR_PX)
        for y in range(start_y, rect.bottom() + 1, WAVE_GRID_MINOR_PX):
            self.painterEcg1.drawLine(rect.left(), y, rect.right(), y)

        self.painterEcg1.setPen(QPen(QColor(colors["wave_grid"]), 1, Qt.SolidLine))
        start_x = rect.left() - (rect.left() % WAVE_GRID_MAJOR_PX)
        for x in range(start_x, rect.right() + 1, WAVE_GRID_MAJOR_PX):
            self.painterEcg1.drawLine(x, rect.top(), x, rect.bottom())
        start_y = rect.top() - (rect.top() % WAVE_GRID_MAJOR_PX)
        for y in range(start_y, rect.bottom() + 1, WAVE_GRID_MAJOR_PX):
            self.painterEcg1.drawLine(rect.left(), y, rect.right(), y)
        self.painterEcg1.restore()

    def drawECG1Wave(self):
        """核心波形绘制：清空旧区域 -> 逐点连线 -> 更新游标 -> 环形回绕。"""
        iCnt = len(self.mECG1WaveList)
        if iCnt >= self.maxECG1Length - self.mECG1XStep:
            rct = QRect(self.mECG1XStep, 0, self.maxECG1Length - self.mECG1XStep, self.maxECG1Height)
            self.draw_wave_background(rct)
            rct = QRect(0, 0, 10 + iCnt - (self.maxECG1Length - self.mECG1XStep), self.maxECG1Height)
            self.draw_wave_background(rct)
        else:
            rct = QRect(self.mECG1XStep, 0, iCnt + 10, self.maxECG1Height)
            self.draw_wave_background(rct)

        self.painterEcg1.setPen(QPen(QColor(ECG_MONITOR_THEME["colors"]["wave_line"]), 2, Qt.SolidLine))
        baseline = self.update_wave_display_baseline(self.mECG1WaveList)
        for i in range(iCnt - 1):
            point1 = QPoint(self.mECG1XStep, self.map_ecg_to_wave_y(self.mECG1WaveList[i], baseline))
            point2 = QPoint(self.mECG1XStep + 1, self.map_ecg_to_wave_y(self.mECG1WaveList[i + 1], baseline))
            self.painterEcg1.drawLine(point1, point2)
            self.mECG1XStep += 1
            if self.mECG1XStep >= self.maxECG1Length:
                self.mECG1XStep = 0

        del self.mECG1WaveList[0:iCnt - 1]
        self.ecg1WaveLabel.setPixmap(self.pixmapECG1)

    def update_wave_display_baseline(self, samples):
        """计算波形显示基线：使用 EMA 平滑采样中位数，避免波形上下跳动。"""
        if not samples:
            return self.waveDisplayBaseline or WAVE_DEFAULT_BASELINE

        sample_baseline = median(samples)
        if self.waveDisplayBaseline is None:
            self.waveDisplayBaseline = sample_baseline
        else:
            self.waveDisplayBaseline = (
                self.waveDisplayBaseline * (1 - WAVE_BASELINE_SMOOTHING)
                + sample_baseline * WAVE_BASELINE_SMOOTHING
            )
        return self.waveDisplayBaseline

    def map_ecg_to_wave_y(self, value, baseline=None):
        """将 ECG 采样值映射为波形 Y 坐标（像素），以基线为中心。"""
        if baseline is None:
            baseline = self.waveDisplayBaseline or WAVE_DEFAULT_BASELINE
        y = self.maxECG1Height / 2 - (value - baseline) / WAVE_DISPLAY_SCALE
        return max(0, min(self.maxECG1Height - 1, int(round(y))))

    def heartShapeFlash(self):
        self.heartLabel.setVisible(not self.heartLabel.isVisible())
        self.heartLabel_3.setVisible(not self.heartLabel_3.isVisible())

    def event(self, event: QtCore.QEvent) -> bool:
        if event.type() == event.StatusTip:
            if event.tip() == "":
                event = QStatusTipEvent(self.statusStr)
        return super().event(event)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """窗口关闭时：停止所有定时器和 Worker，确保线程安全退出。"""
        self.waveDrawTimer.stop()
        self.heartShapeTimer.stop()
        self.reconnectTimer.stop()
        self.stop_serial_worker()
        self.stop_offline_worker()
        super().closeEvent(a0)

    def eventFilter(self, watched, event):
        if watched is self.ecg1WaveLabel and event.type() == QtCore.QEvent.Resize:
            self.sync_wave_canvas_size()
        return super().eventFilter(watched, event)

    def sync_wave_canvas_size(self):
        if not hasattr(self, "pixmapECG1") or not hasattr(self, "painterEcg1"):
            return
        if self.ecg1WaveLabel.width() <= 0 or self.ecg1WaveLabel.height() <= 0:
            return
        if (
            self.pixmapECG1.width() == self.ecg1WaveLabel.width()
            and self.pixmapECG1.height() == self.ecg1WaveLabel.height()
        ):
            return
        if self.painterEcg1.isActive():
            self.painterEcg1.end()
        self.maxECG1Length = self.ecg1WaveLabel.width()
        self.maxECG1Height = self.ecg1WaveLabel.height()
        self.pixmapECG1 = QPixmap(self.maxECG1Length, self.maxECG1Height)
        self.painterEcg1 = QPainter(self.pixmapECG1)
        self.draw_wave_background()
        self.ecg1WaveLabel.setPixmap(self.pixmapECG1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.sync_wave_canvas_size()

    def slot_quit(self):
        app = QApplication.instance()
        app.quit()

    def slot_ecg(self, data):
        self.data_send(data)
