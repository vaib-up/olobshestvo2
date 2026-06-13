// Теория — полностью независимый раздел, только чтение
// TODO: заменить _data на fetch('data/theory_data.json')
const Theory = {

  _data: [
    {
      id: 'soc', name: 'Социология', icon: '👥',
      entries: [
        { id: 'stratification', title: 'Социальная стратификация', preview: 'Теория Сорокина, оси неравенства, мобильность' },
        { id: 'socialization',  title: 'Социализация личности',    preview: 'Первичная и вторичная, Дж. Мид, ресоциализация' },
        { id: 'deviance',       title: 'Девиация',                 preview: 'Аномия Дюркгейма, типы Мертона' },
      ]
    },
    {
      id: 'econ', name: 'Экономика', icon: '📊',
      entries: [
        { id: 'market', title: 'Рыночная система',    preview: 'Спрос, предложение, равновесие' },
        { id: 'gdp',    title: 'ВВП и макроэкономика', preview: 'Три метода, реальный vs номинальный' },
      ]
    },
    {
      id: 'law', name: 'Право', icon: '⚖️',
      entries: [
        { id: 'constitution', title: 'Конституционное право', preview: 'КРФ 1993, основы строя, поправки' },
      ]
    },
    {
      id: 'pol', name: 'Политология', icon: '🏛️',
      entries: [
        { id: 'power', title: 'Природа политической власти', preview: 'Легитимность по Веберу, ресурсы власти' },
      ]
    },
    {
      id: 'phil', name: 'Философия', icon: '🦉',
      entries: [
        { id: 'epistemology', title: 'Теория познания', preview: 'Эмпиризм, рационализм, Кант, Поппер' },
      ]
    },
  ],

  render(filter = '') {
    const screen = document.getElementById('screen-theory');
    const q = filter.toLowerCase().trim();
    screen.innerHTML = `
      <div class="screen-title">Теория</div>
      <div class="theory-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
          style="color:var(--text-faint);flex-shrink:0">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        <input type="text" placeholder="Поиск по темам..."
          oninput="Theory.render(this.value)" value="${filter}"
          style="flex:1;background:none;border:none;outline:none;font:inherit;font-size:var(--text-sm);color:var(--text)">
      </div>`;

    for (const section of this._data) {
      const visible = section.entries.filter(e =>
        !q || e.title.toLowerCase().includes(q) || section.name.toLowerCase().includes(q)
      );
      if (!visible.length) continue;

      const sec = document.createElement('div');
      sec.style.marginBottom = 'var(--space-6)';
      sec.innerHTML = `<div class="section-label">${section.icon} ${section.name}</div>`;
      visible.forEach(e => {
        const card = document.createElement('div');
        card.className = 'theory-entry';
        card.innerHTML = `
          <div class="theory-entry-icon">${section.icon}</div>
          <div class="theory-entry-body">
            <div class="theory-entry-title">${e.title}</div>
            <div class="theory-entry-sub">${e.preview}</div>
          </div>
          <div style="color:var(--text-faint)">›</div>`;
        card.onclick = () => this.openEntry(section, e);
        sec.appendChild(card);
      });
      screen.appendChild(sec);
    }
  },

  openEntry(section, entry) {
    // TODO: заменить на реальный контент из theory_data.json
    Modal.open(() => {
      document.getElementById('modal-content').innerHTML = `
        <div style="display:flex;align-items:center;gap:var(--space-3);margin-bottom:var(--space-4)">
          <div style="font-size:1.4rem">${section.icon}</div>
          <div>
            <div style="font-weight:700">${entry.title}</div>
            <div style="font-size:var(--text-xs);color:var(--text-muted)">${section.name}</div>
          </div>
        </div>
        <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
          padding:var(--space-4);font-size:var(--text-sm);line-height:1.8;color:var(--text-muted);
          margin-bottom:var(--space-4)">
          // TODO: здесь будет реальный текст из theory_data.json
        </div>
        <button class="btn-secondary" onclick="Modal.close()">Закрыть</button>`;
    });
  },
};
