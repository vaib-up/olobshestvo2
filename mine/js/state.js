// Игровое состояние — единый источник правды
const State = {
  gold: 0,
  gems: 0,
  idleAccum: 0,

  // Какие горизонты разблокированы (id строкой)
  unlockedHorizons: [],

  // Какие задания в шахте пройдены (Set из id заданий)
  completedTasks: new Set(),

  // Статистика ответов
  totalAnswers: 0,
  correctAnswers: 0,

  // Данные шахты (горизонты + задания), загружаются из mine_data.json
  mineData: [],
};
