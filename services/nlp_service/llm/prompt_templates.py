from langchain_core.prompts import ChatPromptTemplate

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful assistant that answers questions 
based ONLY on the provided document context.
If the answer is not in the context, say "I don't have enough 
information in the document to answer this."

Context:
{context}
""",
        ),
        ("human", "{question}"),
    ]
)

SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert summarizer. Summarize the following "
            "document clearly and concisely in {language}.",
        ),
        ("human", "{text}"),
    ]
)

CLASSIFY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Classify the document into one of these categories:
[invoice, contract, report, research_paper, legal, other]
Return ONLY the category name, nothing else.""",
        ),
        ("human", "{text}"),
    ]
)
