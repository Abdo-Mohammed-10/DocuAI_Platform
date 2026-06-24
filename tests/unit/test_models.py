import uuid

from shared.db.models.document import Document, DocumentStatus
from shared.db.models.user import User


def test_document_status_values():
    assert DocumentStatus.pending == "pending"
    assert DocumentStatus.processing == "processing"
    assert DocumentStatus.done == "done"
    assert DocumentStatus.failed == "failed"


def test_user_model_tablename():
    assert User.__tablename__ == "users"


def test_document_model_tablename():
    assert Document.__tablename__ == "documents"


def test_document_default_status():
    doc = Document(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        filename="test.pdf",
        status=DocumentStatus.pending,
    )

    assert doc.status == DocumentStatus.pending
