from services.vector_service.embeddings.encoder import TextEncoder
from shared.db.models.chunk import EMBEDDING_DIM


def test_encode_returns_correct_dimension():
    enc = TextEncoder()
    vec = enc.encode("Hello world")
    assert len(vec) == EMBEDDING_DIM


def test_encode_returns_normalized():
    import numpy as np

    enc = TextEncoder()
    vec = np.array(enc.encode("test sentence"))
    norm = float(np.linalg.norm(vec))
    assert abs(norm - 1.0) < 1e-5


def test_encode_batch_consistent():
    enc = TextEncoder()
    single = enc.encode("machine learning")
    batch = enc.encode_batch(["machine learning", "deep learning"])
    import numpy as np

    diff = np.abs(np.array(single) - np.array(batch[0])).max()
    assert diff < 1e-5


def test_similarity_identical_texts():
    enc = TextEncoder()
    v = enc.encode("identical text")
    sim = enc.similarity(v, v)
    assert abs(sim - 1.0) < 1e-5


def test_similarity_different_texts():
    enc = TextEncoder()
    v1 = enc.encode("machine learning algorithms")
    v2 = enc.encode("cooking pasta recipe")
    sim = enc.similarity(v1, v2)
    assert sim < 0.5
