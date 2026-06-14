// Точка входа — инициализация и навигация
const App = {
  init() {
    if (window.Telegram?.WebApp) {
      Telegram.WebApp.expand();
      Telegram.WebApp.setHeaderColor('#0f0e0c');
    }

    Promise.all([
      Mine.loadData(),
      Vseross.loadData(),
      Secret.loadData(),
    ]).then(() => {
      Mine.render();
      Theory.render();
      Vseross.render();
      Secret.render();
      Progress.render();
      UI.updateResources();
      Mine.startIdleTick();
    });
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
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
