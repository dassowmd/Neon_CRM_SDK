"""Unit tests for the logging module."""

import logging
import os
from unittest.mock import patch

from neon_crm.logging import NeonLogger


class TestNeonLogger:
    """Test the NeonLogger class."""

    def setup_method(self):
        """Reset logger state before each test."""
        # Clear any existing loggers
        NeonLogger._loggers.clear()
        # Reset configuration state
        NeonLogger._configured = False
        NeonLogger._default_level = logging.INFO
        # Reset environment variables
        if "NEON_LOG_LEVEL" in os.environ:
            del os.environ["NEON_LOG_LEVEL"]

    def test_get_logger_creates_new_logger(self):
        """Test that get_logger creates a new logger instance."""
        logger = NeonLogger.get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "neon_crm.test.module"

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns the same instance for the same name."""
        logger1 = NeonLogger.get_logger("test.module")
        logger2 = NeonLogger.get_logger("test.module")
        assert logger1 is logger2

    def test_get_logger_with_empty_name_uses_root(self):
        """Test that get_logger with empty name uses root logger."""
        logger = NeonLogger.get_logger("")
        assert logger.name == "neon_crm."

    def test_logger_hierarchy(self):
        """Test that logger hierarchy is properly established."""
        parent_logger = NeonLogger.get_logger("parent")
        child_logger = NeonLogger.get_logger("parent.child")

        # Child should inherit from parent
        assert child_logger.parent.name == parent_logger.name

    def test_set_level_from_string_debug(self):
        """Test setting log level to DEBUG."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("DEBUG")
        assert logger.level == logging.DEBUG

    def test_set_level_from_string_info(self):
        """Test setting log level to INFO."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("INFO")
        assert logger.level == logging.INFO

    def test_set_level_from_string_warning(self):
        """Test setting log level to WARNING."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("WARNING")
        assert logger.level == logging.WARNING

    def test_set_level_from_string_error(self):
        """Test setting log level to ERROR."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("ERROR")
        assert logger.level == logging.ERROR

    def test_set_level_from_string_critical(self):
        """Test setting log level to CRITICAL."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("CRITICAL")
        assert logger.level == logging.CRITICAL

    def test_set_level_from_string_invalid_level(self):
        """Test that invalid log level defaults to INFO."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("INVALID")
        assert logger.level == logging.INFO

    def test_set_level_from_string_case_insensitive(self):
        """Test that log level setting is case insensitive."""
        logger = NeonLogger.get_logger("test")
        NeonLogger.set_level_from_string("debug")
        assert logger.level == logging.DEBUG

    def test_environment_variable_sets_level(self):
        """Test that NEON_LOG_LEVEL environment variable sets the level."""
        with patch.dict(os.environ, {"NEON_LOG_LEVEL": "ERROR"}):
            # Reset configuration to pick up new env var
            NeonLogger._configured = False
            logger = NeonLogger.get_logger("test.env")
            assert logger.level == logging.ERROR

    def test_environment_variable_case_insensitive(self):
        """Test that NEON_LOG_LEVEL is case insensitive."""
        with patch.dict(os.environ, {"NEON_LOG_LEVEL": "warning"}):
            NeonLogger._configured = False
            logger = NeonLogger.get_logger("test.env")
            assert logger.level == logging.WARNING

    def test_environment_variable_invalid_defaults_to_info(self):
        """Test that invalid NEON_LOG_LEVEL defaults to INFO."""
        with patch.dict(os.environ, {"NEON_LOG_LEVEL": "INVALID_LEVEL"}):
            NeonLogger._configured = False
            logger = NeonLogger.get_logger("test.env")
            assert logger.level == logging.INFO

    def test_test_logger_uses_memory_handler(self):
        """Test that test logger uses memory handler."""
        logger = NeonLogger.get_test_logger("test.module")
        # Test logger should have at least one handler
        assert len(logger.handlers) > 0

    def test_multiple_loggers_independent_levels(self):
        """Test that multiple loggers can have different levels."""
        logger1 = NeonLogger.get_logger("test.module1")
        logger2 = NeonLogger.get_logger("test.module2")

        logger1.setLevel(logging.DEBUG)
        logger2.setLevel(logging.ERROR)

        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.ERROR

    def test_logger_propagation_enabled(self):
        """Test that logger propagation is enabled by default."""
        logger = NeonLogger.get_logger("test.propagation")
        assert logger.propagate is True

    def test_logger_thread_safety(self):
        """Test that logger creation is thread-safe."""
        import threading

        results = []

        def create_logger():
            logger = NeonLogger.get_logger("test.thread")
            results.append(logger)

        threads = [threading.Thread(target=create_logger) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should get the same logger instance
        first_logger = results[0]
        assert all(logger is first_logger for logger in results)

    def test_logger_memory_efficiency(self):
        """Test that loggers are cached properly to avoid memory leaks."""
        # Create multiple loggers with same name
        loggers = [NeonLogger.get_logger("test.memory") for _ in range(100)]

        # All should be the same instance
        first_logger = loggers[0]
        assert all(logger is first_logger for logger in loggers)

        # Should only have one entry in the cache
        assert len([name for name in NeonLogger._loggers if "test.memory" in name]) == 1
