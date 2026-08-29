"""Response models for health/status endpoints.

These are intentionally minimal. Domain models for odds data will be
introduced once the normalization pipeline is implemented.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class StatusResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str
