// Шахта: загрузка данных, навигация (издание → класс → горизонты), idle, квиз
const Mine = {

  // Текущий выбор навигации
  _nav: { view: 'editions', editionId: null, gradeId: null },

  async loadData() {
    try {
      const res = await fetch('data/mine_data.json');
      const data = await res.json();
      State.mineEditions = data.editions;
      // Собираем плоский список горизонтов для совместимости с прогрессом
      State.mineData = [];
      for (const ed of data.editions) {
        for (const gr of ed.grades) {
          for (const h of gr.horizons) {
            State.mineData.push(h);
          }
        }
      }
      if (State.mineData.length
          && !State.unlockedHorizons.length
          && State.completedTasks.size === 0
          && State.gold === 0) {
        State.unlockedHorizons.push(State.mineData[0].id);
      }
    } catch (e) {
      console.error('Не удалось загрузить mine_data.json', e);
      State.mineEditions = [];
      State.mineData = [];
    }
  },

  render() {
    const screen = document.getElementById('screen-mine');
    screen.classList.add('shaft-screen');
    screen.innerHTML = '';

    // Idle-тикер всегда сверху
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

    const { view, editionId, gradeId } = this._nav;

    if (view === 'editions') {
      this._renderEditions(screen);
    } else if (view === 'grades') {
      this._renderGrades(screen, editionId);
    } else if (view === 'horizons') {
      this._renderHorizons(screen, editionId, gradeId);
    }
  },

  // ── Экран 1: список изданий (ПВГ25, ПВГ24...) ────────────────────
  _renderEditions(screen) {
    const wrap = document.createElement('div');
    wrap.className = 'mine-nav-list';

    (State.mineEditions || []).forEach(ed => {
      const card = document.createElement('div');
      card.className = 'mine-nav-card';
      card.style.setProperty('--card-color', ed.color || '#4a9ebb');

      // Считаем общий прогресс по изданию
      let total = 0, done = 0;
      for (const gr of ed.grades) {
        for (const h of gr.horizons) {
          total += h.tasks.length;
          done  += h.tasks.filter(t => State.completedTasks.has(t.id)).length;
        }
      }
      const pct = total ? Math.round(done / total * 100) : 0;

      card.innerHTML = `
        <div class="mnc-icon">${ed.icon}</div>
        <div class="mnc-body">
          <div class="mnc-name">${ed.name}</div>
          <div class="mnc-meta">${done}/${total} вопросов · ${pct}%</div>
          <div class="mnc-bar"><div class="mnc-bar-fill" style="width:${pct}%"></div></div>
        </div>
        <div class="mnc-arrow">›</div>`;

      card.onclick = () => {
        this._nav = { view: 'grades', editionId: ed.id, gradeId: null };
        this.render();
      };
      wrap.appendChild(card);
    });

    screen.appendChild(wrap);
  },

  // ── Экран 2: выбор класса (11, 10, 9) ────────────────────────────
  _renderGrades(screen, editionId) {
    const ed = (State.mineEditions || []).find(e => e.id === editionId);
    if (!ed) return;

    // Кнопка «Назад»
    screen.appendChild(this._backBtn(() => {
      this._nav = { view: 'editions', editionId: null, gradeId: null };
      this.render();
    }, ed.name));

    const wrap = document.createElement('div');
    wrap.className = 'mine-nav-list';

    ed.grades.forEach(gr => {
      const card = document.createElement('div');
      card.className = 'mine-nav-card';
      card.style.setProperty('--card-color', ed.color || '#4a9ebb');

      let total = 0, done = 0;
      for (const h of gr.horizons) {
        total += h.tasks.length;
        done  += h.tasks.filter(t => State.completedTasks.has(t.id)).length;
      }
      const pct   = total ? Math.round(done / total * 100) : 0;
      const empty = gr.horizons.length === 0;

      card.innerHTML = `
        <div class="mnc-icon">${gr.icon}</div>
        <div class="mnc-body">
          <div class="mnc-name">${gr.label}</div>
          <div class="mnc-meta">${empty ? 'Скоро...' : `${done}/${total} вопросов · ${pct}%`}</div>
          ${!empty ? `<div class="mnc-bar"><div class="mnc-bar-fill" style="width:${pct}%"></div></div>` : ''}
        </div>
        ${!empty ? '<div class="mnc-arrow">›</div>' : '<div class="mnc-arrow" style="opacity:.3">›</div>'}`;

      if (!empty) {
        card.onclick = () => {
          this._nav = { view: 'horizons', editionId, gradeId: gr.id };
          this.render();
        };
      } else {
        card.style.opacity = '0.55';
        card.style.cursor = 'default';
      }

      wrap.appendChild(card);
    });

    screen.appendChild(wrap);
  },

  // ── Экран 3: список горизонтов (вопросов) ─────────────────────────
  _renderHorizons(screen, editionId, gradeId) {
    const ed = (State.mineEditions || []).find(e => e.id === editionId);
    const gr = ed?.grades.find(g => g.id === gradeId);
    if (!gr) return;

    // Кнопка «Назад»
    screen.appendChild(this._backBtn(() => {
      this._nav = { view: 'grades', editionId, gradeId: null };
      this.render();
    }, `${ed.name} · ${gr.label}`));

    gr.horizons.forEach((h, i) => {
      screen.appendChild(this._buildFloor(h, i));
    });
  },

  // ── Кнопка «Назад» ───────────────────────────────────────────────
  _backBtn(onBack, subtitle) {
    const div = document.createElement('div');
    div.className = 'mine-breadcrumb';
    div.innerHTML = `<button class="mine-back-btn" >‹ Назад</button><span class="mine-bc-sub">${subtitle}</span>`;
    div.querySelector('.mine-back-btn').onclick = onBack;
    return div;
  },

  // ── Горизонт (карточка вопроса) — без изменений ─────────────────
  _buildFloor(h, idx) {
    const unlocked  = State.unlockedHorizons.includes(h.id);
    const cost      = h.unlockCost ?? 4;
    const canAfford = State.gold >= cost;

    const done    = h.tasks.filter(t => State.completedTasks.has(t.id)).length;
    const total   = h.tasks.length;
    const pct     = total ? Math.round(done / total * 100) : 0;
    const allDone = done === total && total > 0;

    let btnCls, btnTxt;
    if (unlocked && allDone) {
      btnCls = 'btn-dig done';
      btnTxt = '✓ Готово';
    } else if (unlocked) {
      btnCls = 'btn-dig';
      btnTxt = '⛏ Копать';
    } else if (canAfford) {
      btnCls = 'btn-dig unlock';
      btnTxt = `🔓 ${cost}⚡`;
    } else {
      btnCls = 'btn-dig locked';
      btnTxt = `🔒 ${cost}⚡`;
    }

    const isActive = unlocked && !allDone;
    const isLocked = !unlocked && !canAfford;

    const floor = document.createElement('div');
    floor.className = 'floor' +
      (isActive ? ' active-floor' : '') +
      (isLocked ? ' floor-locked'  : '');

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
        <button class="${btnCls}" onclick="Mine.handleBtn('${h.id}')">${btnTxt}</button>
      </div>`;

    return floor;
  },

  handleBtn(hid) {
    const h = State.mineData.find(x => x.id === hid);
    if (!h) return;

    if (!State.unlockedHorizons.includes(h.id)) {
      const cost = h.unlockCost ?? 4;
      if (State.gold < cost) {
        UI.toast(`Недостаточно ⚡ (нужно ${cost})`, 'gold');
        return;
      }
      State.gold -= cost;
      State.unlockedHorizons.push(hid);
      UI.updateResources();
      UI.particle(`🔓 ${h.name}`, h.color);
      UI.toast(`Открыт: ${h.name}!`, 'green');
      App.renderAll();
      return;
    }

    const task = h.tasks.find(t => !State.completedTasks.has(t.id));
    if (task) this.openTask(h, task);
    else UI.toast('Горизонт пройден! 🎉', 'green');
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
      return; // Квиз окончен — модал закрывается кнопкой «Закрыть» после последнего вопроса
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
    const { horizon, task } = this._quizState;
    State.totalAnswers++;
    document.querySelectorAll('.quiz-option').forEach(b => b.classList.add('disabled'));
    const fb = document.getElementById('qfb');
    const isCorrect = chosen === correct;

    if (isCorrect) {
      document.querySelectorAll('.quiz-option')[chosen].classList.add('correct');
      State.correctAnswers++;
      this._quizState.correct++;
      fb.className = 'quiz-feedback show ok';
      fb.textContent = '✓ Верно! ' + (q.explain || '');
      // Начисляем награду сразу за правильный ответ
      State.gold += 5;
      UI.particle('+5 ⚡', '#c89b4a');
    } else {
      document.querySelectorAll('.quiz-option')[chosen].classList.add('wrong');
      document.querySelectorAll('.quiz-option')[correct].classList.add('correct');
      fb.className = 'quiz-feedback show fail';
      fb.textContent = '✗ Неверно. ' + (q.explain || '');
    }

    // Переходим к следующему вопросу через 2.2с, но на последнем — кнопка «Закрыть»
    this._quizState.qi++;
    const isLast = this._quizState.qi >= task.questions.length;

    if (isLast) {
      // Последний вопрос — засчитываем задание и показываем кнопку «Закрыть»
      State.completedTasks.add(task.id);
      if (horizon.tasks.every(t => State.completedTasks.has(t.id))) {
        State.gems += 1;
        UI.particle('💎 +1', '#4a9ebb');
        setTimeout(() => UI.toast(`"${horizon.name}" пройден! +1 💎`, 'green'), 400);
      }
      const btn = document.createElement('button');
      btn.className = 'btn-primary';
      btn.style.marginTop = 'var(--space-4)';
      btn.textContent = 'Закрыть';
      btn.onclick = () => { Modal.close(); App.renderAll(); };
      fb.parentNode.appendChild(btn);
    } else {
      setTimeout(() => { this._renderQuizStep(); }, 2200);
    }
  },

  finishTask(_unused) {
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
      const rate = this._idleRate();
      const el   = document.getElementById('idle-rate');
      if (el) el.textContent = `+${rate} ⚡/мин`;
      const btn = document.getElementById('collect-btn');
      if (btn) btn.textContent = rate > 0 ? `Собрать (+${rate})` : 'Собрать';
    }, 60_000);
  },

  collect() {
    const rate = this._idleRate();
    if (rate === 0) { UI.toast('Нечего собирать — открой горизонты!', 'gold'); return; }
    State.gold += rate;
    UI.updateResources();
    UI.particle(`+${rate} ⚡`, '#c89b4a');
  },
};
