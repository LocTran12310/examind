import uuid

from pydantic import BaseModel, Field


class AiModelIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider: str
    model: str = Field(min_length=1, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)
    capabilities: list[str] = ["text"]
    is_free: bool = True
    enabled: bool = True


class AiModelUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    provider: str | None = None
    model: str | None = Field(default=None, max_length=120)
    base_url: str | None = Field(default=None, max_length=300)
    api_key: str | None = Field(default=None, max_length=500)  # "" clears the key
    capabilities: list[str] | None = None
    is_free: bool | None = None
    enabled: bool | None = None


class AiModelOut(BaseModel):
    id: uuid.UUID
    name: str
    provider: str
    model: str
    base_url: str | None
    capabilities: list[str]
    is_free: bool
    enabled: bool
    system: bool
    has_key: bool
    editable: bool


class DiscoverIn(BaseModel):
    base_url: str | None = None


class TestResult(BaseModel):
    ok: bool
    latency_ms: int | None = None
    error: str | None = None
    sample: str | None = None
