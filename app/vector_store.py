import os
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, COLLECTION_NAME


_vector_store: Optional[Chroma] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def get_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is None:
        persist_dir = os.path.abspath(CHROMA_PERSIST_DIR)
        os.makedirs(persist_dir, exist_ok=True)
        embeddings = get_embeddings()
        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )
    return _vector_store


def add_documents(docs: List[Document]) -> None:
    store = get_vector_store()
    store.add_documents(docs)


def search(query: str, k: int = 4) -> List[Document]:
    store = get_vector_store()
    return store.similarity_search(query, k=k)
