// Глобальное состояние приложения
const State = {
  // ID пользователя Telegram (заполняется в App.init)
  tgId: null,

  // Ресурсы
  gold: 0,
  gems: 0,
  idleAccum: 0,

  // Основная шахта
  mineData: [],
  unlockedHorizons: [],
  completedTasks: new Set(),

  // Шахта Всероса
  vserossData: [],
  unlockedVseross: [],
  completedVseross: new Set(),

  // Секретная Шахта
  secretData: [],
  unlockedSecret: [],
  completedSecret: new Set(),

  // Статистика
  totalAnswers: 0,
  correctAnswers: 0,
};
