"""Logging configuration for the Neon CRM SDK."""

import logging
import os


class NeonLogger:
    """Logger configuration for the Neon CRM SDK."""

    _loggers = {}
    _configured = False
    _default_level = logging.INFO

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance for the given name.

        Args:
            name: Logger name (typically module name)

        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            logger = logging.getLogger(f"neon_crm.{name}")
            cls._configure_logger(logger)
            cls._loggers[name] = logger
        return cls._loggers[name]

    @classmethod
    def _configure_logger(cls, logger: logging.Logger) -> None:
        """Configure a logger with appropriate settings."""
        if not cls._configured:
            cls._setup_logging()

        logger.setLevel(cls._default_level)

        # Don't add handlers to child loggers - let them inherit from parent
        # This prevents duplicate log messages
        logger.propagate = True

    @classmethod
    def _setup_logging(cls) -> None:
        """Setup logging configuration for the entire SDK."""
        # Get log level from environment variable or use default
        log_level_str = os.getenv("NEON_LOG_LEVEL", "INFO").upper()

        # Map string to logging level
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        cls._default_level = level_mapping.get(log_level_str, logging.INFO)

        # Create root logger for neon_crm
        neon_root = logging.getLogger("neon_crm")
        neon_root.setLevel(cls._default_level)

        # Only add handler if none exists
        if not neon_root.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(cls._default_level)

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)

            neon_root.addHandler(handler)

            # Prevent propagation to root logger to avoid duplicate messages
            neon_root.propagate = False

        cls._configured = True

    @classmethod
    def set_level(cls, level: int) -> None:
        """Set the logging level for all SDK loggers.

        Args:
            level: Logging level (logging.DEBUG, logging.INFO, etc.)
        """
        cls._default_level = level

        # Update existing loggers
        for logger in cls._loggers.values():
            logger.setLevel(level)

        # Update root logger
        neon_root = logging.getLogger("neon_crm")
        neon_root.setLevel(level)
        for handler in neon_root.handlers:
            handler.setLevel(level)

    @classmethod
    def set_level_from_string(cls, level_str: str) -> None:
        """Set the logging level from a string.

        Args:
            level_str: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        level = level_mapping.get(level_str.upper(), logging.INFO)
        cls.set_level(level)

    @classmethod
    def get_test_logger(cls, name: str) -> logging.Logger:
        """Get a logger specifically configured for testing.

        Args:
            name: Logger name

        Returns:
            Test-configured logger instance
        """
        test_logger_name = f"test.{name}"
        if test_logger_name not in cls._loggers:
            logger = logging.getLogger(f"neon_crm.test.{name}")

            # Configure for testing (typically higher log level)
            test_level_str = os.getenv("NEON_TEST_LOG_LEVEL", "WARNING").upper()
            level_mapping = {
                "DEBUG": logging.DEBUG,
                "INFO": logging.INFO,
                "WARNING": logging.WARNING,
                "ERROR": logging.ERROR,
                "CRITICAL": logging.CRITICAL,
            }
            test_level = level_mapping.get(test_level_str, logging.WARNING)

            logger.setLevel(test_level)

            # Create separate handler for tests
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setLevel(test_level)

                formatter = logging.Formatter(
                    "[TEST] %(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                handler.setFormatter(formatter)

                logger.addHandler(handler)
                logger.propagate = False

            cls._loggers[test_logger_name] = logger

        return cls._loggers[test_logger_name]
