import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from src.client.widgets.main_window import MainWindow


def load_stylesheet(app):
    qss_path = Path(__file__).parent / "styles" / "theme.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WeldingAgentPlatform")
    app.setFont(QFont("Microsoft YaHei", 10))
    load_stylesheet(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
