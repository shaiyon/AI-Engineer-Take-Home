from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.clients.qdrant import maybe_initialize_collection, DOCUMENTS_COLLECTION_NAME
from src.db import Base, engine
from src.documents import router as documents_router
from src.summarize_note import router as summarize_note_router
from src.answer_question import router as answer_question_router
from src.seed import router as seed_documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await maybe_initialize_collection(DOCUMENTS_COLLECTION_NAME)
    # Maybe initialize postgres tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

# Part 1: Documents
app.include_router(documents_router, prefix="/documents", tags=["documents"])
app.include_router(seed_documents_router, tags=["seed"])

# Part 2: LLM
app.include_router(summarize_note_router, tags=["summarize note"])

# Part 3: RAG
app.include_router(answer_question_router, tags=["answer question"])
