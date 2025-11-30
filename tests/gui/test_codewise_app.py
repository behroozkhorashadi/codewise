"""
Unit tests for CodewiseApp (main application widget).

Tests focus on:
1. Initialization and component creation
2. UI element selection (file/directory dialogs)
3. Submission and validation logic
4. Analysis mode switching
5. Progress and response updates
6. Event handling (finished, errors, cancellation)
"""

from unittest.mock import Mock, patch

from source.codewise_gui.codewise_ui_utils import CodewiseApp

# Import the shared fixtures and helper from test_ui_utils
from .test_ui_utils import get_qapp, suppress_message_boxes  # noqa: F401


class TestCodewiseAppInitialization:
    """Test CodewiseApp initialization and component creation"""

    def test_app_initialization(self):
        """Test that the app initializes correctly"""
        get_qapp()
        codewise_app = CodewiseApp()

        assert codewise_app.worker is None
        assert codewise_app.spinner is not None
        assert codewise_app.progress_label is not None
        assert codewise_app.submit_btn is not None

    def test_styled_label_creation(self):
        """Test that styled labels are created correctly"""
        get_qapp()
        codewise_app = CodewiseApp()
        label = codewise_app._styled_label("Test Label")

        assert label.text() == "Test Label"
        assert "font-weight: 600" in label.styleSheet()

    def test_analysis_mode_initialization(self):
        """Test that analysis mode is initialized correctly"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Check default mode
        assert codewise_app.analysis_mode == "single_file"
        assert codewise_app.single_file_radio.isChecked()
        assert not codewise_app.entire_project_radio.isChecked()


class TestCodewiseAppFileSelection:
    """Test file and directory selection dialogs"""

    @patch("PySide6.QtWidgets.QFileDialog.getExistingDirectory")
    def test_select_root_directory(self, mock_dialog):
        """Test root directory selection"""
        get_qapp()
        mock_dialog.return_value = "/test/directory"

        codewise_app = CodewiseApp()
        codewise_app.select_root_directory()

        assert codewise_app.root_dir_entry.text() == "/test/directory"

    @patch("PySide6.QtWidgets.QFileDialog.getOpenFileName")
    def test_select_file(self, mock_dialog):
        """Test file selection"""
        get_qapp()
        mock_dialog.return_value = ("/test/file.py", "")

        codewise_app = CodewiseApp()
        codewise_app.select_file()

        assert codewise_app.file_path_entry.text() == "/test/file.py"


class TestCodewiseAppAnalysisMode:
    """Test analysis mode switching and UI state management"""

    def test_single_file_mode_selection(self):
        """Test single file mode selection"""
        get_qapp()
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
        get_qapp()
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
        get_qapp()
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


class TestCodewiseAppSubmission:
    """Test form submission and validation"""

    def test_on_submit_validation_empty_fields(self):
        """Test submit validation with empty fields"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Mock QMessageBox to avoid actual dialog
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning:
            codewise_app.on_submit()

            # Should show warning for empty fields
            assert mock_warning.called

    def test_on_submit_missing_root_directory(self):
        """Test submit validation when root directory is missing"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Test with no root directory
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning:
            codewise_app.on_submit()
            mock_warning.assert_called_once()

    def test_on_submit_success_single_file(self):
        """Test successful submit in single file mode"""
        get_qapp()

        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker") as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            codewise_app = CodewiseApp()
            codewise_app.analysis_mode = "single_file"
            codewise_app.root_dir_entry.setText("/test/root")
            codewise_app.file_path_entry.setText("/test/file.py")

            with patch("PySide6.QtWidgets.QMessageBox.warning", return_value=None):
                codewise_app.on_submit()

                # Verify worker was created and started
                mock_worker_class.assert_called_once_with("/test/root", "/test/file.py", "single_file")
                assert mock_worker.start.called

    def test_on_submit_single_file_mode_requires_file_path(self):
        """Test that single file mode requires both root and file path"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Set single file mode
        codewise_app.analysis_mode = "single_file"
        codewise_app.root_dir_entry.setText("/test/root")

        # Test missing file path
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warning:
            codewise_app.on_submit()
            mock_warning.assert_called_once()

    def test_on_submit_entire_project_mode(self):
        """Test submit in entire project mode"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Set entire project mode
        codewise_app.analysis_mode = "entire_project"
        codewise_app.root_dir_entry.setText("/test/root")

        # Test with root directory only
        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker") as mock_worker_class:
            mock_worker = Mock()
            mock_worker_class.return_value = mock_worker

            codewise_app.on_submit()

            # Verify worker was created with entire project mode
            mock_worker_class.assert_called_once_with("/test/root", None, "entire_project")


class TestCodewiseAppUpdates:
    """Test progress and response updates"""

    def test_update_progress(self):
        """Test progress update functionality"""
        get_qapp()
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
        get_qapp()
        codewise_app = CodewiseApp()

        # Mock the API response text widget and spinner
        codewise_app.api_response_text = Mock()
        codewise_app.spinner = Mock()

        codewise_app.update_api_response("Test API response")

        # Verify API response text was updated but spinner was NOT stopped
        codewise_app.api_response_text.setText.assert_called_with("Test API response")
        codewise_app.spinner.stop_spinning.assert_not_called()
        codewise_app.spinner.setVisible.assert_not_called()

    def test_update_api_response_no_spinner_stop(self):
        """Test that update_api_response doesn't stop the spinner"""
        get_qapp()
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


class TestCodewiseAppEventHandling:
    """Test event handlers for analysis completion and errors"""

    def test_on_analysis_finished(self):
        """Test analysis finished handling"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Mock components
        codewise_app.output_text = Mock()
        codewise_app.spinner = Mock()
        codewise_app.submit_btn = Mock()

        # Mock QMessageBox to avoid actual dialog
        with patch("PySide6.QtWidgets.QMessageBox.information") as mock_info:
            codewise_app.on_analysis_finished("Test completion message")

            # Verify all components were updated correctly
            codewise_app.output_text.append.assert_called_with("Test completion message\n")
            codewise_app.spinner.stop_spinning.assert_called()
            codewise_app.spinner.setVisible.assert_called_with(False)
            codewise_app.submit_btn.setEnabled.assert_called_with(True)
            mock_info.assert_called()

    def test_on_analysis_error(self):
        """Test analysis error handling"""
        get_qapp()
        codewise_app = CodewiseApp()

        # Mock components
        codewise_app.output_text = Mock()
        codewise_app.spinner = Mock()
        codewise_app.submit_btn = Mock()

        # Mock QMessageBox to avoid actual dialog
        with patch("PySide6.QtWidgets.QMessageBox.critical") as mock_critical:
            codewise_app.on_analysis_error("Test error message")

            # Verify all components were updated correctly
            codewise_app.output_text.append.assert_called_with("Error: Test error message\n")
            codewise_app.spinner.stop_spinning.assert_called()
            codewise_app.spinner.setVisible.assert_called_with(False)
            codewise_app.submit_btn.setEnabled.assert_called_with(True)
            mock_critical.assert_called()

    def test_on_cancel(self):
        """Test cancel functionality"""
        get_qapp()
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
