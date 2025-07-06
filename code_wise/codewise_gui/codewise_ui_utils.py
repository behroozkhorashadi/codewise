from PySide6.QtCore import Qt, QThread, QThreadPool, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from code_wise.llm.code_eval_prompt import generate_code_evaluation_prompt
from code_wise.llm.llm_integration import get_method_ratings
from code_wise.logic.code_ast_parser import collect_method_usages, get_method_body


class AnalysisWorker(QThread):
    """Worker thread for performing code analysis"""

    progress = Signal(str)
    api_response = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, root_directory, file_path):
        super().__init__()
        self.root_directory = root_directory
        self.file_path = file_path

    def run(self):
        try:
            self.progress.emit("Analyzing file...")
            result = collect_method_usages(self.root_directory, self.file_path)

            self.progress.emit(f"Found {len(result)} methods with usages")

            if not result:
                self.finished.emit(
                    "No methods with usages found. This could mean:\n1. The file doesn't contain any function definitions\n2. The functions in the file are not called anywhere in the codebase\n3. There's an issue with the AST parsing"
                )
                return

            function_def = ""
            openai_prompt = ""
            usage_examples = ""

            for method_pointer, call_site_infos in result.items():
                self.progress.emit(f"Processing method: {method_pointer.method_id.method_name}")
                self.progress.emit(f"Found {len(call_site_infos)} usage examples")

                function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)
                self.progress.emit(f"Function definition length: {len(function_def)} characters")

                for call_site_info in call_site_infos:
                    usage_examples += f"{get_method_body(call_site_info.function_node, call_site_info.file_path)}\n"

                self.progress.emit(f"Usage examples length: {len(usage_examples)} characters")

                openai_prompt = generate_code_evaluation_prompt(function_def, usage_examples)
                self.progress.emit(f"Generated prompt length: {len(openai_prompt)} characters")

                self.progress.emit("Calling LLM API...")
                api_response = get_method_ratings(openai_prompt)
                self.api_response.emit(api_response)

                # Only process the first method for now
                break

            self.finished.emit("Analysis completed successfully!")

        except Exception as e:
            self.error.emit(f"Error occurred: {str(e)}")


class CodewiseApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Codewise")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f8f9fa;
                color: #212529;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 12px;
            }
            QLabel {
                color: #495057;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 4px;
            }
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
                background-color: #e9ecef;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """
        )

        self.root_dir_entry = QLineEdit()
        self.file_path_entry = QLineEdit()
        self.output_text = QTextEdit()
        self.submit_btn = None  # Will be set in init_ui
        self.progress_label = None  # Will be set in init_ui
        self.progress_bar = None  # Will be set in init_ui
        self.api_call_indicator = None  # Will be set in init_ui
        self.worker = None  # Keep reference to worker

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Input section
        input_layout = QVBoxLayout()

        # Root Directory
        input_layout.addWidget(self._styled_label("Root Directory:"))
        root_layout = QHBoxLayout()
        root_layout.addWidget(self.root_dir_entry)
        browse_root_btn = QPushButton("Browse")
        browse_root_btn.clicked.connect(self.select_root_directory)
        root_layout.addWidget(browse_root_btn)
        input_layout.addLayout(root_layout)

        # File Path
        input_layout.addWidget(self._styled_label("File Path:"))
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_entry)
        browse_file_btn = QPushButton("Browse")
        browse_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(browse_file_btn)
        input_layout.addLayout(file_layout)

        # Submit button
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setFixedHeight(40)
        self.submit_btn.clicked.connect(self.on_submit)
        self.submit_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """
        )
        self.submit_btn.setEnabled(True)
        input_layout.addWidget(self.submit_btn)

        # Progress label
        self.progress_label = QLabel("Status: Idle")
        input_layout.addWidget(self.progress_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        input_layout.addWidget(self.progress_bar)

        # API call indicator
        self.api_call_indicator = QLabel("API Call: Idle")
        input_layout.addWidget(self.api_call_indicator)

        # Add input section to main layout
        main_layout.addLayout(input_layout)

        # Create splitter for the text areas
        splitter = QSplitter()

        # Debug/Progress section
        debug_widget = QWidget()
        debug_layout = QVBoxLayout(debug_widget)
        debug_layout.addWidget(self._styled_label("Analysis Progress:"))

        # Make output text area scrollable
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        debug_layout.addWidget(self.output_text)

        splitter.addWidget(debug_widget)

        # API Response section
        response_widget = QWidget()
        response_layout = QVBoxLayout(response_widget)
        response_layout.addWidget(self._styled_label("API Response:"))

        # Create a separate text area for API response
        self.api_response_text = QTextEdit()
        self.api_response_text.setReadOnly(True)
        self.api_response_text.setMinimumHeight(200)
        response_layout.addWidget(self.api_response_text)

        splitter.addWidget(response_widget)

        # Set initial splitter proportions (60% debug, 40% response)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter, stretch=1)
        self.setLayout(main_layout)

    def _styled_label(self, text):
        label = QLabel(text)
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
        if self.submit_btn:
            self.submit_btn.setEnabled(False)

        # Reset progress indicators
        if self.progress_bar:
            self.progress_bar.setValue(0)
        if self.api_call_indicator:
            self.api_call_indicator.setText("API Call: Idle")
            self.api_call_indicator.setStyleSheet("")

        try:
            # Add debug output
            self.output_text.append(f"Analyzing file: {file_path}\n")
            self.output_text.append(f"Root directory: {root_directory}\n")

            self.worker = AnalysisWorker(root_directory, file_path)
            self.worker.progress.connect(self.update_progress)
            self.worker.api_response.connect(self.update_api_response)
            self.worker.finished.connect(self.on_analysis_finished)
            self.worker.error.connect(self.on_analysis_error)
            self.worker.start()
        except Exception as e:
            self.output_text.append(f"Error occurred: {str(e)}\n")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            if self.submit_btn:
                self.submit_btn.setEnabled(True)

    def update_progress(self, message):
        self.output_text.append(message + "\n")
        if self.progress_label:
            self.progress_label.setText(f"Status: {message}")

        # Update progress bar based on the message
        if self.progress_bar:
            if "Analyzing file" in message:
                self.progress_bar.setValue(10)
            elif "Found" in message and "methods" in message:
                self.progress_bar.setValue(30)
            elif "Processing method" in message:
                self.progress_bar.setValue(50)
            elif "Generated prompt" in message:
                self.progress_bar.setValue(70)
            elif "Calling LLM API" in message:
                self.progress_bar.setValue(80)
                if self.api_call_indicator:
                    self.api_call_indicator.setText("API Call: In Progress...")
                    self.api_call_indicator.setStyleSheet("color: #007bff; font-weight: bold;")

    def update_api_response(self, api_response):
        self.api_response_text.setText(api_response)
        if self.progress_bar:
            self.progress_bar.setValue(100)
        if self.api_call_indicator:
            self.api_call_indicator.setText("API Call: Completed")
            self.api_call_indicator.setStyleSheet("color: #28a745; font-weight: bold;")

    def on_analysis_finished(self, message):
        self.output_text.append(message + "\n")
        if self.progress_bar:
            self.progress_bar.setValue(100)
        if self.api_call_indicator:
            self.api_call_indicator.setText("API Call: Completed")
            self.api_call_indicator.setStyleSheet("color: #28a745; font-weight: bold;")
        QMessageBox.information(self, "Success", "Process completed successfully!")
        if self.submit_btn:
            self.submit_btn.setEnabled(True)

    def on_analysis_error(self, error_message):
        self.output_text.append(f"Error: {error_message}\n")
        if self.progress_bar:
            self.progress_bar.setValue(0)
        if self.api_call_indicator:
            self.api_call_indicator.setText("API Call: Failed")
            self.api_call_indicator.setStyleSheet("color: #dc3545; font-weight: bold;")
        QMessageBox.critical(self, "Error", error_message)
        if self.submit_btn:
            self.submit_btn.setEnabled(True)
