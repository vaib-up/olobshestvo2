# api.py
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import get_theory, explain_error
from db import get_last_errors

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Модели запросов ──────────────────────────────────────

class TheoryRequest(BaseModel):
    topic: str
    section: Optional[str] = None  # econ, law, pol, soc, phil

class ErrorExplainRequest(BaseModel):
    question_text: str
    correct_answer: str
    section: Optional[str] = None


# ── Очистка вывода ИИ ────────────────────────────────────

def clean_llm_output(text: str) -> str:
    # Убираем LaTeX: \( ... \) и \[ ... \]
    text = re.sub(r'\\\(|\\\)', '', text)
    text = re.sub(r'\\\[|\\\]', '', text)
    # Убираем **жирный** (в т.ч. многострочный)
    text = re.sub(r'\*\*([\s\S]+?)\*\*', r'\1', text)
    # Убираем *курсив*
    text = re.sub(r'\*([\s\S]+?)\*', r'\1', text)
    # Убираем ### заголовки Markdown
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Убираем `код`
    text = re.sub(r'`(.+?)`', r'\1', text)
    return text.strip()


# ── Эндпоинты ────────────────────────────────────────────

@app.get("/ping")
def ping():
    return {"status": "ok"}


@app.post("/theory")
def theory(req: TheoryRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Тема не может быть пустой")
    answer = get_theory(req.topic, section=req.section)
    return {"answer": clean_llm_output(answer)}


@app.post("/explain_error")
def explain(req: ErrorExplainRequest):
    answer = explain_error(req.question_text, req.correct_answer, section=req.section)
    return {"answer": clean_llm_output(answer)}


@app.get("/errors/{user_id}")
def user_errors(user_id: int):
    rows = get_last_errors(user_id, limit=10)
    errors = [
        {
            "question": row[0],
            "correct_answer": row[1],
            "user_answer": row[2],
            "topic": row[3],
            "made_at": row[4],
        }
        for row in rows
    ]
    return {"errors": errors}