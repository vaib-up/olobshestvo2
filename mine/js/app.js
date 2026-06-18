const App = {

  API: 'https://olobshestvo2.online',
  LS_KEY: 'mine_progress_v1',

  async init() {
    if (window.Telegram?.WebApp) {
      Telegram.WebApp.expand();
      Telegram.WebApp.setHeaderColor('#0f0e0c');
      State.tgId = Telegram.WebApp.initDataUnsafe?.user?.id ?? null;
    }

    await Promise.all([
      Mine.loadData(),
      Vseross.loadData(),
      Secret.loadData(),
    ]);

    const { restored } = await this._loadProgress();

    if (!restored && State.mineData.length) {
      State.unlockedHorizons = [State.mineData[0].id];
    }

    Mine.render();
    Theory.render();
    Vseross.render();
    Secret.render();
    Progress.render();
    UI.updateResources();
    Mine.startIdleTick();
  },

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
