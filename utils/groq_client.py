import logging
import logging
import os
import unicodedata
from typing import List, Dict, Any, Optional
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class GroqClient:
    """Groq API istemcisi - Cloud LLM entegrasyonu"""
    
    def __init__(self, api_key: Optional[str] = None):
        raw_key = api_key or os.getenv("GROQ_API_KEY")
        self.api_key = raw_key.strip() if raw_key else None
        if not self.api_key:
            raise ValueError("GROQ_API_KEY eksik")
        
        # Groq client oluştur
        self.client = Groq(api_key=self.api_key)
        
        # LangChain Groq LLM oluştur
        self.llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )
    
    def _contains_non_turkish(self, text: str) -> bool:
        for ch in text:
            if ch.isalpha():
                name = unicodedata.name(ch, "")
                if "LATIN" not in name:
                    return True
        return False

    def _invoke_with_retry(self, prompt_template: str, inputs: dict, retry_note: str) -> str:
        prompt = PromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        result = chain.invoke(inputs).content.strip()
        if self._contains_non_turkish(result):
            retry_template = prompt_template + "\n\n" + retry_note
            prompt = PromptTemplate.from_template(retry_template)
            chain = prompt | self.llm
            result = chain.invoke(inputs).content.strip()
        return result

    def generate_summary(
        self,
        context: str,
        detail_level: str = "orta"
    ) -> str:
        """Ders notlarini ozetle"""

        level = (detail_level or "").lower()
        level = (
            level.replace("\u00e7", "c")
            .replace("\u011f", "g")
            .replace("\u0131", "i")
            .replace("\u00f6", "o")
            .replace("\u015f", "s")
            .replace("\u00fc", "u")
        )
        if "cok" in level and "detay" in level:
            key = "cok_detayli"
        elif "detay" in level:
            key = "detayli"
        elif "k" in level and "sa" in level:
            key = "kisa"
        else:
            key = "orta"

        detail_instructions = {
            "kisa": "Cok kisa ve oz bir ozet yap (3-5 madde)",
            "orta": "Orta uzunlukta, ana noktalari kapsayan bir ozet yap",
            "detayli": "Detayli ve kapsamli bir ozet yap, onemli tum noktalari dahil et",
            "cok_detayli": (
                "Cok detayli bir ozet yaz. Metin uzunsa 2-3 sayfa "
                "uzunlugunda (yaklasik 1200-1800 kelime) olmasini hedefle."
            ),
        }

        instruction = detail_instructions.get(key, detail_instructions["orta"])

        prompt_template = """Asagidaki ders notlarini Turkce olarak ozetle.

{instruction}

Yanit yalnizca Turkce olmali, Turkce karakterleri (c/ç, g/ğ, i/ı, o/ö, s/ş, u/ü) dogru kullanmali ve ogretici, net bir dil kullanmali.

Ders Notlari:
{context}

OZET:"""

        try:
            return self._invoke_with_retry(
                prompt_template,
                {"context": context, "instruction": instruction},
                "Yanit yalnizca Turkce olmali ve Turkce karakterleri dogru kullanmali.",
            )
        except Exception:
            logger.exception("Ozet olusturma hatasi")
            return "Ozet olusturulamadi. Lutfen tekrar deneyin."

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
        except Exception:
            logger.exception("Flashcard olusturma hatasi")
            return [{"error": "Flashcard olusturulamadi. Lutfen tekrar deneyin."}]
    
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
        
        if valid_flashcards:
            return valid_flashcards
        return [{"error": "Flashcard parse edilemedi"}]
    
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
        difficulty: str = "orta",
    ) -> List[Dict[str, Any]]:
        """Çoktan seçmeli quiz oluştur"""

        difficulty_instructions = {
            "kolay": "Temel kavramları test eden basit sorular oluştur.",
            "orta": (
                "Orta seviye, kavramları anlama ve uygulama gerektiren "
                "sorular oluştur."
            ),
            "zor": (
                "İleri seviye, analiz ve sentez gerektiren "
                "zorlayıcı sorular oluştur."
            ),
        }
        difficulty_instruction = (
            difficulty_instructions.get(difficulty) or difficulty_instructions["orta"]
        )

        prompt_template = """Asagidaki ders notlarindan {num_questions} adet coktan secmeli soru olustur.

Yanit yalnizca Turkce olmali. Dogru cevap secenegi aciklama ile uyumlu olmali.

{difficulty_instruction}

Her soru icin:
- Soru metni (Turkce)
- 4 secenek (A, B, C, D)
- Dogru cevap (A, B, C veya D)
- Kisa aciklama

Ders Notlari:
{context}

Lutfen asagidaki formatta yanit ver:

SORU 1:
Soru: [Soru metni]
A) [Secenek A]
B) [Secenek B]
C) [Secenek C]
D) [Secenek D]
Dogru Cevap: [A/B/C/D]
Aciklama: [Kisa aciklama]

SORU 2:
...
"""

        prompt = PromptTemplate.from_template(prompt_template)

        try:
            chain = prompt | self.llm
            result = chain.invoke(
                {
                    "context": context,
                    "num_questions": num_questions,
                    "difficulty_instruction": difficulty_instruction,
                }
            )
            return self._parse_quiz_response(result.content)
        except Exception:
            logger.exception("Quiz olusturma hatasi (mcq)")
            return [{"error": "Quiz olusturulamadi. Lutfen tekrar deneyin."}]
    
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
        
        prompt_template = """Asagidaki ders notlarindan {num_questions} adet Dogru/Yanlis sorusu olustur.

Yanit yalnizca Turkce olmali.

{difficulty_instruction}

Her soru icin:
- Ifade (Turkce)
- Dogru cevap (Dogru veya Yanlis)
- Kisa aciklama

Ders Notlari:
{context}

Lutfen asagidaki formatta yanit ver:

SORU 1:
Ifade: [Ifade metni]
Dogru Cevap: [Dogru/Yanlis]
Aciklama: [Kisa aciklama]

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
        except Exception:
            logger.exception("Quiz olusturma hatasi (mcq)")
            return [{"error": "Quiz olusturulamadi. Lutfen tekrar deneyin."}]
    
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
        
        prompt_template = """Asagidaki ders notlarindan {num_questions} adet bosluk doldurma sorusu olustur.

Yanit yalnizca Turkce olmali.

{difficulty_instruction}

Her soru icin:
- Bosluklu cumle (_____ ile bosluk isaretle)
- Dogru cevap
- Kisa aciklama

Ders Notlari:
{context}

Lutfen asagidaki formatta yanit ver:

SORU 1:
Cumle: [Bosluklu cumle metni]
Dogru Cevap: [Dogru kelime/kelimeler]
Aciklama: [Kisa aciklama]

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
        except Exception:
            logger.exception("Quiz olusturma hatasi (mcq)")
            return [{"error": "Quiz olusturulamadi. Lutfen tekrar deneyin."}]
    
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
        
        prompt_template = """Asagidaki ders notlarindan {num_questions} adet kisa cevapli soru olustur.

Yanit yalnizca Turkce olmali.

{difficulty_instruction}

Her soru icin:
- Soru metni (Turkce)
- Ornek cevap
- Anahtar kelimeler

Ders Notlari:
{context}

Lutfen asagidaki formatta yanit ver:

SORU 1:
Soru: [Soru metni]
Ornek Cevap: [Ornek cevap]
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
        except Exception:
            logger.exception("Quiz olusturma hatasi (mcq)")
            return [{"error": "Quiz olusturulamadi. Lutfen tekrar deneyin."}]
    
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
        """Kullanici sorusuna ders notlarindan yararlanarak cevap ver"""

        context = "\n\n".join([doc.page_content for doc in context_docs])

        prompt_template = """Asagidaki ders notlarini kullanarak soruya Turkce cevap ver.

Yanit dogal ve anlasilir olsun.
Soru bir selamlama veya kisa sohbet ise kisa ve samimi cevap ver, ders notlarina zorla baglama.
Gerektiginde madde listesi kullan, sabit numarali bir format uygulama.
Yabanci dilde kelime veya ifade kullanma.

Ders Notlari:
{context}

Soru: {question}

Cevap:"""

        try:
            return self._invoke_with_retry(
                prompt_template,
                {"context": context, "question": question},
                "Yanit yalnizca Turkce olmali. Latin alfabesi disinda karakter kullanma.",
            )
        except Exception:
            logger.exception("Soru cevaplama hatasi")
            return "Cevap olusturulamadi. Lutfen tekrar deneyin."

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
            content = response.choices[0].message.content
            if self._contains_non_turkish(content):
                retry_messages = [
                    {
                        "role": "system",
                        "content": "Yanit yalnizca Turkce olmali. Latin alfabesi disinda karakter kullanma.",
                    }
                ] + messages
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=retry_messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                content = response.choices[0].message.content
            return content
        except Exception:
            logger.exception("Sohbet cevabi hatasi")
            return "Cevap olusturulamadi. Lutfen tekrar deneyin."
