import os
import mlflow

from services.nlp_service.pipelines.rag_pipeline import RAGResult

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


class LLMTracker:
    def __init__(self, experiment_name: str = "DocuAI-rag"):
        mlflow.set_tracking_uri(MLFLOW_URI)
        mlflow.set_experiment(experiment_name)

    def log_rag_call(
        self,
        question: str,
        result,
        document_id: str,
    ):
        try:
            with mlflow.start_run(nested=True):
                mlflow.log_params({
                    "document_id": document_id,
                    "question_length": len(question),
                    "chunks_used": len(result.source_chunks),
                })
                mlflow.log_metrics({
                    "latency_ms": result.latency_ms or 0,
                    "input_tokens": result.input_tokens or 0,
                    "output_tokens": result.output_tokens or 0,
                    "total_tokens": (result.input_tokens or 0) + (result.output_tokens or 0),
                    "estimated_cost_usd": (
                        (result.input_tokens or 0) * 0.00000015
                        + (result.output_tokens or 0) * 0.0000006
                    ),
                })
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"MLflow logging failed: {e}")