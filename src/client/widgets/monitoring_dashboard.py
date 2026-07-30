"""
实时监控仪表盘
参数卡片 + 实时曲线 + 告警区
"""
import math
import random

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont


class MetricCard(QFrame):
    """参数卡片"""
    def __init__(self, title: str, unit: str, color: str = "#2563EB"):
        super().__init__()
        self.setObjectName("cardFrame")
        self.setFixedHeight(110)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("metricLabel")
        self.value_label = QLabel("--")
        self.value_label.setObjectName("metricValue")
        self.value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
        unit_label = QLabel(unit)
        unit_label.setObjectName("metricUnit")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(unit_label)

    def set_value(self, value: float):
        self.value_label.setText(f"{value:.1f}")


class RealtimeChart(QWidget):
    """实时折线图（自绘）"""
    def __init__(self, title: str = "实时曲线"):
        super().__init__()
        self.setObjectName("cardFrame")
        self.setMinimumHeight(220)
        self.title = title
        self.data = {"cur": [], "vol": [], "spd": []}
        self.max_points = 60
        self.colors = {"cur": "#2563EB", "vol": "#22C55E", "spd": "#F59E0B"}

    def add_point(self, metric: str, value: float):
        if metric in self.data:
            self.data[metric].append(value)
            if len(self.data[metric]) > self.max_points:
                self.data[metric].pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor("#161B22"))
        painter.setPen(QColor("#E6EDF3"))
        painter.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        painter.drawText(16, 24, self.title)
        painter.setPen(QPen(QColor("#21262D"), 1))
        for i in range(1, 5):
            y = 40 + (h - 60) * i // 5
            painter.drawLine(16, y, w - 16, y)
        for metric, values in self.data.items():
            if len(values) < 2:
                continue
            color = QColor(self.colors.get(metric, "#2563EB"))
            painter.setPen(QPen(color, 2))
            step = (w - 32) / max(self.max_points - 1, 1)
            for i in range(1, len(values)):
                x1 = 16 + (i - 1) * step
                y1 = h - 20 - (values[i-1] % 400) * (h - 60) / 400
                x2 = 16 + i * step
                y2 = h - 20 - (values[i] % 400) * (h - 60) / 400
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        legend_x = w - 200
        labels = {"cur": "电流", "vol": "电压", "spd": "焊速"}
        for i, (metric, color) in enumerate(self.colors.items()):
            painter.setPen(QPen(QColor(color), 3))
            painter.drawLine(legend_x + i * 60, 16, legend_x + i * 60 + 16, 16)
            painter.setPen(QColor("#8B949E"))
            painter.setFont(QFont("Microsoft YaHei", 9))
            painter.drawText(legend_x + i * 60 + 20, 20, labels.get(metric, metric))


class MonitoringDashboard(QWidget):
    """实时监控仪表盘"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("焊接设备监控面板")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        info = QLabel("设备: DEV-W001 (1号焊接工位) | MIG焊机 | 状态: 运行中")
        info.setStyleSheet("color: #8B949E; font-size: 12px;")
        layout.addWidget(info)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)
        self.card_current = MetricCard("焊接电流", "A", "#2563EB")
        self.card_voltage = MetricCard("焊接电压", "V", "#22C55E")
        self.card_speed = MetricCard("焊接速度", "mm/min", "#F59E0B")
        self.card_gas = MetricCard("气体流量", "L/min", "#3B82F6")
        self.card_temp = MetricCard("设备温度", "℃", "#EF4444")
        self.card_vibration = MetricCard("设备振动", "m/s²", "#8B5CF6")
        cards_layout.addWidget(self.card_current, 0, 0)
        cards_layout.addWidget(self.card_voltage, 0, 1)
        cards_layout.addWidget(self.card_speed, 0, 2)
        cards_layout.addWidget(self.card_gas, 1, 0)
        cards_layout.addWidget(self.card_temp, 1, 1)
        cards_layout.addWidget(self.card_vibration, 1, 2)
        layout.addLayout(cards_layout)

        self.chart = RealtimeChart("实时参数曲线 (最近60秒)")
        layout.addWidget(self.chart)

        self.alert_frame = QFrame()
        self.alert_frame.setObjectName("cardFrame")
        alert_layout = QVBoxLayout(self.alert_frame)
        alert_title = QLabel("异常告警")
        alert_title.setObjectName("cardTitle")
        alert_title.setStyleSheet("color: #EF4444;")
        self.alert_label = QLabel("所有参数正常")
        self.alert_label.setStyleSheet("color: #22C55E; font-size: 14px; padding: 8px;")
        alert_layout.addWidget(alert_title)
        alert_layout.addWidget(self.alert_label)
        layout.addWidget(self.alert_frame)

        self._tick = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_metrics)
        self.timer.start(1000)

    def _update_metrics(self):
        self._tick += 1
        t = self._tick * 0.1
        cur = 245 + math.sin(t) * 8 + random.uniform(-3, 3)
        vol = 28.5 + math.sin(t * 1.2) * 1.5 + random.uniform(-0.5, 0.5)
        spd = 520 + math.sin(t * 0.8) * 20 + random.uniform(-10, 10)
        gas = 22 + math.sin(t * 0.5) * 1.2 + random.uniform(-0.5, 0.5)
        temp = 55 + math.sin(t * 0.3) * 3 + random.uniform(-1, 1)
        vib = 0.12 + abs(math.sin(t * 2)) * 0.1

        self.card_current.set_value(cur)
        self.card_voltage.set_value(vol)
        self.card_speed.set_value(spd)
        self.card_gas.set_value(gas)
        self.card_temp.set_value(temp)
        self.card_vibration.set_value(vib)

        self.chart.add_point("cur", cur)
        self.chart.add_point("vol", vol)
        self.chart.add_point("spd", spd)

        if temp > 85 or vib > 0.5:
            self.alert_label.setText(f"温度={temp:.1f}℃ 振动={vib:.3f}m/s² 异常!")
            self.alert_label.setStyleSheet("color: #EF4444; font-size: 14px; padding: 8px;")
        else:
            self.alert_label.setText("所有参数正常")
            self.alert_label.setStyleSheet("color: #22C55E; font-size: 14px; padding: 8px;")

    def refresh(self):
        pass
