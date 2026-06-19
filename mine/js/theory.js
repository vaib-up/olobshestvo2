// Теория — RAG-поиск + история запросов с сервера
const Theory = {

  API: 'https://olobshestvo2.online',
  MAX_HISTORY: 10,
  _history: [],  // кэш для текущей сессии, заполняется один раз в App.init()

  // ── Загрузка истории (App.init() вызывает один раз) ───────────────
  async loadHistory() {
    if (!State.tgId) return;
    try {
      const r = await fetch(`${this.API}/theory_history?tg_id=${State.tgId}`);
      if (r.ok) this._history = await r.json();
    } catch (e) {
      console.warn('loadHistory error:', e);
    }
  },

  // ── Сохранение одной записи ─────────────────────────────────
  async _saveHistoryItem(topic, answer) {
    // Обновляем кэш
    this._history = this._history.filter(
      h => h.topic.toLowerCase() !== topic.toLowerCase()
    );
    this._history.unshift({ topic, answer, ts: Date.now() });
    this._history = this._history.slice(0, this.MAX_HISTORY);

    if (!State.tgId) return;
    try {
      await fetch(`${this.API}/theory_history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tg_id: State.tgId, topic, answer, ts: Date.now() }),
      });
    } catch (e) {
      console.warn('theory_history save error:', e);
    }
  },

  // ── Рендер (синхронный) ─────────────────────────────────────────
  render() {
    const screen  = document.getElementById('screen-theory');
    const history = this._history;

    screen.innerHTML = `
      <div class="screen-title">Теория</div>

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

      <div id="theory-history-block" style="padding:0 var(--space-4) var(--space-8)">
        ${ history.length ? `<div class="section-label">История запросов</div>` : '' }
        ${ history.map((h, i) => this._historyCard(h, i)).join('') }
      </div>`;
  },

  _historyCard(h, i) {
    const date = new Date(h.ts).toLocaleString('ru', {
      day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
    });
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

  // ── Запрос к RAG ─────────────────────────────────────────────
  async ask() {
    const input  = document.getElementById('theory-input');
    const topic  = input?.value?.trim();
    if (!topic) { UI.toast('Введи тему запроса', 'gold'); return; }

    const btn    = document.getElementById('theory-ask-btn');
    const result = document.getElementById('theory-result');

    btn.disabled    = true;
    btn.textContent = '⏳ Загрузка...';
    result.innerHTML = `
      <div style="display:flex;align-items:center;gap:var(--space-3);
        color:var(--text-muted);font-size:var(--text-sm);padding:var(--space-4) 0">
        <div style="width:18px;height:18px;border:2px solid var(--primary);
          border-top-color:transparent;border-radius:50%;
          animation:spin .8s linear infinite"></div>
        Ищу ответ в базе знаний...
      </div>`;

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
        body: JSON.stringify({ topic }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data   = await resp.json();
      const answer = data.answer || 'Ответ не получен';

      result.innerHTML = `
        <div style="background:var(--primary-dim);border:1px solid var(--primary);
          border-radius:var(--radius-xl);padding:var(--space-4)">
          <div style="font-size:var(--text-xs);color:var(--primary);font-weight:700;
            margin-bottom:var(--space-3)">📖 ${topic}</div>
          <div style="font-size:var(--text-sm);line-height:1.8;color:var(--text)">
            ${answer.replace(/\n/g, '<br>')}
          </div>
        </div>`;

      await this._saveHistoryItem(topic, answer);
      input.value = '';
      this._refreshHistoryBlock();

    } catch (e) {
      result.innerHTML = `
        <div style="background:#2a0c0e;border:1px solid var(--danger);
          border-radius:var(--radius-xl);padding:var(--space-4);
          font-size:var(--text-sm);color:#e07070">
          ⚠️ Ошибка связи с сервером. Проверь интернет.
        </div>`;
    } finally {
      btn.disabled    = false;
      btn.textContent = '🔍 Спросить';
    }
  },

  _refreshHistoryBlock() {
    const block = document.getElementById('theory-history-block');
    if (!block) return;
    block.innerHTML =
      (this._history.length ? `<div class="section-label">История запросов</div>` : '') +
      this._history.map((h, i) => this._historyCard(h, i)).join('');
  },
};
