from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from code_wise.llm.code_eval_prompt import generate_code_evaluation_prompt
from code_wise.llm.llm_integration import get_method_ratings
from code_wise.logic.code_ast_parser import collect_method_usages, get_method_body


class CodewiseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Codewise")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet("background-color: #2c3e50;")

        self.root_dir_entry = QLineEdit()
        self.file_path_entry = QLineEdit()
        self.output_text = QTextEdit()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Root Directory
        layout.addWidget(self._styled_label("Root Directory:"))
        root_layout = QHBoxLayout()
        root_layout.addWidget(self.root_dir_entry)
        browse_root_btn = QPushButton("Browse")
        browse_root_btn.clicked.connect(self.select_root_directory)
        root_layout.addWidget(browse_root_btn)
        layout.addLayout(root_layout)

        # File Path
        layout.addWidget(self._styled_label("File Path:"))
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_entry)
        browse_file_btn = QPushButton("Browse")
        browse_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(browse_file_btn)
        layout.addLayout(file_layout)

        # Submit button
        submit_btn = QPushButton("Submit")
        submit_btn.setFixedHeight(40)
        submit_btn.clicked.connect(self.on_submit)
        submit_btn.setStyleSheet("background-color: #e74c3c; font-weight: bold;")
        layout.addWidget(submit_btn)

        # Output label and text area
        layout.addWidget(self._styled_label("API Response:"))
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #ecf0f1;")
        layout.addWidget(self.output_text, stretch=1)

        self.setLayout(layout)

    def _styled_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("color: white; font-weight: bold;")
        return label

    def select_root_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Root Directory")
        if directory:
            self.root_dir_entry.setText(directory)

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file:
            self.file_path_entry.setText(file)

    def on_submit(self):
        root_directory = self.root_dir_entry.text()
        file_path = self.file_path_entry.text()

        if not root_directory or not file_path:
            QMessageBox.critical(self, "Input Error", "Both fields must be filled out!")
            return

        self.output_text.clear()

        try:
            result = collect_method_usages(root_directory, file_path)
            function_def = ""
            openai_prompt = ""
            usage_examples = ""

            for method_pointer, call_site_infos in result.items():
                function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)
                for call_site_info in call_site_infos:
                    usage_examples += f"{get_method_body(call_site_info.function_node, call_site_info.file_path)}\n"

                openai_prompt = generate_code_evaluation_prompt(function_def, usage_examples)
                api_response = get_method_ratings(openai_prompt)
                self.output_text.append(f"Response:\n{api_response}\n")
                break

            QMessageBox.information(self, "Success", "Process completed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
