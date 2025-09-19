import sys
import os
import folium
import osmnx as ox
import networkx as nx
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSpinBox, QPlainTextEdit
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from folium.plugins import Draw


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("地圖路徑規劃系統")
        self.resize(1200, 800)
        self.route_planning_active = False

        # ========= 主版面配置 =========
        self.main_layout = QHBoxLayout()

        # ========== 左側地圖顯示 ==========
        self.web_view = QWebEngineView()
        self.main_layout.addWidget(self.web_view, stretch=3)

        # 初始地圖 (台灣科大校區附近)
        self.start_location = [25.0135, 121.5416]
        self.map_file = "map.html"

        # 存放主要點與中繼點
        self.main_points = []  # 黑色點
        self.route_points = []  # 紅色中繼點

        # 初始化地圖
        self.update_map()

        # ========== 右側控制區 ==========
        self.controls_layout = QVBoxLayout()

        # 路線規劃按鈕
        self.btn_route_name = ("路線規劃")
        self.btn_route = QPushButton(self.btn_route_name)
        self.btn_route.clicked.connect(self.toggle_route_planning)
        self.controls_layout.addWidget(self.btn_route)

        # 自駕車資訊按鈕
        self.info_button = QPushButton("自駕車資訊")
        self.info_button.clicked.connect(self.show_car_info)
        self.controls_layout.addWidget(self.info_button)

        # 歷史紀錄按鈕
        self.history_button = QPushButton("歷史紀錄")
        self.history_button.clicked.connect(self.show_history)
        self.controls_layout.addWidget(self.history_button)

        # 中繼點距離設定
        self.step_label = QLabel("中繼點距離 (公尺)：")
        self.controls_layout.addWidget(self.step_label)

        self.step_input = QSpinBox()
        self.step_input.setMinimum(1)
        self.step_input.setMaximum(1000)
        self.step_input.setValue(5)  # 預設 5 公尺
        self.controls_layout.addWidget(self.step_input)

        # 計算路徑按鈕
        self.calc_button = QPushButton("計算路徑")
        self.calc_button.clicked.connect(self.calculate_route)
        self.controls_layout.addWidget(self.calc_button)

        # 清除主要點
        self.clear_button = QPushButton("清除主要點")
        self.clear_button.clicked.connect(self.clear_main_points)
        self.controls_layout.addWidget(self.clear_button)

        # Log 輸出
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Log 輸出...")
        self.controls_layout.addWidget(self.log_output)

        # 把控制區放進主版面
        self.controls_widget = QWidget()
        self.controls_widget.setLayout(self.controls_layout)
        self.main_layout.addWidget(self.controls_widget)

        # 設定 central widget
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    # ========== 功能區 ==========
    def calculate_route(self):
        """計算主要點之間的路徑，並自動產生中繼點 (紅色點)"""
        if len(self.main_points) < 2:
            self.log("❌ 至少需要兩個主要點")
            return

        # 載入 OSMnx 圖資 (500 公尺範圍)
        G = ox.graph_from_point(self.start_location, dist=500, network_type="walk")

        # 將主要點轉換成圖中的節點
        nodes = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in self.main_points]

        # 計算路徑 (使用最短路徑)
        full_path = []
        for i in range(len(nodes) - 1):
            path = nx.shortest_path(G, nodes[i], nodes[i + 1], weight="length")
            full_path.extend(path)

        # 把路徑節點轉回經緯度
        route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in full_path]

        # 產生中繼點 (每隔 step_input 公尺)
        self.route_points = self.generate_waypoints(route_coords, self.step_input.value())

        self.log(f"✅ 路徑計算完成，共 {len(self.route_points)} 個中繼點")
        self.update_map(route_coords)
    #主要點
    def toggle_route_planning(self):
        if not self.route_planning_active:
            self.log("---啟動路線規劃模式---")
            self.btn_route_name = ("退出路線規劃")
            # self.btn_route.setText("退出路線規劃")
            self.route_planning_active = True
            
        else:
            self.log("---退出路線規劃模式---")
            self.btn_route_name = ("路線規劃")
            # self.btn_route.setText("路線規劃")
            self.route_planning_active = False
           
        
           


    def generate_waypoints(self, coords, step):
        """沿路徑每隔 step 公尺生成一個中繼點"""
        import geopy.distance
        waypoints = []
        for i in range(len(coords) - 1):
            start = coords[i]
            end = coords[i + 1]
            dist = geopy.distance.distance(start, end).meters
            steps = int(dist // step)
            for j in range(steps):
                lat = start[0] + (end[0] - start[0]) * (j * step / dist)
                lon = start[1] + (end[1] - start[1]) * (j * step / dist)
                waypoints.append((lat, lon))
        return waypoints

    def clear_main_points(self):
        """清除主要點"""
        self.main_points = []
        self.route_points = []
        self.log("已清除主要點")
        self.update_map()

    def update_map(self, route_coords=None):
        """更新地圖顯示"""
        m = folium.Map(location=self.start_location, zoom_start=17)

        # 啟用 folium Draw 插件 (讓使用者能在地圖上點擊新增 marker)
        draw = Draw(export=True)
        draw.add_to(m)

        # 標記主要點 (黑色)
        for i, (lat, lon) in enumerate(self.main_points, 1):
            folium.Marker([lat, lon], popup=f"主要點 {i}",
                          icon=folium.Icon(color="black")).add_to(m)

        # 標記中繼點 (紅色)
        for i, (lat, lon) in enumerate(self.route_points, 1):
            folium.CircleMarker([lat, lon], radius=3, color="red",
                                fill=True, popup=f"中繼點 {i}").add_to(m)

        # 畫出路徑
        if route_coords:
            folium.PolyLine(route_coords, color="blue", weight=3).add_to(m)

        # 存檔 & 顯示
        m.save(self.map_file)
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(self.map_file)))

    def log(self, text):
        """輸出到 log 視窗"""
        self.log_output.appendPlainText(text)

    def show_car_info(self):
        self.log("🚗 顯示自駕車資訊")

    def show_history(self):
        self.log("📜 顯示歷史紀錄")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
