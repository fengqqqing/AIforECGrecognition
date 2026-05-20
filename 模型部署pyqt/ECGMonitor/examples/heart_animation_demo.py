import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # 设置窗口标题和大小
        self.setWindowTitle('纵向拉长的数字')
        self.setGeometry(100, 100, 400, 300)

        # 创建一个 QLabel 并设置其属性
        self.label = QLabel('1234567890', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Arial', 20))

        # 设置 QLabel 的初始大小和位置
        self.label.setGeometry(50, 50, 300, 100)

        # 初始化拉伸比例和相关参数
        self.stretch_factor = 1.0
        self.step = 0.05
        self.growing = True

        # 创建一个 QTimer 定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_stretch)
        self.timer.start(100)  # 每100毫秒更新一次

    def animate_stretch(self):
        # 更新拉伸比例
        if self.growing:
            self.stretch_factor += self.step
            if self.stretch_factor >= 2.0:  # 拉伸到2.0倍
                self.growing = False
        else:
            self.stretch_factor -= self.step
            if self.stretch_factor <= 1.0:  # 恢复到1.0倍
                self.growing = True

        # 更新 QLabel 的大小
        new_height = int(100 * self.stretch_factor)
        self.label.resize(300, new_height)

        # 更新 QLabel 的字体大小
        font = self.label.font()
        font.setPointSize(20 * self.stretch_factor)
        self.label.setFont(font)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
