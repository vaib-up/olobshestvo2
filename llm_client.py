# llm_client.py
# Весь код работы с нейросетью — только здесь.
# Чтобы сменить провайдера (Mistral → OpenAI → Gemini),
# меняешь только этот файл.

# llm_client.py
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL = "ministral-8b-2512"
API_URL = "https://api.mistral.ai/v1/chat/completions"


def ask_llm(system_prompt: str, user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    response = httpx.post(API_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]