"""
Qt主窗口
QTabWidget多标签页布局，6大功能面板切换
"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QStatusBar
)
from PySide6.QtCore import Qt, QTimer
from datetime import datetime
from pathlib import Path

from src.client.widgets.monitoring_dashboard import MonitoringDashboard
from src.client.widgets.production_board import ProductionBoard
from src.client.widgets.bom_panel import BOMPanel
from src.client.widgets.inventory_board import InventoryBoard
from src.client.widgets.chat_window import ChatWindow
from src.client.widgets.trace_panel import TracePanel


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("焊接设备AI Agent综合管理平台")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 750)

        # 加载样式表
        self._load_stylesheet()

        # 中央Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab导航
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # 初始化6大面板
        self.dashboard = MonitoringDashboard()
        self.production = ProductionBoard()
        self.bom_panel = BOMPanel()
        self.inventory = InventoryBoard()
        self.chat = ChatWindow()
        self.trace = TracePanel()

        self.tabs.addTab(self.dashboard, "  实时监控  ")
        self.tabs.addTab(self.production, "  生产进度  ")
        self.tabs.addTab(self.bom_panel, "  BOM管理  ")
        self.tabs.addTab(self.inventory, "  库存分析  ")
        self.tabs.addTab(self.chat, "  AI对话  ")
        self.tabs.addTab(self.trace, "  执行轨迹  ")

        # 状态栏
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("● 已连接")
        self.status_label.setStyleSheet("color: #22C55E; padding: 0 10px;")
        self.time_label = QLabel()
        self.alert_label = QLabel("告警: 0")
        self.alert_label.setStyleSheet("color: #F59E0B; padding: 0 10px;")
        status.addWidget(self.status_label)
        status.addPermanentWidget(self.alert_label)
        status.addPermanentWidget(self.time_label)

        # 时钟
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)
        self._update_time()

        # 切换Tab时刷新数据
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _load_stylesheet(self):
        qss_path = Path(__file__).parent / "styles" / "theme.qss"
        if qss_path.exists():
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(now)

    def _on_tab_changed(self, index: int):
        """切换Tab时刷新对应面板数据"""
        widget = self.tabs.widget(index)
        if hasattr(widget, "refresh"):
            widget.refresh()

    def update_alerts(self, count: int):
        self.alert_label.setText(f"告警: {count}")
