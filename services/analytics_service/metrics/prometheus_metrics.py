from prometheus_client import Counter, Histogram, Gauge

# ── LLM Metrics ──────────────────────────────────────────────
llm_requests_total = Counter(
    "llm_requests_total",
    "Total number of LLM requests",
    ["service", "endpoint", "status"],
)

llm_latency_seconds = Histogram(
    "llm_latency_seconds",
    "LLM request latency in seconds",
    ["service", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30],
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total tokens used",
    ["service", "token_type"],  # token_type: input / output
)

llm_cost_usd_total = Counter(
    "llm_cost_usd_total",
    "Estimated cumulative LLM cost in USD",
    ["service"],
)

rag_retries_total = Counter(
    "rag_retries_total",
    "Number of LangGraph query rewrites/retries",
)

# ── Document Processing Metrics ─────────────────────────────
documents_processed_total = Counter(
    "documents_processed_total",
    "Total documents processed",
    ["status"],  # done / failed
)

document_processing_seconds = Histogram(
    "document_processing_seconds",
    "Time to process a document end-to-end",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

chunks_created_total = Counter(
    "chunks_created_total",
    "Total chunks created from documents",
)

embeddings_created_total = Counter(
    "embeddings_created_total",
    "Total embeddings generated",
)

# ── Vector Search Metrics ───────────────────────────────────
vector_search_latency_seconds = Histogram(
    "vector_search_latency_seconds",
    "pgvector similarity search latency",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1],
)

vector_search_similarity_score = Histogram(
    "vector_search_similarity_score",
    "Distribution of top-1 similarity scores returned",
    buckets=[0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# ── Active Sessions Gauge ───────────────────────────────────
active_chat_sessions = Gauge(
    "active_chat_sessions",
    "Number of active chat sessions",
)