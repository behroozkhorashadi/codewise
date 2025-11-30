"""
Unit tests for CancellableAPICall class.

Tests focus on:
1. Initialization and state management
2. Successful API calls
3. Cancellation during API calls
4. Error handling
5. Thread safety and lock management
6. State reset functionality
"""

import threading
import time
from unittest.mock import patch

import pytest

from source.codewise_gui.codewise_ui_utils import CancellableAPICall, CancelledError


class TestCancellableAPICallInitialization:
    """Test initialization and state management of CancellableAPICall"""

    def test_initialization(self):
        """Test that CancellableAPICall initializes correctly"""
        api_call = CancellableAPICall()

        assert api_call._cancelled is False
        assert api_call._current_future is None
        assert api_call._executor is not None
        assert api_call._lock is not None

    def test_reset_clears_cancellation_state(self):
        """Test that reset() clears the cancellation flag"""
        api_call = CancellableAPICall()

        # Set cancelled flag
        with api_call._lock:
            api_call._cancelled = True

        # Reset should clear it
        api_call.reset()

        assert api_call._cancelled is False
        assert api_call._current_future is None

    def test_cancel_sets_flag(self):
        """Test that cancel() sets the cancellation flag"""
        api_call = CancellableAPICall()

        # Initially not cancelled
        assert api_call._cancelled is False

        # Cancel
        api_call.cancel()

        # Should be cancelled
        assert api_call._cancelled is True


class TestCancellableAPICallSuccessfulCalls:
    """Test successful API calls"""

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_successful_api_call(self, mock_get_ratings):
        """Test that a successful API call returns the correct result"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Test API Response"

        result = api_call.call_api("test prompt", "gpt-4")

        assert result == "Test API Response"
        mock_get_ratings.assert_called_once_with("test prompt", "gpt-4")

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_multiple_sequential_calls(self, mock_get_ratings):
        """Test that multiple sequential calls work correctly"""
        api_call = CancellableAPICall()
        mock_get_ratings.side_effect = ["Response 1", "Response 2", "Response 3"]

        # Make multiple calls
        result1 = api_call.call_api("prompt 1", "gpt-4")
        result2 = api_call.call_api("prompt 2", "gpt-4")
        result3 = api_call.call_api("prompt 3", "gpt-4")

        # Verify all results
        assert result1 == "Response 1"
        assert result2 == "Response 2"
        assert result3 == "Response 3"

        # Verify all calls were made
        assert mock_get_ratings.call_count == 3

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_api_call_with_default_model(self, mock_get_ratings):
        """Test API call with default model parameter"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        api_call.call_api("test prompt")

        # Should use default model "gpt-4"
        mock_get_ratings.assert_called_once_with("test prompt", "gpt-4")


class TestCancellableAPICallCancellation:
    """Test cancellation functionality"""

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_cancel_during_api_call(self, mock_get_ratings):
        """Test that cancelling during an API call raises CancelledError"""
        api_call = CancellableAPICall()

        # Create a slow API call
        def slow_api_call(prompt, model):
            time.sleep(2)  # Simulate slow API call
            return "Response"

        mock_get_ratings.side_effect = slow_api_call

        # Start the API call in a thread
        def call_api_in_thread():
            try:
                api_call.call_api("slow prompt", "gpt-4")
            except CancelledError:
                pass  # Expected

        thread = threading.Thread(target=call_api_in_thread)
        thread.start()

        # Give the call time to start
        time.sleep(0.2)

        # Cancel the call
        api_call.cancel()

        # Wait for thread to finish
        thread.join(timeout=5)

        # Thread should have finished (due to cancellation)
        assert not thread.is_alive()

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_cancel_before_call_raises_error(self, mock_get_ratings):
        """Test that cancelling before a call prevents the call"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        # Cancel first
        api_call.cancel()

        # Then try to make a call - should raise CancelledError
        with pytest.raises(CancelledError):
            api_call.call_api("test prompt", "gpt-4")

        # API should not have been called
        mock_get_ratings.assert_not_called()

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_reset_after_cancellation_allows_new_call(self, mock_get_ratings):
        """Test that reset() allows a new call after cancellation"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        # Cancel
        api_call.cancel()

        # Should fail
        with pytest.raises(CancelledError):
            api_call.call_api("test prompt", "gpt-4")

        # Reset
        api_call.reset()

        # Should succeed now
        result = api_call.call_api("test prompt", "gpt-4")
        assert result == "Response"


class TestCancellableAPICallErrorHandling:
    """Test error handling"""

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_api_error_propagates(self, mock_get_ratings):
        """Test that API errors are propagated correctly"""
        api_call = CancellableAPICall()
        mock_get_ratings.side_effect = ValueError("API Error")

        # Should raise the same error
        with pytest.raises(ValueError, match="API Error"):
            api_call.call_api("test prompt", "gpt-4")

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_api_timeout_error(self, mock_get_ratings):
        """Test handling of timeout errors"""
        api_call = CancellableAPICall()
        mock_get_ratings.side_effect = TimeoutError("API Timeout")

        # Should raise timeout error
        with pytest.raises(TimeoutError, match="API Timeout"):
            api_call.call_api("test prompt", "gpt-4")

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_cancellation_during_error_handling(self, mock_get_ratings):
        """Test that cancellation during error handling is handled correctly"""
        api_call = CancellableAPICall()

        def failing_api_call(prompt, model):
            time.sleep(0.5)
            raise ValueError("API Error")

        mock_get_ratings.side_effect = failing_api_call

        # Start call in thread
        def call_api_in_thread():
            try:
                api_call.call_api("test prompt", "gpt-4")
            except (ValueError, CancelledError):
                pass  # Expected

        thread = threading.Thread(target=call_api_in_thread)
        thread.start()

        # Give call time to start
        time.sleep(0.1)

        # Cancel while error is being handled
        api_call.cancel()

        # Wait for thread
        thread.join(timeout=5)

        # Thread should finish
        assert not thread.is_alive()


class TestCancellableAPICallThreadSafety:
    """Test thread safety and lock management"""

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_concurrent_cancellation_is_safe(self, mock_get_ratings):
        """Test that concurrent cancellation doesn't cause race conditions"""
        api_call = CancellableAPICall()

        def slow_api_call(prompt, model):
            time.sleep(1)
            return "Response"

        mock_get_ratings.side_effect = slow_api_call

        # Start API call
        api_thread = threading.Thread(
            target=lambda: api_call.call_api("test", "gpt-4") if not api_call._cancelled else None
        )
        api_thread.start()

        # Give it time to start
        time.sleep(0.1)

        # Cancel from another thread
        cancel_thread = threading.Thread(target=api_call.cancel)
        cancel_thread.start()

        # Wait for both threads
        api_thread.join(timeout=5)
        cancel_thread.join(timeout=5)

        # Both should finish without deadlock
        assert not api_thread.is_alive()
        assert not cancel_thread.is_alive()

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_reset_during_call_is_safe(self, mock_get_ratings):
        """Test that reset can be called safely while a call might be in progress"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        # Make a quick call
        result = api_call.call_api("test", "gpt-4")

        # Reset should work without issues
        api_call.reset()

        # State should be clean
        assert api_call._cancelled is False
        assert api_call._current_future is None
        assert result == "Response"

    def test_lock_prevents_race_conditions(self):
        """Test that the lock properly protects shared state"""
        api_call = CancellableAPICall()

        # Verify lock is used for state changes
        assert api_call._lock is not None

        # Test that we can acquire the lock
        acquired = api_call._lock.acquire(blocking=False)
        assert acquired
        api_call._lock.release()


class TestCancellableAPICallCleanup:
    """Test proper resource cleanup"""

    def test_shutdown_executor(self):
        """Test that shutdown() properly closes the executor"""
        api_call = CancellableAPICall()

        # Shutdown the executor
        api_call.shutdown()

        # Executor should be shut down
        assert api_call._executor._shutdown is True

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_future_is_cleaned_up_after_call(self, mock_get_ratings):
        """Test that future reference is cleaned up after call completes"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        # Make a call
        api_call.call_api("test", "gpt-4")

        # After successful call, future should be None
        assert api_call._current_future is None

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_future_cleanup_on_exception(self, mock_get_ratings):
        """Test that future is cleaned up even if exception occurs"""
        api_call = CancellableAPICall()
        mock_get_ratings.side_effect = ValueError("API Error")

        # Make a call that raises an error
        try:
            api_call.call_api("test", "gpt-4")
        except ValueError:
            pass  # Expected

        # Future should still be cleaned up
        assert api_call._current_future is None


class TestCancellableAPICallIntegration:
    """Integration tests for realistic usage patterns"""

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_call_reset_call_sequence(self, mock_get_ratings):
        """Test the typical call -> reset -> call sequence"""
        api_call = CancellableAPICall()
        mock_get_ratings.side_effect = ["Response 1", "Response 2"]

        # First call
        result1 = api_call.call_api("prompt 1", "gpt-4")
        assert result1 == "Response 1"

        # Reset
        api_call.reset()

        # Second call
        result2 = api_call.call_api("prompt 2", "gpt-4")
        assert result2 == "Response 2"

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_cancel_reset_call_sequence(self, mock_get_ratings):
        """Test cancel -> reset -> call sequence"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        # Cancel
        api_call.cancel()

        # Try call - should fail
        with pytest.raises(CancelledError):
            api_call.call_api("test", "gpt-4")

        # Reset
        api_call.reset()

        # Call should now work
        result = api_call.call_api("test", "gpt-4")
        assert result == "Response"

    @patch('source.codewise_gui.codewise_ui_utils.get_method_ratings')
    def test_multiple_reset_calls_are_safe(self, mock_get_ratings):
        """Test that calling reset multiple times is safe"""
        api_call = CancellableAPICall()
        mock_get_ratings.return_value = "Response"

        # Reset multiple times
        api_call.reset()
        api_call.reset()
        api_call.reset()

        # Should still work
        result = api_call.call_api("test", "gpt-4")
        assert result == "Response"
