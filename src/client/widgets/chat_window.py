"""AI对话窗口"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QTextEdit,
    QPushButton, QScrollArea, QHBoxLayout
)
from PySide6.QtCore import Qt, QThread, Signal


class ChatWorker(QThread):
    result_ready = Signal(dict)
    error = Signal(str)
    def __init__(self, msg, sid=None):
        super().__init__()
        self.msg = msg
        self.sid = sid
    def run(self):
        try:
            from src.client.services.http_client import api_client
            self.result_ready.emit(api_client.chat_sync(self.msg, self.sid))
        except Exception as e:
            self.error.emit(str(e))


class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.session_id = None
        L = QVBoxLayout(self)
        L.setSpacing(8); L.setContentsMargins(16,16,16,16)
        t = QLabel("AI Agent 对话交互"); t.setObjectName("sectionTitle"); L.addWidget(t)
        h = QLabel("支持自然语言提问，Agent自动路由到各专业模块")
        h.setStyleSheet("color:#8B949E;font-size:12px;"); L.addWidget(h)
        sc = QScrollArea(); sc.setWidgetResizable(True)
        sc.setStyleSheet("QScrollArea{border:none;}")
        mw = QWidget(); self.ml = QVBoxLayout(mw)
        self.ml.setSpacing(12); self.ml.addStretch()
        sc.setWidget(mw); L.addWidget(sc,1)
        ql = QHBoxLayout()
        for txt in ["当前设备参数","生产进度汇总","库存短缺预警","Q235 10mm怎么焊"]:
            b = QPushButton(txt); b.setObjectName("secondaryBtn")
            b.clicked.connect(lambda _,x=txt: self._send(x)); ql.addWidget(b)
        ql.addStretch(); L.addLayout(ql)
        il = QHBoxLayout()
        self.ib = QTextEdit(); self.ib.setFixedHeight(60)
        self.ib.setPlaceholderText("输入您的问题...")
        self.bs = QPushButton("发送"); self.bs.setFixedHeight(60)
        self.bs.clicked.connect(self._on_send)
        il.addWidget(self.ib,1); il.addWidget(self.bs); L.addLayout(il)
        self._add_agent("您好！我是焊接设备AI Agent助手，可以回答设备、生产、BOM、库存和工艺相关问题。")

    def _on_send(self):
        t = self.ib.toPlainText().strip()
        if t: self._send(t); self.ib.clear()

    def _send(self, text):
        self._add_user(text)
        self.bs.setEnabled(False); self.bs.setText("思考中...")
        self.w = ChatWorker(text, self.session_id)
        self.w.result_ready.connect(self._on_res)
        self.w.error.connect(self._on_err)
        self.w.start()

    def _on_res(self, r):
        self.session_id = r.get("session_id")
        a = r.get("answer","无回复")
        ag = r.get("routed_agents",[])
        p = f"[意图:{r.get('intent','')} | Agent:{', '.join(ag)}]\n\n" if ag else ""
        self._add_agent(p+a); self.bs.setEnabled(True); self.bs.setText("发送")

    def _on_err(self, e):
        self._add_agent(f"请求出错: {e}\n\n请确保后端服务已启动"); self.bs.setEnabled(True); self.bs.setText("发送")

    def _add_user(self, text):
        b = QFrame(); b.setObjectName("userBubble"); b.setMaximumWidth(500)
        l = QVBoxLayout(b); l.setContentsMargins(14,10,14,10)
        lb = QLabel(text); lb.setWordWrap(True); lb.setStyleSheet("color:#FFF;font-size:14px;")
        l.addWidget(lb)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(b)
        self.ml.insertLayout(self.ml.count()-1, row)

    def _add_agent(self, text):
        b = QFrame(); b.setObjectName("agentBubble"); b.setMaximumWidth(600)
        l = QVBoxLayout(b); l.setContentsMargins(14,10,14,10)
        lb = QLabel(text); lb.setWordWrap(True); lb.setStyleSheet("color:#E6EDF3;font-size:14px;")
        l.addWidget(lb)
        row = QHBoxLayout(); row.addWidget(b); row.addStretch()
        self.ml.insertLayout(self.ml.count()-1, row)

    def refresh(self): pass
