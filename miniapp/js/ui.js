// Утилиты интерфейса
const UI = {
  _toastTimer: null,

  updateResources() {
    document.getElementById('res-gold').textContent = Math.floor(State.gold);
    document.getElementById('res-gems').textContent = State.gems;
    const p = Math.floor(State.idleAccum);
    const btn = document.getElementById('collect-btn');
    if (btn) btn.textContent = p > 0 ? `Собрать (${p})` : 'Собрать';
  },

  toast(msg, cls = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast show ${cls}`;
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => t.classList.remove('show'), 2500);
  },

  particle(text, color) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.textContent = text;
    p.style.color = color;
    p.style.left = (25 + Math.random() * 50) + 'vw';
    p.style.top = '50vh';
    document.body.appendChild(p);
    setTimeout(() => p.remove(), 1000);
  },
};
