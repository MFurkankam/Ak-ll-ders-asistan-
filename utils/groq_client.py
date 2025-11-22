import os
from typing import List, Dict, Any, Optional
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

class GroqClient:
    """Groq API istemcisi - Cloud LLM entegrasyonu"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY bulunamadı! Lütfen API anahtarınızı ayarlayın.")
        
        # Groq client oluştur
        self.client = Groq(api_key=self.api_key)
        
        # LangChain Groq LLM oluştur
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )
    
    def generate_summary(
        self, 
        context: str, 
        detail_level: str = "orta"
    ) -> str:
        """Ders notlarını özetle"""
        
        detail_instructions = {
            "kısa": "Çok kısa ve öz bir özet yap (3-5 madde)",
            "orta": "Orta uzunlukta, ana noktaları kapsayan bir özet yap",
            "detaylı": "Detaylı ve kapsamlı bir özet yap, önemli tüm noktaları dahil et"
        }
        
        instruction = detail_instructions.get(detail_level, detail_instructions["orta"])
        
        prompt_template = """Aşağıdaki ders notlarını Türkçe olarak özetle.

{instruction}

Ders Notları:
{context}

ÖZET:"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"context": context, "instruction": instruction})
            return result.content.strip()
        except Exception as e:
            return f"Özet oluşturulurken hata: {str(e)}"
    
    def generate_quiz(
        self, 
        context: str, 
        num_questions: int = 5
    ) -> List[Dict[str, Any]]:
        """Ders notlarından quiz soruları oluştur"""
        
        prompt_template = """Aşağıdaki ders notlarından {num_questions} adet çoktan seçmeli soru oluştur.

Her soru için:
- Soru metni (Türkçe)
- 4 seçenek (A, B, C, D)
- Doğru cevap (A, B, C veya D)
- Kısa açıklama

Ders Notları:
{context}

Lütfen aşağıdaki formatta yanıt ver:

SORU 1:
Soru: [Soru metni]
A) [Seçenek A]
B) [Seçenek B]
C) [Seçenek C]
D) [Seçenek D]
Doğru Cevap: [A/B/C/D]
Açıklama: [Kısa açıklama]

SORU 2:
...
"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"context": context, "num_questions": num_questions})
            return self._parse_quiz_response(result.content)
        except Exception as e:
            return [{"error": f"Quiz oluşturulurken hata: {str(e)}"}]
    
    def _parse_quiz_response(self, response: str) -> List[Dict[str, Any]]:
        """Quiz yanıtını parse et"""
        questions = []
        current_question = {}
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('SORU ') or line.startswith('Soru:'):
                if current_question and 'question' in current_question:
                    questions.append(current_question)
                current_question = {}
                
                if line.startswith('Soru:'):
                    current_question['question'] = line.replace('Soru:', '').strip()
            
            elif line.startswith('Soru:') and 'question' not in current_question:
                current_question['question'] = line.replace('Soru:', '').strip()
            
            elif line.startswith('A)'):
                current_question['A'] = line[2:].strip()
            elif line.startswith('B)'):
                current_question['B'] = line[2:].strip()
            elif line.startswith('C)'):
                current_question['C'] = line[2:].strip()
            elif line.startswith('D)'):
                current_question['D'] = line[2:].strip()
            
            elif line.startswith('Doğru Cevap:'):
                answer = line.replace('Doğru Cevap:', '').strip()
                current_question['correct_answer'] = answer.upper()[0] if answer else 'A'
            
            elif line.startswith('Açıklama:'):
                current_question['explanation'] = line.replace('Açıklama:', '').strip()
        
        # Son soruyu ekle
        if current_question and 'question' in current_question:
            questions.append(current_question)
        
        # Geçerli sorular döndür (en az soru metni ve 2 seçenek olmalı)
        valid_questions = []
        for q in questions:
            if 'question' in q and ('A' in q or 'B' in q):
                # Eksik seçenekleri varsayılan değerlerle doldur
                q.setdefault('A', 'Seçenek mevcut değil')
                q.setdefault('B', 'Seçenek mevcut değil')
                q.setdefault('C', 'Seçenek mevcut değil')
                q.setdefault('D', 'Seçenek mevcut değil')
                q.setdefault('correct_answer', 'A')
                q.setdefault('explanation', 'Açıklama mevcut değil')
                valid_questions.append(q)
        
        return valid_questions if valid_questions else [{"error": "Quiz parse edilemedi"}]
    
    def answer_question(
        self, 
        question: str, 
        context_docs: List[Document]
    ) -> str:
        """Kullanıcı sorusuna ders notlarından yararlanarak cevap ver"""
        
        # Dokümanlardan bağlam oluştur
        context = "\n\n".join([doc.page_content for doc in context_docs])
        
        prompt_template = """Aşağıdaki ders notlarını kullanarak soruya Türkçe cevap ver.

Ders Notları:
{context}

Soru: {question}

Cevap:"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"context": context, "question": question})
            return result.content.strip()
        except Exception as e:
            return f"Cevap oluşturulurken hata: {str(e)}"
    
    def chat(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Sohbet modunda cevap ver"""
        
        messages = []
        
        # Geçmiş mesajları ekle
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Yeni mesajı ekle
        messages.append({
            "role": "user",
            "content": message
        })
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Cevap oluşturulurken hata: {str(e)}"
