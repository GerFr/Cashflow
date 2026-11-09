from __future__ import annotations

from urllib.parse import unquote

from fastapi import HTTPException, Request


async def read_limited_body(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > limit:
                raise HTTPException(status_code=413, detail="payload too large")
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid content-length") from None
    buffer = bytearray()
    async for chunk in request.stream():
        buffer.extend(chunk)
        if len(buffer) > limit:
            raise HTTPException(status_code=413, detail="payload too large")
    return bytes(buffer)


def clean_filename(header: str | None) -> str:
    """Decode the URL-encoded X-Filename header and reject empty or control-character names."""
    if not header:
        raise HTTPException(status_code=400, detail="X-Filename header required")
    filename = unquote(header)
    if not filename or any(ord(char) < 32 or ord(char) == 127 for char in filename):
        raise HTTPException(status_code=400, detail="invalid X-Filename header")
    return filename
