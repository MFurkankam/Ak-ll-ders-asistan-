from langchain_core.documents import Document

from utils.rag_processor import RAGProcessor


def test_search_documents_deterministic(tmp_path):
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    docs = [
        Document(page_content="Alpha beta gamma", metadata={"source": "a.txt", "chunk_id": 0}),
        Document(page_content="Delta epsilon zeta", metadata={"source": "b.txt", "chunk_id": 0}),
    ]
    rag.add_documents_to_vectorstore(docs, collection_name="search_test")
    results = rag.search_documents("alpha", k=1, collection_name="search_test")
    assert len(results) == 1
    assert "Alpha" in results[0].page_content or "alpha" in results[0].page_content
