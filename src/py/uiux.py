from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, QObject
from PyQt5.QtWebChannel import QWebChannel
import sys, os, json

# ---------------------- 與 JS 溝通的橋樑 ----------------------
class Bridge(QObject):
    def __init__(self):
        super().__init__()
        self.routes = {
            "路線 A": [
                [25.012190, 121.541713],
                [25.012927, 121.540954],
                [25.013330, 121.541423],
                [25.012674, 121.542094],
                [25.012268, 121.541638]
            ],
            "路線 B": [
                [25.012190, 121.541713],
                [25.012259, 121.541646],
                [25.012664, 121.542099],
                [25.013355, 121.542834],
                [25.013984, 121.542191],
                [25.013318, 121.541429],
                [25.013556, 121.541174],
                [25.013151, 121.540710],
                [25.012920, 121.540954]
            ],
            "路線 C": [
                [25.012190, 121.541713],
                [25.012927, 121.540954],
                [25.013326, 121.541423],
                [25.013979, 121.542188],
                [25.013350, 121.542837],
                [25.012672, 121.542091],
                [25.012266, 121.541646]
            ]
        }
        self.current_route = []

    @pyqtSlot(float, float)
    def receiveCoords(self, lat, lng):
        print(f"新增節點: [{lat:.6f}, {lng:.6f}]")
        self.current_route.append([lat, lng])

    @pyqtSlot(int)
    def deleteNode(self, index):
        if 0 <= index < len(self.current_route):
            lat, lng = self.current_route[index]
            print(f"刪除節點: [{lat:.6f}, {lng:.6f}]")
            self.current_route.pop(index)

    @pyqtSlot("QVariantList")
    def updateRoute(self, new_route):
        formatted_route = [[round(lat,6), round(lng,6)] for lat, lng in new_route]
        self.current_route = formatted_route
        print(f"更新後路線: {formatted_route}")

# ---------------------- 自訂 Logger ----------------------
class Logger:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        message = message.strip()
        if message:
            self.widget.append(message)
            self.widget.verticalScrollBar().setValue(self.widget.verticalScrollBar().maximum())

    def flush(self):
        pass

# ---------------------- 主視窗 ----------------------
class MainWindow(QMainWindow):
    def __init__(self, html_file):
        super().__init__()
        self.setWindowTitle("智慧校園自駕巡檢系統")
        self.resize(1280, 720)

        self.route_planning_active = False

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # ---------------- 左側地圖 ----------------
        self.webview = QWebEngineView()
        file_path = os.path.abspath(html_file)

        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("bridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        self.webview.load(QUrl.fromLocalFile(file_path))
        main_layout.addWidget(self.webview, 3)

        # ---------------- 右側面板 ----------------
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, 1)

        # 按鈕區
        self.button_layout = QVBoxLayout()
        right_layout.addLayout(self.button_layout)

        self.btn_route = QPushButton("路線規劃")
        self.btn_route.clicked.connect(self.toggle_route_planning)
        self.button_layout.addWidget(self.btn_route)

        self.route_buttons = []

        self.btn_info = QPushButton("自駕車資訊")
        self.btn_info.clicked.connect(self.self_driving_information)
        self.button_layout.addWidget(self.btn_info)

        self.btn_history = QPushButton("歷史紀錄")
        self.btn_history.clicked.connect(self.historical_record)
        self.button_layout.addWidget(self.btn_history)

        self.button_layout.addStretch()  # 按鈕區可自動拉伸

        # Log 視窗固定在右側下方
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setFixedHeight(200)  # 固定高度
        right_layout.addWidget(self.log_widget)  # 放在按鈕區下方

        # 將 print 重定向到 log_widget
        sys.stdout = Logger(self.log_widget)
        sys.stderr = Logger(self.log_widget)

    # ---------------------- 路線規劃 ----------------------
    def toggle_route_planning(self):
        if not self.route_planning_active:
            print("---啟動路線規劃模式---")
            self.webview.page().runJavaScript("enableRoutePlanning();")
            self.btn_route.setText("退出路線規劃")
            self.route_planning_active = True
            self.show_route_buttons()

            # 禁用其他按鈕
            self.btn_info.setEnabled(False)
            self.btn_history.setEnabled(False)
        else:
            print("---退出路線規劃模式---")
            self.webview.page().runJavaScript("disableRoutePlanning();")
            self.btn_route.setText("路線規劃")
            self.route_planning_active = False
            self.clear_route_buttons()

            # 啟用其他按鈕
            self.btn_info.setEnabled(True)
            self.btn_history.setEnabled(True)

            # 退出規劃模式時輸出更新後路線
            if self.bridge.current_route:
                print(f"更新後路線: ")
                for point in self.bridge.current_route:
                    lat, lng = point
                    print(f"[{lat:.6f}, {lng:.6f}]")

    def show_route_buttons(self):
        for i, (name, route) in enumerate(self.bridge.routes.items()):
            btn = QPushButton(name)
            btn.setFixedWidth(280)  # 設定小一點的寬度
            btn.clicked.connect(lambda checked, r=route: self.load_route(r))

            # 使用水平 layout 讓按鈕靠右
            h_layout = QHBoxLayout()
            h_layout.addStretch()       # 左側空間自動撐開
            h_layout.addWidget(btn)     # 按鈕靠右
            self.button_layout.insertLayout(i + 1, h_layout)

            self.route_buttons.append(btn)

    def clear_route_buttons(self):
        for btn in self.route_buttons:
            self.button_layout.removeWidget(btn)
            btn.deleteLater()
        self.route_buttons = []

    def load_route(self, route):
        print(f"載入路線: ")
        for point in route:
            lat, lng = point
            print(f"[{lat:.6f}, {lng:.6f}]")
        self.bridge.current_route = route
        self.webview.page().runJavaScript(f"drawInitialRoute({json.dumps(route)});")

    def self_driving_information(self):
        print("自駕車資訊")

    def historical_record(self):
        print("歷史紀錄")

# ----------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    html_file = "code/map.html"
    window = MainWindow(html_file)
    window.show()
    sys.exit(app.exec_())
