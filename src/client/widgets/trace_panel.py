"""Agent Trace Panel"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit
)
from PySide6.QtCore import Qt


class TracePanel(QWidget):
    def __init__(self):
        super().__init__()
        L = QVBoxLayout(self)
        L.setSpacing(12)
        L.setContentsMargins(16, 16, 16, 16)
        t = QLabel("Agent执行轨迹追踪")
        t.setObjectName("sectionTitle")
        L.addWidget(t)
        h = QLabel("展示Agent每一步思考-行动-观察过程")
        h.setStyleSheet("color:#8B949E;font-size:12px;")
        L.addWidget(h)

        qbar = QHBoxLayout()
        qbar.addWidget(QLabel("会话ID:"))
        self.sid_input = QLineEdit()
        self.sid_input.setPlaceholderText("session_id")
        qbar.addWidget(self.sid_input, 1)
        btn = QPushButton("查询轨迹")
        btn.clicked.connect(self._load_trace)
        qbar.addWidget(btn)
        L.addLayout(qbar)

        sb = QHBoxLayout()
        self.lbl_steps = QLabel("步骤: 0")
        self.lbl_dur = QLabel("耗时: 0ms")
        self.lbl_tok = QLabel("Token: 0")
        for lb in [self.lbl_steps, self.lbl_dur, self.lbl_tok]:
            lb.setStyleSheet("color:#8B949E;font-size:13px;padding:4px 16px;")
            sb.addWidget(lb)
        sb.addStretch()
        L.addLayout(sb)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setStyleSheet("QScrollArea{border:none;}")
        mw = QWidget()
        self.tl = QVBoxLayout(mw)
        self.tl.setSpacing(8)
        self.tl.addStretch()
        sc.setWidget(mw)
        L.addWidget(sc, 1)

    def _load_trace(self):
        sid = self.sid_input.text().strip()
        if not sid:
            return
        try:
            from src.client.services.http_client import api_client
            data = api_client.get_trace(sid)
            if "error" in data:
                self._show_empty(data["error"])
                return
            self._display(data)
        except Exception as e:
            self._show_empty("failed: " + str(e))

    def set_trace(self, trace):
        self._display(trace)

    def _display(self, trace):
        self._clear()
        steps = trace.get("steps", [])
        self.lbl_steps.setText("步骤: " + str(len(steps)))
        self.lbl_dur.setText("耗时: " + str(trace.get("total_duration_ms", 0)) + "ms")
        self.lbl_tok.setText("Token: " + str(trace.get("total_token_usage", 0)))
        for s in steps:
            self._add_card(s)

    def _add_card(self, s):
        b = QFrame()
        b.setObjectName("cardFrame")
        l = QVBoxLayout(b)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(4)
        ph = s.get("phase", "")
        pc = "#8B949E"
        if ph == "routing":
            pc = "#3B82F6"
        elif ph == "action":
            pc = "#22C55E"
        elif ph == "observation":
            pc = "#F59E0B"
        elif ph == "answer":
            pc = "#2563EB"
        hdr = QHBoxLayout()
        si = QLabel("Step " + str(s.get("step", 0)))
        si.setStyleSheet("color:" + pc + ";font-weight:600;font-size:14px;")
        ag = QLabel(s.get("agent", ""))
        ag.setStyleSheet("color:#E6EDF3;font-size:12px;")
        pl = QLabel("[" + ph + "]")
        pl.setStyleSheet("color:" + pc + ";font-size:12px;font-weight:600;")
        d = QLabel(str(s.get("duration_ms", 0)) + "ms")
        d.setStyleSheet("color:#8B949E;font-size:11px;")
        hdr.addWidget(si)
        hdr.addWidget(ag)
        hdr.addWidget(pl)
        hdr.addStretch()
        hdr.addWidget(d)
        l.addLayout(hdr)
        for key, label, color in [("thought", "思考", "#8B949E"), ("action", "行动", "#E6EDF3"), ("observation", "观察", "#8B949E")]:
            v = s.get(key)
            if v:
                lb = QLabel(label + ": " + str(v))
                lb.setWordWrap(True)
                lb.setStyleSheet("color:" + color + ";font-size:12px;")
                l.addWidget(lb)
        self.tl.insertWidget(self.tl.count() - 1, b)

    def _clear(self):
        while self.tl.count() > 1:
            it = self.tl.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def _show_empty(self, msg):
        self._clear()
        lb = QLabel(msg)
        lb.setStyleSheet("color:#EF4444;font-size:14px;padding:20px;")
        self.tl.insertWidget(0, lb)

    def refresh(self):
        pass
