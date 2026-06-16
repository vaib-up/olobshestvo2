// Точка входа — инициализация, навигация, сохранение прогресса
const App = {

  API: 'https://olobshestvo2.online',

  init() {
    if (window.Telegram?.WebApp) {
      Telegram.WebApp.expand();
      Telegram.WebApp.setHeaderColor('#0f0e0c');
      // Получаем tg_id из initDataUnsafe
      const user = Telegram.WebApp.initDataUnsafe?.user;
      State.tgId = user?.id ?? null;
    }

    Promise.all([
      Mine.loadData(),
      Vseross.loadData(),
      Secret.loadData(),
    ]).then(async () => {
      // Грузим прогресс с сервера если есть tg_id
      if (State.tgId) {
        await this.loadProgress();
      }
      Mine.render();
      Theory.render();
      Vseross.render();
      Secret.render();
      Progress.render();
      UI.updateResources();
      Mine.startIdleTick();
    });
  },

  // ── Загрузка прогресса ────────────────────────────────────────────────────
  async loadProgress() {
    try {
      const resp = await fetch(`${this.API}/progress?tg_id=${State.tgId}`);
      if (!resp.ok) return;
      const d = await resp.json();
      if (!d.exists) return; // новый пользователь — стартуем с нуля

      State.gold           = d.gold           ?? 0;
      State.gems           = d.gems           ?? 0;
      State.idleAccum      = d.idle_accum     ?? 0;
      State.totalAnswers   = d.total_answers  ?? 0;
      State.correctAnswers = d.correct_answers ?? 0;

      State.unlockedHorizons = d.unlocked_horizons ?? [];
      State.completedTasks   = new Set(d.completed_tasks ?? []);
      State.unlockedVseross  = d.unlocked_vseross  ?? [];
      State.completedVseross = new Set(d.completed_vseross ?? []);
      State.unlockedSecret   = d.unlocked_secret   ?? [];
      State.completedSecret  = new Set(d.completed_secret  ?? []);
    } catch (e) {
      console.warn('Не удалось загрузить прогресс:', e);
    }
  },

  // ── Сохранение прогресса ──────────────────────────────────────────────────
  async saveProgress() {
    if (!State.tgId) return; // без tg_id не сохраняем
    try {
      await fetch(`${this.API}/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tg_id:              State.tgId,
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
        }),
      });
    } catch (e) {
      console.warn('Не удалось сохранить прогресс:', e);
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
    // Сохраняем после каждого renderAll (вызывается после любого игрового действия)
    this.saveProgress();
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
