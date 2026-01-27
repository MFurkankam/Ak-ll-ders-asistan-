from langchain_core.documents import Document

from utils.rag_processor import RAGProcessor


def test_add_documents_to_vectorstore_smoke(tmp_path):
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    docs = [
        Document(page_content="alpha", metadata={"source": "a.txt", "chunk_id": 0}),
        Document(page_content="beta", metadata={"source": "b.txt", "chunk_id": 0}),
    ]
    collection = rag.add_documents_to_vectorstore(docs, collection_name="test_docs")
    assert collection is not None
    data = collection.get()
    assert data and "documents" in data
    assert len(data["documents"]) == 2


def test_add_documents_upsert_dedup(tmp_path):
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    docs = [
        Document(page_content="alpha", metadata={"source": "a.txt", "chunk_id": 0}),
        Document(page_content="beta", metadata={"source": "b.txt", "chunk_id": 0}),
    ]
    rag.add_documents_to_vectorstore(docs, collection_name="test_docs")
    rag.add_documents_to_vectorstore(docs, collection_name="test_docs")
    data = rag.get_collection("test_docs").get()
    assert len(data["documents"]) == 2
