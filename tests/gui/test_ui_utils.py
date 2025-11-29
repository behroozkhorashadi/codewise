import threading
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from PySide6.QtCore import QTimer
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


class TestAnalysisWorker:
    """Test the AnalysisWorker thread functionality"""

    def test_worker_initialization(self):
        """Test that the worker initializes correctly"""
        worker = AnalysisWorker("/test/root", "/test/file.py")

        assert worker.root_directory == "/test/root"
        assert worker.file_path == "/test/file.py"

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
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
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
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

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    def test_worker_no_methods_found(self, mock_collect_usages):
        """Test worker behavior when no methods are found"""
        mock_collect_usages.return_value = {}

        worker = AnalysisWorker("/test/root", "/test/file.py")

        # Mock signals
        error_signal = Mock()
        worker.error.connect(error_signal)

        # Run the worker
        worker.run()

        # Verify error signal was emitted with appropriate message
        assert error_signal.called
        call_args = error_signal.call_args[0][0]
        assert "No methods found in the specified file" in call_args

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
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
        assert "Error during analysis" in call_args

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages_entire_project')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_entire_project_analysis(self, mock_get_ratings, mock_collect_entire_project):
        """Test entire project analysis workflow"""
        # Mock the method collection for entire project
        mock_method_pointer = Mock()
        mock_method_pointer.method_id.method_name = "test_method"
        mock_method_pointer.file_path = "/test/file.py"
        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        mock_collect_entire_project.return_value = {
            "test_file.py:test_method": (mock_method_pointer, [mock_call_site_info])
        }

        # Mock the API call
        mock_get_ratings.return_value = "Test API response"

        # Mock get_method_body
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", analysis_mode="entire_project")

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

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages_entire_project')
    def test_worker_entire_project_no_methods_found(self, mock_collect_entire_project):
        """Test worker behavior when no methods are found in entire project"""
        mock_collect_entire_project.return_value = {}

        worker = AnalysisWorker("/test/root", analysis_mode="entire_project")

        # Mock signals
        error_signal = Mock()
        worker.error.connect(error_signal)

        # Run the worker
        worker.run()

        # Verify error signal was emitted
        assert error_signal.called
        call_args = error_signal.call_args[0][0]
        assert "No methods found in the project" in call_args

    def test_worker_cancel_functionality(self):
        """Test worker cancel functionality"""
        worker = AnalysisWorker("/test/root", "/test/file.py")

        # Initially not cancelled
        assert not worker._is_cancelled

        # Cancel the worker
        worker.cancel()

        # Check cancelled flag
        assert worker._is_cancelled

        # Verify quit and wait are called
        with patch.object(worker, 'quit') as mock_quit:
            with patch.object(worker, 'wait') as mock_wait:
                worker.cancel()
                mock_quit.assert_called_once()
                mock_wait.assert_called_once()

    def test_collect_method_usages_entire_project(self):
        """Test the collect_method_usages_entire_project function"""
        from source.codewise_gui.codewise_ui_utils import collect_method_usages_entire_project

        with patch('source.codewise_gui.codewise_ui_utils.collect_method_usages') as mock_collect:
            # Mock the collect_method_usages function
            mock_method_pointer = Mock()
            mock_method_pointer.file_path = "/test/file.py"
            mock_method_pointer.method_id.method_name = "test_method"
            mock_call_site_info = Mock()

            mock_collect.return_value = {mock_method_pointer: [mock_call_site_info]}

            # Mock os.walk to return test files
            with patch('os.walk') as mock_walk:
                mock_walk.return_value = [("/test/root", ["src"], ["test.py"]), ("/test/root/src", [], ["main.py"])]

                result = collect_method_usages_entire_project("/test/root")

                # Verify the function processes files correctly
                assert len(result) > 0
                assert "/test/file.py:test_method" in result

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_processes_all_methods_single_file(self, mock_get_ratings, mock_collect_usages):
        """Test that the worker processes all methods in single file mode, not just the first one"""
        # Mock multiple method pointers
        mock_method_pointer1 = Mock()
        mock_method_pointer1.method_id.method_name = "test_method_1"
        mock_method_pointer1.file_path = "/test/file.py"

        mock_method_pointer2 = Mock()
        mock_method_pointer2.method_id.method_name = "test_method_2"
        mock_method_pointer2.file_path = "/test/file.py"

        mock_method_pointer3 = Mock()
        mock_method_pointer3.method_id.method_name = "test_method_3"
        mock_method_pointer3.file_path = "/test/file.py"

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        # Return multiple methods
        mock_collect_usages.return_value = {
            mock_method_pointer1: [mock_call_site_info],
            mock_method_pointer2: [mock_call_site_info],
            mock_method_pointer3: [mock_call_site_info],
        }

        # Mock the API call to return different responses for each method
        mock_get_ratings.side_effect = [
            "API response for method 1",
            "API response for method 2",
            "API response for method 3",
        ]

        # Mock get_method_body
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
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

            # Verify that API was called for all three methods
            assert mock_get_ratings.call_count == 3

            # Verify that progress was emitted for all methods
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Processing method: test_method_1" in call for call in progress_calls)
            assert any("Processing method: test_method_2" in call for call in progress_calls)
            assert any("Processing method: test_method_3" in call for call in progress_calls)

            # Verify that API responses were emitted for all methods
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 3
            assert any("Analysis for method: test_method_1" in call for call in api_response_calls)
            assert any("Analysis for method: test_method_2" in call for call in api_response_calls)
            assert any("Analysis for method: test_method_3" in call for call in api_response_calls)

            # Verify finished signal was emitted
            assert finished_signal.called

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_processes_methods_in_classes(self, mock_get_ratings, mock_collect_usages):
        """Test that the worker processes methods inside classes as well as standalone functions"""
        # Mock method pointers for both class methods and standalone functions
        mock_class_method_pointer = Mock()
        mock_class_method_pointer.method_id.method_name = "class_method"
        mock_class_method_pointer.file_path = "/test/file.py"

        mock_function_pointer = Mock()
        mock_function_pointer.method_id.method_name = "standalone_function"
        mock_function_pointer.file_path = "/test/file.py"

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        # Return both class methods and standalone functions
        mock_collect_usages.return_value = {
            mock_class_method_pointer: [mock_call_site_info],
            mock_function_pointer: [mock_call_site_info],
        }

        # Mock the API call
        mock_get_ratings.side_effect = ["API response for class method", "API response for standalone function"]

        # Mock get_method_body
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
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

            # Verify that API was called for both methods
            assert mock_get_ratings.call_count == 2

            # Verify that progress was emitted for both methods
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Processing method: class_method" in call for call in progress_calls)
            assert any("Processing method: standalone_function" in call for call in progress_calls)

            # Verify that API responses were emitted for both methods
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 2
            assert any("Analysis for method: class_method" in call for call in api_response_calls)
            assert any("Analysis for method: standalone_function" in call for call in api_response_calls)

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_handles_api_errors_gracefully(self, mock_get_ratings, mock_collect_usages):
        """Test that the worker continues processing other methods even if one API call fails"""
        # Mock multiple method pointers
        mock_method_pointer1 = Mock()
        mock_method_pointer1.method_id.method_name = "test_method_1"
        mock_method_pointer1.file_path = "/test/file.py"

        mock_method_pointer2 = Mock()
        mock_method_pointer2.method_id.method_name = "test_method_2"
        mock_method_pointer2.file_path = "/test/file.py"

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        # Return multiple methods
        mock_collect_usages.return_value = {
            mock_method_pointer1: [mock_call_site_info],
            mock_method_pointer2: [mock_call_site_info],
        }

        # Mock the API call to fail for first method, succeed for second
        mock_get_ratings.side_effect = [Exception("API Error for method 1"), "API response for method 2"]

        # Mock get_method_body
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
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

            # Verify that API was called for both methods
            assert mock_get_ratings.call_count == 2

            # Verify that error was logged for first method
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Error calling API for test_method_1" in call for call in progress_calls)

            # Verify that success was logged for second method
            assert any("API call completed for test_method_2" in call for call in progress_calls)

            # Verify that API response was emitted only for successful method
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 1
            assert "Analysis for method: test_method_2" in api_response_calls[0]

            # Verify finished signal was emitted
            assert finished_signal.called

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    def test_worker_cancellation_stops_processing(self, mock_collect_usages):
        """Test that cancellation stops processing of remaining methods"""
        # Mock multiple method pointers
        mock_method_pointer1 = Mock()
        mock_method_pointer1.method_id.method_name = "test_method_1"
        mock_method_pointer1.file_path = "/test/file.py"

        mock_method_pointer2 = Mock()
        mock_method_pointer2.method_id.method_name = "test_method_2"
        mock_method_pointer2.file_path = "/test/file.py"

        mock_method_pointer3 = Mock()
        mock_method_pointer3.method_id.method_name = "test_method_3"
        mock_method_pointer3.file_path = "/test/file.py"

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        # Return multiple methods
        mock_collect_usages.return_value = {
            mock_method_pointer1: [mock_call_site_info],
            mock_method_pointer2: [mock_call_site_info],
            mock_method_pointer3: [mock_call_site_info],
        }

        # Mock get_method_body
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", "/test/file.py")

            # Mock the CancellableAPICall.call_api method
            with patch.object(worker._api_call, 'call_api') as mock_call_api:
                mock_call_api.return_value = "Test API response"

                # Mock signals
                progress_signal = Mock()
                api_response_signal = Mock()
                finished_signal = Mock()

                worker.progress.connect(progress_signal)
                worker.api_response.connect(api_response_signal)
                worker.finished.connect(finished_signal)

                # Cancel the worker after it starts
                def cancel_after_first_method():
                    # Cancel after the first method is processed
                    if mock_call_api.call_count >= 1:
                        worker.cancel()

                # Mock the API call to trigger cancellation
                def call_api_with_cancel(*args, **kwargs):
                    cancel_after_first_method()
                    return "Test API response"

                mock_call_api.side_effect = call_api_with_cancel

                # Run the worker
                worker.run()

                # Verify that only the first method was processed
                assert mock_call_api.call_count == 1

                # Verify that no API responses were emitted (cancellation happened during API call)
                api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
                assert len(api_response_calls) == 0

                # Verify finished signal was not emitted (due to cancellation)
                assert not finished_signal.called

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_processes_methods_with_usage_examples(self, mock_get_ratings, mock_collect_usages):
        """Test that the worker correctly processes methods with their usage examples"""
        # Mock method pointer
        mock_method_pointer = Mock()
        mock_method_pointer.method_id.method_name = "test_method"
        mock_method_pointer.file_path = "/test/file.py"

        # Mock multiple call site infos (usage examples)
        mock_call_site_info1 = Mock()
        mock_call_site_info1.function_node = Mock()
        mock_call_site_info1.file_path = "/test/usage1.py"

        mock_call_site_info2 = Mock()
        mock_call_site_info2.function_node = Mock()
        mock_call_site_info2.file_path = "/test/usage2.py"

        # Return method with multiple usage examples
        mock_collect_usages.return_value = {mock_method_pointer: [mock_call_site_info1, mock_call_site_info2]}

        # Mock the API call
        mock_get_ratings.return_value = "Test API response"

        # Mock get_method_body to return different content for method and usages
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:

            def get_method_body_side_effect(node, file_path):
                if file_path == "/test/file.py":
                    return "def test_method(): pass"
                elif file_path == "/test/usage1.py":
                    return "def usage1(): test_method()"
                elif file_path == "/test/usage2.py":
                    return "def usage2(): test_method()"
                return "def unknown(): pass"

            mock_get_body.side_effect = get_method_body_side_effect

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

            # Verify that get_method_body was called for the method and both usage examples
            assert mock_get_body.call_count == 3

            # Verify that progress was emitted for the method
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Processing method: test_method" in call for call in progress_calls)
            assert any("Found 2 usage examples" in call for call in progress_calls)

            # Verify that API response was emitted
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 1
            assert "Analysis for method: test_method" in api_response_calls[0]

            # Verify finished signal was emitted
            assert finished_signal.called

    @patch('source.codewise_gui.codewise_ui_utils.collect_method_usages')
    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_worker_verifies_no_break_statement_behavior(self, mock_get_ratings, mock_collect_usages):
        """Test that the worker processes ALL methods, not just the first one (verifying the fix)"""
        # Mock multiple method pointers to simulate a file with many methods
        method_pointers = []
        for i in range(5):  # Create 5 methods
            mock_pointer = Mock()
            mock_pointer.method_id.method_name = f"method_{i}"
            mock_pointer.file_path = "/test/file.py"
            method_pointers.append(mock_pointer)

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        # Return all 5 methods
        mock_collect_usages.return_value = {pointer: [mock_call_site_info] for pointer in method_pointers}

        # Mock the API call to return different responses for each method
        mock_get_ratings.side_effect = [f"API response for method_{i}" for i in range(5)]

        # Mock get_method_body
        with patch('source.codewise_gui.codewise_ui_utils.get_method_body') as mock_get_body:
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

            # CRITICAL: Verify that ALL 5 methods were processed (not just the first one)
            assert mock_get_ratings.call_count == 5, f"Expected 5 API calls, got {mock_get_ratings.call_count}"

            # Verify that progress was emitted for all 5 methods
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            for i in range(5):
                assert any(
                    f"Processing method: method_{i}" in call for call in progress_calls
                ), f"Progress not emitted for method_{i}"

            # Verify that API responses were emitted for all 5 methods
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 5, f"Expected 5 API responses, got {len(api_response_calls)}"

            for i in range(5):
                assert any(
                    f"Analysis for method: method_{i}" in call for call in api_response_calls
                ), f"API response not emitted for method_{i}"

            # Verify finished signal was emitted
            assert finished_signal.called

            # Verify the final progress message shows all methods were processed
            final_progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any(
                "Processed 5 methods" in call for call in final_progress_calls
            ), "Final progress message should indicate all 5 methods were processed"


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

    def test_cancel_button_resets_ui_immediately(self):
        """Test that clicking Cancel during a long-running API call resets the UI immediately and no API response is emitted."""
        from unittest.mock import MagicMock, patch

        from PySide6.QtWidgets import QApplication

        from source.codewise_gui.codewise_ui_utils import AnalysisWorker, CodewiseApp

        app = QApplication.instance() or QApplication([])
        codewise_app = CodewiseApp()

        # Set up the UI for analysis
        codewise_app.root_dir_entry.setText("/fake/root")
        codewise_app.file_path_entry.setText("/fake/file.py")
        codewise_app.analysis_mode = "single_file"

        # Patch AnalysisWorker to simulate a long-running API call
        with patch.object(AnalysisWorker, '_process_methods') as mock_process_methods:

            def long_running_process_methods(result):
                # Simulate a long-running API call
                time.sleep(2)

            mock_process_methods.side_effect = long_running_process_methods

            # Patch collect_method_usages to return a fake method
            with patch('source.codewise_gui.codewise_ui_utils.collect_method_usages') as mock_collect:
                mock_method_pointer = MagicMock()
                mock_method_pointer.method_id.method_name = "test_method"
                mock_method_pointer.file_path = "/fake/file.py"
                mock_call_site_info = MagicMock()
                mock_call_site_info.function_node = MagicMock()
                mock_call_site_info.file_path = "/fake/file.py"
                mock_collect.return_value = {mock_method_pointer: [mock_call_site_info]}

                # Start analysis in a thread to allow cancellation
                def start_analysis():
                    codewise_app.on_submit()

                analysis_thread = threading.Thread(target=start_analysis)
                analysis_thread.start()
                time.sleep(0.2)  # Let the analysis start

                # Click Cancel while API call is in progress
                codewise_app.on_cancel_clicked()

                # UI should reset immediately
                if codewise_app.spinner is not None:
                    assert not codewise_app.spinner.isVisible()
                if codewise_app.cancel_btn is not None:
                    assert codewise_app.cancel_btn.isVisible() is False
                if codewise_app.submit_btn is not None:
                    assert codewise_app.submit_btn.isEnabled() is True
                if codewise_app.progress_label is not None:
                    assert "cancelled" in codewise_app.progress_label.text().lower()
                assert "Analysis cancelled by user." in codewise_app.output_text.toPlainText()
                assert codewise_app.api_response_text.toPlainText() == ""

                # Wait for analysis thread to finish
                analysis_thread.join(timeout=3)

                # No API response should be emitted after cancellation
                assert codewise_app.api_response_text.toPlainText() == ""

    def test_input_controls_disabled_during_analysis(self):
        """Test that browse buttons and text input boxes are disabled during analysis and re-enabled when complete."""
        from unittest.mock import MagicMock, patch

        from PySide6.QtWidgets import QApplication

        from source.codewise_gui.codewise_ui_utils import AnalysisWorker, CodewiseApp

        app = QApplication.instance() or QApplication([])
        codewise_app = CodewiseApp()

        # Set up the UI for analysis
        codewise_app.root_dir_entry.setText("/fake/root")
        codewise_app.file_path_entry.setText("/fake/file.py")
        codewise_app.analysis_mode = "single_file"

        # Verify initial state - controls should be enabled
        assert codewise_app.browse_root_btn.isEnabled() is True
        assert codewise_app.browse_file_btn.isEnabled() is True
        assert codewise_app.root_dir_entry.isEnabled() is True
        assert codewise_app.file_path_entry.isEnabled() is True

        # Patch AnalysisWorker to simulate a quick analysis
        with patch.object(AnalysisWorker, '_process_methods') as mock_process_methods:

            def quick_process_methods(result):
                # Simulate a quick analysis
                pass

            mock_process_methods.side_effect = quick_process_methods

            # Patch collect_method_usages to return a fake method
            with patch('source.codewise_gui.codewise_ui_utils.collect_method_usages') as mock_collect:
                mock_method_pointer = MagicMock()
                mock_method_pointer.method_id.method_name = "test_method"
                mock_method_pointer.file_path = "/fake/file.py"
                mock_call_site_info = MagicMock()
                mock_call_site_info.function_node = MagicMock()
                mock_call_site_info.file_path = "/fake/file.py"
                mock_collect.return_value = {mock_method_pointer: [mock_call_site_info]}

                # Start analysis
                codewise_app.on_submit()

                # Verify controls are disabled during analysis
                assert codewise_app.browse_root_btn.isEnabled() is False
                assert codewise_app.browse_file_btn.isEnabled() is False
                assert codewise_app.root_dir_entry.isEnabled() is False
                assert codewise_app.file_path_entry.isEnabled() is False

                # Mock QMessageBox to prevent popup during test
                with patch('PySide6.QtWidgets.QMessageBox.information') as mock_info:
                    # Simulate analysis completion
                    codewise_app.on_analysis_finished("Analysis completed successfully!")

                    # Verify QMessageBox was called
                    mock_info.assert_called_once()

                # Verify controls are re-enabled after analysis
                assert codewise_app.browse_root_btn.isEnabled() is True
                assert codewise_app.browse_file_btn.isEnabled() is True
                assert codewise_app.root_dir_entry.isEnabled() is True
                assert codewise_app.file_path_entry.isEnabled() is True

                # Wait for the worker thread to finish to avoid QThread destroyed while running error
                if codewise_app.worker:
                    codewise_app.worker.wait()

    def test_input_controls_re_enabled_after_cancellation(self):
        """Test that browse buttons and text input boxes are re-enabled after cancellation."""
        from unittest.mock import MagicMock, patch

        from PySide6.QtWidgets import QApplication

        from source.codewise_gui.codewise_ui_utils import AnalysisWorker, CodewiseApp

        app = QApplication.instance() or QApplication([])
        codewise_app = CodewiseApp()

        # Set up the UI for analysis
        codewise_app.root_dir_entry.setText("/fake/root")
        codewise_app.file_path_entry.setText("/fake/file.py")
        codewise_app.analysis_mode = "single_file"

        # Patch AnalysisWorker to simulate a long-running API call
        with patch.object(AnalysisWorker, '_process_methods') as mock_process_methods:

            def long_running_process_methods(result):
                # Simulate a long-running API call
                time.sleep(2)

            mock_process_methods.side_effect = long_running_process_methods

            # Patch collect_method_usages to return a fake method
            with patch('source.codewise_gui.codewise_ui_utils.collect_method_usages') as mock_collect:
                mock_method_pointer = MagicMock()
                mock_method_pointer.method_id.method_name = "test_method"
                mock_method_pointer.file_path = "/fake/file.py"
                mock_call_site_info = MagicMock()
                mock_call_site_info.function_node = MagicMock()
                mock_call_site_info.file_path = "/fake/file.py"
                mock_collect.return_value = {mock_method_pointer: [mock_call_site_info]}

                # Start analysis in a thread to allow cancellation
                def start_analysis():
                    codewise_app.on_submit()

                analysis_thread = threading.Thread(target=start_analysis)
                analysis_thread.start()
                time.sleep(0.2)  # Let the analysis start

                # Verify controls are disabled during analysis
                assert codewise_app.browse_root_btn.isEnabled() is False
                assert codewise_app.browse_file_btn.isEnabled() is False
                assert codewise_app.root_dir_entry.isEnabled() is False
                assert codewise_app.file_path_entry.isEnabled() is False

                # Click Cancel while API call is in progress
                codewise_app.on_cancel_clicked()

                # Verify controls are re-enabled after cancellation
                assert codewise_app.browse_root_btn.isEnabled() is True
                assert codewise_app.browse_file_btn.isEnabled() is True
                assert codewise_app.root_dir_entry.isEnabled() is True
                assert codewise_app.file_path_entry.isEnabled() is True

                # Wait for analysis thread to finish
                analysis_thread.join(timeout=3)


# Cleanup function to destroy QApplication
def pytest_sessionfinish(session, exitstatus):
    """Clean up QApplication after all tests"""
    global _qapp
    if _qapp is not None:
        _qapp.quit()
        _qapp = None
