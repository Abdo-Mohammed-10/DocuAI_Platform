import mlflow

from services.nlp_service.pipelines.rag_pipeline import RAGResult


class LLMTracker:
    def __init__(self, experiment_name: str = "DocuAI-rag"):
        mlflow.set_experiment(experiment_name)

    def log_rag_call(
        self,
        question: str,
        result: RAGResult,
        document_id: str,
    ):
        with mlflow.start_run(nested=True):
            mlflow.log_params(
                {
                    "document_id": document_id,
                    "question_length": len(question),
                    "chunks_used": len(result.source_chunks),
                }
            )
            mlflow.log_metrics(
                {
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "total_tokens": result.input_tokens + result.output_tokens,
                    "estimated_cost_usd": (
                        result.input_tokens * 0.00000015
                        + result.output_tokens * 0.0000006
                    ),
                }
            )