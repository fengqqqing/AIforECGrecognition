import unittest
from unittest import mock

import ui_rules
from ui_theme import ECG_MONITOR_THEME

from ui_rules import (
    format_metrics_panel_values,
    format_worker_metrics,
    get_diagnosis_label,
    get_diagnosis_style,
    get_lead_status_style,
    get_lead_status_text,
    get_ui_state_copy,
    is_lead_connected,
    should_display_heart_rate,
)


def _contract(labels):
    return {
        "output": {
            "num_classes": len(labels),
            "labels": labels,
        }
    }


class UiRulesTest(unittest.TestCase):
    def tearDown(self):
        if hasattr(ui_rules, "_LABELS_CACHE"):
            ui_rules._LABELS_CACHE = None

    @mock.patch("ui_rules.load_model_contract")
    def test_diagnosis_rules(self, mock_load):
        labels = [
            "契约正常",
            "契约RT室早",
            "契约ST上移",
            "契约ST下移",
            "契约窦性房颤",
            "契约窦性室颤",
            "契约单发室早",
            "契约窦性静止",
            "契约二联律",
            "契约房扑",
            "契约房早",
            "契约双重起搏",
        ]
        mock_load.return_value = _contract(labels)

        self.assertEqual(get_diagnosis_label(0), "契约正常")
        self.assertEqual(get_diagnosis_label(11), "契约双重起搏")
        self.assertEqual(get_diagnosis_label(99), "")
        normal_style = get_diagnosis_style(0)
        abnormal_style = get_diagnosis_style(1)
        self.assertIn(ECG_MONITOR_THEME["colors"]["normal"], normal_style)
        self.assertIn(ECG_MONITOR_THEME["colors"]["warning"], abnormal_style)
        self.assertIn("border-radius", normal_style)
        self.assertIn("font-weight", normal_style)
        self.assertNotIn("临床诊断", normal_style)

    def test_assistant_result_hint_copy_keeps_medical_boundary(self):
        self.assertTrue(hasattr(ui_rules, "get_assistant_result_hint"))
        forbidden_terms = ["最终诊断", "临床诊断", "临床处置", "分诊决策"]

        hints = {
            "empty": ui_rules.get_assistant_result_hint(None),
            "normal": ui_rules.get_assistant_result_hint(0),
            "abnormal": ui_rules.get_assistant_result_hint(1),
            "unknown": ui_rules.get_assistant_result_hint("bad-index"),
        }

        self.assertEqual(hints["empty"], "等待 ECG 窗口完成后显示辅助提示")
        self.assertIn("辅助提示", hints["normal"])
        self.assertIn("正式判读前", hints["normal"])
        self.assertIn("医生复核", hints["abnormal"])
        self.assertIn("正式判读前", hints["abnormal"])
        self.assertIn("模型契约", hints["unknown"])
        for hint in hints.values():
            for term in forbidden_terms:
                self.assertNotIn(term, hint)

    def test_lead_status_rules(self):
        self.assertEqual(get_lead_status_text(0), "导联连接")
        self.assertEqual(get_lead_status_text(1), "导联脱落")
        self.assertEqual(get_lead_status_text(3), "导联未知")
        self.assertTrue(is_lead_connected(0))
        self.assertFalse(is_lead_connected(1))
        connected_style = get_lead_status_style(0)
        disconnected_style = get_lead_status_style(1)
        unknown_style = get_lead_status_style(3)
        self.assertIn(ECG_MONITOR_THEME["colors"]["normal"], connected_style)
        self.assertIn(ECG_MONITOR_THEME["colors"]["warning"], disconnected_style)
        self.assertIn(ECG_MONITOR_THEME["colors"]["unknown"], unknown_style)
        self.assertIn("border-radius", connected_style)

    def test_heart_rate_display_rule(self):
        self.assertTrue(should_display_heart_rate(72))
        self.assertFalse(should_display_heart_rate(0))
        self.assertFalse(should_display_heart_rate(400))
        self.assertTrue(hasattr(ui_rules, "get_heart_rate_style"))
        valid_style = ui_rules.get_heart_rate_style(72)
        invalid_style = ui_rules.get_heart_rate_style(0)
        self.assertIn(ECG_MONITOR_THEME["colors"]["normal"], valid_style)
        self.assertIn(ECG_MONITOR_THEME["colors"]["unknown"], invalid_style)
        self.assertIn("font-weight", valid_style)

    def test_worker_metrics_format(self):
        text = format_worker_metrics(
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
        self.assertIn("包=12", text)
        self.assertIn("诊断=1", text)
        self.assertIn("单次推理=8.5ms", text)
        self.assertIn("吞吐量=240.5点/s", text)

    def test_metrics_panel_values(self):
        values = format_metrics_panel_values(
            {
                "total_packets": 12,
                "ecg_packets": 10,
                "diagnosis_count": 1,
                "lead_events": 2,
                "heart_rate_events": 3,
                "last_inference_ms": 8.5,
                "throughput_samples_per_sec": 240.5,
            }
        )
        self.assertEqual(values["packets"], "12 / ECG 10")
        self.assertEqual(values["diagnosis"], "1")
        self.assertEqual(values["latency"], "8.5 ms")
        self.assertEqual(values["throughput"], "240.5 点/s")
        self.assertEqual(values["events"], "导联 2 · 心率 3")

        empty_values = format_metrics_panel_values({})
        self.assertEqual(empty_values["packets"], "0 / ECG 0")
        self.assertEqual(empty_values["diagnosis"], "0")
        self.assertEqual(empty_values["latency"], "0.0 ms")
        self.assertEqual(empty_values["throughput"], "0.0 点/s")

    def test_ui_state_copy_covers_demo_flow(self):
        ready = get_ui_state_copy("demo_ready", detail="固定场景 row=3 · 2000 点")
        self.assertEqual(ready["badge"], "Demo 就绪")
        self.assertEqual(ready["detail"], "固定场景 row=3 · 2000 点")
        self.assertEqual(ready["hint"], "预检通过 · 等待自动启动")
        self.assertEqual(ready["next_action"], "等待自动启动")

        running = get_ui_state_copy("demo_running", detail="固定场景 row=3 · 2000 点")
        self.assertEqual(running["badge"], "Demo 运行中")
        self.assertEqual(running["hint"], "先确认波形、导联和心率，再查看 AI 辅助提示")
        self.assertIn("最近摘要", get_ui_state_copy("demo_completed")["next_action"])

    def test_ui_state_copy_uses_conservative_medical_language(self):
        states = [
            "idle",
            "demo_ready",
            "demo_starting",
            "demo_running",
            "inference_done",
            "demo_completed",
            "error",
            "reset",
        ]
        forbidden_terms = ["最终诊断", "临床诊断", "临床处置", "分诊决策"]

        for state in states:
            copy = get_ui_state_copy(state)
            combined = " ".join(copy.values())
            self.assertIn("badge", copy)
            self.assertIn("detail", copy)
            self.assertIn("hint", copy)
            self.assertIn("next_action", copy)
            for term in forbidden_terms:
                self.assertNotIn(term, combined)

    def test_unknown_ui_state_falls_back_to_safe_copy(self):
        copy = get_ui_state_copy("missing-state")

        self.assertEqual(copy["badge"], "状态未知")
        self.assertIn("辅助提示", copy["hint"])
        self.assertIn("重置", copy["next_action"])


if __name__ == "__main__":
    unittest.main()
