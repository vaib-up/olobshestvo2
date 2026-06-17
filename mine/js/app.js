// Точка входа — инициализация, навигация, сохранение прогресса
const App = {

  API: 'https://olobshestvo2.online',
  LS_KEY: 'mine_progress_v1',

  init() {
    if (window.Telegram?.WebApp) {
      Telegram.WebApp.expand();
      Telegram.WebApp.setHeaderColor('#0f0e0c');
      const user = Telegram.WebApp.initDataUnsafe?.user;
      State.tgId = user?.id ?? null;
    }

    Promise.all([
      Mine.loadData(),
      Vseross.loadData(),
      Secret.loadData(),
    ]).then(async () => {
      await this.loadProgress();
      Mine.render();
      Theory.render();
      Vseross.render();
      Secret.render();
      Progress.render();
      UI.updateResources();
      Mine.startIdleTick();
    });
  },

  // ── Сериализация / десериализация State ───────────────────────────
  _stateToObj() {
    return {
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
  },

  _applyObj(d) {
    if (!d) return;
    State.gold           = d.gold            ?? State.gold;
    State.gems           = d.gems            ?? State.gems;
    State.idleAccum      = d.idle_accum      ?? State.idleAccum;
    State.totalAnswers   = d.total_answers   ?? State.totalAnswers;
    State.correctAnswers = d.correct_answers ?? State.correctAnswers;
    if (Array.isArray(d.unlocked_horizons) && d.unlocked_horizons.length)
      State.unlockedHorizons = d.unlocked_horizons;
    if (Array.isArray(d.completed_tasks)   && d.completed_tasks.length)
      State.completedTasks   = new Set(d.completed_tasks);
    if (Array.isArray(d.unlocked_vseross)  && d.unlocked_vseross.length)
      State.unlockedVseross  = d.unlocked_vseross;
    if (Array.isArray(d.completed_vseross) && d.completed_vseross.length)
      State.completedVseross = new Set(d.completed_vseross);
    if (Array.isArray(d.unlocked_secret)   && d.unlocked_secret.length)
      State.unlockedSecret   = d.unlocked_secret;
    if (Array.isArray(d.completed_secret)  && d.completed_secret.length)
      State.completedSecret  = new Set(d.completed_secret);
  },

  // ── Загрузка: сервер → localStorage ──────────────────────────────────
  async loadProgress() {
    let loaded = false;

    // 1. Пробуем сервер (только если есть tgId)
    if (State.tgId) {
      try {
        const resp = await fetch(`${this.API}/progress?tg_id=${State.tgId}`);
        if (resp.ok) {
          const d = await resp.json();
          if (d.exists) {
            this._applyObj(d);
            loaded = true;
          }
        }
      } catch (e) {
        console.warn('Сервер недоступен, берём localStorage:', e);
      }
    }

    // 2. Если сервер не ответил — берём из localStorage
    if (!loaded) {
      try {
        const raw = localStorage.getItem(this.LS_KEY);
        if (raw) {
          this._applyObj(JSON.parse(raw));
          loaded = true;
        }
      } catch (e) {
        console.warn('localStorage недоступен:', e);
      }
    }

    // 3. Новый пользователь — открываем первый горизонт
    if (!loaded && State.mineData.length) {
      State.unlockedHorizons = [State.mineData[0].id];
    }
  },

  // ── Сохранение: localStorage сразу + сервер асинхронно ───────────────
  saveProgress() {
    const obj = this._stateToObj();

    // Мгновенно в localStorage — работает всегда
    try {
      localStorage.setItem(this.LS_KEY, JSON.stringify(obj));
    } catch (e) {
      console.warn('localStorage ошибка:', e);
    }

    // Асинхронно на сервер — если есть tgId
    if (State.tgId) {
      fetch(`${this.API}/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tg_id: State.tgId, ...obj }),
      }).catch(e => console.warn('Сервер недоступен при сохранении:', e));
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
