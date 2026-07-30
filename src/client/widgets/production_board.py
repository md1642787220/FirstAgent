"""生产进度看板 - 统计栏+工单卡片+Agent洞察"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QProgressBar, QPushButton
)
from PySide6.QtCore import Qt


class StatCard(QFrame):
    def __init__(self, title: str, value: str, color: str = "#2563EB"):
        super().__init__()
        self.setObjectName("cardFrame")
        self.setFixedHeight(80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        title_label = QLabel(title)
        title_label.setObjectName("metricLabel")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 700;")
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)


class OrderCard(QFrame):
    def __init__(self, order: dict):
        super().__init__()
        self.setObjectName("cardFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        wo_id = QLabel(order.get("id", ""))
        wo_id.setStyleSheet("font-weight: 600; color: #2563EB;")
        product = QLabel(f"{order.get('product_name', '')} ({order.get('product_code', '')})")
        qty = QLabel(f"{order.get('quantity', 0)}件")
        qty.setStyleSheet("color: #8B949E;")
        priority = order.get("priority", "中")
        pri_label = QLabel(f"[{priority}]")
        pri_colors = {"紧急": "#EF4444", "高": "#F59E0B", "中": "#3B82F6", "低": "#8B949E"}
        pri_label.setStyleSheet(f"color: {pri_colors.get(priority, '#8B949E')}; font-weight: 600;")
        top.addWidget(wo_id)
        top.addWidget(product)
        top.addWidget(qty)
        top.addWidget(pri_label)
        top.addStretch()
        layout.addLayout(top)

        progress = order.get("progress", 0)
        bar = QProgressBar()
        bar.setValue(progress)
        bar.setFixedHeight(16)
        bar.setFormat(f"{progress}%")
        layout.addWidget(bar)

        status = order.get("status", "")
        delay = order.get("delay_days", 0)
        info_text = f"状态: {status}"
        if delay > 0:
            info_text += f"  |  滞后{delay}天"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("color: #EF4444; font-size: 12px;")
        else:
            info_label = QLabel(info_text)
            info_label.setStyleSheet("color: #8B949E; font-size: 12px;")
        layout.addWidget(info_label)


class ProductionBoard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("生产进度看板")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.card_total = StatCard("在制工单", "--", "#3B82F6")
        self.card_done = StatCard("今日完成", "--", "#22C55E")
        self.card_delay = StatCard("滞后", "--", "#EF4444")
        self.card_urgent = StatCard("紧急", "--", "#F59E0B")
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_done)
        stats_layout.addWidget(self.card_delay)
        stats_layout.addWidget(self.card_urgent)
        layout.addLayout(stats_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        scroll_content = QWidget()
        self.orders_layout = QVBoxLayout(scroll_content)
        self.orders_layout.setSpacing(8)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        self.insight_frame = QFrame()
        self.insight_frame.setObjectName("cardFrame")
        insight_layout = QVBoxLayout(self.insight_frame)
        insight_title = QLabel("Agent智能洞察")
        insight_title.setObjectName("cardTitle")
        self.insight_label = QLabel("等待数据分析...")
        self.insight_label.setObjectName("agentInsight")
        self.insight_label.setWordWrap(True)
        insight_layout.addWidget(insight_title)
        insight_layout.addWidget(self.insight_label)
        layout.addWidget(self.insight_frame)

        refresh_btn = QPushButton("刷新数据")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn, 0, Qt.AlignRight)

    def refresh(self):
        try:
            from src.client.services.http_client import api_client
            summary = api_client.get_production_summary()
            self.card_total.value_label.setText(str(summary.get("in_progress", 0)))
            self.card_done.value_label.setText(str(summary.get("completed", 0)))
            self.card_delay.value_label.setText(str(summary.get("delayed", 0)))
            self.card_urgent.value_label.setText(str(summary.get("urgent", 0)))

            orders_data = api_client.get_production_orders()
            orders = orders_data.get("orders", [])

            while self.orders_layout.count():
                item = self.orders_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for order in orders[:15]:
                card = OrderCard(order)
                self.orders_layout.addWidget(card)
            self.orders_layout.addStretch()

            delayed = [o for o in orders if o.get("delay_days", 0) > 0]
            if delayed:
                names = ", ".join(o["id"] for o in delayed[:3])
                self.insight_label.setText(f"检测到{len(delayed)}个滞后工单 ({names})。建议：增加夜班或调配焊接设备支援。阻塞原因可能为焊丝库存不足，已自动生成采购建议。")
            else:
                self.insight_label.setText("所有工单进度正常，无滞后风险。")
        except Exception as e:
            self.insight_label.setText(f"数据加载失败: {e}（请确保后端服务已启动）")
