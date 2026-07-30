"""BOM管理面板 - 树形展示+齐套分析"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QComboBox
)
from PySide6.QtCore import Qt


class BOMPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("BOM智能管理")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.bom_selector = QComboBox()
        self.bom_selector.setMinimumWidth(250)
        self.btn_query = QPushButton("查询BOM")
        self.btn_availability = QPushButton("齐套分析")
        self.btn_availability.setObjectName("secondaryBtn")
        toolbar.addWidget(QLabel("选择BOM:"))
        toolbar.addWidget(self.bom_selector)
        toolbar.addWidget(self.btn_query)
        toolbar.addWidget(self.btn_availability)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["物料编码", "物料名称", "规格", "用量", "单位", "类型", "单价", "供应商"])
        self.tree.header().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tree, 1)

        stats_bar = QHBoxLayout()
        self.label_items = QLabel("物料项: 0")
        self.label_cost = QLabel("总成本: 0.00")
        self.label_availability = QLabel("齐套率: --")
        for lbl in [self.label_items, self.label_cost, self.label_availability]:
            lbl.setStyleSheet("color: #8B949E; font-size: 13px; padding: 4px 16px;")
            stats_bar.addWidget(lbl)
        stats_bar.addStretch()
        layout.addLayout(stats_bar)

        self.btn_query.clicked.connect(self.refresh)
        self.btn_availability.clicked.connect(self._check_availability)

    def refresh(self):
        try:
            from src.client.services.http_client import api_client
            boms_data = api_client.get_all_boms()
            boms = boms_data.get("boms", [])
            self.bom_selector.clear()
            for bom in boms:
                self.bom_selector.addItem(f"{bom['id']} - {bom['product_name']} ({bom['version']})", bom["id"])
            if boms:
                self._load_bom(boms[0]["id"])
        except Exception as e:
            self.label_items.setText(f"加载失败: {e}")

    def _load_bom(self, bom_id: str):
        from src.client.services.http_client import api_client
        data = api_client.get_bom(bom_id)
        self.tree.clear()
        items = data.get("items", [])
        for item in items:
            tree_item = QTreeWidgetItem([
                item.get("material_code", ""),
                item.get("material_name", ""),
                item.get("specification", ""),
                str(item.get("quantity", 0)),
                item.get("unit", ""),
                item.get("material_type", ""),
                f"{item.get('cost', 0):.2f}",
                item.get("source_supplier", ""),
            ])
            self.tree.addTopLevelItem(tree_item)
        self.label_items.setText(f"物料项: {len(items)}")
        self.label_cost.setText(f"总成本: {data.get('total_cost', 0):.2f}")
        self.label_availability.setText("齐套率: --")

    def _check_availability(self):
        bom_id = self.bom_selector.currentData()
        if not bom_id:
            return
        try:
            from src.client.services.http_client import api_client
            data = api_client.check_availability(bom_id)
            rate = data.get("availability_rate", 0)
            shortage = data.get("shortage_items", 0)
            color = "#22C55E" if rate >= 80 else "#EF4444"
            self.label_availability.setText(f"齐套率: {rate}% (缺货{shortage}项)")
            self.label_availability.setStyleSheet(f"color: {color}; font-size: 13px; padding: 4px 16px; font-weight: 600;")
        except Exception as e:
            self.label_availability.setText(f"分析失败: {e}")
