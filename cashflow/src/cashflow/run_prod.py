from __future__ import annotations

from cashflow.utils.config import get_settings
from cashflow.utils.logger import setup_logging


def main() -> None:
    import uvicorn

    settings = get_settings()
    setup_logging("INFO")
    uvicorn.run(
        "cashflow.app:app",
        host=settings.host,
        port=settings.port,
        workers=1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
