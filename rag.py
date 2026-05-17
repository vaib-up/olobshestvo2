# rag.py
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from llm_client import ask_llm

DB_DIR = "./chroma_db"

# Глобальные переменные — None до первого вызова
_ef = None
_collection = None

def _get_collection():
    """Инициализация только при первом обращении"""
    global _ef, _collection
    if _collection is None:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        _ef = SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        _client = chromadb.PersistentClient(path=DB_DIR)
        _collection = _client.get_collection(name="books", embedding_function=_ef)
    return _collection


def get_theory(topic: str, section: str = None) -> str:
    collection = _get_collection()
    where = {"section": section} if section else None
    results = collection.query(query_texts=[topic], n_results=5, where=where)
    chunks = results["documents"][0]
    if not chunks:
        return "По этой теме материал в базе не найден."
    context = "\n\n---\n\n".join(chunks)
    system_prompt = """Ты учитель обществознания. 
    Отвечай СТРОГО на основе предоставленного контекста из учебников.
    Если в контексте нет информации по теме — ответь только:
    "Материал по этой теме отсутствует в базе учебников."
    Не добавляй ничего от себя. Отвечай на русском языке."""
    user_message = f"Контекст из учебников:\n{context}\n\nОбъясни тему: {topic}"
    return ask_llm(system_prompt, user_message)


def explain_error(question_text: str, correct_answer: str, section: str = None) -> str:
    collection = _get_collection()
    where = {"section": section} if section else None
    results = collection.query(query_texts=[question_text], n_results=5, where=where)
    chunks = results["documents"][0]
    context = "\n\n---\n\n".join(chunks) if chunks else "Контекст не найден."
    system_prompt = """Ты учитель обществознания. 
    Отвечай СТРОГО на основе предоставленного контекста из учебников.
    Если в контексте нет информации по теме — ответь только:
    "Материал по этой теме отсутствует в базе учебников."
    Не добавляй ничего от себя. Отвечай на русском языке."""
    user_message = f"Контекст из учебников:\n{context}\n\nВопрос: {question_text}\nПравильный ответ: {correct_answer}\n\nОбъясни почему именно этот ответ правильный."
    return ask_llm(system_prompt, user_message)