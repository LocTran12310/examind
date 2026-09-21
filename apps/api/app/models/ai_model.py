import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, IdMixin, TimestampMixin

PROVIDERS = ("ollama", "openai", "anthropic")
CAPABILITIES = ("text", "vision")


class AiModel(IdMixin, TimestampMixin, Base):
    """A model an org (or, with organization_id NULL, every org) may use for splitting, tagging or OCR."""

    __tablename__ = "ai_models"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    provider: Mapped[str] = mapped_column(String(16))
    model: Mapped[str] = mapped_column(String(120))
    base_url: Mapped[str | None] = mapped_column(String(300))
    api_key_enc: Mapped[str | None] = mapped_column(Text)
    capabilities: Mapped[list[str]] = mapped_column(ARRAY(String(16)), default=lambda: ["text"])
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
