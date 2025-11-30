"""
Unit tests for AnalysisWorker class.

Tests focus on:
1. Basic initialization and state
2. Single file analysis workflows
3. Entire project analysis workflows
4. Error handling during analysis
5. Cancellation functionality
6. Processing multiple methods (critical fix verification)
"""

from unittest.mock import Mock, patch

from source.codewise_gui.codewise_ui_utils import AnalysisWorker

# Import the shared fixtures and helper from test_ui_utils
from .test_ui_utils import get_qapp, suppress_message_boxes  # noqa: F401


class TestAnalysisWorkerInitialization:
    """Test AnalysisWorker initialization"""

    def test_initialization_single_file(self):
        """Test worker initializes correctly for single file mode"""
        worker = AnalysisWorker("/test/root", "/test/file.py")

        assert worker.root_directory == "/test/root"
        assert worker.file_path == "/test/file.py"

    def test_initialization_entire_project(self):
        """Test worker initializes correctly for entire project mode"""
        worker = AnalysisWorker("/test/root", analysis_mode="entire_project")

        assert worker.root_directory == "/test/root"
        assert worker.file_path is None

    def test_cancel_functionality(self):
        """Test cancel sets the cancelled flag"""
        worker = AnalysisWorker("/test/root", "/test/file.py")

        assert not worker._is_cancelled

        # Mock quit and wait to avoid thread operations
        with patch.object(worker, "quit"), patch.object(worker, "wait"):
            worker.cancel()

        assert worker._is_cancelled


class TestAnalysisWorkerSingleFileMode:
    """Test AnalysisWorker single file analysis"""

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    @patch("source.codewise_gui.codewise_ui_utils.get_method_ratings")
    def test_successful_single_file_analysis(self, mock_get_ratings, mock_collect_usages):
        """Test successful single file analysis workflow"""
        # Setup mocks
        mock_method_pointer = Mock()
        mock_method_pointer.method_id.method_name = "test_method"
        mock_method_pointer.file_path = "/test/file.py"
        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        mock_collect_usages.return_value = {mock_method_pointer: [mock_call_site_info]}
        mock_get_ratings.return_value = "Test API response"

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:
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

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    def test_single_file_no_methods_found(self, mock_collect_usages):
        """Test single file analysis when no methods are found"""
        mock_collect_usages.return_value = {}

        worker = AnalysisWorker("/test/root", "/test/file.py")

        error_signal = Mock()
        worker.error.connect(error_signal)

        worker.run()

        assert error_signal.called
        call_args = error_signal.call_args[0][0]
        assert "No methods found in the specified file" in call_args

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    def test_single_file_exception_handling(self, mock_collect_usages):
        """Test exception handling during single file analysis"""
        mock_collect_usages.side_effect = Exception("Test error")

        worker = AnalysisWorker("/test/root", "/test/file.py")

        error_signal = Mock()
        worker.error.connect(error_signal)

        worker.run()

        assert error_signal.called
        call_args = error_signal.call_args[0][0]
        assert "Error during analysis" in call_args


class TestAnalysisWorkerEntireProjectMode:
    """Test AnalysisWorker entire project analysis"""

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages_entire_project")
    @patch("source.codewise_gui.codewise_ui_utils.get_method_ratings")
    def test_successful_entire_project_analysis(self, mock_get_ratings, mock_collect_entire_project):
        """Test successful entire project analysis workflow"""
        # Setup mocks
        mock_method_pointer = Mock()
        mock_method_pointer.method_id.method_name = "test_method"
        mock_method_pointer.file_path = "/test/file.py"
        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        mock_collect_entire_project.return_value = {
            "test_file.py:test_method": (mock_method_pointer, [mock_call_site_info])
        }
        mock_get_ratings.return_value = "Test API response"

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", analysis_mode="entire_project")

            progress_signal = Mock()
            api_response_signal = Mock()
            finished_signal = Mock()

            worker.progress.connect(progress_signal)
            worker.api_response.connect(api_response_signal)
            worker.finished.connect(finished_signal)

            worker.run()

            assert progress_signal.called
            assert api_response_signal.called
            assert finished_signal.called

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages_entire_project")
    def test_entire_project_no_methods_found(self, mock_collect_entire_project):
        """Test entire project analysis when no methods are found"""
        mock_collect_entire_project.return_value = {}

        worker = AnalysisWorker("/test/root", analysis_mode="entire_project")

        error_signal = Mock()
        worker.error.connect(error_signal)

        worker.run()

        assert error_signal.called
        call_args = error_signal.call_args[0][0]
        assert "No methods found in the project" in call_args

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    def test_collect_method_usages_entire_project_helper(self, mock_collect):
        """Test the collect_method_usages_entire_project function"""
        from source.codewise_gui.codewise_ui_utils import collect_method_usages_entire_project

        mock_method_pointer = Mock()
        mock_method_pointer.file_path = "/test/file.py"
        mock_method_pointer.method_id.method_name = "test_method"
        mock_call_site_info = Mock()

        mock_collect.return_value = {mock_method_pointer: [mock_call_site_info]}

        with patch("os.walk") as mock_walk:
            mock_walk.return_value = [
                ("/test/root", ["src"], ["test.py"]),
                ("/test/root/src", [], ["main.py"]),
            ]

            result = collect_method_usages_entire_project("/test/root")

            assert len(result) > 0
            assert "/test/file.py:test_method" in result


class TestAnalysisWorkerMultipleMethods:
    """Test processing of multiple methods (critical fix verification)"""

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    @patch("source.codewise_gui.codewise_ui_utils.get_method_ratings")
    def test_processes_all_methods_in_file(self, mock_get_ratings, mock_collect_usages):
        """Test that ALL methods in a file are processed, not just the first one"""
        # Create 3 methods to verify all are processed
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

        mock_collect_usages.return_value = {
            mock_method_pointer1: [mock_call_site_info],
            mock_method_pointer2: [mock_call_site_info],
            mock_method_pointer3: [mock_call_site_info],
        }

        mock_get_ratings.side_effect = [
            "API response for method 1",
            "API response for method 2",
            "API response for method 3",
        ]

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", "/test/file.py")

            progress_signal = Mock()
            api_response_signal = Mock()
            finished_signal = Mock()

            worker.progress.connect(progress_signal)
            worker.api_response.connect(api_response_signal)
            worker.finished.connect(finished_signal)

            worker.run()

            # CRITICAL: Verify that ALL 3 methods were processed
            assert mock_get_ratings.call_count == 3

            # Verify progress for all methods
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Processing method: test_method_1" in call for call in progress_calls)
            assert any("Processing method: test_method_2" in call for call in progress_calls)
            assert any("Processing method: test_method_3" in call for call in progress_calls)

            # Verify API responses for all methods
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 3
            assert any("Analysis for method: test_method_1" in call for call in api_response_calls)
            assert any("Analysis for method: test_method_2" in call for call in api_response_calls)
            assert any("Analysis for method: test_method_3" in call for call in api_response_calls)

            assert finished_signal.called

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    @patch("source.codewise_gui.codewise_ui_utils.get_method_ratings")
    def test_processes_class_methods_and_functions(self, mock_get_ratings, mock_collect_usages):
        """Test processing of both class methods and standalone functions"""
        mock_class_method = Mock()
        mock_class_method.method_id.method_name = "class_method"
        mock_class_method.file_path = "/test/file.py"

        mock_function = Mock()
        mock_function.method_id.method_name = "standalone_function"
        mock_function.file_path = "/test/file.py"

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        mock_collect_usages.return_value = {
            mock_class_method: [mock_call_site_info],
            mock_function: [mock_call_site_info],
        }

        mock_get_ratings.side_effect = ["API response for class method", "API response for function"]

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", "/test/file.py")

            progress_signal = Mock()
            api_response_signal = Mock()

            worker.progress.connect(progress_signal)
            worker.api_response.connect(api_response_signal)

            worker.run()

            assert mock_get_ratings.call_count == 2

            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Processing method: class_method" in call for call in progress_calls)
            assert any("Processing method: standalone_function" in call for call in progress_calls)


class TestAnalysisWorkerErrorHandling:
    """Test error handling during analysis"""

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    @patch("source.codewise_gui.codewise_ui_utils.get_method_ratings")
    def test_continues_after_api_error(self, mock_get_ratings, mock_collect_usages):
        """Test that analysis continues even if one API call fails"""
        mock_method_pointer1 = Mock()
        mock_method_pointer1.method_id.method_name = "test_method_1"
        mock_method_pointer1.file_path = "/test/file.py"

        mock_method_pointer2 = Mock()
        mock_method_pointer2.method_id.method_name = "test_method_2"
        mock_method_pointer2.file_path = "/test/file.py"

        mock_call_site_info = Mock()
        mock_call_site_info.function_node = Mock()
        mock_call_site_info.file_path = "/test/file.py"

        mock_collect_usages.return_value = {
            mock_method_pointer1: [mock_call_site_info],
            mock_method_pointer2: [mock_call_site_info],
        }

        # First call fails, second succeeds
        mock_get_ratings.side_effect = [Exception("API Error for method 1"), "API response for method 2"]

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", "/test/file.py")

            progress_signal = Mock()
            api_response_signal = Mock()
            finished_signal = Mock()

            worker.progress.connect(progress_signal)
            worker.api_response.connect(api_response_signal)
            worker.finished.connect(finished_signal)

            worker.run()

            # Both API calls were attempted
            assert mock_get_ratings.call_count == 2

            # Error logged for first method
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Error calling API for test_method_1" in call for call in progress_calls)

            # Success logged for second method
            assert any("API call completed for test_method_2" in call for call in progress_calls)

            # Only successful response emitted
            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 1
            assert "Analysis for method: test_method_2" in api_response_calls[0]

            assert finished_signal.called


class TestAnalysisWorkerCancellation:
    """Test cancellation during analysis"""

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    def test_cancellation_stops_processing(self, mock_collect_usages):
        """Test that cancellation stops processing of remaining methods"""
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

        mock_collect_usages.return_value = {
            mock_method_pointer1: [mock_call_site_info],
            mock_method_pointer2: [mock_call_site_info],
            mock_method_pointer3: [mock_call_site_info],
        }

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:
            mock_get_body.return_value = "def test_method(): pass"

            worker = AnalysisWorker("/test/root", "/test/file.py")

            # Mock the API call to cancel after first method
            with patch.object(worker._api_call, "call_api") as mock_call_api:
                mock_call_api.return_value = "Test API response"

                progress_signal = Mock()
                api_response_signal = Mock()
                finished_signal = Mock()

                worker.progress.connect(progress_signal)
                worker.api_response.connect(api_response_signal)
                worker.finished.connect(finished_signal)

                # Cancel after first method
                def cancel_after_first_method():
                    if mock_call_api.call_count >= 1:
                        worker.cancel()

                def call_api_with_cancel(*args, **kwargs):
                    cancel_after_first_method()
                    return "Test API response"

                mock_call_api.side_effect = call_api_with_cancel

                worker.run()

                # Only first method should be processed
                assert mock_call_api.call_count == 1

                # No API responses emitted (cancellation stopped processing)
                api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
                assert len(api_response_calls) == 0

                # Finished not called due to cancellation
                assert not finished_signal.called

    @patch("source.codewise_gui.codewise_ui_utils.collect_method_usages")
    @patch("source.codewise_gui.codewise_ui_utils.get_method_ratings")
    def test_processes_methods_with_multiple_usages(self, mock_get_ratings, mock_collect_usages):
        """Test processing of methods with multiple usage examples"""
        mock_method_pointer = Mock()
        mock_method_pointer.method_id.method_name = "test_method"
        mock_method_pointer.file_path = "/test/file.py"

        mock_call_site_info1 = Mock()
        mock_call_site_info1.function_node = Mock()
        mock_call_site_info1.file_path = "/test/usage1.py"

        mock_call_site_info2 = Mock()
        mock_call_site_info2.function_node = Mock()
        mock_call_site_info2.file_path = "/test/usage2.py"

        mock_collect_usages.return_value = {mock_method_pointer: [mock_call_site_info1, mock_call_site_info2]}

        mock_get_ratings.return_value = "Test API response"

        with patch("source.codewise_gui.codewise_ui_utils.get_method_body") as mock_get_body:

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

            progress_signal = Mock()
            api_response_signal = Mock()
            finished_signal = Mock()

            worker.progress.connect(progress_signal)
            worker.api_response.connect(api_response_signal)
            worker.finished.connect(finished_signal)

            worker.run()

            # Method body + 2 usage examples
            assert mock_get_body.call_count == 3

            # Verify usage examples were included
            progress_calls = [call[0][0] for call in progress_signal.call_args_list]
            assert any("Processing method: test_method" in call for call in progress_calls)
            assert any("Found 2 usage examples" in call for call in progress_calls)

            api_response_calls = [call[0][0] for call in api_response_signal.call_args_list]
            assert len(api_response_calls) == 1
            assert "Analysis for method: test_method" in api_response_calls[0]

            assert finished_signal.called
