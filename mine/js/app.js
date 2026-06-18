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

    // 3. Восстанавливаем прогресс
    const { restored, source } = await this._loadProgress();

    // 4. Новый пользователь
    if (!restored && State.mineData.length) {
      State.unlockedHorizons = [State.mineData[0].id];
    }

    // 5. Рендерим
    Mine.render();
    Theory.render();
    Vseross.render();
    Secret.render();
    Progress.render();
    UI.updateResources();
    Mine.startIdleTick();

    // 6. Диагностика — временный тост
    const lsRaw = (() => { try { return localStorage.getItem(this.LS_KEY); } catch(_){return null;} })();
    const lsObj = lsRaw ? JSON.parse(lsRaw) : null;
    const diagLines = [
      `tgId: ${State.tgId ?? 'null'}`,
      `source: ${source}`,
      `gold: ${State.gold}`,
      `horizons: ${State.unlockedHorizons.length}`,
      `tasks: ${State.completedTasks.size}`,
      `ls_gold: ${lsObj?.gold ?? '—'}`,
    ];
    this._diagToast(diagLines.join(' | '));
  },

  _diagToast(msg) {
    const el = document.createElement('div');
    el.style.cssText = [
      'position:fixed', 'top:10px', 'left:8px', 'right:8px',
      'background:#1a1a2e', 'color:#e2c97e', 'border:1px solid #e2c97e',
      'border-radius:10px', 'padding:10px 12px', 'font-size:11px',
      'line-height:1.6', 'z-index:9999', 'word-break:break-all',
      'white-space:pre-wrap',
    ].join(';');
    el.textContent = '🔧 ' + msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 8000);
  },

  // ── Загрузка ──────────────────────────────────────────────────────────────────
  async _loadProgress() {
    if (State.tgId) {
      try {
        const r = await fetch(`${this.API}/progress?tg_id=${State.tgId}`);
        if (r.ok) {
          const d = await r.json();
          if (d.exists) {
            this._apply(d);
            return { restored: true, source: 'server' };
          }
        }
      } catch (_) {}
    }

    try {
      const raw = localStorage.getItem(this.LS_KEY);
      if (raw) {
        this._apply(JSON.parse(raw));
        return { restored: true, source: 'localStorage' };
      }
    } catch (_) {}

    return { restored: false, source: 'none' };
  },

  // ── Применяем — полная перезапись ──────────────────────────────────
  _apply(d) {
    State.gold             = d.gold             ?? 0;
    State.gems             = d.gems             ?? 0;
    State.idleAccum        = d.idle_accum        ?? 0;
    State.totalAnswers     = d.total_answers     ?? 0;
    State.correctAnswers   = d.correct_answers   ?? 0;
    State.unlockedHorizons = d.unlocked_horizons ?? [];
    State.completedTasks   = new Set(d.completed_tasks   ?? []);
    State.unlockedVseross  = d.unlocked_vseross  ?? [];
    State.completedVseross = new Set(d.completed_vseross ?? []);
    State.unlockedSecret   = d.unlocked_secret   ?? [];
    State.completedSecret  = new Set(d.completed_secret  ?? []);
  },

  // ── Сохранение ──────────────────────────────────────────────────────────────────
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
    try { localStorage.setItem(this.LS_KEY, JSON.stringify(obj)); } catch (_) {}
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
