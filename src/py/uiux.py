from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import sys
import os

# ----------------------
class MainWindow(QMainWindow):
    def __init__(self, html_file):
        super().__init__()
        self.setWindowTitle("智慧校園自駕巡檢系統")
        self.resize(1280, 720)

        # 主 widget 與 layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 左側地圖
        self.webview = QWebEngineView()
        file_path = os.path.abspath(html_file)
        self.webview.load(QUrl.fromLocalFile(file_path))
        main_layout.addWidget(self.webview, 3)

        # 右側按鈕區
        button_layout = QVBoxLayout()
        main_layout.addLayout(button_layout, 1)

        # 按鈕
        btn_route = QPushButton("路線規劃")
        btn_route.clicked.connect(self.route_planning)
        button_layout.addWidget(btn_route)

        btn_info = QPushButton("自駕車資訊")
        btn_info.clicked.connect(self.self_driving_information)
        button_layout.addWidget(btn_info)

        btn_history = QPushButton("歷史紀錄")
        btn_history.clicked.connect(self.historical_record)
        button_layout.addWidget(btn_history)

        button_layout.addStretch()

    # ----------------------
    def route_planning(self):
        print("route_planning")
        file_path = os.path.abspath(html_file)
        self.webview.load(QUrl.fromLocalFile(file_path))

    def self_driving_information(self):
        print("self_driving_information")

    def historical_record(self):
        print("historical_record")

# ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    html_file = "code\map.html"
    window = MainWindow(html_file)
    window.show()
    sys.exit(app.exec_())
