import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, QFormLayout

class ButtonListWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Dynamic Button List with Scroll')

        # 創建一個總布局
        layout = QVBoxLayout(self)

        # 創建一個 QScrollArea，來管理滾動
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)  # 自適應大小

        # 創建一個內部窗口用來承載按鈕
        button_container = QWidget()
        button_layout = QFormLayout(button_container)

        # 動態添加按鈕
        self.buttons = []
        for i in range(5):  # 可以調整按鈕數量
            button = QPushButton(f'Button {i + 1}', self)
            self.buttons.append(button)
            button_layout.addRow(button)

        # 設置 scroll_area 的主窗口為按鈕容器
        scroll_area.setWidget(button_container)

        # 把 scroll_area 添加到主 layout
        layout.addWidget(scroll_area)

        # 設置窗口大小
        self.setGeometry(200, 200, 20, 20)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ButtonListWindow()
    window.show()
    sys.exit(app.exec_())