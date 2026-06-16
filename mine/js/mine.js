// Шахта: загрузка данных, рендер, idle, квиз
const Mine = {

  async loadData() {
    try {
      const res = await fetch('data/mine_data.json');
      const data = await res.json();
      State.mineData = data.horizons;
      if (State.mineData.length && !State.unlockedHorizons.length) {
        State.unlockedHorizons.push(State.mineData[0].id);
      }
    } catch (e) {
      console.error('Не удалось загрузить mine_data.json', e);
      State.mineData = [];
    }
  },

  render() {
    const screen = document.getElementById('screen-mine');
    screen.classList.add('shaft-screen');
    screen.innerHTML = '';

    // Полоса пассивной добычи
    const ticker = document.createElement('div');
    ticker.className = 'idle-ticker';
    ticker.innerHTML = `
      <div style="font-size:1.4rem">⛏</div>
      <div class="idle-info">
        <div class="idle-label">Пассивная добыча</div>
        <div class="idle-rate" id="idle-rate">+0 ⚡/мин</div>
      </div>
      <div style="font-size:var(--text-xs);color:var(--text-muted)">
        Горизонт <strong style="color:var(--primary)">${State.unlockedHorizons.length}</strong>/${State.mineData.length}
      </div>
      <button class="collect-btn" id="collect-btn" onclick="Mine.collect()">Собрать</button>`;
    screen.appendChild(ticker);

    // Этажи
    State.mineData.forEach((h, i) => {
      screen.appendChild(this._buildFloor(h, i));
    });
  },

  _buildFloor(h, idx) {
    const unlocked  = State.unlockedHorizons.includes(h.id);
    const prevOk    = idx === 0 || State.mineData[idx - 1].tasks
      .every(t => State.completedTasks.has(t.id));
    const canUnlock = !unlocked && prevOk;

    const done    = h.tasks.filter(t => State.completedTasks.has(t.id)).length;
    const total   = h.tasks.length;
    const pct     = total ? Math.round(done / total * 100) : 0;
    const allDone = done === total && total > 0;

    let btnCls = 'btn-dig', btnTxt = '⛏ Копать';
    if (canUnlock)      { btnCls = 'btn-dig unlock'; btnTxt = '🔓 Открыть'; }
    else if (!unlocked) { btnCls = 'btn-dig locked'; btnTxt = '🔒'; }
    else if (allDone)   { btnCls = 'btn-dig done';   btnTxt = '✓ Готово'; }

    const isActive = unlocked && !allDone;
    const isLocked = !unlocked && !canUnlock;

    const floor = document.createElement('div');
    floor.className = 'floor' +
      (isActive  ? ' active-floor'  : '') +
      (isLocked  ? ' floor-locked'  : '');

    floor.innerHTML = `
      <div class="floor-side">
        <div class="floor-num">${idx + 1}</div>
        <div class="floor-icon">${h.icon}</div>
      </div>

      <div class="floor-body">
        <div class="floor-name">${h.name}</div>
        <div class="floor-meta">
          <span class="floor-sub">${done}/${total} · +${done * (h.incomeRate || 1)}⚡/мин</span>
          <span class="floor-sub">${pct}%</span>
        </div>
        <div class="floor-progress">
          <div class="floor-progress-fill" style="width:${pct}%"></div>
        </div>
      </div>

      <div class="floor-btn-wrap">
        <button class="${btnCls}" onclick="Mine.handleBtn('${h.id}', ${canUnlock})">${btnTxt}</button>
      </div>`;

    return floor;
  },

  handleBtn(hid, canUnlock) {
    if (canUnlock) { this.unlock(hid); return; }
    const h = State.mineData.find(x => x.id === hid);
    if (!h) return;
    const task = h.tasks.find(t => !State.completedTasks.has(t.id));
    if (task) this.openTask(h, task);
    else UI.toast('Горизонт пройден! 🎉', 'green');
  },

  unlock(hid) {
    State.unlockedHorizons.push(hid);
    const h = State.mineData.find(x => x.id === hid);
    UI.particle(`🔓 ${h.name}`, h.color);
    UI.toast(`Открыт горизонт: ${h.name}!`, 'green');
    App.renderAll();
  },

  openTask(horizon, task) {
    Modal.open(() => this._renderTaskModal(horizon, task));
  },

  _quizState: { qi: 0, correct: 0, horizon: null, task: null },

  _renderTaskModal(horizon, task) {
    this._quizState = { qi: 0, correct: 0, horizon, task };
    this._renderQuizStep();
  },

  _renderQuizStep() {
    const { horizon, task } = this._quizState;
    const mc = document.getElementById('modal-content');

    const headerHTML = `
      <div style="display:flex;align-items:center;gap:var(--space-3);
        background:var(--primary-dim);border:1px solid var(--primary);
        border-radius:var(--radius-xl);padding:var(--space-4);margin-bottom:var(--space-4)">
        <div style="font-size:1.8rem">${horizon.icon}</div>
        <div>
          <div style="font-weight:700;color:var(--primary)">${horizon.name}</div>
          <div style="font-size:var(--text-xs);color:var(--text-muted)">${task.title}</div>
        </div>
      </div>`;

    if (this._quizState.qi >= task.questions.length) {
      const ok = this._quizState.correct === task.questions.length;
      mc.innerHTML = headerHTML + `
        <div class="quiz-feedback show ${ok ? 'ok' : 'fail'}">
          ${ok
            ? `🎉 Задание пройдено! +${task.questions.length * 5} ⚡`
            : `Не все ответы верны. Попробуй ещё раз.`}
        </div>
        <button class="btn-primary" style="margin-top:var(--space-4)"
          onclick="Mine.finishTask(${ok})">
          ${ok ? '⛏ Продолжить' : 'Закрыть'}
        </button>`;
      return;
    }

    const q = task.questions[this._quizState.qi];
    const optsHTML = q.options.map((o, i) =>
      `<button class="quiz-option" onclick="Mine.answerQuiz(${i}, ${q.correct})">${o}</button>`
    ).join('');

    mc.innerHTML = headerHTML + `
      <div class="quiz-question">
        Вопрос ${this._quizState.qi + 1}/${task.questions.length}: ${q.text}
      </div>
      <div class="quiz-options">${optsHTML}</div>
      <div class="quiz-feedback" id="qfb"></div>`;
  },

  answerQuiz(chosen, correct) {
    const q = this._quizState.task.questions[this._quizState.qi];
    State.totalAnswers++;
    document.querySelectorAll('.quiz-option').forEach(b => b.classList.add('disabled'));
    const fb = document.getElementById('qfb');
    if (chosen === correct) {
      document.querySelectorAll('.quiz-option')[chosen].classList.add('correct');
      State.correctAnswers++;
      this._quizState.correct++;
      fb.className = 'quiz-feedback show ok';
      fb.textContent = '✓ Верно! ' + (q.explain || '');
    } else {
      document.querySelectorAll('.quiz-option')[chosen].classList.add('wrong');
      document.querySelectorAll('.quiz-option')[correct].classList.add('correct');
      fb.className = 'quiz-feedback show fail';
      fb.textContent = '✗ Неверно. ' + (q.explain || '');
    }
    setTimeout(() => { this._quizState.qi++; this._renderQuizStep(); }, 2200);
  },

  finishTask(success) {
    const { horizon, task } = this._quizState;
    State.completedTasks.add(task.id);
    if (success) {
      const reward = task.questions.length * 5;
      State.gold += reward;
      UI.particle(`+${reward} ⚡`, '#c89b4a');
      if (horizon.tasks.every(t => State.completedTasks.has(t.id))) {
        State.gems += 1;
        UI.particle('💎 +1', '#4a9ebb');
        setTimeout(() => UI.toast(`"${horizon.name}" пройден! +1 💎`, 'green'), 400);
        const idx = State.mineData.indexOf(horizon);
        if (idx < State.mineData.length - 1) {
          const next = State.mineData[idx + 1];
          if (!State.unlockedHorizons.includes(next.id)) {
            setTimeout(() => this.unlock(next.id), 1200);
          }
        }
      }
    }
    Modal.close();
    App.renderAll();
  },

  _idleRate() {
    let r = 0;
    for (const h of State.mineData) {
      if (!State.unlockedHorizons.includes(h.id)) continue;
      r += h.tasks.filter(t => State.completedTasks.has(t.id)).length * (h.incomeRate || 1);
    }
    return r;
  },

  startIdleTick() {
    setInterval(() => {
      const r = this._idleRate();
      const el = document.getElementById('idle-rate');
      if (el) el.textContent = `+${r} ⚡/мин`;
      if (r > 0) { State.idleAccum += r / 60; UI.updateResources(); }
    }, 1000);
  },

  collect() {
    const n = Math.floor(State.idleAccum);
    if (n <= 0) { UI.toast('Проходи задания в шахте', 'gold'); return; }
    State.gold += n;
    State.idleAccum = 0;
    UI.updateResources();
    UI.particle(`+${n} ⚡`, '#c89b4a');
    UI.toast(`Собрано ${n} ⚡`, 'gold');
  },
};
