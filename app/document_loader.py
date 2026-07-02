import os
import re
from typing import List

from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    UnstructuredXMLLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def _looks_like_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) < 3:
        return False
    if len(stripped) > 60:
        return False
    if not stripped[0].isupper():
        return False
    if stripped.endswith((".", ",", ";", ":", "!", "?")):
        return False
    if len(stripped.split()) > 8:
        return False
    return True


def _split_into_sections(text: str) -> List[str]:
    lines = text.split("\n")
    heading_indices = [
        i for i, line in enumerate(lines) if _looks_like_heading(line)
    ]
    if not heading_indices:
        return [text]
    sections = []
    for idx, h_idx in enumerate(heading_indices):
        start = h_idx
        end = heading_indices[idx + 1] if idx + 1 < len(heading_indices) else len(lines)
        section_lines = lines[start:end]
        section_text = "\n".join(section_lines).strip()
        if section_text:
            sections.append(section_text)
    return sections


def split_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    result = []
    for doc in docs:
        sections = _split_into_sections(doc.page_content)
        for section in sections:
            if len(section) <= CHUNK_SIZE:
                result.append(Document(page_content=section, metadata=doc.metadata.copy()))
            else:
                sub_docs = splitter.split_documents(
                    [Document(page_content=section, metadata=doc.metadata.copy())]
                )
                result.extend(sub_docs)
    return result


def load_document(file_path: str) -> List[Document]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".csv":
        loader = CSVLoader(file_path)
    elif ext == ".xml":
        loader = UnstructuredXMLLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()


def load_and_split(file_path: str) -> List[Document]:
    docs = load_document(file_path)
    return split_documents(docs)
