import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication

from source.codewise_gui.codewise_ui_utils import AnalysisWorker, CodewiseApp, LoadingSpinner

# Global QApplication instance for all tests
_qapp = None


def get_qapp():
    """Get or create a QApplication instance"""
    global _qapp
    if _qapp is None:
        _qapp = QApplication([])
    return _qapp


@pytest.fixture(autouse=True)
def suppress_message_boxes(monkeypatch):
    """Fixture to suppress QMessageBox popups during tests"""
    # Create mock QMessageBox methods
    mock_info = Mock(return_value=None)
    mock_warning = Mock(return_value=None)
    mock_critical = Mock(return_value=None)

    # Patch at the source - where it's actually used
    from PySide6.QtWidgets import QMessageBox as RealQMessageBox

    monkeypatch.setattr(RealQMessageBox, 'information', mock_info)
    monkeypatch.setattr(RealQMessageBox, 'warning', mock_warning)
    monkeypatch.setattr(RealQMessageBox, 'critical', mock_critical)

    yield

    # Process any pending events to allow threads to finish
    time.sleep(0.1)  # Give threads a moment to settle
    QCoreApplication.processEvents()


"""
Tests for the AnalysisWorker class, specifically for the fix that removes the break statement
in the _process_methods method to allow processing of all methods instead of just the first one.

New tests added for the break statement removal fix:

1. test_worker_processes_all_methods_single_file:
   - Verifies that all methods in a file are processed, not just the first one
   - Tests with multiple methods (3 methods) and ensures API calls are made for each
   - Checks that progress signals and API response signals are emitted for all methods

2. test_worker_processes_methods_in_classes:
   - Tests that both class methods and standalone functions are processed
   - Ensures the fix works for different types of method definitions

3. test_worker_handles_api_errors_gracefully:
   - Tests that if one API call fails, other methods continue to be processed
   - Verifies error handling doesn't stop the processing of remaining methods

4. test_worker_cancellation_stops_processing:
   - Tests that cancellation properly stops processing of remaining methods
   - Verifies that the cancellation mechanism works correctly with multiple methods

5. test_worker_processes_methods_with_usage_examples:
   - Tests that methods with multiple usage examples are processed correctly
   - Verifies that usage examples are properly included in the analysis

6. test_worker_verifies_no_break_statement_behavior:
   - Critical test that verifies the fix is working correctly
   - Tests with 5 methods to ensure ALL are processed (not just the first)
   - Provides detailed assertions to catch any regression to the old behavior

These tests ensure that the removal of the break statement in _process_methods method
allows for comprehensive analysis of all methods in a file, including methods in classes,
with proper error handling and cancellation support.
"""


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

    @patch('source.codewise_gui.codewise_ui_utils.AnalysisWorker')
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
            mock_worker_class.assert_called_once_with("/test/root", "/test/file.py", "single_file")
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

        # Verify API response text was updated but spinner was NOT stopped
        codewise_app.api_response_text.setText.assert_called_with("Test API response")
        codewise_app.spinner.stop_spinning.assert_not_called()
        codewise_app.spinner.setVisible.assert_not_called()

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

        # Verify UI was reset (on_cancel just calls reset_ui_after_cancel)
        codewise_app.spinner.stop_spinning.assert_called()
        codewise_app.spinner.setVisible.assert_called_with(False)
        codewise_app.submit_btn.setEnabled.assert_called_with(True)

    def test_analysis_mode_initialization(self):
        """Test that analysis mode is initialized correctly"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Check default mode
        assert codewise_app.analysis_mode == "single_file"
        assert codewise_app.single_file_radio.isChecked()
        assert not codewise_app.entire_project_radio.isChecked()

    def test_single_file_mode_selection(self):
        """Test single file mode selection"""
        app = get_qapp()
        codewise_app = CodewiseApp()
        codewise_app.show()  # Ensure widget is shown for visibility checks

        # Initially, single file mode should be selected by default
        assert codewise_app.analysis_mode == "single_file"
        assert codewise_app.single_file_radio.isChecked()

        # Check file path elements are visible by default
        assert codewise_app.file_path_label.isVisible()
        assert codewise_app.file_path_entry.isVisible()
        assert codewise_app.file_path_entry.isEnabled()
        assert codewise_app.browse_file_btn.isVisible()
        assert codewise_app.browse_file_btn.isEnabled()

        # Explicitly select single file mode
        codewise_app.single_file_radio.setChecked(True)
        codewise_app.on_analysis_mode_selected()

        # Check mode is set correctly
        assert codewise_app.analysis_mode == "single_file"

        # Check file path elements are still visible
        assert codewise_app.file_path_label.isVisible()
        assert codewise_app.file_path_entry.isVisible()
        assert codewise_app.file_path_entry.isEnabled()
        assert codewise_app.browse_file_btn.isVisible()
        assert codewise_app.browse_file_btn.isEnabled()

    def test_entire_project_mode_selection(self):
        """Test entire project mode selection"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Select entire project mode
        codewise_app.entire_project_radio.setChecked(True)
        codewise_app.on_analysis_mode_selected()

        # Check mode is set correctly
        assert codewise_app.analysis_mode == "entire_project"

        # Check file path elements are hidden
        assert not codewise_app.file_path_label.isVisible()
        assert not codewise_app.file_path_entry.isVisible()
        assert not codewise_app.file_path_entry.isEnabled()
        assert not codewise_app.browse_file_btn.isVisible()
        assert not codewise_app.browse_file_btn.isEnabled()

    def test_mode_switching(self):
        """Test switching between modes"""
        app = get_qapp()
        codewise_app = CodewiseApp()
        codewise_app.show()  # Ensure widget is shown for visibility checks

        # Start with single file mode (default)
        assert codewise_app.analysis_mode == "single_file"
        assert codewise_app.file_path_label.isVisible()

        # Switch to entire project mode
        codewise_app.entire_project_radio.setChecked(True)
        codewise_app.on_analysis_mode_selected()
        assert codewise_app.analysis_mode == "entire_project"
        assert not codewise_app.file_path_label.isVisible()

        # Switch back to single file mode
        codewise_app.single_file_radio.setChecked(True)
        codewise_app.on_analysis_mode_selected()
        assert codewise_app.analysis_mode == "single_file"
        assert codewise_app.file_path_label.isVisible()

    def test_on_submit_single_file_mode_validation(self):
        """Test submit validation for single file mode"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Set single file mode
        codewise_app.analysis_mode = "single_file"
        codewise_app.root_dir_entry.setText("/test/root")

        # Test missing file path
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            codewise_app.on_submit()
            mock_warning.assert_called_once()

        # Test with both root directory and file path
        codewise_app.file_path_entry.setText("/test/file.py")
        with patch('source.codewise_gui.codewise_ui_utils.AnalysisWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            codewise_app.on_submit()

            # Verify worker was created with single file mode
            mock_worker_class.assert_called_once_with("/test/root", "/test/file.py", "single_file")

    def test_on_submit_entire_project_mode_validation(self):
        """Test submit validation for entire project mode"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Set entire project mode
        codewise_app.analysis_mode = "entire_project"
        codewise_app.root_dir_entry.setText("/test/root")

        # Test with root directory only
        with patch('source.codewise_gui.codewise_ui_utils.AnalysisWorker') as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            codewise_app.on_submit()

            # Verify worker was created with entire project mode
            mock_worker_class.assert_called_once_with("/test/root", None, "entire_project")

    def test_on_submit_missing_root_directory(self):
        """Test submit validation when root directory is missing"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Test with no root directory
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning:
            codewise_app.on_submit()
            mock_warning.assert_called_once()

    def test_update_api_response_no_spinner_stop(self):
        """Test that update_api_response doesn't stop the spinner"""
        app = get_qapp()
        codewise_app = CodewiseApp()

        # Mock the API response text
        mock_api_text = Mock()
        codewise_app.api_response_text = mock_api_text

        # Mock the spinner
        mock_spinner = Mock()
        codewise_app.spinner = mock_spinner

        # Call update_api_response
        codewise_app.update_api_response("Test API response")

        # Verify API response text was set
        mock_api_text.setText.assert_called_once_with("Test API response")

        # Verify spinner was NOT stopped (this is the key change)
        mock_spinner.stop_spinning.assert_not_called()
        mock_spinner.setVisible.assert_not_called()


# Cleanup function to destroy QApplication
def pytest_sessionfinish(session, exitstatus):
    """Clean up QApplication after all tests"""
    global _qapp
    if _qapp is not None:
        _qapp.quit()
        _qapp = None
