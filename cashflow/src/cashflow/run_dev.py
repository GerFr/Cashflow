from __future__ import annotations

from cashflow.utils.config import get_settings
from cashflow.utils.logger import setup_logging


def main() -> None:
    import uvicorn

    settings = get_settings()
    setup_logging("DEBUG")
    uvicorn.run(
        "cashflow.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
