import uuid
from shared.db.models.document import Document, DocumentStatus
from shared.db.models.user import User


def test_document_status_values():
    assert DocumentStatus.PENDING == "pending"
    assert DocumentStatus.PROCESSING == "processing"
    assert DocumentStatus.DONE == "done"
    assert DocumentStatus.FAILED == "failed"


def test_user_model_tablename():
    assert User.__tablename__ == "users"


def test_document_model_tablename():
    assert Document.__tablename__ == "documents"


def test_document_default_status():
    doc = Document(
    id=uuid.uuid4(),
    owner_id=uuid.uuid4(),
    filename="test.pdf",
    status=DocumentStatus.PENDING,
)

    assert doc.status == DocumentStatus.PENDING