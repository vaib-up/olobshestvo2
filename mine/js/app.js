const App = {

  API: 'https://olobshestvo2.online',
  LS_KEY: 'mine_progress_v1',

  async init() {
    // 1. tgId
    if (window.Telegram?.WebApp) {
      Telegram.WebApp.expand();
      Telegram.WebApp.setHeaderColor('#0f0e0c');
      State.tgId = Telegram.WebApp.initDataUnsafe?.user?.id ?? null;
    }

    // 2. Загружаем JSON-данные (не трогаем State)
    await Promise.all([
      Mine.loadData(),
      Vseross.loadData(),
      Secret.loadData(),
    ]);

    // 3. Восстанавливаем прогресс (полностью перезаписывает State)
    const restored = await this._loadProgress();

    // 4. Если прогресса нет — новый пользователь
    if (!restored && State.mineData.length) {
      State.unlockedHorizons = [State.mineData[0].id];
    }

    // 5. Рендерим всё
    Mine.render();
    Theory.render();
    Vseross.render();
    Secret.render();
    Progress.render();
    UI.updateResources();
    Mine.startIdleTick();
  },

  // ── Загрузка: сервер → localStorage → null ──────────────────────────────
  async _loadProgress() {
    // Пробуем сервер
    if (State.tgId) {
      try {
        const r = await fetch(`${this.API}/progress?tg_id=${State.tgId}`);
        if (r.ok) {
          const d = await r.json();
          if (d.exists) {
            this._apply(d);
            return true;
          }
        }
      } catch (_) {}
    }

    // Фоллбэк: localStorage
    try {
      const raw = localStorage.getItem(this.LS_KEY);
      if (raw) {
        this._apply(JSON.parse(raw));
        return true;
      }
    } catch (_) {}

    return false; // новый пользователь
  },

  // ── Применяем данные — БЕЗ условий, полная перезапись ────────────────
  _apply(d) {
    State.gold               = d.gold             ?? 0;
    State.gems               = d.gems             ?? 0;
    State.idleAccum          = d.idle_accum        ?? 0;
    State.totalAnswers       = d.total_answers     ?? 0;
    State.correctAnswers     = d.correct_answers   ?? 0;
    State.unlockedHorizons   = d.unlocked_horizons ?? [];
    State.completedTasks     = new Set(d.completed_tasks   ?? []);
    State.unlockedVseross    = d.unlocked_vseross  ?? [];
    State.completedVseross   = new Set(d.completed_vseross ?? []);
    State.unlockedSecret     = d.unlocked_secret   ?? [];
    State.completedSecret    = new Set(d.completed_secret  ?? []);
  },

  // ── Сохранение: localStorage мгновенно + сервер асинхронно ─────────────
  saveProgress() {
    const obj = {
      gold:               State.gold,
      gems:               State.gems,
      idle_accum:         State.idleAccum,
      unlocked_horizons:  State.unlockedHorizons,
      completed_tasks:    [...State.completedTasks],
      unlocked_vseross:   State.unlockedVseross,
      completed_vseross:  [...State.completedVseross],
      unlocked_secret:    State.unlockedSecret,
      completed_secret:   [...State.completedSecret],
      total_answers:      State.totalAnswers,
      correct_answers:    State.correctAnswers,
    };

    // Мгновенно — всегда
    try { localStorage.setItem(this.LS_KEY, JSON.stringify(obj)); } catch (_) {}

    // Асинхронно на сервер — если есть tgId
    if (State.tgId) {
      fetch(`${this.API}/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tg_id: State.tgId, ...obj }),
      }).catch(() => {});
    }
  },

  // ── Навигация ──────────────────────────────────────────────────────────────────
  switchScreen(name) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`screen-${name}`).classList.add('active');
    document.getElementById(`nav-${name}`).classList.add('active');
  },

  renderAll() {
    Mine.render();
    Theory.render();
    Vseross.render();
    Secret.render();
    Progress.render();
    UI.updateResources();
    this.saveProgress();
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
