from services.analytics_service.metrics.prometheus_metrics import (
    llm_requests_total,
    llm_latency_seconds,
    rag_retries_total,
    documents_processed_total,
    chunks_created_total,
)

def test_llm_requests_counter_increments():
    before = llm_requests_total.labels(
        service="nlp", endpoint="/ask", status="success"
    )._value.get()

    llm_requests_total.labels(
        service="nlp", endpoint="/ask", status="success"
    ).inc()

    after = llm_requests_total.labels(
        service="nlp", endpoint="/ask", status="success"
    )._value.get()

    assert after == before + 1


def test_latency_histogram_observe():
    llm_latency_seconds.labels(service="nlp", endpoint="/ask").observe(1.5)
    assert True


def test_rag_retries_counter():
    before = rag_retries_total._value.get()
    rag_retries_total.inc(2)
    after = rag_retries_total._value.get()
    assert after == before + 2


def test_documents_processed_counter():
    before = documents_processed_total.labels(status="done")._value.get()
    documents_processed_total.labels(status="done").inc()
    after = documents_processed_total.labels(status="done")._value.get()
    assert after == before + 1


def test_chunks_created_counter():
    before = chunks_created_total._value.get()
    chunks_created_total.inc(5)
    after = chunks_created_total._value.get()
    assert after == before + 5