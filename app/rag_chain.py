from typing import Dict

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import GOOGLE_API_KEY
from app.vector_store import get_vector_store


_system_prompt = (
    "You are a helpful assistant for answering questions using the provided documents. "
    "Use the following pieces of context to answer the question at the end. "
    "If you don't know the answer, just say you don't know. "
    "Keep the answer concise.\n"
    "\n"
    "CRITICAL INSTRUCTION — FACT ACCURACY AND ATTRIBUTION:\n"
    "1. Answer using ONLY the facts explicitly stated in the provided context.\n"
    "2. Do NOT merge facts that appear in different sentences, under different "
    "headings, or with different dates/names into a single claim — even if they "
    "appear in the same context block — unless the source text explicitly "
    "connects them.\n"
    "3. When a fact comes from a specific section or heading in the source, "
    "mention that section/heading in your answer (e.g. \"According to the "
    "'Key Innovations' section...\").\n"
    "4. If you are unsure whether two facts are related, treat them as separate "
    "and present them separately.\n"
    "5. Do not infer causal or temporal relationships between facts from "
    "different parts of the context.\n"
    "\n"
    "Context:\n{context}"
)

_prompt = ChatPromptTemplate.from_messages([
    ("system", _system_prompt),
    ("human", "{input}"),
])


def _get_llm():
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_gemini_api_key_here":
        raise ValueError(
            "GOOGLE_API_KEY not set. "
            "Get your free key at https://aistudio.google.com/app/apikey "
            "and add it to the .env file."
        )
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.3,
        max_retries=1,
    )


_chain = None


def get_rag_chain():
    global _chain
    if _chain is None:
        llm = _get_llm()
        store = get_vector_store()
        combine_chain = create_stuff_documents_chain(llm, _prompt)
        _chain = create_retrieval_chain(store.as_retriever(search_kwargs={"k": 4}), combine_chain)
    return _chain


def query_documents(question: str) -> Dict:
    chain = get_rag_chain()
    result = chain.invoke({"input": question})
    return {
        "answer": result["answer"],
        "source_documents": [
            {
                "content": doc.page_content[:500],
                "source": doc.metadata.get("source", "unknown"),
            }
            for doc in result["context"]
        ],
    }
