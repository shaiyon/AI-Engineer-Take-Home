from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from src.clients.openai import AsyncOpenAI, get_openai_client, get_openai_embedding
from src.clients.qdrant import (
    AsyncQdrantClient,
    get_qdrant_client,
    DOCUMENTS_COLLECTION_NAME,
)
from src.db import get_db, Session, DocumentModel

# from pydantic import Field

router = APIRouter()


class Document(BaseModel):
    id: int
    title: str
    content: str
    in_vector_db: bool
    created_at: str
    updated_at: str


class CreateDocument(BaseModel):
    title: str
    content: str


class UpdateDocument(BaseModel):
    title: str | None = None
    content: str | None = None


@router.get("", response_model=list[Document])
def get_documents(db: Session = Depends(get_db)):
    db_documents = db.query(DocumentModel).all()
    return db_documents


@router.get("/{document_id}", response_model=Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    db_document = (
        db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    )

    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return db_document


@router.post("", response_model=Document, status_code=201)
async def create_document(
    request_body: CreateDocument,
    add_to_vector_db: bool = Query(False),
    openai_client: AsyncOpenAI = Depends(get_openai_client),
    qdrant_client: AsyncQdrantClient = Depends(get_qdrant_client),
    db: Session = Depends(get_db),
) -> Document:
    db_document = DocumentModel(
        title=request_body.title,
        content=request_body.content,
        in_vector_db=add_to_vector_db,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    if add_to_vector_db:
        text = f"**{db_document.title}**\n\n{db_document.content}"
        embedding: list[float] = await get_openai_embedding(text, openai_client)

        await qdrant_client.upsert(
            collection_name=DOCUMENTS_COLLECTION_NAME,
            points=[
                {
                    "id": db_document.id,
                    "vector": embedding,
                    "payload": {
                        "title": db_document.title,
                        "content": db_document.content,
                    },
                }
            ],
        )

    # TODO - handle rollback on error to prevent state mismatch between dbs
    return db_document


@router.patch("/{document_id}", response_model=Document)
def update_document(
    document_id: int, request_body: UpdateDocument, db: Session = Depends(get_db)
):
    db_document = (
        db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    )

    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = request_body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_document, key, value)

    db.commit()
    db.refresh(db_document)
    return db_document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    db_document = (
        db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    )

    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(db_document)
    db.commit()
    return None
