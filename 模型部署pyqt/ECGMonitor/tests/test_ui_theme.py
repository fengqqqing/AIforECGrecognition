import unittest
import importlib
import importlib.util


class UiThemeTest(unittest.TestCase):
    def load_theme_module(self):
        spec = importlib.util.find_spec("ui_theme")
        self.assertIsNotNone(spec, "ui_theme module should exist")
        return importlib.import_module("ui_theme")

    def test_theme_tokens_cover_monitoring_states(self):
        ui_theme = self.load_theme_module()
        colors = ui_theme.ECG_MONITOR_THEME["colors"]

        for name in (
            "background",
            "surface",
            "surface_muted",
            "border",
            "text_primary",
            "text_secondary",
            "wave_background",
            "wave_grid",
            "wave_line",
            "normal",
            "warning",
            "unknown",
        ):
            self.assertIn(name, colors)

    def test_main_window_stylesheet_centralizes_core_widgets(self):
        ui_theme = self.load_theme_module()
        stylesheet = ui_theme.build_main_window_stylesheet()

        self.assertIn("QMainWindow", stylesheet)
        self.assertIn("QMenuBar", stylesheet)
        self.assertIn("QStatusBar", stylesheet)
        self.assertIn("QWidget#centralwidget", stylesheet)
        self.assertIn("QPushButton#helpButton", stylesheet)
        self.assertNotIn("\nQWidget {\n", stylesheet)
        self.assertNotIn("\nQLabel {\n", stylesheet)
        self.assertNotIn("\nQPushButton {\n", stylesheet)
        self.assertIn(ui_theme.ECG_MONITOR_THEME["colors"]["background"], stylesheet)

    def test_wave_and_metrics_styles_are_exposed_for_runtime_widgets(self):
        ui_theme = self.load_theme_module()
        wave_style = ui_theme.get_wave_panel_style()
        metrics_style = ui_theme.get_metrics_label_style()
        metric_card_style = ui_theme.get_metric_card_style()
        metric_value_style = ui_theme.get_metric_value_style()

        self.assertIn(ui_theme.ECG_MONITOR_THEME["colors"]["wave_background"], wave_style)
        self.assertIn(ui_theme.ECG_MONITOR_THEME["colors"]["wave_grid"], wave_style)
        self.assertIn(ui_theme.ECG_MONITOR_THEME["colors"]["text_secondary"], metrics_style)
        self.assertIn(ui_theme.ECG_MONITOR_THEME["colors"]["surface_muted"], metric_card_style)
        self.assertIn(ui_theme.ECG_MONITOR_THEME["colors"]["normal"], metric_value_style)


if __name__ == "__main__":
    unittest.main()
