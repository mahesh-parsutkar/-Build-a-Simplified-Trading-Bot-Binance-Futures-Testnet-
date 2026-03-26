from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path


def setup_logging(log_dir: str | os.PathLike = "logs", log_level: str = "INFO") -> Path:
    """
    Configure root logging to a timestamped log file + console.

    Returns the created log file path.
    """
    level = getattr(logging, str(log_level).upper(), logging.INFO)

    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_file = log_dir_path / f"trading_bot_{ts}.log"

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times.
    if root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    fmt = logging.Formatter(
        fmt="%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Ensure our timestamps look like UTC (Formatter uses local time by default)
    logging.Formatter.converter = time_gmtime 

    logging.getLogger(__name__).info("Logging initialized. log_file=%s level=%s", log_file, logging.getLevelName(level))
    return log_file


def time_gmtime(*args):  
    import time
    return time.gmtime(*args)

    return time.gmtime(*args)
