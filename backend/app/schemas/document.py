from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator


class DocumentResponse(BaseModel):
    id: str
    expense_id: int
    original_filename: str
    detected_mime_type: str
    file_size_bytes: int
    publication_status: Literal['private', 'published']
    created_at: datetime
    is_redacted_version: bool
    duplicate_in_project: bool | None = None


class PublishDocument(BaseModel):
    model_config = ConfigDict(extra='forbid')
    redaction_reviewed: Literal[True]

    @field_validator('redaction_reviewed', mode='before')
    @classmethod
    def explicit_boolean_approval(cls, value):
        if value is not True:
            raise ValueError('Explicit human review approval is required')
        return value


class DownloadResponse(BaseModel):
    url: str
    expires_in: Literal[60] = 60
