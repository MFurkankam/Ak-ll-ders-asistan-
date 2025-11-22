import os
import tempfile
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import PyPDF2
from docx import Document as DocxDocument

class RAGProcessor:
    """RAG işleme sınıfı - ChromaDB ile yerel vektör veritabanı yönetimi"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # ChromaDB istemcisini başlat
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        # Text splitter oluştur
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def extract_text_from_pdf(self, pdf_file) -> str:
        """PDF dosyasından metin çıkar"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"PDF okuma hatası: {str(e)}")
    
    def extract_text_from_docx(self, docx_file) -> str:
        """DOCX dosyasından metin çıkar"""
        try:
            doc = DocxDocument(docx_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"DOCX okuma hatası: {str(e)}")
    
    def extract_text_from_txt(self, txt_file) -> str:
        """TXT dosyasından metin çıkar"""
        try:
            return txt_file.read().decode('utf-8')
        except Exception as e:
            raise Exception(f"TXT okuma hatası: {str(e)}")
    
    def process_document(self, file, filename: str) -> List[Document]:
        """Dosyayı işle ve parçalara ayır"""
        # Dosya türüne göre metin çıkar
        file_extension = filename.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            text = self.extract_text_from_pdf(file)
        elif file_extension == 'docx':
            text = self.extract_text_from_docx(file)
        elif file_extension == 'txt':
            text = self.extract_text_from_txt(file)
        else:
            raise ValueError(f"Desteklenmeyen dosya türü: {file_extension}")
        
        # Metni parçalara ayır
        chunks = self.text_splitter.split_text(text)
        
        # Document nesneleri oluştur
        documents = [
            Document(
                page_content=chunk,
                metadata={"source": filename, "chunk_id": i}
            )
            for i, chunk in enumerate(chunks)
        ]
        
        return documents
    
    def add_documents_to_vectorstore(
        self, 
        documents: List[Document], 
        collection_name: str = "ders_notlari"
    ) -> Chroma:
        """Dokümanları vektör veritabanına ekle"""
        try:
            # Mevcut koleksiyonu al veya yeni oluştur
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Dokümanları ekle
            vectorstore.add_documents(documents)
            
            # Veritabanını kalıcı hale getir
            vectorstore.persist()
            
            return vectorstore
        except Exception as e:
            raise Exception(f"Vektör veritabanına ekleme hatası: {str(e)}")
    
    def get_vectorstore(self, collection_name: str = "ders_notlari") -> Optional[Chroma]:
        """Mevcut vektör veritabanını al"""
        try:
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            return vectorstore
        except Exception as e:
            return None
    
    def search_documents(
        self, 
        query: str, 
        k: int = 4,
        collection_name: str = "ders_notlari"
    ) -> List[Document]:
        """Sorguya göre en ilgili dokümanları bul"""
        vectorstore = self.get_vectorstore(collection_name)
        if vectorstore is None:
            return []
        
        try:
            docs = vectorstore.similarity_search(query, k=k)
            return docs
        except Exception as e:
            return []
    
    def get_all_sources(self, collection_name: str = "ders_notlari") -> List[str]:
        """Veritabanındaki tüm kaynak dosyaları listele"""
        vectorstore = self.get_vectorstore(collection_name)
        if vectorstore is None:
            return []
        
        try:
            # Koleksiyondaki tüm metadataları al
            collection = vectorstore._collection
            all_data = collection.get()
            
            # Benzersiz kaynak dosyaları bul
            sources = set()
            if all_data and 'metadatas' in all_data:
                for metadata in all_data['metadatas']:
                    if metadata and 'source' in metadata:
                        sources.add(metadata['source'])
            
            return sorted(list(sources))
        except Exception as e:
            return []
    
    def delete_collection(self, collection_name: str = "ders_notlari"):
        """Koleksiyonu sil"""
        try:
            self.chroma_client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            return False
