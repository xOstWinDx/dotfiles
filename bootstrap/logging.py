"""Logging module for Bootstrap - structured logging with color support."""
import logging
import sys
from pathlib import Path
from typing import Optional


# Color codes for terminal output
class Colors:
    """ANSI color codes."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        "DEBUG": Colors.GRAY,
        "INFO": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "CRITICAL": Colors.RED + Colors.BOLD,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            color = self.COLORS[levelname]
            record.levelname = f"{color}{levelname}{Colors.RESET}"
        
        return super().format(record)


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False
) -> logging.Logger:
    """Setup logging configuration."""
    
    if verbose:
        level = logging.DEBUG
    if quiet:
        level = logging.WARNING
    
    # Create logger
    logger = logging.getLogger("bootstrap")
    logger.setLevel(level)
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = ColoredFormatter(
        "%(levelname)s: %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "bootstrap") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)
