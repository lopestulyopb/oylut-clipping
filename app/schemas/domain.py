from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=2, max_length=150, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    logo_url: HttpUrl | None = None


class Client(ClientCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MonitoringCreate(BaseModel):
    client_id: UUID
    name: str = Field(min_length=2, max_length=150)


class Monitoring(MonitoringCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TermCreate(BaseModel):
    monitoring_id: UUID
    text: str = Field(min_length=2, max_length=200)
    is_primary: bool = False


class Term(TermCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime


class SearchCreate(BaseModel):
    monitoring_id: UUID
    period_hours: int = Field(default=24, ge=1, le=720)


class Search(SearchCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: SearchStatus
    started_at: datetime
    finished_at: datetime | None = None
    result_count: int = 0
    error_message: str | None = None
