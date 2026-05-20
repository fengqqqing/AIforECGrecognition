import os
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import main
from config import DEMO_REPLAY_POLICY
from ParamMonitor import ParamMonitor


class _FakeExporter:
    def __init__(self):
        self.finalized = False
        self.replay_path = ""
        self.base_dir = "fake-dir"

    def finalize(self):
        self.finalized = True

    def latest_summary(self):
        return "运行模式: offline\n导出目录: fake-dir"


class _FakeStatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, message):
        self.messages.append(message)


def _fake_window(**overrides):
    status_bar = _FakeStatusBar()
    values = {
        "demo_ready": True,
        "model_ready": True,
        "demo_mode": False,
        "demo_replay_active": False,
        "demo_readiness_error": "",
        "last_error_message": "",
        "offline_policy": {},
        "statusStr": "",
        "run_exporter": None,
        "last_run_exporter": None,
        "offline_running": False,
        "offline_worker": object(),
        "offline_thread": object(),
        "serial_running": False,
        "last_offline_summary": None,
        "demo_policy_summary": lambda: "固定场景 row=3 · 2000 点",
        "statusBar": lambda: status_bar,
        "start_offline_worker": mock.Mock(),
        "show_demo_not_ready": mock.Mock(),
        "show_model_not_ready": mock.Mock(),
        "update_mode_banner": mock.Mock(),
    }
    values.update(overrides)
    window = SimpleNamespace(**values)
    window._status_bar = status_bar
    return window


class DemoModeTest(unittest.TestCase):
    def test_parse_args_accepts_demo_flag(self):
        args = main.parse_args(["--demo"])

        self.assertTrue(args.demo)

    def test_param_monitor_accepts_demo_mode_constructor_flag(self):
        self.assertIn("demo_mode", ParamMonitor.__init__.__code__.co_varnames)

    def test_start_demo_mode_uses_fixed_demo_policy_and_starts_replay(self):
        window = _fake_window()

        ParamMonitor.start_demo_mode(window)

        self.assertTrue(window.demo_replay_active)
        self.assertEqual(window.offline_policy["row"], DEMO_REPLAY_POLICY["row"])
        self.assertEqual(window.offline_policy["samples"], DEMO_REPLAY_POLICY["samples"])
        self.assertTrue(window.offline_policy["use_real_model"])
        self.assertIn("Demo", window.statusStr)
        window.start_offline_worker.assert_called_once_with()
        window.update_mode_banner.assert_called_with(
            "Demo 启动中",
            "固定场景 row=3 · 2000 点",
            "离线回放正在启动",
        )

    def test_start_demo_mode_blocks_when_precheck_failed(self):
        window = _fake_window(
            demo_ready=False,
            demo_readiness_error="Demo 预检失败:\n- 样例数据不存在: missing.csv",
        )

        ParamMonitor.start_demo_mode(window)

        self.assertFalse(window.demo_replay_active)
        self.assertFalse(window.start_offline_worker.called)
        window.show_demo_not_ready.assert_called_once_with("无法启动 Demo 演示")

    def test_demo_status_and_summary_survive_natural_finish(self):
        exporter = _FakeExporter()
        window = _fake_window(run_exporter=exporter, demo_replay_active=True)

        ParamMonitor.on_offline_opened(window, "OFFLINE_REPLAY")
        self.assertIn("Demo", window.statusStr)
        window.update_mode_banner.assert_called_with(
            "Demo 运行中",
            "固定场景 row=3 · 2000 点",
            "离线回放进行中",
        )

        ParamMonitor.on_offline_thread_finished(window)

        self.assertTrue(exporter.finalized)
        self.assertIs(window.last_run_exporter, exporter)
        self.assertIsNone(window.run_exporter)
        self.assertFalse(window.demo_replay_active)
        self.assertIn("最近运行摘要", window.statusStr)
        window.update_mode_banner.assert_called_with(
            "Demo 已完成",
            "固定场景 row=3 · 2000 点",
            "可查看最近运行摘要和导出文件",
        )

    def test_latest_summary_text_merges_exporter_and_offline_compare(self):
        exporter = _FakeExporter()
        window = _fake_window(
            last_run_exporter=exporter,
            last_offline_summary={
                "source_path": "sample_data/test.csv",
                "source_label": 0,
                "used_real_model": True,
                "latest_diagnosis": 0,
                "diagnosis_count": 1,
                "matched": True,
            },
        )

        summary = ParamMonitor.latest_summary_text(window)

        self.assertIn("运行模式: offline", summary)
        self.assertIn("回放对照", summary)
        self.assertIn("来源文件: sample_data/test.csv", summary)
        self.assertIn("源标签: 0", summary)
        self.assertIn("本次诊断: 0", summary)
        self.assertIn("是否一致: 是", summary)


if __name__ == "__main__":
    unittest.main()
