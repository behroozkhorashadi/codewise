from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication

from code_wise.codewise_gui.codewise_ui_utils import AnalysisWorker, CodewiseApp, LoadingSpinner

# Global QApplication instance for all tests
_qapp = None


def get_qapp():
    """Get or create a QApplication instance"""
    global _qapp
    if _qapp is None:
        _qapp = QApplication([])
    return _qapp


class TestLoadingSpinner:
    """Test the LoadingSpinner widget functionality"""

    def test_spinner_initialization(self):
        """Test that the spinner initializes correctly"""
        app = get_qapp()
        spinner = LoadingSpinner()

        assert spinner.angle == 0
        assert spinner.timer is not None
        assert spinner.width() == 60
        assert spinner.height() == 60
        assert not spinner.timer.isActive()

    def test_spinner_start_stop(self):
        """Test that the spinner starts and stops correctly"""
        app = get_qapp()
        spinner = LoadingSpinner()

        # Initially not spinning
        assert not spinner.timer.isActive()

        # Start spinning
        spinner.start_spinning()
        assert spinner.timer.isActive()
        assert spinner.timer.interval() == 50

        # Stop spinning
        spinner.stop_spinning()
        assert not spinner.timer.isActive()

    def test_spinner_rotation(self):
        """Test that the spinner rotates correctly"""
        app = get_qapp()
        spinner = LoadingSpinner()

        initial_angle = spinner.angle
        spinner.rotate()

        # Should rotate by 30 degrees
        assert spinner.angle == (initial_angle + 30) % 360

    def test_spinner_paint_event(self):
        """Test that the spinner can be painted without errors"""
        app = get_qapp()
        spinner = LoadingSpinner()

        # Mock the painter to avoid actual rendering
        with patch.object(QPainter, '__init__', return_value=None):
            with patch.object(QPainter, 'setRenderHint'):
                with patch.object(QPainter, 'setPen'):
                    with patch.object(QPainter, 'setBrush'):
                        with patch.object(QPainter, 'drawEllipse'):
                            # This should not raise any exceptions
                            spinner.paintEvent(None)


class TestAnalysisWorker:
    """Test the AnalysisWorker thread functionality"""

    def test_worker_initialization(self):
        """Test that the worker initializes correctly"""
        worker = AnalysisWorker("/test/root", "/test/file.py")

        assert worker.root_directory == "/test/root"
        assert worker.file_path == "/test/file.py"

    @patch('code_wise.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('code_wise.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_successful_analysis(self, mock_get_ratings, mock_collect_usages):
        """Test successful analysis workflow"""
        # Mock the method collection
        mock_method_pointer = Mock()
        mock_method_pointer.method_id.method_name = "test_method"
        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        mock_collect_usages.return_value = {mock_method_pointer: [mock_call_site_info]}

        # Mock the API call
        mock_get_ratings.return_value = "Test API response"

        # Mock get_method_body
        with patch('code_wise.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", "/test/file.py")

            # Mock signals
            progress_signal = Mock()
            api_response_signal = Mock()
            finished_signal = Mock()

            worker.progress.connect(progress_signal)
            worker.api_response.connect(api_response_signal)
            worker.finished.connect(finished_signal)

            # Run the worker
            worker.run()

            # Verify signals were emitted
            assert progress_signal.called
            assert api_response_signal.called
            assert finished_signal.called

    @patch('code_wise.codewise_gui.codewise_ui_utils.collect_method_usages')
    def test_worker_no_methods_found(self, mock_collect_usages):
        """Test worker behavior when no methods are found"""
        mock_collect_usages.return_value = {}

        worker = AnalysisWorker("/test/root", "/test/file.py")

        # Mock signals
        finished_signal = Mock()
        worker.finished.connect(finished_signal)

        # Run the worker
        worker.run()

        # Verify finished signal was emitted with appropriate message
        assert finished_signal.called
        call_args = finished_signal.call_args[0][0]
        assert "No methods with usages found" in call_args

    @patch('code_wise.codewise_gui.codewise_ui_utils.collect_method_usages')
    def test_worker_exception_handling(self, mock_collect_usages):
        """Test worker exception handling"""
        mock_collect_usages.side_effect = Exception("Test error")

        worker = AnalysisWorker("/test/root", "/test/file.py")

        # Mock signals
        error_signal = Mock()
        worker.error.connect(error_signal)

        # Run the worker
        worker.run()

        # Verify error signal was emitted
        assert error_signal.called
        call_args = error_signal.call_args[0][0]
        assert "Error occurred" in call_args


class TestCodewiseApp:
    """Test the main application logic"""

    def test_app_initialization(self):
        """Test that the app initializes correctly"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        assert codewise_app.worker is None
        assert codewise_app.spinner is not None
        assert codewise_app.progress_label is not None
        assert codewise_app.submit_btn is not None

    def test_styled_label_creation(self):
        """Test that styled labels are created correctly"""
        app = get_qapp()
        codewise_app = CodewiseApp()
        label = codewise_app._styled_label("Test Label")

        assert label.text() == "Test Label"
        assert "font-weight: 600" in label.styleSheet()

    @patch('PySide6.QtWidgets.QFileDialog.getExistingDirectory')
    def test_select_root_directory(self, mock_dialog):
        """Test root directory selection"""
        app = get_qapp()
        mock_dialog.return_value = "/test/directory"

        codewise_app = CodewiseApp()
        codewise_app.select_root_directory()

        assert codewise_app.root_dir_entry.text() == "/test/directory"

    @patch('PySide6.QtWidgets.QFileDialog.getOpenFileName')
    def test_select_file(self, mock_dialog):
        """Test file selection"""
        app = get_qapp()
        mock_dialog.return_value = ("/test/file.py", "")

        codewise_app = CodewiseApp()
        codewise_app.select_file()

        assert codewise_app.file_path_entry.text() == "/test/file.py"

    def test_on_submit_validation(self):
        """Test submit validation with empty fields"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock QMessageBox to avoid actual dialog
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            codewise_app.on_submit()

            # Should show warning for empty fields
            assert mock_warning.called

    @patch('code_wise.codewise_gui.codewise_ui_utils.AnalysisWorker')
    def test_on_submit_success(self, mock_worker_class):
        """Test successful submit workflow"""
        app = get_qapp()
        # Mock the worker
        mock_worker = Mock()
        mock_worker_class.return_value = mock_worker

        codewise_app = CodewiseApp()
        codewise_app.root_dir_entry.setText("/test/root")
        codewise_app.file_path_entry.setText("/test/file.py")

        # Mock QMessageBox to avoid actual dialog
        with patch('PySide6.QtWidgets.QMessageBox.warning', return_value=None):
            codewise_app.on_submit()

            # Verify worker was created and started
            mock_worker_class.assert_called_once_with("/test/root", "/test/file.py")
            assert mock_worker.start.called

    def test_update_progress(self):
        """Test progress update functionality"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock the output text widget
        codewise_app.output_text = Mock()
        codewise_app.progress_label = Mock()

        codewise_app.update_progress("Test message")

        # Verify both output text and progress label were updated
        codewise_app.output_text.append.assert_called_with("Test message\n")
        codewise_app.progress_label.setText.assert_called_with("Status: Test message")

    def test_update_api_response(self):
        """Test API response update functionality"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock the API response text widget and spinner
        codewise_app.api_response_text = Mock()
        codewise_app.spinner = Mock()

        codewise_app.update_api_response("Test API response")

        # Verify API response text was updated and spinner stopped
        codewise_app.api_response_text.setText.assert_called_with("Test API response")
        codewise_app.spinner.stop_spinning.assert_called()
        codewise_app.spinner.setVisible.assert_called_with(False)

    def test_on_analysis_finished(self):
        """Test analysis finished handling"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock components
        codewise_app.output_text = Mock()
        codewise_app.spinner = Mock()
        codewise_app.submit_btn = Mock()

        # Mock QMessageBox to avoid actual dialog
        with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
            codewise_app.on_analysis_finished("Test completion message")

            # Verify all components were updated correctly
            codewise_app.output_text.append.assert_called_with("Test completion message\n")
            codewise_app.spinner.stop_spinning.assert_called()
            codewise_app.spinner.setVisible.assert_called_with(False)
            codewise_app.submit_btn.setEnabled.assert_called_with(True)
            mock_info.assert_called()

    def test_on_analysis_error(self):
        """Test analysis error handling"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock components
        codewise_app.output_text = Mock()
        codewise_app.spinner = Mock()
        codewise_app.submit_btn = Mock()

        # Mock QMessageBox to avoid actual dialog
        with patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical:
            codewise_app.on_analysis_error("Test error message")

            # Verify all components were updated correctly
            codewise_app.output_text.append.assert_called_with("Error: Test error message\n")
            codewise_app.spinner.stop_spinning.assert_called()
            codewise_app.spinner.setVisible.assert_called_with(False)
            codewise_app.submit_btn.setEnabled.assert_called_with(True)
            mock_critical.assert_called()

    def test_on_cancel(self):
        """Test cancel functionality"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock worker and components
        codewise_app.worker = Mock()
        codewise_app.spinner = Mock()
        codewise_app.submit_btn = Mock()

        codewise_app.on_cancel()

        # Verify worker was stopped and UI was reset
        codewise_app.worker.quit.assert_called()
        codewise_app.worker.wait.assert_called()
        codewise_app.spinner.stop_spinning.assert_called()
        codewise_app.spinner.setVisible.assert_called_with(False)
        codewise_app.submit_btn.setEnabled.assert_called_with(True)


# Cleanup function to destroy QApplication
def pytest_sessionfinish(session, exitstatus):
    """Clean up QApplication after all tests"""
    global _qapp
    if _qapp is not None:
        _qapp.quit()
        _qapp = None
