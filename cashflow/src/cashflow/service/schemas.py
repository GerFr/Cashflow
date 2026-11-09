from __future__ import annotations

from pydantic import BaseModel

from cashflow.connectors.registry import Connector


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
    def from_connector(cls, connector: Connector) -> ConnectorInfo:
        return cls(
            id=connector.id,
            name=connector.name,
            version=connector.version,
            status=connector.status,
            institution=connector.institution,
        )
