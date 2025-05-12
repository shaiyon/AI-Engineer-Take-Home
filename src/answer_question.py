from textwrap import dedent

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from src.clients.openai import (
    AsyncOpenAI,
    get_openai_client,
    call_openai_parsed,
    get_openai_embedding,
)
from src.clients.qdrant import (
    DOCUMENTS_COLLECTION_NAME,
    AsyncQdrantClient,
    get_qdrant_client,
)

router = APIRouter()


class Question(BaseModel):
    query: str


class LLMAnswer(BaseModel):
    answer: str | None
    document_ids: list[int] | None


class AnswerDocument(BaseModel):
    id: int
    title: str
    content: str


class Answer(BaseModel):
    answer: str
    documents: list[AnswerDocument]


PROMPT = """\
You are a highly trained medical expert with 25 years of experience. 
Your task is to answer a question based ONLY from the provided list of medical documents.
Be concise, precise, and factual in your extractions.
Avoid non-factual information, exposition, and hyperbole.
If you cannot confirm with absolute certainty the relationship between the question and a document, you may NOT reference it.
You may NOT link information about a generic individual to a named inividual.

Extract the following information in the specified format exactly:
`answer`: str | None — The answer to the user's question, if it is able to be discerned from the documents.
`document_ids`: list[int] | None  — A list of integer ids that were highly relevant to and used in answering the question.
"""


@router.post(
    "/answer_question",
    response_model=Answer,
    description="Answer a question based on documents stored inside the application's vector database.",
)
async def answer_question(
    request_body: Question,
    top_k: int = Query(3, ge=1, le=10),
    openai_client: AsyncOpenAI = Depends(get_openai_client),
    qdrant_client: AsyncQdrantClient = Depends(get_qdrant_client),
):
    query_embedding: list[float] = await get_openai_embedding(
        request_body.query, openai_client
    )

    search_results = await qdrant_client.search(
        collection_name=DOCUMENTS_COLLECTION_NAME,
        query_vector=query_embedding,
        # score_threshold=0.7,  # Adjust as needed
        limit=top_k,
    )
    if not search_results:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found for the given question.",
        )

    documents = {
        int(result.id): {
            "title": str(result.payload["title"]),
            "content": str(result.payload["content"]),
        }
        for result in search_results
    }
    formatted_docs = "\n".join(
        [
            f"<document id={doc_id}><title>{doc['title']}</title><content>{doc['content']}</content></document>"
            for doc_id, doc in documents.items()
        ]
    )
    question_and_documents = dedent(
        f"""\
        <question>{request_body.query}</question>
        <documents>{formatted_docs}</documents>"""
    )

    try:
        llm_answer: LLMAnswer = await call_openai_parsed(
            system_content=PROMPT,
            user_content=question_and_documents,
            response_pydantic_model=LLMAnswer,
            openai_client=openai_client,
        )
    except Exception as e:
        error = f"Error answering question: {e}"
        print(error)
        raise HTTPException(
            status_code=500,
            detail=error,
        )

    # We could also retry if no answer was extracted. However,
    # this could lead to false positives and hallucinations.
    if llm_answer.answer is None or llm_answer.document_ids is None:
        raise HTTPException(
            status_code=404,
            detail="No answer was able to be generated for the given question.",
        )

    return Answer(
        answer=llm_answer.answer,
        documents=[
            AnswerDocument(
                id=document_id,
                title=documents[document_id]["title"],
                content=documents[document_id]["content"],
            )
            for document_id in llm_answer.document_ids
        ],
    )
