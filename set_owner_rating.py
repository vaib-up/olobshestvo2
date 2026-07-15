import os
from dotenv import load_dotenv

from db import (init_db,
                set_admin_rating,
                clear_admin_rating,
                get_user_stats)

load_dotenv()

OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))

# ====== НАСТРОЙ ТОЛЬКО ЭТИ ПОЛЯ ======
TARGET_SCORE = 500
TARGET_TOTAL = 500
RESET_ONLY = False
LABEL = "manual"
# =====================================


def main():
    if OWNER_ID <= 0:
        raise ValueError("BOT_OWNER_ID не найден в окружении или задан некорректно")

    init_db()

    if RESET_ONLY:
        clear_admin_rating(OWNER_ID)
        print(f"OK: admin rating cleared for user_id={OWNER_ID}")
        return

    set_admin_rating(
        user_id=OWNER_ID,
        score=TARGET_SCORE,
        total=TARGET_TOTAL,
        label=LABEL,
    )

    tests_count, sum_score, sum_total, tests = get_user_stats(OWNER_ID)
    print("OK: admin rating updated")
    print(f"user_id={OWNER_ID}")
    print(f"tests_count={tests_count}")
    print(f"sum_score={sum_score}")
    print(f"sum_total={sum_total}")
    print("records:")
    for row in tests:
        print(row)


if __name__ == "__main__":
    main()