import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rag import get_theory, explain_error
from db import (
    get_last_errors,
    get_mine_progress, save_mine_progress,
    get_theory_history, save_theory_history_item,
    get_helper_history, save_helper_history_item,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/mine",    StaticFiles(directory="mine",    html=True), name="mine")
app.mount("/miniapp", StaticFiles(directory="miniapp", html=True), name="miniapp")


# ── Модели ───────────────────────────────────────────────────────────────────

class TheoryRequest(BaseModel):
    topic: str
    section: Optional[str] = None

class ErrorExplainRequest(BaseModel):
    question_text: str
    correct_answer: str
    section: Optional[str] = None

class ProgressPayload(BaseModel):
    tg_id: int
    gold: int = 0
    gems: int = 0
    idle_accum: float = 0
    unlocked_horizons: list[str] = []
    completed_tasks: list[str] = []
    unlocked_vseross: list[str] = []
    completed_vseross: list[str] = []
    unlocked_secret: list[str] = []
    completed_secret: list[str] = []
    total_answers: int = 0
    correct_answers: int = 0

class HistoryPayload(BaseModel):
    tg_id: int
    topic: str
    answer: str
    ts: int


# ── Очистка вывода LLM ───────────────────────────────────────────────────────

def clean_llm_output(text: str) -> str:
    text = re.sub(r'\\\(|\\\)', '', text)
    text = re.sub(r'\\\[|\\\]', '', text)
    text = re.sub(r'\*\*([\s\S]+?)\*\*', r'\1', text)
    text = re.sub(r'\*([\s\S]+?)\*', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'`(.+?)`', r'\1', text)
    return text.strip()


# ── Эндпоинты ────────────────────────────────────────────────────────────────

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
    return {"errors": [
        {"question": r[0], "correct_answer": r[1],
         "user_answer": r[2], "topic": r[3], "made_at": r[4]}
        for r in rows
    ]}


# ── Прогресс шахты ───────────────────────────────────────────────────────────

@app.get("/progress")
def load_progress(tg_id: int):
    data = get_mine_progress(tg_id)
    if data is None:
        return {"exists": False}
    data["exists"] = True
    return data


@app.post("/progress")
def store_progress(payload: ProgressPayload):
    save_mine_progress(payload.tg_id, payload.dict())
    return {"ok": True}


# ── История Теории (Шахта) ──────────────────────────────────────────────────

@app.get("/theory_history")
def load_theory_history(tg_id: int):
    return get_theory_history(tg_id, limit=10)


@app.post("/theory_history")
def store_theory_history(payload: HistoryPayload):
    save_theory_history_item(payload.tg_id, payload.topic, payload.answer, payload.ts)
    return {"ok": True}


# ── История Помощника ─────────────────────────────────────────────────────

@app.get("/helper_history")
def load_helper_history(tg_id: int):
    return get_helper_history(tg_id, limit=10)


@app.post("/helper_history")
def store_helper_history(payload: HistoryPayload):
    save_helper_history_item(payload.tg_id, payload.topic, payload.answer, payload.ts)
    return {"ok": True}
