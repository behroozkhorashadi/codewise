import math
import os
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional

from PySide6.QtCore import Qt, QThread, QThreadPool, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from code_wise.llm.code_eval_prompt import generate_code_evaluation_prompt
from code_wise.llm.llm_integration import get_method_ratings
from code_wise.logic.code_ast_parser import collect_method_usages, get_method_body


class CancellableAPICall:
    """A cancellable API call that runs in a separate thread."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._current_future: Optional[Future] = None
        self._cancelled = False
        self._lock = threading.Lock()

    def call_api(self, prompt: str, model: str = "gpt-4") -> str:
        """
        Make a cancellable API call.

        Args:
            prompt: The prompt to send to the API
            model: The model to use

        Returns:
            The API response or error message

        Raises:
            CancelledError: If the call was cancelled
        """
        with self._lock:
            if self._cancelled:
                raise CancelledError("API call was cancelled")

            # Submit the API call to the thread pool
            self._current_future = self._executor.submit(get_method_ratings, prompt, model)

        try:
            # Wait for the result, checking for cancellation periodically
            while not self._current_future.done():
                with self._lock:
                    if self._cancelled:
                        self._current_future.cancel()
                        raise CancelledError("API call was cancelled")
                time.sleep(0.1)  # Check every 100ms

            # Get the result
            result = self._current_future.result()
            with self._lock:
                if self._cancelled:
                    raise CancelledError("API call was cancelled")
                return result

        except Exception as e:
            with self._lock:
                if self._cancelled:
                    raise CancelledError("API call was cancelled")
                raise e
        finally:
            with self._lock:
                self._current_future = None

    def cancel(self):
        """Cancel the current API call if one is in progress."""
        with self._lock:
            self._cancelled = True
            if self._current_future and not self._current_future.done():
                self._current_future.cancel()

    def reset(self):
        """Reset the cancellation state for the next call."""
        with self._lock:
            self._cancelled = False
            self._current_future = None

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=False)


class CancelledError(Exception):
    """Exception raised when an API call is cancelled."""

    pass


class LoadingSpinner(QWidget):
    """A simple loading spinner widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(60, 60)

    def start_spinning(self):
        """Start the spinner animation"""
        self.timer.start(50)  # Update every 50ms

    def stop_spinning(self):
        """Stop the spinner animation"""
        self.timer.stop()

    def rotate(self):
        """Rotate the spinner"""
        self.angle = (self.angle + 30) % 360
        self.update()

    def paintEvent(self, event):
        """Paint the spinner"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set up the pen and brush
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#007bff"))

        # Calculate center and radius
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 2 - 5

        # Draw 8 dots in a circle
        for i in range(8):
            angle_rad = (self.angle + (i * 45)) * 3.14159 / 180
            x = center_x + radius * 0.7 * math.cos(angle_rad)
            y = center_y + radius * 0.7 * math.sin(angle_rad)

            # Make dots fade based on position
            alpha = 255 - (i * 30) % 255
            painter.setBrush(QColor(0, 123, 255, alpha))

            painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)


def collect_method_usages_entire_project(root_directory):
    """Collect method usages from all Python files in the entire project."""
    all_methods = {}

    # Walk through all Python files in the project
    for root, dirs, files in os.walk(root_directory):
        # Skip common directories that shouldn't be analyzed
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']]

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    # Collect methods from this file
                    file_methods = collect_method_usages(root_directory, file_path)

                    # Add to overall results
                    for method_pointer, call_site_infos in file_methods.items():
                        # Create a unique key for the method
                        method_key = f"{method_pointer.file_path}:{method_pointer.method_id.method_name}"
                        if method_key not in all_methods:
                            all_methods[method_key] = (method_pointer, call_site_infos)
                        else:
                            # Merge call site infos if method exists in multiple files
                            existing_pointer, existing_infos = all_methods[method_key]
                            all_methods[method_key] = (existing_pointer, existing_infos + call_site_infos)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue

    return all_methods


class AnalysisWorker(QThread):
    """Worker thread for performing code analysis"""

    progress = Signal(str)
    api_response = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, root_directory, file_path=None, analysis_mode="single_file"):
        super().__init__()
        self.root_directory = root_directory
        self.file_path = file_path
        self.analysis_mode = analysis_mode
        self._is_cancelled = False
        self._api_call = CancellableAPICall()

    def cancel(self):
        """Cancel the analysis."""
        self._is_cancelled = True
        self._api_call.cancel()
        self.quit()
        self.wait()

    def run(self):
        try:
            if self._is_cancelled:
                return

            if self.analysis_mode == "single_file":
                self.progress.emit(f"Analyzing single file: {self.file_path}")
                result = collect_method_usages(self.root_directory, self.file_path)
                if result:
                    self._process_methods(result)
                else:
                    self.error.emit("No methods found in the specified file.")
            else:
                self.progress.emit(f"Analyzing entire project: {self.root_directory}")
                result = collect_method_usages_entire_project(self.root_directory)
                if result:
                    self._process_entire_project(result)
                else:
                    self.error.emit("No methods found in the project.")

            if not self._is_cancelled:
                self.finished.emit("Analysis completed successfully!")

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(f"Error during analysis: {str(e)}")
        finally:
            self._api_call.shutdown()

    def _process_methods(self, result):
        """Process methods for single file analysis."""
        all_results = []

        for method_pointer, call_site_infos in result.items():
            if self._is_cancelled:
                return

            method_name = method_pointer.method_id.method_name
            self.progress.emit(f"Processing method: {method_name}")
            self.progress.emit(f"Found {len(call_site_infos)} usage examples")

            # Get method content and usage examples
            function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)
            usage_examples = []
            for call_site_info in call_site_infos:
                usage_content = get_method_body(call_site_info.function_node, call_site_info.file_path)
                usage_examples.append(usage_content)

            # Generate prompt and call API
            usage_examples_text = "\n\n".join(usage_examples) if usage_examples else ""
            prompt = generate_code_evaluation_prompt(function_def, usage_examples_text)
            self.progress.emit(f"Generated prompt for {method_name}")
            self.progress.emit("Calling LLM API...")

            try:
                # Reset API call state for this method
                self._api_call.reset()

                # Make the cancellable API call
                api_response = self._api_call.call_api(prompt)

                if self._is_cancelled:
                    return

                self.progress.emit(f"API call completed for {method_name}")

                all_results.append({"method_name": method_name, "api_response": api_response})

                # Emit individual API response for popup
                self.api_response.emit(f"Analysis for method: {method_name}\n\n{api_response}")

            except CancelledError:
                self.progress.emit(f"API call cancelled for {method_name}")
                return
            except Exception as e:
                self.progress.emit(f"Error calling API for {method_name}: {str(e)}")

        self.progress.emit(f"Processed {len(all_results)} methods")

    def _process_entire_project(self, result):
        """Process methods for entire project analysis."""
        total_methods = len(result)
        processed_methods = 0
        all_results = []

        self.progress.emit(f"Processing {total_methods} methods from entire project...")

        # Group methods by file for better organization
        methods_by_file = {}
        for method_key, (method_pointer, call_site_infos) in result.items():
            file_path = method_pointer.file_path
            if file_path not in methods_by_file:
                methods_by_file[file_path] = []
            methods_by_file[file_path].append((method_pointer, call_site_infos))

        self.progress.emit(f"Found methods in {len(methods_by_file)} files")

        for file_path, methods in methods_by_file.items():
            if self._is_cancelled:
                return

            self.progress.emit(f"Processing file: {file_path}")

            for method_pointer, call_site_infos in methods:
                if self._is_cancelled:
                    return

                method_name = method_pointer.method_id.method_name
                self.progress.emit(f"Processing method: {method_name}")

                # Get method content and usage examples
                function_def = get_method_body(method_pointer.function_node, method_pointer.file_path)
                usage_examples = []
                for call_site_info in call_site_infos:
                    usage_content = get_method_body(call_site_info.function_node, call_site_info.file_path)
                    usage_examples.append(usage_content)

                # Generate prompt and call API
                usage_examples_text = "\n\n".join(usage_examples) if usage_examples else ""
                prompt = generate_code_evaluation_prompt(function_def, usage_examples_text)
                self.progress.emit(f"Generated prompt for {method_name}")
                self.progress.emit("Calling LLM API...")

                try:
                    # Reset API call state for this method
                    self._api_call.reset()

                    # Make the cancellable API call
                    api_response = self._api_call.call_api(prompt)

                    if self._is_cancelled:
                        return

                    self.progress.emit(f"API call completed for {method_name}")

                    all_results.append(
                        {
                            "method_name": method_name,
                            "file_path": method_pointer.file_path,
                            "api_response": api_response,
                        }
                    )
                    processed_methods += 1

                    # Emit individual API response for popup
                    self.api_response.emit(f"Analysis for method: {method_name}\n\n{api_response}")

                except CancelledError:
                    self.progress.emit(f"API call cancelled for {method_name}")
                    return
                except Exception as e:
                    self.progress.emit(f"Error calling API for {method_name}: {str(e)}")

                # Update progress
                progress_percent = (processed_methods / total_methods) * 100
                self.progress.emit(f"Progress: {processed_methods}/{total_methods} methods ({progress_percent:.1f}%)")

        self.progress.emit(f"Total analysis completed. Processed {len(all_results)} methods.")


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
            QRadioButton {
                color: #495057;
                font-weight: 500;
                font-size: 14px;
                margin: 4px 0;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
        """
        )

        self.root_dir_entry = QLineEdit()
        self.file_path_entry = QLineEdit()
        self.output_text = QTextEdit()
        self.submit_btn = None  # Will be set in init_ui
        self.progress_label = None  # Will be set in init_ui
        self.spinner = None  # Will be set in init_ui
        self.worker = None  # Keep reference to worker
        self.analysis_mode = "single_file"  # Default mode

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Input section
        input_layout = QVBoxLayout()

        # Analysis Mode Selection
        input_layout.addWidget(self._styled_label("Analysis Mode:"))
        mode_layout = QHBoxLayout()

        self.single_file_radio = QRadioButton("Single File Mode")
        self.single_file_radio.setChecked(True)
        self.single_file_radio.toggled.connect(self.on_analysis_mode_selected)

        self.entire_project_radio = QRadioButton("Entire Project Mode")
        self.entire_project_radio.toggled.connect(self.on_analysis_mode_selected)

        mode_layout.addWidget(self.single_file_radio)
        mode_layout.addWidget(self.entire_project_radio)
        mode_layout.addStretch()

        input_layout.addLayout(mode_layout)

        # Root Directory
        input_layout.addWidget(self._styled_label("Root Directory:"))
        root_layout = QHBoxLayout()
        root_layout.addWidget(self.root_dir_entry)
        browse_root_btn = QPushButton("Browse")
        browse_root_btn.clicked.connect(self.select_root_directory)
        root_layout.addWidget(browse_root_btn)
        input_layout.addLayout(root_layout)

        # File Path (initially visible for single file mode)
        self.file_path_label = self._styled_label("File Path:")
        input_layout.addWidget(self.file_path_label)
        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_entry)
        self.browse_file_btn = QPushButton("Browse")
        self.browse_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.browse_file_btn)
        input_layout.addLayout(file_layout)

        # Submit button
        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setFixedHeight(40)
        self.submit_btn.clicked.connect(self.on_submit)
        self.submit_btn.setStyleSheet(
            """
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
        """
        )
        self.submit_btn.setEnabled(True)

        # Cancel button (initially hidden)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b52a37;
            }
            QPushButton:pressed {
                background-color: #8a1c28;
            }
            QPushButton:disabled {
                background-color: #e2aeb1;
                color: #fff0f1;
            }
        """
        )
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.cancel_btn)
        input_layout.addLayout(btn_layout)

        # Progress label
        self.progress_label = QLabel("Status: Idle")
        input_layout.addWidget(self.progress_label)

        # Add input section to main layout
        main_layout.addLayout(input_layout)

        # Centered loading spinner
        self.spinner = LoadingSpinner(self)
        self.spinner.setFixedSize(60, 60)
        self.spinner.setVisible(False)
        spinner_layout = QHBoxLayout()
        spinner_layout.addStretch()
        spinner_layout.addWidget(self.spinner)
        spinner_layout.addStretch()
        main_layout.addLayout(spinner_layout)

        # Create splitter for the text areas
        splitter = QSplitter(Qt.Horizontal)

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

        # Set initial splitter proportions (40% debug, 60% response)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter, stretch=1)
        self.setLayout(main_layout)

        # Initialize the mode selection to ensure proper visibility
        self.on_analysis_mode_selected()

    def on_analysis_mode_selected(self):
        """Handle analysis mode selection"""
        if self.single_file_radio.isChecked():
            self.analysis_mode = "single_file"
            self.file_path_label.setVisible(True)
            self.file_path_entry.setVisible(True)
            self.file_path_entry.setEnabled(True)
            self.browse_file_btn.setVisible(True)
            self.browse_file_btn.setEnabled(True)
        else:
            self.analysis_mode = "entire_project"
            self.file_path_label.setVisible(False)
            self.file_path_entry.setVisible(False)
            self.file_path_entry.setEnabled(False)
            self.browse_file_btn.setVisible(False)
            self.browse_file_btn.setEnabled(False)

    def _styled_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; margin-bottom: 4px;")
        return label

    def select_root_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Root Directory")
        if directory:
            self.root_dir_entry.setText(directory)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Python Files (*.py)")
        if file_path:
            self.file_path_entry.setText(file_path)

    def on_submit(self):
        root_directory = self.root_dir_entry.text()

        if not root_directory:
            QMessageBox.warning(self, "Warning", "Please provide a root directory.")
            return

        if self.analysis_mode == "single_file":
            file_path = self.file_path_entry.text()
            if not file_path:
                QMessageBox.warning(self, "Warning", "Please provide a file path for single file mode.")
                return
        else:
            file_path = None

        # Reset cancellation state
        self._cancelled = False

        # Update UI for analysis start
        if self.submit_btn:
            self.submit_btn.setEnabled(False)
        if self.cancel_btn:
            self.cancel_btn.setVisible(True)
            self.cancel_btn.setEnabled(True)
        if self.progress_label:
            self.progress_label.setText("Status: Starting...")

        # Show spinner and update status
        self.spinner.setVisible(True)
        self.spinner.start_spinning()

        try:
            # Add debug output
            if self.analysis_mode == "single_file":
                self.output_text.append(f"Analyzing file: {file_path}\n")
            else:
                self.output_text.append(f"Analyzing entire project: {root_directory}\n")
            self.output_text.append(f"Root directory: {root_directory}\n")

            # Start the actual analysis with API calls
            self.worker = AnalysisWorker(root_directory, file_path, self.analysis_mode)
            self.worker.progress.connect(self.update_progress)
            self.worker.api_response.connect(self.update_api_response)
            self.worker.finished.connect(self.on_analysis_finished)
            self.worker.error.connect(self.on_analysis_error)
            self.worker.start()

        except Exception as e:
            self.output_text.append(f"Error: {str(e)}\n")
            self.reset_ui_after_cancel()

    def update_progress(self, message):
        self.output_text.append(message + "\n")
        if self.progress_label:
            self.progress_label.setText(f"Status: {message}")

    def update_api_response(self, api_response):
        self.api_response_text.setText(api_response)
        # Don't stop the spinner here - let it continue for multiple API responses

    def on_analysis_finished(self, message):
        # Only process if not cancelled
        if hasattr(self, '_cancelled') and self._cancelled:
            return
        self.output_text.append(message + "\n")
        self.spinner.stop_spinning()
        self.spinner.setVisible(False)
        if self.cancel_btn:
            self.cancel_btn.setVisible(False)
            self.cancel_btn.setEnabled(True)
        if self.progress_label:
            self.progress_label.setText("Status: Completed")
        QMessageBox.information(self, "Success", "Process completed successfully!")
        if self.submit_btn:
            self.submit_btn.setEnabled(True)

    def on_analysis_error(self, error_message):
        # Only process if not cancelled
        if hasattr(self, '_cancelled') and self._cancelled:
            return
        self.output_text.append(f"Error: {error_message}\n")
        self.spinner.stop_spinning()
        self.spinner.setVisible(False)
        if self.cancel_btn:
            self.cancel_btn.setVisible(False)
            self.cancel_btn.setEnabled(True)
        if self.progress_label:
            self.progress_label.setText("Status: Error")
        QMessageBox.critical(self, "Error", error_message)
        if self.submit_btn:
            self.submit_btn.setEnabled(True)

    def on_cancel_clicked(self):
        # Prevent repeated/fast clicks
        if hasattr(self, '_cancelled') and self._cancelled:
            return
        self._cancelled = True

        # Immediately disable the cancel button and reset UI
        if self.cancel_btn:
            self.cancel_btn.setEnabled(False)

        # Reset UI immediately for responsive feel
        self.reset_ui_after_cancel()

        # Cancel the worker (this will also cancel any ongoing API calls)
        if self.worker:
            self.worker.cancel()

    def reset_ui_after_cancel(self):
        # Reset UI to initial state after cancellation
        self.spinner.stop_spinning()
        self.spinner.setVisible(False)
        if self.submit_btn:
            self.submit_btn.setEnabled(True)
        if self.cancel_btn:
            self.cancel_btn.setVisible(False)
            self.cancel_btn.setEnabled(True)
        if self.progress_label:
            self.progress_label.setText("Status: Cancelled")
        self.output_text.append("\nAnalysis cancelled by user.\n")
        self.api_response_text.clear()
        # Clear worker reference
        self.worker = None
        # Reset cancellation flag
        self._cancelled = False

    def on_cancel(self):
        # This method is not used for the button anymore, but keep for compatibility
        self.reset_ui_after_cancel()
