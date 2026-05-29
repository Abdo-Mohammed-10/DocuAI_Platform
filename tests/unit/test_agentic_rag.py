import pytest
from services.nlp_service.pipelines.agentic_rag import should_retry


def test_should_retry_when_not_relevant_and_no_retries():
    state = {"is_relevant": False, "retry_count": 0}
    assert should_retry(state) == "rewrite_query"


def test_should_generate_when_relevant():
    state = {"is_relevant": True, "retry_count": 0}
    assert should_retry(state) == "generate_answer"


def test_should_generate_when_max_retries_reached():
    state = {"is_relevant": False, "retry_count": 2}
    assert should_retry(state) == "generate_answer"


def test_should_retry_once_more_if_retry_count_is_1():
    state = {"is_relevant": False, "retry_count": 1}
    assert should_retry(state) == "rewrite_query"