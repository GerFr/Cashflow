from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Health(BaseModel):
    status: str
    version: str
    connectors: int


class ConnectorInfo(BaseModel):
    id: str
    name: str
    version: str
    status: str
    institution: str

    @classmethod
    def from_definition(cls, definition: dict[str, Any]) -> ConnectorInfo:
        return cls(
            id=definition["id"],
            name=definition["name"],
            version=definition["version"],
            status=definition["status"],
            institution=definition["institution"]["name"],
        )
