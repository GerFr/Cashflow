from __future__ import annotations

from importlib.metadata import version
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Query, Request

from cashflow.connectors.engine import ConnectorError, parse
from cashflow.service.schemas import ConnectorInfo, Health
from cashflow.utils.config import get_settings
from cashflow.utils.http import clean_filename, read_limited_body
from cashflow.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
def health(request: Request) -> Health:
    return Health(status="ok", version=version("cashflow"), connectors=len(request.app.state.connectors))


@router.get("/connectors")
def list_connectors(request: Request) -> list[ConnectorInfo]:
    return [ConnectorInfo.from_definition(d) for d in request.app.state.connectors.definitions.values()]


@router.post("/parse")
async def parse_file(
    request: Request,
    connector: Annotated[str | None, Query(description="Connector id; detected from the file if omitted.")] = None,
    filename: Annotated[str | None, Header(alias="X-Filename")] = None,
) -> dict[str, Any]:
    """Parse a bank export (raw bytes in the body) into canonical transaction records. Nothing is stored."""
    name = clean_filename(filename)
    content = await read_limited_body(request, get_settings().max_upload_mb * 1024 * 1024)

    registry = request.app.state.connectors
    if connector is not None:
        definition = registry.get(connector)
        if definition is None:
            raise HTTPException(status_code=404, detail=f"unknown connector {connector!r}")
    else:
        definition = registry.detect(content, name)
        if definition is None:
            raise HTTPException(status_code=422, detail="no connector recognises this file")

    try:
        result = parse(definition, content)
    except (ConnectorError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"{definition['id']}: {exc}") from None
    logger.info("parsed connector=%s bytes=%d rows=%d", definition["id"], len(content), len(result.transactions))
    return result.to_json()
