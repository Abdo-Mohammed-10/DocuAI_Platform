import uuid
from datetime import datetime

from pydantic import BaseModel

from shared.db.models.document import DocumentStatus


class DocumentsUploadedResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    file_size: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
