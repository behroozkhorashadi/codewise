import sys

from PySide6.QtWidgets import QApplication

from source.codewise_gui.codewise_ui_utils import CodewiseApp


def main():
    app = QApplication(sys.argv)
    codewise_app = CodewiseApp()
    codewise_app.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
