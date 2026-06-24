import uuid
from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from services.nlp_service.llm.client import get_llm
from services.nlp_service.llm.prompt_templates import RAG_PROMPT
from shared.db.models.chunk import Chunk


# State
class RAGState(TypedDict):
    question: str
    document_id: str
    chunks: list[dict]
    context: str
    answer: str
    is_relevant: bool
    retry_count: int
    db: AsyncSession


async def retrieve_chunks(state: RAGState) -> RAGState:
    from services.vector_service.stores.pgvector_store import PGVectorStore

    db = state["db"]
    doc_id = uuid.UUID(state["document_id"])
    store = PGVectorStore()

    chunks_data = await store.similarity_search(
        query=state["question"],
        document_id=doc_id,
        db=db,
        top_k=5,
    )

    if not chunks_data:
        from sqlalchemy import select

        result = await db.execute(
            select(Chunk).where(Chunk.document_id == doc_id).limit(5)
        )
        raw = result.scalars().all()
        chunks_data = [
            {
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "content": c.content,
                "preview": c.content[:200],
                "similarity": 0.0,
            }
            for c in raw
        ]

    context = "\n\n---\n\n".join(
        [
            f"[Page {c['page_number']}] (similarity: {c.get('similarity', 0):.2f}):\n{c['content']}"  # noqa: E501
            for c in chunks_data
        ]
    )

    return {**state, "chunks": chunks_data, "context": context}


async def grade_relevance(state: RAGState) -> RAGState:
    llm = get_llm(temperature=0.0)

    messages = [
        SystemMessage(
            content=(
                "You are a grader. Given a question and context, "
                "decide if the context is sufficient to answer. "
                "Reply with ONLY 'yes' or 'no'."
            )
        ),
        HumanMessage(
            content=(
                f"Question: {state['question']}\n\n"
                f"Context: {state['context'][:1000]}"
            )
        ),
    ]

    response = await llm.ainvoke(messages)
    is_relevant = response.content.strip().lower() == "yes"

    return {**state, "is_relevant": is_relevant}


async def rewrite_query(state: RAGState) -> RAGState:
    llm = get_llm(temperature=0.7)

    messages = [
        SystemMessage(
            content=(
                "Rewrite the question to be more specific and "
                "help retrieve better document context. "
                "Return ONLY the rewritten question."
            )
        ),
        HumanMessage(content=state["question"]),
    ]

    response = await llm.ainvoke(messages)
    new_question = response.content.strip()

    return {
        **state,
        "question": new_question,
        "retry_count": state.get("retry_count", 0) + 1,
    }


async def generate_answer(state: RAGState) -> RAGState:
    llm = get_llm(temperature=0.0)
    chain = RAG_PROMPT | llm

    response = await chain.ainvoke(
        {
            "context": state["context"],
            "question": state["question"],
        }
    )

    return {**state, "answer": response.content}


# Routing
def should_retry(state: RAGState) -> Literal["rewrite_query", "generate_answer"]:
    if not state["is_relevant"] and state.get("retry_count", 0) < 2:
        return "rewrite_query"
    return "generate_answer"


def build_rag_graph() -> StateGraph:
    graph = StateGraph(RAGState)

    graph.add_node("retrieve_chunks", retrieve_chunks)
    graph.add_node("grade_relevance", grade_relevance)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("generate_answer", generate_answer)

    graph.set_entry_point("retrieve_chunks")
    graph.add_edge("retrieve_chunks", "grade_relevance")

    graph.add_conditional_edges(
        "grade_relevance",
        should_retry,
        {
            "rewrite_query": "rewrite_query",
            "generate_answer": "generate_answer",
        },
    )

    graph.add_edge("rewrite_query", "retrieve_chunks")
    graph.add_edge("generate_answer", END)

    return graph.compile()


rag_graph = build_rag_graph()
