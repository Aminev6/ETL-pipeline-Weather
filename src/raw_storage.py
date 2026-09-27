"""Save raw extracted weather records as timestamped JSON files."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SOURCE_NAME = "open-meteo"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def save_raw_data(records: list[dict]) -> Path:
    """Write one extraction run to data/raw and return the file path."""
    extracted_at = datetime.now(timezone.utc)
    document = {
        "extracted_at": extracted_at.isoformat(),
        "source": SOURCE_NAME,
        "records": records,
    }
    path = RAW_DIR / f"weather_{extracted_at.strftime('%Y%m%d_%H%M%S')}.json"

    try:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        logger.error("Failed to write raw weather file %s: %s", path, exc)
        raise
    except (TypeError, ValueError) as exc:
        logger.error("Failed to serialize raw weather data: %s", exc)
        raise

    logger.info("Saved raw weather data to %s", path)
    return path
