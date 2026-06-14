// Секретная Шахта — загрузка данных, рендер, задания
const Secret = {

  async loadData() {
    try {
      const res = await fetch('data/secret_data.json');
      const data = await res.json();
      State.secretData = data.horizons;
      if (State.secretData.length && !State.unlockedSecret.length) {
        State.unlockedSecret.push(State.secretData[0].id);
      }
    } catch (e) {
      console.error('Не удалось загрузить secret_data.json', e);
      State.secretData = [];
    }
  },

  render() {
    const screen = document.getElementById('screen-secret');
    screen.innerHTML = '';

    const header = document.createElement('div');
    header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)';
    header.innerHTML = `
      <div style="font-size:var(--text-lg);font-weight:700">🔐 Секретная Шахта</div>
      <div style="font-size:var(--text-xs);font-weight:600;color:var(--text-muted);
        background:var(--surface-2);border:1px solid var(--border);
        border-radius:var(--radius-full);padding:var(--space-1) var(--space-3)" id="secret-depth-badge">
        Горизонт ${State.unlockedSecret.length}/${State.secretData.length}
      </div>`;
    screen.appendChild(header);

    if (!State.secretData.length) {
      screen.innerHTML += '<div style="color:var(--text-muted);text-align:center;margin-top:40px">🔒 Раздел засекречен</div>';
      return;
    }

    State.secretData.forEach((h, i) => {
      screen.appendChild(this._buildHorizonCard(h, i));
    });
  },

  _buildHorizonCard(h, idx) {
    const unlocked = State.unlockedSecret.includes(h.id);
    const prevOk = idx === 0 || State.secretData[idx - 1].tasks
      .every(t => State.completedSecret.has(t.id));
    const canUnlock = !unlocked && prevOk;

    const done  = h.tasks.filter(t => State.completedSecret.has(t.id)).length;
    const total = h.tasks.length;
    const pct   = total ? Math.round(done / total * 100) : 0;
    const allDone = done === total;

    let btnCls = 'btn-dig', btnTxt = 'Копать';
    if (canUnlock)      { btnCls = 'btn-dig unlock'; btnTxt = '🔓 Открыть'; }
    else if (!unlocked) { btnCls = 'btn-dig locked'; btnTxt = '🔒 Закрыто'; }
    else if (allDone)   { btnCls = 'btn-dig done';   btnTxt = '✓ Пройден';  }

    const card = document.createElement('div');
    const isActive = unlocked && !allDone;
    card.className = 'horizon-card' +
      ((!unlocked && !canUnlock) ? ' locked' : '') +
      (isActive ? ' active-h' : '');

    card.innerHTML = `
      <div class="horizon-top">
        <div class="horizon-icon" style="background:${h.colorDim};color:${h.color}">${h.icon}</div>
        <div class="horizon-info">
          <div class="horizon-name">${h.name}</div>
          <div class="horizon-sub">${done}/${total} заданий</div>
        </div>
        <button class="${btnCls}" onclick="Secret.handleBtn('${h.id}', ${canUnlock})">${btnTxt}</button>
      </div>
      <div class="horizon-footer">
        <div class="progress-meta"><span>Прогресс</span><span>${pct}%</span></div>
        <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
      </div>`;
    return card;
  },

  handleBtn(hid, canUnlock) {
    if (canUnlock) { this.unlock(hid); return; }
    const h = State.secretData.find(x => x.id === hid);
    if (!h) return;
    const task = h.tasks.find(t => !State.completedSecret.has(t.id));
    if (task) this.openTask(h, task);
    else UI.toast('Горизонт пройден! 🎉', 'green');
  },

  unlock(hid) {
    State.unlockedSecret.push(hid);
    const h = State.secretData.find(x => x.id === hid);
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
          ${ok ? '🎉 Задание пройдено!' : 'Не все ответы верны. Попробуй ещё раз.'}
        </div>
        <button class="btn-primary" style="margin-top:var(--space-4)"
          onclick="Secret.finishTask(${ok})">
          ${ok ? '⛏ Продолжить' : 'Закрыть'}
        </button>`;
      return;
    }

    const q = task.questions[this._quizState.qi];
    const optsHTML = q.options.map((o, i) =>
      `<button class="quiz-option" onclick="Secret.answerQuiz(${i}, ${q.correct})">${o}</button>`
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
    document.querySelectorAll('.quiz-option').forEach(b => b.classList.add('disabled'));
    const fb = document.getElementById('qfb');
    if (chosen === correct) {
      document.querySelectorAll('.quiz-option')[chosen].classList.add('correct');
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
    State.completedSecret.add(task.id);
    if (success) {
      State.gold += task.questions.length * 5;
      UI.particle(`+${task.questions.length * 5} ⚡`, '#c89b4a');
      if (horizon.tasks.every(t => State.completedSecret.has(t.id))) {
        State.gems += 1;
        UI.particle('💎 +1', '#4a9ebb');
        setTimeout(() => UI.toast(`"${horizon.name}" пройден! +1 💎`, 'green'), 400);
        const idx = State.secretData.indexOf(horizon);
        if (idx < State.secretData.length - 1) {
          const next = State.secretData[idx + 1];
          if (!State.unlockedSecret.includes(next.id)) {
            setTimeout(() => this.unlock(next.id), 1200);
          }
        }
      }
    }
    Modal.close();
    App.renderAll();
  },
};
