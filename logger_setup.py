from datetime import datetime
import logging
from pathlib import Path


def setup_logger(name: str = "threat_intel") -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = (
        log_dir / f"threat_intel_{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Undvik dubbla handlers om funktionen körs flera gånger
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Fil-handler (forensisk spårbarhet)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Konsol-handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger