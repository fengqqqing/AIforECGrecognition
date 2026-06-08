# ECG Monitor 上位机入口模块
# 职责：解析命令行参数、初始化日志和高 DPI 支持、启动 PyQt 主窗口。
# 启动方式：python main.py [--demo]
#   --demo 启动后自动进入固定场景的 Demo 离线回放（使用真实模型推理）。

import argparse
import logging
import sys

from ParamMonitor import ParamMonitor
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore as qc


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="ECG Monitor")
    parser.add_argument("--demo", action="store_true", help="启动后自动进入固定 demo 离线回放")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    qc.QCoreApplication.setAttribute(qc.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = ParamMonitor(demo_mode=args.demo)
    window.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
