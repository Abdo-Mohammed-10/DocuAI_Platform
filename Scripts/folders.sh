#!/bin/bash

mkdir -p \
  services/api_gateway/routers \
  services/api_gateway/schemas \
  services/api_gateway/middleware \
  services/ingestion_service/processors \
  services/ingestion_service/tasks \
  services/nlp_service/pipelines \
  services/nlp_service/llm \
  services/vector_service/embeddings \
  services/vector_service/stores \
  services/analytics_service/metrics \
  shared/db/models \
  shared/migrations/versions \
  frontend/streamlit_app/pages \
  mlops/evaluation \
  tests/unit \
  tests/integration \
  tests/e2e \
  scripts \
  .github/workflows