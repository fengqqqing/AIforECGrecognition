ECG_MONITOR_THEME = {
    "colors": {
        "background": "#0b1117",
        "surface": "#111a22",
        "surface_muted": "#16212b",
        "border": "#263645",
        "text_primary": "#edf3f7",
        "text_secondary": "#a8b5c2",
        "wave_background": "#020807",
        "wave_grid_minor": "#071c14",
        "wave_grid": "#0f3f26",
        "wave_line": "#36d46f",
        "normal": "#52d273",
        "warning": "#ff5f57",
        "unknown": "#7c8a96",
    },
    "fonts": {
        "family": "Microsoft YaHei UI",
        "mono_family": "Consolas",
        "base_size": 10,
    },
    "radius": {
        "small": 4,
        "medium": 6,
    },
    "spacing": {
        "xs": 4,
        "sm": 8,
        "md": 12,
        "lg": 16,
    },
}


def _colors(theme=None):
    return (theme or ECG_MONITOR_THEME)["colors"]


def _fonts(theme=None):
    return (theme or ECG_MONITOR_THEME)["fonts"]


def _radius(theme=None):
    return (theme or ECG_MONITOR_THEME)["radius"]


def build_main_window_stylesheet(theme=None):
    colors = _colors(theme)
    fonts = _fonts(theme)
    radius = _radius(theme)

    return f"""
QMainWindow {{
    background-color: {colors["background"]};
    color: {colors["text_primary"]};
    font-family: "{fonts["family"]}";
    font-size: {fonts["base_size"]}pt;
}}
QWidget#centralwidget {{
    background-color: {colors["background"]};
    color: {colors["text_primary"]};
    font-family: "{fonts["family"]}";
}}
QMenuBar {{
    background-color: {colors["surface"]};
    color: {colors["text_primary"]};
    border-bottom: 1px solid {colors["border"]};
    spacing: 8px;
}}
QMenuBar::item {{
    padding: 6px 10px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: {colors["surface_muted"]};
    border-radius: {radius["small"]}px;
}}
QStatusBar {{
    background-color: {colors["surface"]};
    color: {colors["text_secondary"]};
    border-top: 1px solid {colors["border"]};
}}
QPushButton#helpButton,
QWidget#centralwidget QPushButton {{
    background-color: {colors["surface_muted"]};
    color: {colors["text_primary"]};
    border: 1px solid {colors["border"]};
    border-radius: {radius["small"]}px;
    padding: 4px 10px;
}}
QPushButton#helpButton:hover,
QWidget#centralwidget QPushButton:hover {{
    border-color: {colors["normal"]};
}}
QPushButton#replayActionButton,
QPushButton#configActionButton,
QPushButton#summaryActionButton,
QPushButton#exportActionButton,
QPushButton#resetActionButton {{
    padding: 5px 10px;
    min-width: 66px;
}}
QWidget#centralwidget QFrame#topBarFrame,
QWidget#centralwidget QFrame#waveformCard,
QWidget#centralwidget QFrame#metricsPanel {{
    background-color: {colors["surface"]};
    border: 1px solid {colors["border"]};
    border-radius: {radius["medium"]}px;
}}
QScrollArea#rightInfoScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollArea#rightInfoScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}
QWidget#centralwidget QGroupBox {{
    background-color: {colors["surface"]};
    border: 1px solid {colors["border"]};
    border-radius: {radius["medium"]}px;
    margin-top: 6px;
}}
QGroupBox#aiResultCard {{
    background-color: {colors["surface_muted"]};
    border-color: {colors["border"]};
}}
QGroupBox#heartRateCard,
QGroupBox#leadStatusCard {{
    background-color: {colors["surface_muted"]};
    border-color: {colors["border"]};
}}
QWidget#centralwidget QLabel {{
    color: {colors["text_primary"]};
}}
QLabel#heartRateTextLabel_3 {{
    color: {colors["text_primary"]};
}}
QLabel#assistantHintLabel {{
    color: {colors["text_secondary"]};
}}
""".strip()


def get_wave_panel_style(theme=None):
    colors = _colors(theme)
    radius = _radius(theme)

    return (
        f"background-color: {colors['wave_background']}; "
        f"border: 1px solid {colors['wave_grid']}; "
        f"border-radius: {radius['medium']}px;"
    )


def get_mode_badge_style(state="normal", theme=None):
    colors = _colors(theme)
    radius = _radius(theme)
    if state == "warning":
        color = colors["warning"]
        background = "#2a1518"
    elif state == "unknown":
        color = colors["unknown"]
        background = "#151d25"
    else:
        color = colors["normal"]
        background = "#0d2619"

    return (
        f"background-color: {background}; "
        f"color: {color}; "
        f"border: 1px solid {color}; "
        f"border-radius: {radius['small']}px; "
        "font-weight: 700; "
        "padding: 2px 10px;"
    )


def get_metrics_label_style(theme=None):
    colors = _colors(theme)
    fonts = _fonts(theme)

    return (
        f"color: {colors['text_secondary']}; "
        f"font-family: \"{fonts['mono_family']}\"; "
        "padding: 0 8px;"
    )


def get_metric_card_style(theme=None):
    colors = _colors(theme)
    radius = _radius(theme)

    return (
        f"background-color: {colors['surface_muted']}; "
        f"border: 1px solid {colors['border']}; "
        f"border-radius: {radius['small']}px;"
    )


def get_metric_caption_style(theme=None):
    colors = _colors(theme)

    return (
        f"color: {colors['text_secondary']}; "
        "font-size: 9pt;"
    )


def get_metric_value_style(theme=None):
    colors = _colors(theme)
    fonts = _fonts(theme)

    return (
        f"color: {colors['normal']}; "
        f"font-family: \"{fonts['mono_family']}\"; "
        "font-size: 12pt; "
        "font-weight: 700;"
    )


def apply_main_window_theme(window, theme=None):
    window.setStyleSheet(build_main_window_stylesheet(theme))

    if hasattr(window, "ecg1WaveLabel"):
        window.ecg1WaveLabel.setStyleSheet(get_wave_panel_style(theme))
    if hasattr(window, "metricsLabel"):
        window.metricsLabel.setStyleSheet(get_metrics_label_style(theme))
