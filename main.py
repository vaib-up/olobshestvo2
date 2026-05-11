import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import CommandStart

TOKEN = "8750895420:AAEAN9K_t7adv0hFc-nKeryySgxasNF_B44"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== ЗАГРУЗКА ТЕСТОВ ==========

def load_tests():
    with open('tests.json', 'r', encoding='utf-8') as f:
        return json.load(f)

TESTS = load_tests()

# {user_id: {"test_id": str, "type": str, "current": int, "score": int, "total": int}}
user_progress = {}

# ========== КЛАВИАТУРЫ ==========

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Экономика"), KeyboardButton(text="🏛 Политология")],
            [KeyboardButton(text="⚖️ Право"), KeyboardButton(text="🤔 Философия")],
            [KeyboardButton(text="👥 Социология")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел..."
    )

def get_subsection_keyboard(section_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Тесты - Выпуск №1", callback_data=f"{section_code}_test1")],
            [InlineKeyboardButton(text="📝 Тесты - Выпуск №2", callback_data=f"{section_code}_test2")],
            [InlineKeyboardButton(text="↩️ К разделам", callback_data="back_sections")]
        ]
    )

def get_question_type_keyboard(test_id: str):
    # test_id вида "law_test1" → section_code = "law"
    section_code = test_id.split("_", maxsplit=1)[0]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да / Нет", callback_data=f"type|{test_id}|да_нет")],
            [InlineKeyboardButton(text="🔤 Тест (варианты ответов)", callback_data=f"type|{test_id}|тест")],
            [InlineKeyboardButton(text="📖 Развёрнутые ответы", callback_data=f"type|{test_id}|развёрнутый")],
            [InlineKeyboardButton(text="↩️ К выбору выпусков", callback_data=f"back_issues|{section_code}")]
        ]
    )

def get_yes_no_keyboard(test_id: str, q_num: int):
    # формат: ans|{test_id}|да_нет|{q_num}|{answer}
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Да",
                callback_data=f"ans|{test_id}|да_нет|{q_num}|да"
            ),
            InlineKeyboardButton(
                text="❌ Нет",
                callback_data=f"ans|{test_id}|да_нет|{q_num}|нет"
            )
        ]]
    )

def get_options_keyboard(test_id: str, q_num: int, options: list):
    letters = ["А", "Б", "В", "Г"]
    buttons = []
    for i, _ in enumerate(options):
        letter = letters[i]
        buttons.append([
            InlineKeyboardButton(
                text=letter,
                callback_data=f"ans|{test_id}|тест|{q_num}|{letter.lower()}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_next_keyboard(test_id: str, q_num: int):
    # формат: next|{test_id}|развёрнутый|{q_num}
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="➡️ Следующий вопрос",
                callback_data=f"next|{test_id}|развёрнутый|{q_num}"
            )
        ]]
    )

def get_back_to_types_keyboard(test_id: str):
    # формат: back_types|{test_id}
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="↩️ К выбору типа вопросов",
                callback_data=f"back_types|{test_id}"
            )
        ]]
    )

# ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ==========

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Выбери интересующий раздел:", reply_markup=get_main_keyboard())

@dp.message(F.text == "📊 Экономика")
async def economics_handler(message: Message):
    await message.answer(
        "📊 <b>Экономика</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("econ"),
        parse_mode="HTML"
    )

@dp.message(F.text == "🏛 Политология")
async def politics_handler(message: Message):
    await message.answer(
        "🏛 <b>Политология</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("pol"),
        parse_mode="HTML"
    )

@dp.message(F.text == "⚖️ Право")
async def law_handler(message: Message):
    await message.answer(
        "⚖️ <b>Право</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("law"),
        parse_mode="HTML"
    )

@dp.message(F.text == "🤔 Философия")
async def philosophy_handler(message: Message):
    await message.answer(
        "🤔 <b>Философия</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("phil"),
        parse_mode="HTML"
    )

@dp.message(F.text == "👥 Социология")
async def sociology_handler(message: Message):
    await message.answer(
        "👥 <b>Социология</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("soc"),
        parse_mode="HTML"
    )

@dp.message(F.text)
async def extended_answer_handler(message: Message):
    user_id = message.from_user.id
    progress = user_progress.get(user_id)

    # Если пользователь не в режиме развёрнутых ответов — не трогаем
    if not progress or progress["type"] != "развёрнутый":
        return

    test_id = progress["test_id"]
    q_num = progress["current"]
    questions = TESTS[test_id]["развёрнутый"]

    user_text = message.text  # можно сохранить, если нужно

    # Эталонный ответ
    correct_answer = questions[q_num].get("answer", "Ответ не задан.")

    # Сначала отвечаем по текущему вопросу
    # (кнопку "Следующий" дадим только если впереди ещё есть вопросы)
    has_next = (q_num + 1 < progress["total"])

    if has_next:
        kb = get_next_keyboard(test_id, q_num)
    else:
        kb = get_back_to_types_keyboard(test_id)

    await message.answer(
        f"Ваш ответ:\n{user_text}\n\nЭталонный ответ:\n{correct_answer}",
        reply_markup=kb
    )

    # Теперь сдвигаем "current" вперёд
    if has_next:
        progress["current"] += 1
        user_progress[user_id] = progress
    else:
        # Вопросов больше нет — завершаем сессию
        del user_progress[user_id]


# ========== ВЫБОР ВЫПУСКА ==========

@dp.callback_query(
    F.data.startswith("law_test") |
    F.data.startswith("soc_test") |
    F.data.startswith("econ_test") |
    F.data.startswith("pol_test") |
    F.data.startswith("phil_test")
)
async def any_test_selected(callback: CallbackQuery):
    # data: например "law_test1" или "soc_test1"
    test_id = callback.data

    if test_id not in TESTS:
        await callback.message.answer("Этот тест пока в разработке.")
        await callback.answer()
        return

    section_code, num_part = test_id.split("_", maxsplit=1)
    num = num_part.replace("test", "")

    section_titles = {
        "law": "⚖️ Право",
        "soc": "👥 Социология",
        "econ": "📊 Экономика",
        "pol": "🏛 Политология",
        "phil": "🤔 Философия"
    }
    section_title = section_titles.get(section_code, "Тест")

    text = f"{section_title} — Выпуск №{num}\n\nВыберите тип вопросов:"

    await callback.message.answer(
        text,
        reply_markup=get_question_type_keyboard(test_id),
        parse_mode="HTML"
    )
    await callback.answer()

# ========== ЗАПУСК КОНКРЕТНОГО ТИПА ВОПРОСОВ ==========

@dp.callback_query(F.data.startswith("type|"))
async def question_type_selected(callback: CallbackQuery):
    # data: type|law_test1|да_нет  или  type|law_test1|тест
    _, test_id, q_type = callback.data.split("|")

    user_id = callback.from_user.id
    questions = TESTS[test_id][q_type]

    user_progress[user_id] = {
        "test_id": test_id,
        "type": q_type,
        "current": 0,
        "score": 0,
        "total": len(questions)
    }

    first_q = questions[0]["question"]

    topic = questions[0].get("topic", "")

    if q_type == "да_нет":
        kb = get_yes_no_keyboard(test_id, 0)
        await callback.message.answer(
            f"Вопрос 1 из {len(questions)}:\n\n{first_q}",
            reply_markup=kb
        )
    elif q_type == "тест":
        options = questions[0]["options"]
        options_text = "\n".join(options)
        kb = get_options_keyboard(test_id, 0, options)
        await callback.message.answer(
            f"Вопрос 1 из {len(questions)}:\n\n{first_q}\n\n{options_text}",
            reply_markup=kb
        )
    elif q_type == "развёрнутый":
        await callback.message.answer(
            f"Вопрос 1 из {len(questions)}\nТема: {topic}\n\n{first_q}\n\nНапишите свой ответ в чате:"
        )
    else:
        await callback.message.answer("Пока реализованы все три блока для этого теста.")

    await callback.answer()

# ========== ОБРАБОТКА ОТВЕТОВ ДА/НЕТ ==========

@dp.callback_query(F.data.startswith("ans|"))
async def answer_handler(callback: CallbackQuery):
    # data: ans|law_test1|да_нет|0|да   или   ans|law_test1|тест|0|б
    _, test_id, q_type, q_num_str, user_ans = callback.data.split("|")
    q_num = int(q_num_str)
    user_id = callback.from_user.id

    progress = user_progress.get(user_id)
    if not progress or progress["test_id"] != test_id or progress["type"] != q_type:
        await callback.answer("Сессия теста не найдена. Начните заново.")
        return

    questions = TESTS[test_id][q_type]
    correct_ans = questions[q_num]["correct"]

    if user_ans == correct_ans:
        progress["score"] += 1

    # сдвинули текущий номер вопроса
    progress["current"] += 1
    user_progress[user_id] = progress

    # Если есть следующий вопрос
    if progress["current"] < progress["total"]:
        next_q_num = progress["current"]
        next_q = questions[next_q_num]["question"]

        if q_type == "да_нет":
           kb = get_yes_no_keyboard(test_id, next_q_num)
           await callback.message.answer(
               f"Вопрос {next_q_num + 1} из {progress['total']}:\n\n{next_q}",
               reply_markup=kb
           )

        elif q_type == "тест":
           options = questions[next_q_num]["options"]
           options_text = "\n".join(options)
           kb = get_options_keyboard(test_id, next_q_num, options)
           await callback.message.answer(
               f"Вопрос {next_q_num + 1} из {progress['total']}:\n\n{next_q}\n\n{options_text}",
               reply_markup=kb
           )

        else:
           # на всякий случай, для других типов
           await callback.message.answer(next_q)

    else:
        # ВОТ ЭТА ВЕТКА ОТВЕЧАЕТ ЗА КОНЕЦ ТЕСТА
        kb = get_back_to_types_keyboard(test_id)
        await callback.message.answer(
            f"Тест завершён!\n\nВаш результат: {progress['score']} из {progress['total']}.",
            reply_markup=kb
        )
        del user_progress[user_id]

    await callback.answer()

@dp.callback_query(F.data.startswith("next|"))
async def next_extended_question(callback: CallbackQuery):
    # data: next|law_test1|развёрнутый|0  (номер предыдущего вопроса нам не нужен)
    _, test_id, q_type, _ = callback.data.split("|")
    user_id = callback.from_user.id

    progress = user_progress.get(user_id)
    if not progress or progress["test_id"] != test_id or progress["type"] != q_type:
        await callback.answer("Сессия теста не найдена. Начните заново.")
        return

    questions = TESTS[test_id][q_type]

    # Здесь progress["current"] УЖЕ указывает на следующий вопрос,
    # потому что мы увеличили его в extended_answer_handler
    if progress["current"] < progress["total"]:
        q_num = progress["current"]
        q = questions[q_num]["question"]
        topic = questions[q_num].get("topic", "")

        await callback.message.answer(
            f"Вопрос {q_num + 1} из {progress['total']}\nТема: {topic}\n\n{q}\n\nНапишите свой ответ в чате:"
        )
        await callback.answer()
    else:
        # На случай, если вопросов уже нет (обычно до этого не дойдём)
        kb = get_back_to_types_keyboard(test_id)
        await callback.message.answer(
            "Блок с развёрнутыми ответами завершён! Спасибо за ответы.",
            reply_markup=kb
        )
        del user_progress[user_id]
        await callback.answer()

@dp.callback_query(F.data.startswith("back_types|"))
async def back_to_types(callback: CallbackQuery):
    # data: back_types|law_test1
    _, test_id = callback.data.split("|")

    if test_id not in TESTS:
        await callback.answer("Тест не найден.")
        return

    # Можно считать, что сессия завершена
    user_id = callback.from_user.id
    user_progress.pop(user_id, None)

    # Показываем меню выбора типа вопросов
    await callback.message.answer(
        "Выберите тип вопросов для этого выпуска:",
        reply_markup=get_question_type_keyboard(test_id)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("back_issues|"))
async def back_to_issues(callback: CallbackQuery):
    # data: back_issues|law  → section_code = "law"
    _, section_code = callback.data.split("|")

    # Показываем клавиатуру с выпусками для этого раздела
    await callback.message.answer(
        "Выберите выпуск:",
        reply_markup=get_subsection_keyboard(section_code)
    )
    await callback.answer()

@dp.callback_query(F.data == "back_sections")
async def back_to_sections(callback: CallbackQuery):
    # Возвращаем пользователя к главному меню разделов
    await callback.message.answer(
        "Выберите раздел:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

# ========== ЗАПУСК БОТА ==========

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())