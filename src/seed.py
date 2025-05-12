from pathlib import Path

from fastapi import APIRouter, Depends

from src.clients.openai import get_openai_client, AsyncOpenAI
from src.clients.qdrant import get_qdrant_client, AsyncQdrantClient
from src.db import get_db, Session
from src.documents import create_document, CreateDocument

router = APIRouter()


@router.post("/seed", status_code=201)
async def seed_documents(
    db: Session = Depends(get_db),
    openai_client: AsyncOpenAI = Depends(get_openai_client),
    qdrant_client: AsyncQdrantClient = Depends(get_qdrant_client),
):
    notes_dir = Path("./notes")
    notes_found: list[str] = []

    if notes_dir.exists():
        for note_file in notes_dir.glob("*.txt"):
            with open(note_file, "r") as f:
                content = f.read().strip()

            notes_found.append({"filename": note_file.name, "content": content})

    if not notes_found:
        return {"message": "No notes found to seed."}

    results = []
    for note in notes_found:
        lines = note["content"].split("\n")
        title = lines[0] if lines else note["filename"]
        content = "\n".join(lines[1:]) if len(lines) > 1 else ""

        doc = CreateDocument(title=title, content=content)
        result = await create_document(
            request_body=doc,
            add_to_vector_db=True,
            openai_client=openai_client,
            qdrant_client=qdrant_client,
            db=db,
        )
        results.append(
            {"id": result.id, "title": result.title, "source": note["filename"]}
        )

    return {
        "message": f"Seeded {len(results)} documents successfully",
        "documents": results,
    }
