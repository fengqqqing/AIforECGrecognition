import os
import sys
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from PyQt5 import QtCore, QtWidgets

from demo_readiness import DemoReadinessError
from ParamMonitor import ParamMonitor
from ui_rules import get_assistant_result_hint
from ui_theme import ECG_MONITOR_THEME


LAYOUT_TEST_SIZES = (
    (1024, 600),
    (1280, 720),
    (1915, 860),
    (1920, 1080),
    (2560, 1440),
)

LAYOUT_STATE_SCENARIOS = (
    {
        "name": "standby_unknown_empty_metrics",
        "badge": "串口待机",
        "detail": "在线采集 / 离线回放可用",
        "hint": "辅助提示 · 等待信号输入",
        "heart_rate": 0,
        "lead_status": None,
        "metrics": {},
    },
    {
        "name": "demo_running_connected_metrics",
        "badge": "Demo 运行中",
        "detail": "固定场景 row=3 · 2000 点",
        "hint": "先确认波形、导联和心率，再查看 AI 辅助提示",
        "heart_rate": 65,
        "lead_status": 0,
        "metrics": {
            "total_packets": 2006,
            "ecg_packets": 2000,
            "diagnosis_count": 0,
            "lead_events": 3,
            "heart_rate_events": 3,
            "last_inference_ms": 0.0,
            "throughput_samples_per_sec": 0.0,
        },
    },
    {
        "name": "offline_complete_connected_metrics",
        "badge": "离线回放已完成",
        "detail": "当前回放配置",
        "hint": "可查看最近运行摘要和导出文件",
        "heart_rate": 65,
        "lead_status": 0,
        "metrics": {
            "total_packets": 2006,
            "ecg_packets": 2000,
            "diagnosis_count": 1,
            "lead_events": 3,
            "heart_rate_events": 3,
            "last_inference_ms": 8.5,
            "throughput_samples_per_sec": 240.5,
        },
    },
    {
        "name": "offline_complete_lead_off_long_metrics",
        "badge": "离线回放已完成",
        "detail": "当前回放配置",
        "hint": "可查看最近运行摘要和导出文件",
        "heart_rate": 120,
        "lead_status": 1,
        "metrics": {
            "total_packets": 123456,
            "ecg_packets": 123000,
            "diagnosis_count": 12,
            "lead_events": 18,
            "heart_rate_events": 24,
            "last_inference_ms": 123.4,
            "throughput_samples_per_sec": 1024.5,
        },
    },
)


def pixel_color_name(pixmap, x, y):
    return pixmap.toImage().pixelColor(x, y).name().lower()


def bottom(widget):
    geometry = widget.geometry()
    return geometry.y() + geometry.height()


def right(widget):
    geometry = widget.geometry()
    return geometry.x() + geometry.width()


def assert_vertical_order(*widgets):
    for previous, current in zip(widgets, widgets[1:]):
        assert bottom(previous) <= current.geometry().y()


def assert_contained(child, parent):
    child_geometry = child.geometry()
    parent_geometry = parent.contentsRect()
    assert child_geometry.x() >= parent_geometry.x()
    assert child_geometry.y() >= parent_geometry.y()
    assert right(child) <= parent_geometry.x() + parent_geometry.width()
    assert bottom(child) <= parent_geometry.y() + parent_geometry.height()


def wrapped_text_height(label):
    text_rect = label.fontMetrics().boundingRect(
        QtCore.QRect(0, 0, max(1, label.width()), 1000),
        QtCore.Qt.TextWordWrap | QtCore.Qt.AlignCenter,
        label.text(),
    )
    return text_rect.height()


def direct_layout_widgets(layout):
    widgets = []
    for index in range(layout.count()):
        item = layout.itemAt(index)
        widget = item.widget()
        if widget is not None:
            widgets.append(widget)
    return widgets


def apply_layout_state(window, scenario):
    window.reset_display_state()
    window.update_mode_banner(scenario["badge"], scenario["detail"], scenario["hint"])
    window.on_heart_rate(scenario["heart_rate"])
    if scenario["lead_status"] is not None:
        window.on_lead_status(scenario["lead_status"])
    window.on_metrics_updated(scenario["metrics"])


def center_y(widget):
    geometry = widget.geometry()
    return geometry.y() + geometry.height() / 2


def assert_right_panel_three_card_contract(window):
    direct_children = [widget.objectName() for widget in direct_layout_widgets(window.rightInfoLayout)]
    assert direct_children.count("aiResultCard") == 1
    assert direct_children.count("heartRateCard") == 1
    assert direct_children.count("leadStatusCard") == 1
    assert "vitalsStatusCard" not in direct_children
    assert window.heartRateCard.parentWidget() is window.rightInfoPanel
    assert window.leadStatusCard.parentWidget() is window.rightInfoPanel


def assert_right_scroll_contract(window):
    assert hasattr(window, "rightInfoScrollArea")
    assert window.rightInfoScrollArea.widget() is window.rightInfoPanel
    assert window.rightInfoScrollArea.horizontalScrollBarPolicy() == QtCore.Qt.ScrollBarAlwaysOff
    assert window.rightInfoScrollArea.viewport().height() > 0


def assert_layout_matrix(window):
    assert_right_panel_three_card_contract(window)
    assert_right_scroll_contract(window)
    for width, height in LAYOUT_TEST_SIZES:
        window.resize(width, height)
        QtWidgets.QApplication.processEvents()
        for scenario in LAYOUT_STATE_SCENARIOS:
            apply_layout_state(window, scenario)
            QtWidgets.QApplication.processEvents()
            assert_demo_layout_budget(window)
            assert_top_bar_rows_do_not_collide(window)
            assert_metric_cards_readable(window)
            assert_compact_right_panel(window)
            assert window.ecg1WaveLabel.height() >= 180


def assert_compact_right_panel(window):
    assert_right_panel_three_card_contract(window)
    assert window.connectStateLabel_2.height() <= 52
    assert window.connectStateLabel_2.font().pointSize() <= 24
    assert window.heartRateLabel.width() <= 118
    assert window.heartRateLabel.height() <= 34
    assert window.heartRateLabel.font().pointSize() == window.heartRateUnitLabel.font().pointSize()
    assert window.heartRateLabel.font().pointSize() <= 18
    assert "background-color" not in window.heartRateLabel.styleSheet()
    assert "padding" not in window.heartRateLabel.styleSheet()
    assert window.heartRateUnitLabel.geometry().x() - right(window.heartRateLabel) >= 6
    assert abs(center_y(window.heartRateLabel) - center_y(window.heartRateUnitLabel)) <= 4
    assert window.heartRateTextLabel_2.width() <= 150
    assert window.heartRateTextLabel_2.height() <= 36
    assert window.heartRateTextLabel_2.font().pointSize() <= 16
    assert bottom(window.heartRateTextLabel_2) <= window.leadStructureLabel.geometry().y()
    assert window.heartRateCard.height() <= 86
    assert window.leadStatusCard.height() <= 112
    assert bottom(window.leadStatusCard) <= window.rightInfoPanel.height()
    assert window.rightInfoPanel.height() <= window.rightInfoScrollArea.viewport().height() or window.rightInfoScrollArea.verticalScrollBar().maximum() > 0
    assert_vertical_order(window.aiResultCard, window.heartRateCard, window.leadStatusCard)
    assert window.leadStructureLabel.wordWrap()
    lead_contents = window.leadStatusCard.contentsRect()
    lead_contents_bottom = lead_contents.y() + lead_contents.height()
    assert window.leadStructureLabel.height() >= wrapped_text_height(window.leadStructureLabel)
    assert bottom(window.leadStructureLabel) + 2 <= lead_contents_bottom


def assert_runtime_icons_loaded(window):
    for label in (
        window.heartLabel,
        window.heartLabel_3,
        window.connectStateLabel_5,
        window.connectStateLabel,
    ):
        pixmap = label.pixmap()
        assert pixmap is not None
        assert not pixmap.isNull()


def assert_large_font_right_panel_accessible(window):
    window.resize(1280, 720)
    QtWidgets.QApplication.processEvents()
    assert_right_scroll_contract(window)
    assert window.heartRateLabel.height() >= window.heartRateLabel.fontMetrics().height()
    assert window.heartRateUnitLabel.height() >= window.heartRateUnitLabel.fontMetrics().height()
    assert window.heartRateTextLabel_2.height() >= window.heartRateTextLabel_2.fontMetrics().height()
    assert window.leadStructureLabel.height() >= wrapped_text_height(window.leadStructureLabel)
    assert window.rightInfoPanel.height() <= window.rightInfoScrollArea.viewport().height() or window.rightInfoScrollArea.verticalScrollBar().maximum() > 0


def assert_top_bar_rows_do_not_collide(window):
    assert window.modeBadgeLabel.height() <= 30
    assert bottom(window.modeBadgeLabel) + 8 <= window.topActionFrame.geometry().y()
    assert bottom(window.demoPolicyLabel) + 8 <= window.topActionFrame.geometry().y()
    assert bottom(window.modeHintLabel) + 8 <= window.topActionFrame.geometry().y()


def assert_metric_cards_readable(window):
    assert window.metricsPanel.height() >= 62
    assert window.metricEventValueLabel.font().pointSize() <= 12
    for value_label, card in (
        (window.metricPacketValueLabel, window.metricPacketCard),
        (window.metricDiagnosisValueLabel, window.metricDiagnosisCard),
        (window.metricInferenceValueLabel, window.metricInferenceCard),
        (window.metricThroughputValueLabel, window.metricThroughputCard),
        (window.metricEventValueLabel, window.metricEventCard),
    ):
        assert_contained(value_label, card)
        assert value_label.height() >= value_label.fontMetrics().height() + 2


def assert_demo_layout_budget(window):
    assert window.topBarFrame.height() <= 128
    assert window.metricsPanel.height() <= 92
    assert window.aiResultCard.height() <= 98
    assert window.heartRateCard.height() <= 86
    assert window.leadStatusCard.height() <= 112
    assert window.ecg1WaveLabel.geometry().y() <= 64
    assert window.ecg1WaveLabel.height() >= window.waveformCard.height() - 88
    assert bottom(window.ecg1WaveLabel) + 10 <= window.waveformCard.height()
    assert bottom(window.leadStatusCard) <= window.rightInfoPanel.height()


def dominant_wave_line_y(pixmap, color_name):
    image = pixmap.toImage()
    target = color_name.lower()
    best_y = -1
    best_count = 0
    for y in range(image.height()):
        count = 0
        for x in range(image.width()):
            if image.pixelColor(x, y).name().lower() == target:
                count += 1
        if count > best_count:
            best_count = count
            best_y = y
    assert best_count > 30
    return best_y


def assert_wave_line_visually_centered(window, baseline_value):
    window.mECG1WaveList = [baseline_value] * 100
    window.mECG1XStep = 0
    window.draw_wave_background()
    window.drawECG1Wave()
    line_y = dominant_wave_line_y(window.pixmapECG1, ECG_MONITOR_THEME["colors"]["wave_line"])
    visual_center_y = window.ecg1WaveLabel.height() / 2
    assert abs(line_y - visual_center_y) <= 12


def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)

    original_cwd = os.getcwd()
    os.chdir(PROJECT_DIR)
    with mock.patch("ParamMonitor.warmup_model", return_value=None), mock.patch(
        "ParamMonitor.check_demo_readiness", return_value={"source_path": "demo.csv"}
    ) as readiness, mock.patch("ParamMonitor.QMessageBox.warning") as warning:
        window = ParamMonitor()
        window.waveDrawTimer.stop()
        window.heartShapeTimer.stop()
        window.reconnectTimer.stop()

        try:
            window.show()
            app.processEvents()
            assert window.demo_ready is False
            assert window.demo_readiness is None
            assert not readiness.called
            assert not warning.called
            assert window.minimumWidth() <= 1280
            assert window.minimumHeight() <= 600
            assert hasattr(window, "topBarFrame")
            assert hasattr(window, "mainContentFrame")
            assert hasattr(window, "waveformCard")
            assert hasattr(window, "rightInfoPanel")
            assert hasattr(window, "rightInfoScrollArea")
            assert hasattr(window, "metricsPanel")
            assert hasattr(window, "topActionFrame")
            assert hasattr(window, "replayActionButton")
            assert hasattr(window, "configActionButton")
            assert hasattr(window, "summaryActionButton")
            assert hasattr(window, "exportActionButton")
            assert hasattr(window, "resetActionButton")
            assert hasattr(window, "metricDiagnosisValueLabel")
            assert hasattr(window, "metricInferenceValueLabel")
            assert hasattr(window, "metricThroughputValueLabel")
            assert hasattr(window, "metricPacketValueLabel")
            assert hasattr(window, "metricEventValueLabel")
            assert window.ecg1WaveLabel.minimumWidth() <= 620
            assert window.ecg1WaveLabel.minimumHeight() <= 320
            assert "QMainWindow" in window.styleSheet()
            assert "QStatusBar" in window.styleSheet()
            assert [action.text() for action in window.menubar.actions()] == ["串口设置", "退出"]
            assert "串口待机" in window.modeBadgeLabel.text()
            assert "离线回放" in window.demoPolicyLabel.text()
            assert "等待信号输入" in window.modeHintLabel.text()
            assert window.replayActionButton.text() == "离线回放"
            assert window.configActionButton.text() == "回放设置"
            assert window.summaryActionButton.text() == "最近摘要"
            assert window.exportActionButton.text() == "导出目录"
            assert window.resetActionButton.text() == "重置显示"
            assert "采集与初筛流程" in window.replayActionButton.toolTip()
            assert "样本数" in window.configActionButton.toolTip()
            assert "最近一次运行" in window.summaryActionButton.toolTip()
            assert "metrics" in window.exportActionButton.toolTip()
            assert "重新运行" in window.resetActionButton.toolTip()
            assert not hasattr(window, "metricsLabel")
            assert window.helpButton.text() == "说明"
            assert_runtime_icons_loaded(window)
            assert_layout_matrix(window)

            window.resize(1280, 720)
            app.processEvents()
            assert_demo_layout_budget(window)
            assert_top_bar_rows_do_not_collide(window)
            assert bottom(window.topBarFrame) <= window.mainContentFrame.geometry().y()
            assert bottom(window.mainContentFrame) <= window.metricsPanel.geometry().y()
            assert bottom(window.metricsPanel) <= window.centralwidget.height()
            assert right(window.waveformCard) <= window.rightInfoScrollArea.geometry().x()
            for widget in (
                window.topBarFrame,
                window.mainContentFrame,
                window.metricsPanel,
                window.ecg1WaveLabel,
                window.rightInfoScrollArea,
            ):
                assert widget.isVisible()
                assert widget.width() > 0
                assert widget.height() > 0
            assert window.pixmapECG1.width() == window.ecg1WaveLabel.width()
            assert window.pixmapECG1.height() == window.ecg1WaveLabel.height()
            assert_vertical_order(window.aiResultCard, window.heartRateCard, window.leadStatusCard)
            assert_contained(window.heartRateTextLabel_3, window.aiResultCard)
            assert_contained(window.connectStateLabel_2, window.aiResultCard)
            assert_contained(window.assistantHintLabel, window.aiResultCard)
            assert_vertical_order(window.heartRateTextLabel_3, window.connectStateLabel_2, window.assistantHintLabel)
            assert_contained(window.heartRateTitleLabel, window.heartRateCard)
            assert_contained(window.heartRateLabel, window.heartRateCard)
            assert_contained(window.heartRateUnitLabel, window.heartRateCard)
            assert right(window.heartRateLabel) <= window.heartRateUnitLabel.geometry().x()
            assert_contained(window.leadStatusTitleLabel, window.leadStatusCard)
            assert_contained(window.heartRateTextLabel_2, window.leadStatusCard)
            assert_contained(window.leadStructureLabel, window.leadStatusCard)
            assert bottom(window.heartRateTextLabel_2) <= window.leadStructureLabel.geometry().y()
            assert_compact_right_panel(window)
            assert "border-radius" in window.ecg1WaveLabel.styleSheet()
            assert pixel_color_name(window.pixmapECG1, 5, 5) == ECG_MONITOR_THEME["colors"]["wave_background"]
            assert pixel_color_name(window.pixmapECG1, 40, 5) == ECG_MONITOR_THEME["colors"]["wave_grid"]
            assert window.heartRateTextLabel_3.text() == "AI 辅助识别"
            assert window.assistantHintLabel.text() == get_assistant_result_hint(None)
            assert "临床诊断" not in window.assistantHintLabel.text()

            window.on_diagnosis(0)
            assert window.connectStateLabel_2.text() == "正常"
            assert window.assistantHintLabel.text() == get_assistant_result_hint(0)
            assert ECG_MONITOR_THEME["colors"]["normal"] in window.connectStateLabel_2.styleSheet()
            assert "border-radius" in window.connectStateLabel_2.styleSheet()

            window.on_diagnosis(1)
            assert window.assistantHintLabel.text() == get_assistant_result_hint(1)
            assert "医生复核" in window.assistantHintLabel.text()
            assert "临床诊断" not in window.assistantHintLabel.text()

            window.on_lead_status(0)
            assert window.heartRateTextLabel_2.text() == "导联连接"
            assert ECG_MONITOR_THEME["colors"]["normal"] in window.heartRateTextLabel_2.styleSheet()
            assert "border-radius" in window.heartRateTextLabel_2.styleSheet()

            window.on_lead_status(1)
            assert window.heartRateTextLabel_2.text() == "导联脱落"
            assert ECG_MONITOR_THEME["colors"]["warning"] in window.heartRateTextLabel_2.styleSheet()

            window.on_heart_rate(72)
            assert window.heartRateLabel.text() == "72"
            assert ECG_MONITOR_THEME["colors"]["normal"] in window.heartRateLabel.styleSheet()

            window.on_heart_rate(0)
            assert window.heartRateLabel.text() == "--"
            assert ECG_MONITOR_THEME["colors"]["unknown"] in window.heartRateLabel.styleSheet()

            window.resize(1911, 959)
            app.processEvents()
            window.update_mode_banner("离线回放已完成", "当前回放配置", "可查看最近运行摘要和导出文件")
            window.on_heart_rate(65)
            window.on_lead_status(0)
            assert_demo_layout_budget(window)
            assert_top_bar_rows_do_not_collide(window)
            assert_compact_right_panel(window)
            assert_wave_line_visually_centered(window, 1200)

            for width, height in ((1024, 600), (1024, 640), (1366, 768), (1920, 1017), (2560, 1440)):
                window.resize(width, height)
                app.processEvents()
                assert window.height() <= max(height, window.minimumHeight()) + 4
                assert_demo_layout_budget(window)
                assert_top_bar_rows_do_not_collide(window)
                assert_compact_right_panel(window)

            window.on_metrics_updated(
                {
                    "total_packets": 12,
                    "ecg_packets": 10,
                    "diagnosis_count": 1,
                    "lead_events": 1,
                    "heart_rate_events": 1,
                    "last_inference_ms": 8.5,
                    "throughput_samples_per_sec": 240.5,
                }
            )
            assert window.metricsSummaryLabel.text() == "运行指标: 包=12 ECG=10 诊断=1 导联=1 心率=1 单次推理=8.5ms 吞吐量=240.5点/s"
            assert window.metricPacketValueLabel.text() == "12 / ECG 10"
            assert window.metricDiagnosisValueLabel.text() == "1"
            assert window.metricInferenceValueLabel.text() == "8.5 ms"
            assert window.metricThroughputValueLabel.text() == "240.5 点/s"
            assert window.metricEventValueLabel.text() == "导联 1 · 心率 1"
            assert "background-color" in window.metricDiagnosisCard.styleSheet()
            assert_metric_cards_readable(window)

            with mock.patch.object(window, "slot_offlineReplay") as replay_slot:
                window.replayActionButton.click()
                assert replay_slot.called
            with mock.patch.object(window, "slot_offlineReplayConfig") as config_slot:
                window.configActionButton.click()
                assert config_slot.called
            with mock.patch.object(window, "slot_showLatestSummary") as summary_slot:
                window.summaryActionButton.click()
                assert summary_slot.called
            with mock.patch.object(window, "slot_openExportDir") as export_slot:
                window.exportActionButton.click()
                assert export_slot.called
            with mock.patch.object(window, "slot_resetDisplay") as reset_slot:
                window.resetActionButton.click()
                assert reset_slot.called

            window.slot_resetDisplay()
            assert window.modeBadgeLabel.text() == "显示已重置"
            assert window.modeHintLabel.text() == "辅助提示 · 等待新的信号输入"
            assert window.heartRateLabel.text() == "--"
            assert window.heartRateTextLabel_2.text() == "导联未知"
            assert window.connectStateLabel_2.text() == ""
            assert window.assistantHintLabel.text() == get_assistant_result_hint(None)
            assert ECG_MONITOR_THEME["colors"]["unknown"] in window.heartRateLabel.styleSheet()
            assert ECG_MONITOR_THEME["colors"]["unknown"] in window.heartRateTextLabel_2.styleSheet()
            assert window.metricsSummaryLabel.text() == "运行指标: 未开始"
            assert window.metricDiagnosisValueLabel.text() == "0"
            assert window.metricInferenceValueLabel.text() == "0.0 ms"
            assert window.metricThroughputValueLabel.text() == "0.0 点/s"
            assert pixel_color_name(window.pixmapECG1, 5, 5) == ECG_MONITOR_THEME["colors"]["wave_background"]
            assert pixel_color_name(window.pixmapECG1, 40, 5) == ECG_MONITOR_THEME["colors"]["wave_grid"]
        finally:
            window.close()
            app.processEvents()

    default_font = app.font()
    large_font = QtWidgets.QApplication.font()
    large_font.setPointSize(max(large_font.pointSize() + 4, 14))
    app.setFont(large_font)
    try:
        with mock.patch("ParamMonitor.warmup_model", return_value=None), mock.patch(
            "ParamMonitor.check_demo_readiness", return_value={"source_path": "demo.csv"}
        ):
            large_font_window = ParamMonitor()
            large_font_window.waveDrawTimer.stop()
            large_font_window.heartShapeTimer.stop()
            large_font_window.reconnectTimer.stop()

            try:
                large_font_window.show()
                app.processEvents()
                assert_large_font_right_panel_accessible(large_font_window)
            finally:
                large_font_window.close()
                app.processEvents()
    finally:
        app.setFont(default_font)

    with mock.patch("ParamMonitor.warmup_model", return_value=None), mock.patch(
        "ParamMonitor.check_demo_readiness", return_value={"source_path": "demo.csv"}
    ) as readiness, mock.patch("ParamMonitor.QTimer.singleShot") as single_shot:
        demo_window = ParamMonitor(demo_mode=True)
        demo_window.waveDrawTimer.stop()
        demo_window.heartShapeTimer.stop()
        demo_window.reconnectTimer.stop()

        try:
            assert demo_window.demo_mode is True
            assert demo_window.demo_ready is True
            assert readiness.called
            assert single_shot.called
            assert single_shot.call_args.args[0] == 0
            assert "Demo 就绪" in demo_window.modeBadgeLabel.text()
            assert "row=3" in demo_window.demoPolicyLabel.text()
            assert "预检通过" in demo_window.modeHintLabel.text()
        finally:
            demo_window.close()
            app.processEvents()

    with mock.patch("ParamMonitor.warmup_model", side_effect=RuntimeError("bad contract")):
        with mock.patch("ParamMonitor.QMessageBox.warning"):
            with mock.patch("ParamMonitor.logger.exception"), mock.patch("ParamMonitor.check_demo_readiness") as readiness:
                failed_window = ParamMonitor()
                failed_window.waveDrawTimer.stop()
                failed_window.heartShapeTimer.stop()
                failed_window.reconnectTimer.stop()

            try:
                assert failed_window.model_ready is False
                assert not readiness.called

                with mock.patch("ParamMonitor.SerialInferenceWorker") as worker_factory:
                    failed_window.start_serial_worker("COM1", "115200", "8", "1", "N")
                    assert not worker_factory.called

                failed_window.offline_policy["use_real_model"] = True
                with mock.patch("ParamMonitor.OfflineReplayWorker") as replay_worker_factory:
                    failed_window.start_offline_worker()
                    assert not replay_worker_factory.called
            finally:
                failed_window.close()
                app.processEvents()

    with mock.patch("ParamMonitor.warmup_model", return_value=None), mock.patch(
        "ParamMonitor.check_demo_readiness",
        side_effect=DemoReadinessError(["样例数据不存在: missing.csv"]),
    ):
        with mock.patch("ParamMonitor.QMessageBox.warning") as warning:
            demo_failed_window = ParamMonitor(demo_mode=True)
            demo_failed_window.waveDrawTimer.stop()
            demo_failed_window.heartShapeTimer.stop()
            demo_failed_window.reconnectTimer.stop()

        try:
            assert demo_failed_window.model_ready is True
            assert demo_failed_window.demo_ready is False
            assert "样例数据不存在" in demo_failed_window.demo_readiness_error
            assert warning.called
            assert "Demo 预检失败" in warning.call_args.args[1]
            assert warning.call_count == 1
            assert demo_failed_window.modeBadgeLabel.text() == "状态异常"
            assert demo_failed_window.demoPolicyLabel.text() == "Demo 预检未通过"
            assert "请检查模型契约" in demo_failed_window.modeHintLabel.text()
        finally:
            demo_failed_window.close()
            app.processEvents()
    os.chdir(original_cwd)

    print("ParamMonitor UI smoke check passed.")
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
