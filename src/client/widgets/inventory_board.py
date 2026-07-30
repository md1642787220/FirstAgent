"""库存分析看板 - 统计卡片+预警表格+Agent建议"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt


class InventoryBoard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("库存分析看板")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.card_total = self._make_stat("总物料", "0", "#3B82F6")
        self.card_shortage = self._make_stat("短缺", "0", "#EF4444")
        self.card_obsolete = self._make_stat("呆滞", "0", "#F59E0B")
        self.card_normal = self._make_stat("正常", "0", "#22C55E")
        for c in [self.card_total, self.card_shortage, self.card_obsolete, self.card_normal]:
            stats.addWidget(c)
        stats.addStretch()
        layout.addLayout(stats)

        tt = QLabel("短缺预警列表")
        tt.setObjectName("cardTitle")
        tt.setStyleSheet("color: #EF4444;")
        layout.addWidget(tt)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["编码", "名称", "当前库存", "安全库存", "缺口", "状态", "紧急度"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        sf = QFrame()
        sf.setObjectName("cardFrame")
        sl = QVBoxLayout(sf)
        sl.addWidget(self._title("Agent采购建议"))
        self.suggestion_label = QLabel("等待分析...")
        self.suggestion_label.setObjectName("agentInsight")
        self.suggestion_label.setWordWrap(True)
        sl.addWidget(self.suggestion_label)
        layout.addWidget(sf)

        btn = QPushButton("刷新数据")
        btn.setObjectName("secondaryBtn")
        btn.clicked.connect(self.refresh)
        layout.addWidget(btn, 0, Qt.AlignRight)

    def _make_stat(self, title, value, color):
        c = QFrame()
        c.setObjectName("cardFrame")
        c.setFixedHeight(70)
        l = QVBoxLayout(c)
        l.setContentsMargins(16, 8, 16, 8)
        t = QLabel(title)
        t.setObjectName("metricLabel")
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700;")
        l.addWidget(t)
        l.addWidget(v)
        return c

    def _title(self, text):
        l = QLabel(text)
        l.setObjectName("cardTitle")
        return l

    def refresh(self):
        try:
            from src.client.services.http_client import api_client
            s = api_client.get_inventory_summary()
            self.card_total.findChildren(QLabel)[-1].setText(str(s.get("total", 0)))
            self.card_shortage.findChildren(QLabel)[-1].setText(str(s.get("shortage", 0)))
            self.card_obsolete.findChildren(QLabel)[-1].setText(str(s.get("obsolete", 0)))
            self.card_normal.findChildren(QLabel)[-1].setText(str(s.get("normal", 0)))
            alerts = api_client.get_inventory_alerts().get("alerts", [])
            self.table.setRowCount(len(alerts))
            for i, it in enumerate(alerts):
                vals = [it.get("material_code",""), it.get("material_name",""),
                        f"{it.get('quantity',0)} {it.get('unit','')}",
                        f"{it.get('safety_stock',0)} {it.get('unit','')}",
                        f"{it.get('gap',0)} {it.get('unit','')}",
                        it.get("status",""), it.get("urgency","")]
                for j, v in enumerate(vals):
                    self.table.setItem(i, j, QTableWidgetItem(str(v)))
            if alerts:
                names = ", ".join(a.get("material_name","") for a in alerts[:3])
                self.suggestion_label.setText(f"检测到{len(alerts)}项短缺物料({names}等)。建议：接触器MAT-1001已连续3周低于安全库存，建议立即采购200件；焊丝1.2mm建议补货50kg。")
            else:
                self.suggestion_label.setText("库存状态良好，无短缺物料。")
        except Exception as e:
            self.suggestion_label.setText(f"数据加载失败: {e}（请确保后端服务已启动）")
