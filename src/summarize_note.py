from hashlib import md5

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.clients.openai import (
    AsyncOpenAI,
    get_openai_client,
    call_openai_parsed,
)
from src.clients.redis import Redis, get_redis_client


router = APIRouter()


class Note(BaseModel):
    text: str


class NoteSummary(BaseModel):
    summary: str
    layperson_paraphrase: str
    keywords: list[str]
    patient_chief_complaint: str | None = None


PROMPT = """\
You are a highly trained medical expert with 25 years of experience. 
Your task is to extract and structure critical information from the provided medical document.
Be concise, precise, and factual in your extractions.
Avoid non-factual information, exposition, and hyperbole.

Extract the following information in the specified format exactly:
`summary`: str — A ~100 word summary of the document.
`layperson_paraphrase`: str — A ~50-100 word layperson's paraphrase of the summary.
`keywords`: list[str] — A list of keywords to help categorize the document. You can be generous with the number of keywords, up to around 25.
`patient_chief_complaint`: str | None — One sentence about the patient's chief complaint, if available.
"""


@router.post(
    "/summarize_note",
    response_model=NoteSummary,
    description="Extract structured information from a medical note, namely a summary, a layperson's paraphrase, a list of keywords, and the patient's chief complaint.",
)
async def summarize_note(
    request_body: Note,
    redis_client: Redis = Depends(get_redis_client),
    openai_client: AsyncOpenAI = Depends(get_openai_client),
):
    note = request_body.text
    # Basic validation
    # TODO - Stronger validation around note content to prevent hallucinations
    if len(note) < 200:
        raise HTTPException(
            status_code=400,
            detail="Note must be at least 200 characters long.",
        )

    # Check cache if note has been summarized before
    note_hash = md5(note.encode()).hexdigest()
    cached_note = await redis_client.get(note_hash)
    if cached_note:
        print(f'Cache hit for note: "{note[:75]}"...')
        return NoteSummary.model_validate_json(cached_note)

    try:
        note_summary: NoteSummary = await call_openai_parsed(
            system_content=PROMPT,
            user_content=note,
            response_pydantic_model=NoteSummary,
            openai_client=openai_client,
        )
        await redis_client.set(note_hash, note_summary.model_dump_json())
        return note_summary

    except Exception as e:
        error = f"Error summarizing note: {e}"
        print(error)
        raise HTTPException(
            status_code=500,
            detail=error,
        )
