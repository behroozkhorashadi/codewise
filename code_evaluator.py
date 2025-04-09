from code_wise.codewise_gui.codewise_ui_utils import CodewiseApp
from PySide6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    codewise_app = CodewiseApp()
    codewise_app.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
