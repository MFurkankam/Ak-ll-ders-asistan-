import io

import pytest
from docx import Document as DocxDocument

from utils.rag_processor import RAGProcessor


def test_extract_text_from_txt(tmp_path):
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    data = "Merhaba dunya"
    buf = io.BytesIO(data.encode("utf-8"))
    assert rag.extract_text_from_txt(buf) == data


def test_extract_text_from_docx(tmp_path):
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    doc = DocxDocument()
    doc.add_paragraph("Docx text")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    text = rag.extract_text_from_docx(buf)
    assert "Docx text" in text


def test_extract_text_from_pdf(tmp_path):
    fitz = pytest.importorskip("fitz")
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello PDF")
    pdf_bytes = doc.write()
    buf = io.BytesIO(pdf_bytes)
    text = rag.extract_text_from_pdf(buf)
    assert "Hello PDF" in text


def test_process_document_chunking(monkeypatch, tmp_path):
    monkeypatch.setenv("RAG_CHUNK_SIZE", "10")
    monkeypatch.setenv("RAG_CHUNK_OVERLAP", "2")
    rag = RAGProcessor(persist_directory=str(tmp_path / "chroma"))
    data = "abcdefghijklmnopqrstuvwxyz"
    buf = io.BytesIO(data.encode("utf-8"))
    docs = rag.process_document(buf, "sample.txt")
    assert len(docs) == 3
    assert docs[0].metadata.get("source") == "sample.txt"
    assert [d.metadata.get("chunk_id") for d in docs] == [0, 1, 2]
