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
    
    def generate_flashcards(
        self, 
        context: str, 
        num_cards: int = 10
    ) -> List[Dict[str, str]]:
        """Ders notlarından flashcard'lar oluştur"""
        
        prompt_template = """Aşağıdaki ders notlarından {num_cards} adet flashcard oluştur.

Her flashcard için:
- Ön yüz: Soru veya kavram (kısa)
- Arka yüz: Cevap veya açıklama (orta uzunlukta)

Ders Notları:
{context}

Lütfen aşağıdaki formatta yanıt ver:

KART 1:
Ön Yüz: [Soru veya kavram]
Arka Yüz: [Cevap veya açıklama]

KART 2:
...
"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({"context": context, "num_cards": num_cards})
            return self._parse_flashcard_response(result.content)
        except Exception as e:
            return [{"error": f"Flashcard oluşturulurken hata: {str(e)}"}]
    
    def _parse_flashcard_response(self, response: str) -> List[Dict[str, str]]:
        """Flashcard yanıtını parse et"""
        flashcards = []
        current_card = {}
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('KART ') or line.startswith('Ön Yüz:'):
                if current_card and 'front' in current_card:
                    flashcards.append(current_card)
                current_card = {}
                
                if line.startswith('Ön Yüz:'):
                    current_card['front'] = line.replace('Ön Yüz:', '').strip()
            
            elif line.startswith('Ön Yüz:') and 'front' not in current_card:
                current_card['front'] = line.replace('Ön Yüz:', '').strip()
            
            elif line.startswith('Arka Yüz:'):
                current_card['back'] = line.replace('Arka Yüz:', '').strip()
        
        if current_card and 'front' in current_card:
            flashcards.append(current_card)
        
        valid_flashcards = []
        for card in flashcards:
            if 'front' in card and 'back' in card:
                valid_flashcards.append(card)
        
        return valid_flashcards if valid_flashcards else [{"error": "Flashcard parse edilemedi"}]
    
    def generate_quiz(
        self, 
        context: str, 
        num_questions: int = 5,
        quiz_type: str = "multiple_choice",
        difficulty: str = "orta"
    ) -> List[Dict[str, Any]]:
        """Ders notlarından quiz soruları oluştur"""
        
        if quiz_type == "true_false":
            return self._generate_true_false_quiz(context, num_questions, difficulty)
        elif quiz_type == "fill_blank":
            return self._generate_fill_blank_quiz(context, num_questions, difficulty)
        elif quiz_type == "short_answer":
            return self._generate_short_answer_quiz(context, num_questions, difficulty)
        else:
            return self._generate_multiple_choice_quiz(context, num_questions, difficulty)
    
    def _generate_multiple_choice_quiz(
        self, 
        context: str, 
        num_questions: int = 5,
        difficulty: str = "orta"
    ) -> List[Dict[str, Any]]:
        """Çoktan seçmeli quiz oluştur"""
        
        difficulty_instructions = {
            "kolay": "Temel kavramları test eden basit sorular oluştur.",
            "orta": "Orta seviye, kavramları anlama ve uygulama gerektiren sorular oluştur.",
            "zor": "İleri seviye, analiz ve sentez gerektiren zorlayıcı sorular oluştur."
        }
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["orta"])
        
        prompt_template = """Aşağıdaki ders notlarından {num_questions} adet çoktan seçmeli soru oluştur.

{difficulty_instruction}

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
            result = chain.invoke({
                "context": context, 
                "num_questions": num_questions,
                "difficulty_instruction": difficulty_instruction
            })
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
    
    def _generate_true_false_quiz(
        self, 
        context: str, 
        num_questions: int = 5,
        difficulty: str = "orta"
    ) -> List[Dict[str, Any]]:
        """Doğru/Yanlış quiz oluştur"""
        
        difficulty_instructions = {
            "kolay": "Basit, doğrudan ifadeler kullan.",
            "orta": "Orta seviye, dikkat gerektiren ifadeler kullan.",
            "zor": "Karmaşık, ince ayrıntılar içeren ifadeler kullan."
        }
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["orta"])
        
        prompt_template = """Aşağıdaki ders notlarından {num_questions} adet Doğru/Yanlış sorusu oluştur.

{difficulty_instruction}

Her soru için:
- İfade (Türkçe)
- Doğru cevap (Doğru veya Yanlış)
- Kısa açıklama

Ders Notları:
{context}

Lütfen aşağıdaki formatta yanıt ver:

SORU 1:
İfade: [İfade metni]
Doğru Cevap: [Doğru/Yanlış]
Açıklama: [Kısa açıklama]

SORU 2:
...
"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({
                "context": context, 
                "num_questions": num_questions,
                "difficulty_instruction": difficulty_instruction
            })
            return self._parse_true_false_response(result.content)
        except Exception as e:
            return [{"error": f"Quiz oluşturulurken hata: {str(e)}"}]
    
    def _generate_fill_blank_quiz(
        self, 
        context: str, 
        num_questions: int = 5,
        difficulty: str = "orta"
    ) -> List[Dict[str, Any]]:
        """Boşluk doldurma quiz oluştur"""
        
        difficulty_instructions = {
            "kolay": "Sık kullanılan temel terimleri boşluk yap.",
            "orta": "Orta seviye kavramları boşluk yap.",
            "zor": "Teknik terimleri ve detaylı kavramları boşluk yap."
        }
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["orta"])
        
        prompt_template = """Aşağıdaki ders notlarından {num_questions} adet boşluk doldurma sorusu oluştur.

{difficulty_instruction}

Her soru için:
- Boşluklu cümle (_____ ile boşluk işaretle)
- Doğru cevap
- Kısa açıklama

Ders Notları:
{context}

Lütfen aşağıdaki formatta yanıt ver:

SORU 1:
Cümle: [Boşluklu cümle metni]
Doğru Cevap: [Doğru kelime/kelimeler]
Açıklama: [Kısa açıklama]

SORU 2:
...
"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({
                "context": context, 
                "num_questions": num_questions,
                "difficulty_instruction": difficulty_instruction
            })
            return self._parse_fill_blank_response(result.content)
        except Exception as e:
            return [{"error": f"Quiz oluşturulurken hata: {str(e)}"}]
    
    def _generate_short_answer_quiz(
        self, 
        context: str, 
        num_questions: int = 5,
        difficulty: str = "orta"
    ) -> List[Dict[str, Any]]:
        """Kısa cevap quiz oluştur"""
        
        difficulty_instructions = {
            "kolay": "Basit, kısa cevaplı sorular sor.",
            "orta": "Açıklama gerektiren orta seviye sorular sor.",
            "zor": "Detaylı analiz ve açıklama gerektiren sorular sor."
        }
        difficulty_instruction = difficulty_instructions.get(difficulty, difficulty_instructions["orta"])
        
        prompt_template = """Aşağıdaki ders notlarından {num_questions} adet kısa cevaplı soru oluştur.

{difficulty_instruction}

Her soru için:
- Soru metni (Türkçe)
- Örnek cevap
- Anahtar kelimeler

Ders Notları:
{context}

Lütfen aşağıdaki formatta yanıt ver:

SORU 1:
Soru: [Soru metni]
Örnek Cevap: [Örnek cevap]
Anahtar Kelimeler: [kelime1, kelime2, kelime3]

SORU 2:
...
"""

        prompt = PromptTemplate.from_template(prompt_template)
        
        try:
            chain = prompt | self.llm
            result = chain.invoke({
                "context": context, 
                "num_questions": num_questions,
                "difficulty_instruction": difficulty_instruction
            })
            return self._parse_short_answer_response(result.content)
        except Exception as e:
            return [{"error": f"Quiz oluşturulurken hata: {str(e)}"}]
    
    def _parse_true_false_response(self, response: str) -> List[Dict[str, Any]]:
        """Doğru/Yanlış quiz yanıtını parse et"""
        questions = []
        current_question = {}
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('SORU ') or line.startswith('İfade:'):
                if current_question and 'statement' in current_question:
                    questions.append(current_question)
                current_question = {'type': 'true_false'}
                
                if line.startswith('İfade:'):
                    current_question['statement'] = line.replace('İfade:', '').strip()
            
            elif line.startswith('İfade:') and 'statement' not in current_question:
                current_question['statement'] = line.replace('İfade:', '').strip()
            
            elif line.startswith('Doğru Cevap:'):
                answer = line.replace('Doğru Cevap:', '').strip().lower()
                current_question['correct_answer'] = 'Doğru' if 'doğru' in answer else 'Yanlış'
            
            elif line.startswith('Açıklama:'):
                current_question['explanation'] = line.replace('Açıklama:', '').strip()
        
        if current_question and 'statement' in current_question:
            questions.append(current_question)
        
        valid_questions = []
        for q in questions:
            if 'statement' in q:
                q.setdefault('correct_answer', 'Doğru')
                q.setdefault('explanation', 'Açıklama mevcut değil')
                valid_questions.append(q)
        
        return valid_questions if valid_questions else [{"error": "Quiz parse edilemedi"}]
    
    def _parse_fill_blank_response(self, response: str) -> List[Dict[str, Any]]:
        """Boşluk doldurma quiz yanıtını parse et"""
        questions = []
        current_question = {}
        
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('SORU ') or line.startswith('Cümle:'):
                if current_question and 'sentence' in current_question:
                    questions.append(current_question)
                current_question = {'type': 'fill_blank'}
                
                if line.startswith('Cümle:'):
                    current_question['sentence'] = line.replace('Cümle:', '').strip()
            
            elif line.startswith('Cümle:') and 'sentence' not in current_question:
                current_question['sentence'] = line.replace('Cümle:', '').strip()
            
            elif line.startswith('Doğru Cevap:'):
                current_question['correct_answer'] = line.replace('Doğru Cevap:', '').strip()
            
            elif line.startswith('Açıklama:'):
                current_question['explanation'] = line.replace('Açıklama:', '').strip()
        
        if current_question and 'sentence' in current_question:
            questions.append(current_question)
        
        valid_questions = []
        for q in questions:
            if 'sentence' in q:
                q.setdefault('correct_answer', '')
                q.setdefault('explanation', 'Açıklama mevcut değil')
                valid_questions.append(q)
        
        return valid_questions if valid_questions else [{"error": "Quiz parse edilemedi"}]
    
    def _parse_short_answer_response(self, response: str) -> List[Dict[str, Any]]:
        """Kısa cevap quiz yanıtını parse et"""
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
                current_question = {'type': 'short_answer'}
                
                if line.startswith('Soru:'):
                    current_question['question'] = line.replace('Soru:', '').strip()
            
            elif line.startswith('Soru:') and 'question' not in current_question:
                current_question['question'] = line.replace('Soru:', '').strip()
            
            elif line.startswith('Örnek Cevap:'):
                current_question['sample_answer'] = line.replace('Örnek Cevap:', '').strip()
            
            elif line.startswith('Anahtar Kelimeler:'):
                keywords = line.replace('Anahtar Kelimeler:', '').strip()
                current_question['keywords'] = [k.strip() for k in keywords.split(',')]
        
        if current_question and 'question' in current_question:
            questions.append(current_question)
        
        valid_questions = []
        for q in questions:
            if 'question' in q:
                q.setdefault('sample_answer', '')
                q.setdefault('keywords', [])
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
