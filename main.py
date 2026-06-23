import os
import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery,  WebAppInfo,
)
from aiogram.filters import CommandStart, Command

from dotenv import load_dotenv

from db import init_db, save_first_attempt, get_user_stats, save_error

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())
dp = Dispatcher()

# ========== ЗАГРУЗКА ТЕСТОВ ==========

def load_tests():
    with open("tests.json", "r", encoding="utf-8") as f:
        return json.load(f)

TESTS = load_tests()

# {user_id: {"test_id": str, "type": str, "current": int, "score": int, "total": int}}
user_progress = {}

# ========== ТЕКСТЫ ТЕМ ПО РАЗДЕЛАМ ==========

SECTION_TOPICS = {
    "law": (
        "Право темы выпусков:\n\n"
        "<i>Выпуск №1:</i>\n\n"
        "Предмет и участники гражданского права\n"
        "Принципы и источники гражданского законодательства\n"
        "Правоспособность и дееспособность граждан\n"
        "Статус безвестно отсутствующего и объявление умершим\n"
        "Объекты гражданских правоотношений\n"
        "Обычай в гражданском праве\n\n"
        "<i>Выпуск №2:</i>\n\n"
        "Понятие и условия действительности сделки\n"
        "Основные виды сделок\n"
        "Форма сделок и способы волеизъявления\n"
        "Недействительность сделок\n"
        "Представительство, исковая давность и приобретательная давность\n\n"
        "<i>Выпуск №3:</i>\n\n"
        "Понятие и возникновение обязательств\n"
        "Виды обязательств (альтернативные, факультативные, солидарные)\n"
        "Исполнение обязательств и денежные обязательства\n"
        "Обеспечение исполнения обязательств и неустойка\n"
        "Договоры: публичный, присоединения, оферта и акцепт\n"
        "Обеспечительные обязательства и их связь с основным"
    ),
    "econ": (
        "Экономика темы выпусков:\n\n"
"<i>Выпуск №1:</i>\n\n"
"Внешние эффекты\n"
"Трагедия общих ресурсов\n"
"Проблема безбилетника\n"
"Общественные блага\n"
"Государственное регулирование рынка\n"
"Функции рынка\n"
"Спрос и предложение\n"
"Главная экономическая проблема\n"
"<i>Выпуск №2:</i>\n\n"
"Совершенная конкуренция\n"
"Монополия\n"
"Монополистическая конкуренция\n"
"Олигополия и взаимодействие фирм\n"
"Формы объединения фирм и соглашения\n"
"Эффект масштаба\n"
"Монополизация\n"
"Парадокс Бертрана\n"
"<i>Выпуск №3:</i>\n\n"
"Факторы производства и доходы\n"
"Рынок труда и теории труда\n"
"Информация и человеческий капитал\n"
"Издержки производства\n"
"Ценовая дискриминация\n"
    ),
    "pol":  "Здесь будут темы по политологии.",
    "phil": "Здесь будут темы по философии.",
    "soc":  "Здесь будут темы по социологии.",
}

# ========== КЛАВИАТУРЫ ==========

def get_main_keyboard(user_id: int = None):
    assistant_url = "https://olobshestvo2.online/miniapp/index.html"
    mine_url = "https://olobshestvo2.online/mine/index.html"
    if user_id:
        assistant_url += f"?uid={user_id}"
        mine_url += f"?uid={user_id}"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Разделы")],
            [KeyboardButton(text="🔁 Старт"), KeyboardButton(text="📈 Статистика")],
            [KeyboardButton(
                text="🤖 Помощник",
                web_app=WebAppInfo(url=assistant_url)
            )],
            [KeyboardButton(
                text="⛏️ Шахта Знаний",
                web_app=WebAppInfo(url=mine_url)
            )],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_sections_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Экономика"), KeyboardButton(text="🏛 Политология")],
            [KeyboardButton(text="⚖️ Право"), KeyboardButton(text="🤔 Философия")],
            [KeyboardButton(text="👥 Социология")],
            [KeyboardButton(text="↩️ Назад")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел или вернитесь назад...",
    )


def get_subsection_keyboard(section_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Темы всех выпусков", callback_data=f"topics_{section_code}")],
            [InlineKeyboardButton(text="📝Выпуск №1", callback_data=f"{section_code}_test1")],
            [InlineKeyboardButton(text="📝Выпуск №2", callback_data=f"{section_code}_test2")],
            [InlineKeyboardButton(text="📝Выпуск №3", callback_data=f"{section_code}_test3")],
            [InlineKeyboardButton(text="📝Выпуск №4", callback_data=f"{section_code}_test4")],
            [InlineKeyboardButton(text="↩️ К разделам", callback_data="back_sections")],
        ]
    )


def get_question_type_keyboard(test_id: str):
    section_code = test_id.split("_", maxsplit=1)[0]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да / Нет", callback_data=f"type|{test_id}|да_нет")],
            [InlineKeyboardButton(text="🔤 Тест (варианты ответов)", callback_data=f"type|{test_id}|тест")],
            [InlineKeyboardButton(text="📖 Развёрнутые ответы", callback_data=f"type|{test_id}|развёрнутый")],
            [InlineKeyboardButton(text="↩️ К выбору выпусков", callback_data=f"back_issues|{section_code}")],
        ]
    )


def get_yes_no_keyboard(test_id: str, q_num: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"ans|{test_id}|да_нет|{q_num}|да"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"ans|{test_id}|да_нет|{q_num}|нет"),
            ]
        ]
    )


def get_options_keyboard(test_id: str, q_num: int, options: list):
    letters = ["А", "Б", "В", "Г"]
    buttons = []
    for i, _ in enumerate(options):
        letter = letters[i]
        buttons.append(
            [InlineKeyboardButton(text=letter, callback_data=f"ans|{test_id}|тест|{q_num}|{letter.lower()}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_next_keyboard(test_id: str, q_num: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data=f"next|{test_id}|развёрнутый|{q_num}")]
        ]
    )


def get_back_to_types_keyboard(test_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ К выбору типа вопросов", callback_data=f"back_types|{test_id}")]
        ]
    )

def get_stats_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ К разделам", callback_data="back_sections")]
        ]
    )

# ========== ОБРАБОТЧИКИ СООБЩЕНИЙ ==========

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=get_main_keyboard(message.from_user.id),
    )


@dp.message(F.text == "📚 Разделы")
async def sections_menu(message: Message):
    await message.answer(
        "Выберите раздел:",
        reply_markup=get_sections_keyboard(),
    )


@dp.message(F.text == "🔁 Старт")
async def restart_handler(message: Message):
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=get_main_keyboard(message.from_user.id),
    )


@dp.message(F.text == "📈 Статистика")
async def stats_button_handler(message: Message):
    await cmd_stats(message)


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    user_id = message.from_user.id
    tests_count, sum_score, sum_total, tests = get_user_stats(user_id)

    if tests_count == 0:
        await message.answer(
            "Пока нет ни одного завершённого блока. Пройдите тесты с вариантами или да/нет.",
            reply_markup=get_stats_back_keyboard()
        )
        return

    percent = (sum_score / sum_total * 100) if sum_total else 0.0

    lines = [
        "Ваша статистика по первым прохождениям блоков:",
        f"Блоков завершено: {tests_count}",
        f"Суммарный результат: {sum_score} из {sum_total} ({percent:.1f}%)",
        "",
        "По блокам:",
    ]

    for raw_id, score, total, _ in tests:
        base_id, block_type = raw_id.split("|", maxsplit=1)
        section_code, num_part = base_id.split("_", maxsplit=1)
        num = num_part.replace("test", "")

        section_titles = {
            "law": "Право",
            "soc": "Социология",
            "econ": "Экономика",
            "pol": "Политология",
            "phil": "Философия",
        }
        type_titles = {
            "да_нет": "Блок да/нет",
            "тест": "Блок тест",
        }

        section_title = section_titles.get(section_code, section_code)
        block_title = type_titles.get(block_type, block_type)
        lines.append(f"• {section_title}, выпуск {num}, {block_title}: {score}/{total}")

    text = "\n".join(lines)
    await message.answer(text, reply_markup=get_stats_back_keyboard())


@dp.message(F.text == "↩️ Назад")
async def back_from_sections_menu(message: Message):
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(message.from_user.id),
    )

@dp.message(F.text == "📊 Экономика")
async def economics_handler(message: Message):
    await message.answer(
        "📊 <b>Экономика</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("econ"),
        parse_mode="HTML",
    )


@dp.message(F.text == "🏛 Политология")
async def politics_handler(message: Message):
    await message.answer(
        "🏛 <b>Политология</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("pol"),
        parse_mode="HTML",
    )


@dp.message(F.text == "⚖️ Право")
async def law_handler(message: Message):
    await message.answer(
        "⚖️ <b>Право</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("law"),
        parse_mode="HTML",
    )


@dp.message(F.text == "🤔 Философия")
async def philosophy_handler(message: Message):
    await message.answer(
        "🤔 <b>Философия</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("phil"),
        parse_mode="HTML",
    )


@dp.message(F.text == "👥 Социология")
async def sociology_handler(message: Message):
    await message.answer(
        "👥 <b>Социология</b>\n\nВыберите подраздел:",
        reply_markup=get_subsection_keyboard("soc"),
        parse_mode="HTML",
    )


@dp.message(F.text)
async def extended_answer_handler(message: Message):
    user_id = message.from_user.id
    progress = user_progress.get(user_id)

    if not progress or progress["type"] != "развёрнутый":
        return

    test_id = progress["test_id"]
    q_num = progress["current"]
    questions = TESTS[test_id]["развёрнутый"]

    user_text = message.text
    correct_answer = questions[q_num].get("answer", "Ответ не задан.")

    has_next = (q_num + 1 < progress["total"])

    if has_next:
        kb = get_next_keyboard(test_id, q_num)
    else:
        kb = get_back_to_types_keyboard(test_id)

    await message.answer(
        f"Ваш ответ:\n{user_text}\n\nЭталонный ответ:\n{correct_answer}",
        reply_markup=kb,
    )

    if has_next:
        progress["current"] += 1
        user_progress[user_id] = progress
    else:
        del user_progress[user_id]

# ========== ВЫБОР ВЫПУСКА ==========

@dp.callback_query(
    F.data.startswith("law_test")
    | F.data.startswith("soc_test")
    | F.data.startswith("econ_test")
    | F.data.startswith("pol_test")
    | F.data.startswith("phil_test")
)
async def any_test_selected(callback: CallbackQuery):
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
        "phil": "🤔 Философия",
    }
    section_title = section_titles.get(section_code, "Тест")
    text = f"{section_title} — Выпуск №{num}\n\nВыберите тип вопросов:"

    await callback.message.answer(
        text,
        reply_markup=get_question_type_keyboard(test_id),
        parse_mode="HTML",
    )
    await callback.answer()

# ========== ТЕМЫ ВСЕХ ВЫПУСКОВ ==========

@dp.callback_query(F.data.startswith("topics_"))
async def topics_handler(callback: CallbackQuery):
    section_code = callback.data.removeprefix("topics_")
    text = SECTION_TOPICS.get(section_code, "Темы пока не добавлены.")
    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ К выпускам", callback_data=f"back_issues|{section_code}")]
        ]
    )
    await callback.message.answer(text, reply_markup=back_kb, parse_mode="HTML")
    await callback.answer()

# ========== ЗАПУСК КОНКРЕТНОГО ТИПА ==========

@dp.callback_query(F.data.startswith("type|"))
async def question_type_selected(callback: CallbackQuery):
    _, test_id, q_type = callback.data.split("|")
    user_id = callback.from_user.id

    questions = TESTS[test_id][q_type]

    user_progress[user_id] = {
        "test_id": test_id,
        "type": q_type,
        "current": 0,
        "score": 0,
        "total": len(questions),
        "wrong": []
    }

    first_q = questions[0]["question"]
    topic = questions[0].get("topic", "")

    if q_type == "да_нет":
        kb = get_yes_no_keyboard(test_id, 0)
        await callback.message.answer(
            f"Вопрос 1 из {len(questions)}:\n\n{first_q}",
            reply_markup=kb,
        )
    elif q_type == "тест":
        options = questions[0]["options"]
        options_text = "\n".join(options)
        kb = get_options_keyboard(test_id, 0, options)
        await callback.message.answer(
            f"Вопрос 1 из {len(questions)}:\n\n{first_q}\n\n{options_text}",
            reply_markup=kb,
        )
    elif q_type == "развёрнутый":
        await callback.message.answer(
            f"Вопрос 1 из {len(questions)}\nТема: {topic}\n\n{first_q}\n\nНапишите свой ответ в чате:"
        )
    else:
        await callback.message.answer("Пока реализованы все три блока для этого теста.")

    await callback.answer()

# ========== ОБРАБОТКА ОТВЕТОВ ==========

@dp.callback_query(F.data.startswith("ans|"))
async def answer_handler(callback: CallbackQuery):
    _, test_id, q_type, q_num_str, user_ans = callback.data.split("|")
    q_num = int(q_num_str)
    user_id = callback.from_user.id

    progress = user_progress.get(user_id)
    if not progress or progress["test_id"] != test_id or progress["type"] != q_type:
        await callback.answer("Сессия теста не найдена. Начните заново.")
        return

    questions = TESTS[test_id][q_type]
    correct_ans_raw = questions[q_num]["correct"]

    user_norm = str(user_ans).strip().lower()
    correct_norm = str(correct_ans_raw).strip().lower()

    if user_norm == correct_norm:
        progress["score"] += 1
    else:
        progress["wrong"].append((q_num, user_ans, correct_ans_raw))
        question_text = questions[q_num]["question"]
        topic = questions[q_num].get("topic", None)
        save_error(
            user_id=user_id,
            test_id=test_id,
            question_text=question_text,
            correct_answer=str(correct_ans_raw),
            user_answer=str(user_ans),
            topic=topic,
        )

    progress["current"] += 1
    user_progress[user_id] = progress

    if progress["current"] < progress["total"]:
        next_q_num = progress["current"]
        next_q = questions[next_q_num]["question"]

        if q_type == "да_нет":
            kb = get_yes_no_keyboard(test_id, next_q_num)
            await callback.message.answer(
                f"Вопрос {next_q_num + 1} из {progress['total']}:\n\n{next_q}",
                reply_markup=kb,
            )
        elif q_type == "тест":
            options = questions[next_q_num]["options"]
            options_text = "\n".join(options)
            kb = get_options_keyboard(test_id, next_q_num, options)
            await callback.message.answer(
                f"Вопрос {next_q_num + 1} из {progress['total']}:\n\n{next_q}\n\n{options_text}",
                reply_markup=kb,
            )
        else:
            await callback.message.answer(next_q)
    else:
        kb = get_back_to_types_keyboard(test_id)

        if q_type in ("да_нет", "тест"):
            block_id = f"{test_id}|{q_type}"
            save_first_attempt(
                user_id=user_id,
                test_id=block_id,
                score=progress["score"],
                total=progress["total"],
            )

        await callback.message.answer(
            f"Блок завершён!\n\nВаш результат: {progress['score']} из {progress['total']}.",
            reply_markup=kb,
        )

        wrong = progress.get("wrong", [])
        if wrong:
            questions = TESTS[test_id][q_type]
            lines = ["Ошибки в этом прохождении:"]
            for bad_q_num, bad_user_ans, bad_correct_ans in wrong:
                q_text = questions[bad_q_num]["question"]
                user_ans_display = str(bad_user_ans).upper()
                correct_ans_display = str(bad_correct_ans).upper()
                lines.append(
                    f"\nВопрос {bad_q_num + 1}:\n{q_text}"
                    f"\nВаш ответ: {user_ans_display}"
                    f"\nПравильный ответ: {correct_ans_display}"
                )
            await callback.message.answer("\n".join(lines))

        del user_progress[user_id]

    await callback.answer()


# ========== СЛЕДУЮЩИЙ РАЗВЁРНУТЫЙ ==========

@dp.callback_query(F.data.startswith("next|"))
async def next_extended_question(callback: CallbackQuery):
    _, test_id, q_type, _ = callback.data.split("|")
    user_id = callback.from_user.id

    progress = user_progress.get(user_id)
    if not progress or progress["test_id"] != test_id or progress["type"] != q_type:
        await callback.answer("Сессия теста не найдена. Начните заново.")
        return

    questions = TESTS[test_id][q_type]

    if progress["current"] < progress["total"]:
        q_num = progress["current"]
        q = questions[q_num]["question"]
        topic = questions[q_num].get("topic", "")
        await callback.message.answer(
            f"Вопрос {q_num + 1} из {progress['total']}\nТема: {topic}\n\n{q}\n\nНапишите свой ответ в чате:"
        )
        await callback.answer()
    else:
        kb = get_back_to_types_keyboard(test_id)
        await callback.message.answer(
            "Блок с развёрнутыми ответами завершён!",
            reply_markup=kb,
        )
        del user_progress[user_id]
        await callback.answer()

# ========== НАВИГАЦИЯ НАЗАД ==========

@dp.callback_query(F.data.startswith("back_types|"))
async def back_to_types(callback: CallbackQuery):
    _, test_id = callback.data.split("|")
    if test_id not in TESTS:
        await callback.answer("Тест не найден.")
        return
    user_id = callback.from_user.id
    user_progress.pop(user_id, None)
    await callback.message.answer(
        "Выберите тип вопросов:",
        reply_markup=get_question_type_keyboard(test_id),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("back_issues|"))
async def back_to_issues(callback: CallbackQuery):
    _, section_code = callback.data.split("|")
    await callback.message.answer(
        "Выберите выпуск:",
        reply_markup=get_subsection_keyboard(section_code),
    )
    await callback.answer()


@dp.callback_query(F.data == "back_sections")
async def back_to_sections(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_progress.pop(user_id, None)
    await callback.message.answer(
        "Выберите раздел:",
        reply_markup=get_sections_keyboard(),
    )
    await callback.answer()

# ========== ЗАПУСК ==========

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
