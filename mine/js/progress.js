// Прогресс — только по шахте
const Progress = {
  render() {
    const screen = document.getElementById('screen-progress');
    const allTasks = State.mineData.flatMap(h => h.tasks);
    const doneCnt = State.completedTasks.size;
    const totalCnt = allTasks.length;
    const pct = State.totalAnswers
      ? Math.round(State.correctAnswers / State.totalAnswers * 100) : 0;

    screen.innerHTML = `
      <div class="screen-title">Прогресс</div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">${doneCnt}/${totalCnt}</div>
          <div class="stat-label">Заданий пройдено</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${pct}%</div>
          <div class="stat-label">Верных ответов</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${State.unlockedHorizons.length}/${State.mineData.length}</div>
          <div class="stat-label">Горизонтов</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">${State.gems}</div>
          <div class="stat-label">Самоцветов</div>
        </div>
      </div>
      <div class="section-label" style="margin-bottom:var(--space-3)">По горизонтам</div>
      ${State.mineData.map(h => {
        const d = h.tasks.filter(t => State.completedTasks.has(t.id)).length;
        const tot = h.tasks.length;
        const p = tot ? Math.round(d / tot * 100) : 0;
        const locked = !State.unlockedHorizons.includes(h.id);
        return `
          <div class="mastery-item" ${locked ? 'style="opacity:.4"' : ''}>
            <div class="mastery-header">
              <div class="mastery-name">${h.icon} ${h.name}</div>
              <div class="mastery-pct">${p}%</div>
            </div>
            <div class="progress-track" style="margin-bottom:var(--space-2)">
              <div class="progress-fill" style="width:${p}%"></div>
            </div>
            <div style="font-size:var(--text-xs);color:var(--text-muted)">
              ${d} из ${tot} заданий${locked ? ' · 🔒' : ''}
            </div>
          </div>`;
      }).join('')}`;
  },
};
