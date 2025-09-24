from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, QObject
from PyQt5.QtWebChannel import QWebChannel
import sys, os, json, copy

# ======= OSMnx & NetworkX (路徑計算) =======
import osmnx as ox
import networkx as nx
import numpy as np

# 建立一次圖，避免每次都下載
center_point = (25.013503424902265, 121.54059751813759)  # 台科大中心
dist = 800  # 公尺
G = ox.graph_from_point(center_point, dist=dist, network_type="walk")
print("地圖下載完成 (OSMnx)")

def calculate_route(points, points_per_segment=20):
    """
    points: [(lat, lon), ...] 起點 + 中繼點 + 終點
    return: [(lat, lon), ...] 最佳化完整路徑
    """
    # 內插中繼點
    interpolated_points = []
    for i in range(len(points) - 1):
        lat1, lon1 = points[i]
        lat2, lon2 = points[i + 1]
        lats = np.linspace(lat1, lat2, points_per_segment, endpoint=False)
        lons = np.linspace(lon1, lon2, points_per_segment, endpoint=False)
        interpolated_points.extend(zip(lats, lons))
    interpolated_points.append(points[-1])

    # 找最近 OSM 節點
    nodes = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in interpolated_points]
    deduped_nodes = []
    [deduped_nodes.append(n) for n in nodes if n not in deduped_nodes]

    # 計算最短路徑
    full_route = []
    for i in range(len(deduped_nodes) - 1):
        start, end = deduped_nodes[i], deduped_nodes[i + 1]
        try:
            segment = nx.shortest_path(G, start, end, weight="length")
            if i > 0:
                segment = segment[1:]  # 避免重複節點
            full_route.extend(segment)
        except nx.NetworkXNoPath:
            print(f"找不到路徑: {start} → {end}")
            continue

    # 轉回座標
    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in full_route]
    return coords


# ======= 與 JS 溝通的橋樑 =======
class Bridge(QObject):
    def __init__(self, routes_file="code/routes.json"):
        super().__init__()
        self.routes = self.load_routes(routes_file).get("routes", {}).get("default_route", {})
        self.current_route = self.load_routes(routes_file).get("routes", {}).get("current_route", [])

    def load_routes(self, filename):
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print("JSON 格式錯誤，載入失敗")
                    return {}
        else:
            print(f"找不到 {filename}，使用空路線")
            return {}

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

        js_code = f"drawInitialRoute({json.dumps(self.current_route)});"
        self.parent_window.webview.page().runJavaScript(js_code)

    @pyqtSlot(int, float, float)
    def nodeMoved(self, index, lat, lng):
        if 0 <= index < len(self.current_route):
            self.current_route[index] = [round(lat, 6), round(lng, 6)]
            print(f"節點 {index + 1} 移動到座標: [{lat:.6f}, {lng:.6f}]")

    @pyqtSlot("QVariantList")
    def updateRoute(self, new_route):
        formatted_route = [[round(lat, 6), round(lng, 6)] for lat, lng in new_route]
        self.current_route = formatted_route
        print("更新後路線:")
        for point in self.current_route:
            print(f"[{point[0]:.6f}, {point[1]:.6f}]")


# ======= 自訂 Logger =======
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


# ======= 主視窗 =======
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

        # 左側地圖
        self.webview = QWebEngineView()
        file_path = os.path.abspath(html_file)

        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.bridge.parent_window = self
        self.channel.registerObject("bridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        self.webview.load(QUrl.fromLocalFile(file_path))
        main_layout.addWidget(self.webview, 3)

        # 右側面板
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

        self.btn_optimize = QPushButton("最佳化路線")
        self.btn_optimize.clicked.connect(self.optimize_route)
        self.button_layout.addWidget(self.btn_optimize)

        self.route_buttons = []

        self.btn_info = QPushButton("自駕車資訊")
        self.btn_info.clicked.connect(self.self_driving_information)
        self.button_layout.addWidget(self.btn_info)

        self.btn_history = QPushButton("歷史紀錄")
        self.btn_history.clicked.connect(self.historical_record)
        self.button_layout.addWidget(self.btn_history)

        self.button_layout.addStretch()

        # Log 視窗
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setFixedHeight(200)
        right_layout.addWidget(self.log_widget)

        self.webview.loadFinished.connect(self.on_page_load_finished)

        # 重定向 print 到 log_widget
        sys.stdout = Logger(self.log_widget)
        sys.stderr = Logger(self.log_widget)

    def on_page_load_finished(self):
        if self.bridge.current_route:
            js_code = f"drawInitialRoute({json.dumps(self.bridge.current_route)});"
            self.webview.page().runJavaScript(js_code)
            print("---已載入當前路線到地圖---")

    def toggle_route_planning(self):
        if not self.route_planning_active:
            print("---啟動路線規劃模式---")
            self.webview.page().runJavaScript("enableRoutePlanning();")
            self.btn_route.setText("退出路線規劃")
            self.route_planning_active = True
            self.show_route_buttons()
            self.btn_info.setEnabled(False)
            self.btn_history.setEnabled(False)
        else:
            print("---退出路線規劃模式---")
            self.webview.page().runJavaScript("disableRoutePlanning();")
            self.btn_route.setText("路線規劃")
            self.route_planning_active = False
            self.clear_route_buttons()
            self.btn_info.setEnabled(True)
            self.btn_history.setEnabled(True)
            self.save_routes_to_json()

    def show_route_buttons(self):
        for i, (name, route) in enumerate(self.bridge.routes.items()):
            btn = QPushButton(name)
            btn.setFixedWidth(int(self.btn_route.width() * 0.9))
            btn.clicked.connect(lambda checked, r=route: self.load_route(r))
            h_layout = QHBoxLayout()
            h_layout.addStretch()
            h_layout.addWidget(btn)
            self.button_layout.insertLayout(i + 1, h_layout)
            self.route_buttons.append(btn)

    def clear_route_buttons(self):
        for btn in self.route_buttons:
            self.button_layout.removeWidget(btn)
            btn.deleteLater()
        self.route_buttons = []

    def load_route(self, route):
        print("載入路線:")
        for point in route:
            print(f"[{point[0]:.6f}, {point[1]:.6f}]")
        self.bridge.current_route = copy.deepcopy(route)
        self.webview.page().runJavaScript(f"drawInitialRoute({json.dumps(route)});")

    def save_routes_to_json(self, filename="code/routes.json"):
        data = {
            "routes": {
                "default_route": self.bridge.routes,
                "current_route": self.bridge.current_route
            }
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"---路線已儲存於 {filename}---")

    def optimize_route(self):
        if not self.bridge.current_route or len(self.bridge.current_route) < 2:
            print("請至少設定起點與終點")
            return
        print("正在計算最佳化路徑...")
        new_route = calculate_route(self.bridge.current_route)
        self.bridge.current_route = new_route
        js_code = f"drawInitialRoute({json.dumps(new_route)});"
        self.webview.page().runJavaScript(js_code)
        print("---最佳化路徑已更新---")

    def self_driving_information(self):
        print("自駕車資訊")

    def historical_record(self):
        print("歷史紀錄")


# ======= 主程式 =======
if __name__ == "__main__":
    app = QApplication(sys.argv)
    html_file = "code/map.html"  # 你的地圖 HTML
    window = MainWindow(html_file)
    window.show()
    sys.exit(app.exec_())
