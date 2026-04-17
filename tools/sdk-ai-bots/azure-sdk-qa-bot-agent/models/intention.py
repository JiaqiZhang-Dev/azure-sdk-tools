"""Data models for the intention detection endpoint."""

from __future__ import annotations

from pydantic import BaseModel
from models.conversation import ConversationType
from models.chat import Message
from config.tenant_config import TenantID


class IntentionRequest(BaseModel):
    """Request for intention classification.

    The Logic App provides the message content and conversation metadata.
    The server checks saved conversation messages to determine whether
    an expert has already replied, then falls back to LLM classification.

    ``tenant_id`` is optional. When provided, the classifier is told the
    tenant's domain scope so it can correctly treat messages that fall
    inside that tenant's coverage as in-scope — even when they would be
    off-topic for the default Azure SDK bot. This matters for
    domain-specific tenants like ``digital_avatar_jay_parikh``, where
    broader strategy questions are explicitly in-scope.
    """

    message: Message
    conversation_id: str | None = None
    conversation_type: ConversationType | None = None
    tenant_id: TenantID | None = None


class IntentionResponse(BaseModel):
    """Result of intention classification."""

    should_respond: bool
    reason: str
