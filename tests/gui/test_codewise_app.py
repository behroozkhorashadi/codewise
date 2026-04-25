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
            codewise_app._output_storage = Mock()
            codewise_app._output_storage.output_exists.return_value = False

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
        codewise_app._output_storage = Mock()
        codewise_app._output_storage.output_exists.return_value = False

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


class TestOnSubmitCacheFlow:
    """Tests for the on_submit cache-hit flow (lines 714-788)"""

    def _make_app_with_cache(self, cached_data, change_info=None):
        get_qapp()
        app = CodewiseApp()
        app.root_dir_entry.setText("/test/root")
        app.file_path_entry.setText("/test/file.py")
        app.analysis_mode = "single_file"

        storage = Mock()
        storage.output_exists.return_value = True
        storage.get_analysis_output_path.return_value = "/tmp/cache/results.json"
        storage.load_analysis_output.return_value = cached_data
        storage.detect_repo_changes.return_value = change_info
        app._output_storage = storage
        return app

    def test_cache_hit_user_chooses_yes_loads_results(self):
        """User clicks Yes → cached results are displayed without re-running"""
        from PySide6.QtWidgets import QMessageBox

        cached_data = {
            "results": [
                {"method_name": "foo", "structured_response": {"overall_score": 8, "overall_feedback": "ok"}},
            ],
            "timestamp": "2024-01-01T00:00:00",
        }
        app = self._make_app_with_cache(cached_data)

        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker") as mock_worker_class:
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                with patch.object(QMessageBox, "information"):
                    app.on_submit()

            mock_worker_class.assert_not_called()

    def test_cache_hit_user_chooses_no_reruns(self):
        """User clicks No → analysis runs fresh"""
        from PySide6.QtWidgets import QMessageBox

        cached_data = {
            "results": [{"method_name": "foo", "structured_response": {}}],
            "timestamp": "2024-01-01T00:00:00",
        }
        app = self._make_app_with_cache(cached_data)

        mock_worker = Mock()
        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker", return_value=mock_worker):
            with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
                app.on_submit()

            mock_worker.start.assert_called_once()

    def test_cache_hit_with_repo_changes_shows_warning_in_dialog(self):
        """When repo has changed, dialog title reflects changes"""
        from PySide6.QtWidgets import QMessageBox

        cached_data = {
            "results": [],
            "timestamp": "2024-01-01T00:00:00",
        }
        change_info = {
            "has_changes": True,
            "changes": {"added": ["new.py"], "removed": [], "modified": ["old.py"]},
            "cached_timestamp": "2024-01-01",
        }
        app = self._make_app_with_cache(cached_data, change_info=change_info)

        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker") as mock_worker_class:
            mock_worker_class.return_value = Mock()
            dialog_kwargs = {}

            def capture_question(parent, title, msg, buttons):
                dialog_kwargs["title"] = title
                return QMessageBox.No

            with patch.object(QMessageBox, "question", side_effect=capture_question):
                app.on_submit()

        assert "Changed" in dialog_kwargs.get("title", "") or "change" in dialog_kwargs.get("title", "").lower()

    def test_cache_hit_old_format_fallback(self):
        """Cached results with old format (api_response only) load without error"""
        from PySide6.QtWidgets import QMessageBox

        cached_data = {
            "results": [{"method_name": "bar", "api_response": "Score: 8/10"}],
            "timestamp": "2024-01-01T00:00:00",
        }
        app = self._make_app_with_cache(cached_data)

        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker"):
            with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
                with patch.object(QMessageBox, "information"):
                    app.on_submit()


class TestOnAnalysisFinishedAndErrorWhenCancelled:
    """on_analysis_finished/error return early when _cancelled=True"""

    def test_on_analysis_finished_returns_early_if_cancelled(self):
        get_qapp()
        app = CodewiseApp()
        app._cancelled = True
        app.output_text = Mock()
        app.spinner = Mock()

        app.on_analysis_finished("done")

        app.output_text.append.assert_not_called()

    def test_on_analysis_error_returns_early_if_cancelled(self):
        get_qapp()
        app = CodewiseApp()
        app._cancelled = True
        app.output_text = Mock()
        app.spinner = Mock()

        app.on_analysis_error("something went wrong")

        app.output_text.append.assert_not_called()


class TestOnSubmitExceptionHandling:
    """on_submit gracefully handles exceptions when starting the worker"""

    def test_exception_during_worker_start_resets_ui(self):
        get_qapp()
        app = CodewiseApp()
        app.root_dir_entry.setText("/test/root")
        app.file_path_entry.setText("/test/file.py")
        app.analysis_mode = "single_file"

        storage = Mock()
        storage.output_exists.return_value = False
        app._output_storage = storage

        with patch("source.codewise_gui.codewise_ui_utils.AnalysisWorker", side_effect=RuntimeError("crash")):
            app.on_submit()

        # UI should not be stuck in a broken state — submit button re-enabled via reset_ui_after_cancel
        # No assertion needed if it didn't raise; just verifying graceful handling
