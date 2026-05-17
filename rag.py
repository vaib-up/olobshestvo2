# rag.py
# Поиск по векторной базе + генерация ответа через LLM.

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from llm_client import ask_llm

DB_DIR = "./chroma_db"

_ef = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
_client = chromadb.PersistentClient(path=DB_DIR)
_collection = _client.get_collection(name="books", embedding_function=_ef)


def get_theory(topic: str, section: str = None) -> str:
    """
    Ищет в учебниках материал по теме и возвращает объяснение.
    section — необязательный фильтр по разделу (econ, law, pol, soc, phil)
    """
    where = {"section": section} if section else None

    results = _collection.query(
        query_texts=[topic],
        n_results=5,
        where=where,
    )

    chunks = results["documents"][0]
    if not chunks:
        return "По этой теме материал в базе не найден."

    context = "\n\n---\n\n".join(chunks)

    system_prompt = """Ты учитель обществознания. 
    Отвечай СТРОГО на основе предоставленного контекста из учебников.
    Если в контексте нет информации по теме — ответь только:
    "Материал по этой теме отсутствует в базе учебников."
    Не добавляй ничего от себя. Отвечай на русском языке."""

    user_message = f"""Контекст из учебников:
{context}

Объясни тему: {topic}"""

    return ask_llm(system_prompt, user_message)


def explain_error(question_text: str, correct_answer: str, section: str = None) -> str:
    """
    Объясняет ошибку ученика на основе учебников.
    """
    where = {"section": section} if section else None

    results = _collection.query(
        query_texts=[question_text],
        n_results=5,
        where=where,
    )

    chunks = results["documents"][0]
    context = "\n\n---\n\n".join(chunks) if chunks else "Контекст не найден."

    system_prompt = """Ты учитель обществознания. 
    Отвечай СТРОГО на основе предоставленного контекста из учебников.
    Если в контексте нет информации по теме — ответь только:
    "Материал по этой теме отсутствует в базе учебников."
    Не добавляй ничего от себя. Отвечай на русском языке."""

    user_message = f"""Контекст из учебников:
{context}

Вопрос: {question_text}
Правильный ответ: {correct_answer}

Объясни почему именно этот ответ правильный."""

    return ask_llm(system_prompt, user_message)