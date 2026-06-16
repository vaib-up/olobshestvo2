// Теория — RAG-поиск + история запросов (последние 10)
const Theory = {

  API: 'https://olobshestvo2.online',
  HISTORY_KEY: 'theory_history',
  MAX_HISTORY: 10,

  // ── Хранение истории ─────────────────────────────────────────
  _getHistory() {
    try { return JSON.parse(localStorage.getItem(this.HISTORY_KEY) || '[]'); }
    catch { return []; }
  },

  _saveHistory(items) {
    localStorage.setItem(this.HISTORY_KEY, JSON.stringify(items));
  },

  _addToHistory(topic, answer) {
    const history = this._getHistory();
    // Убираем дубликат если есть
    const filtered = history.filter(h => h.topic.toLowerCase() !== topic.toLowerCase());
    filtered.unshift({ topic, answer, ts: Date.now() });
    this._saveHistory(filtered.slice(0, this.MAX_HISTORY));
  },

  // ── Рендер ──────────────────────────────────────────────────
  render() {
    const screen = document.getElementById('screen-theory');
    const history = this._getHistory();

    screen.innerHTML = `
      <div class="screen-title">Теория</div>

      <!-- Поле запроса -->
      <div style="padding:0 var(--space-4) var(--space-4)">
        <div class="theory-search" style="margin-bottom:var(--space-3)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            style="color:var(--text-faint);flex-shrink:0">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input id="theory-input" type="text"
            placeholder="Спроси по любой теме..."
            style="flex:1;background:none;border:none;outline:none;font:inherit;
              font-size:var(--text-sm);color:var(--text)"
            onkeydown="if(event.key==='Enter')Theory.ask()">
        </div>
        <button class="btn-primary" onclick="Theory.ask()" id="theory-ask-btn">
          🔍 Спросить
        </button>
        <div id="theory-result" style="margin-top:var(--space-4)"></div>
      </div>

      <!-- История — показываем только если есть записи -->
      <div id="theory-history-block" style="padding:0 var(--space-4) var(--space-8)">
        ${ history.length ? `<div class="section-label">История запросов</div>` : '' }
        ${ history.map((h, i) => this._historyCard(h, i)).join('') }
      </div>`;
  },

  _historyCard(h, i) {
    const date = new Date(h.ts).toLocaleString('ru', {
      day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'
    });
    // Превью — первые 120 символов ответа
    const preview = h.answer.length > 120 ? h.answer.slice(0, 120) + '...' : h.answer;
    return `
      <div class="theory-entry" style="flex-direction:column;align-items:flex-start;gap:var(--space-2)"
        onclick="Theory.toggleHistory(${i})">
        <div style="display:flex;align-items:center;gap:var(--space-2);width:100%">
          <div style="font-size:1rem">📖</div>
          <div style="flex:1;min-width:0">
            <div class="theory-entry-title" style="white-space:normal">${h.topic}</div>
            <div class="theory-entry-sub">${date}</div>
          </div>
          <div id="theory-chevron-${i}" style="color:var(--text-faint);transition:transform .2s">›</div>
        </div>
        <div id="theory-ans-${i}" style="display:none;font-size:var(--text-sm);line-height:1.8;
          color:var(--text-muted);border-top:1px solid var(--border);padding-top:var(--space-3);width:100%">
          ${h.answer.replace(/\n/g, '<br>')}
        </div>
      </div>`;
  },

  toggleHistory(i) {
    const el = document.getElementById(`theory-ans-${i}`);
    const ch = document.getElementById(`theory-chevron-${i}`);
    if (!el) return;
    const open = el.style.display !== 'none';
    el.style.display = open ? 'none' : 'block';
    if (ch) ch.style.transform = open ? '' : 'rotate(90deg)';
  },

  // ── Запрос к RAG ──────────────────────────────────────────
  async ask() {
    const input = document.getElementById('theory-input');
    const topic = input?.value?.trim();
    if (!topic) { UI.toast('Введи тему запроса', 'gold'); return; }

    const btn = document.getElementById('theory-ask-btn');
    const result = document.getElementById('theory-result');

    // Состояние загрузки
    btn.disabled = true;
    btn.textContent = '⏳ Загрузка...';
    result.innerHTML = `
      <div style="display:flex;align-items:center;gap:var(--space-3);
        color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4) 0">
        <div style="width:18px;height:18px;border:2px solid var(--primary);
          border-top-color:transparent;border-radius:50%;
          animation:spin .8s linear infinite"></div>
        Ищу ответ в базе знаний...
      </div>`;

    // Добавляем keyframes если ещё не добавлены
    if (!document.getElementById('spin-style')) {
      const s = document.createElement('style');
      s.id = 'spin-style';
      s.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
      document.head.appendChild(s);
    }

    try {
      const resp = await fetch(`${this.API}/theory`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic })
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const answer = data.answer || 'Ответ не получен';

      // Отображаем ответ
      result.innerHTML = `
        <div style="background:var(--primary-dim);border:1px solid var(--primary);
          border-radius:var(--radius-xl);padding:var(--space-4)">
          <div style="font-size:var(--text-xs);color:var(--primary);font-weight:700;
            margin-bottom:var(--space-3)">📖 ${topic}</div>
          <div style="font-size:var(--text-sm);line-height:1.8;color:var(--text)">
            ${answer.replace(/\n/g, '<br>')}
          </div>
        </div>`;

      // Сохраняем в историю
      this._addToHistory(topic, answer);
      input.value = '';
      // Обновляем блок истории без полного ререндера
      this._refreshHistoryBlock();

    } catch (e) {
      result.innerHTML = `
        <div style="background:#2a0c0e;border:1px solid var(--danger);
          border-radius:var(--radius-xl);padding:var(--space-4);
          font-size:var(--text-sm);color:#e07070">
          ⚠️ Ошибка связи с сервером. Проверь интернет.
        </div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = '🔍 Спросить';
    }
  },

  _refreshHistoryBlock() {
    const history = this._getHistory();
    const block = document.getElementById('theory-history-block');
    if (!block) return;
    block.innerHTML =
      (history.length ? `<div class="section-label">История запросов</div>` : '') +
      history.map((h, i) => this._historyCard(h, i)).join('');
  },
};
