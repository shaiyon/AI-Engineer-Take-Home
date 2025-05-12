import os

from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams, Distance

load_dotenv()

DOCUMENTS_COLLECTION_NAME = "documents"
EMBEDDING_DIMS = 1536

_qdrant_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(host=os.getenv("QDRANT_HOST"))

    return _qdrant_client


async def maybe_initialize_collection(
    collection_name: str = DOCUMENTS_COLLECTION_NAME, vector_size: int = EMBEDDING_DIMS
):
    client = get_qdrant_client()
    collections = await client.get_collections()
    if collection_name not in {
        collection.name for collection in collections.collections
    }:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
