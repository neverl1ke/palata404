# Палата 404

Браузерна гра з кімнатами десятого поверху, спорядженням, боями й локальними збереженнями. Головний вхід — [play.html](play.html).

У режимі **Пацієнт** доступні всі секції A–B–C та пацієнтський комплект. У **ТРИП** використовується бойове спорядження, а секції відкриваються за прогресом. Окрема кнопка «Відкрити всі секції» тимчасово знімає обмеження доступу без виконання завдань і видачі нагород.

На карті одиночне натискання на двері показує опис і доступні дії. Подвійне натискання або кнопка «Відкрити двері» відкриває кімнату на всю ігрову область. Листок з описом розташований поверх сцени й може бути згорнутий.

Для локального запуску відкрийте корінь репозиторію через HTTP-сервер, наприклад `python -m http.server 8000`, та перейдіть до `http://localhost:8000/play.html`.

Збереження використовує одну активну вкладку гри. Інша вкладка показує повідомлення й не завантажує старий стан: щоб продовжити в ній, закрийте першу та натисніть «Загрузить игру». Потрібен браузер із Web Locks та HTTPS або localhost. Якщо захищену сесію відкрити неможливо, вихідне збереження не змінюється.

## Документація

- [Структура проєкту](docs/project-architecture.md)
- [Правила графічних ресурсів і незмінних аватарів](docs/PAPER_DOLL_ASSET_PIPELINE.md)
- [Одяг, зовнішність і збереження](docs/paper-doll.md)
- [Поверх, кімнати й завдання](docs/FLOOR10_INTEGRATION.md)
- [Спорядження та розвиток зброї](docs/weapon-progression.md)
- [Перелік збережених джерел і фікстур](review/README.md)

## Перевірки

`node --test --test-isolation=none tests/game-logic.test.cjs`

`node --test tests/trip-switch.test.cjs tests/outline-finish.test.cjs tests/paper-doll-modes.test.cjs`

`python tools/prepare-pages.py --check`

`python tools/audit-project.py --check`

`node --test tests/profile-session.test.cjs tests/quest-interaction-feedback.test.cjs tests/quest-navigation.test.cjs`

`python -m unittest tests.test_profile_session -v`

Застарілі звіти, галереї, знімки й невикористані генератори звітів видалено з поточної версії. Оригінали графіки, погоджені майстри та потрібні тестам дані залишені. Попередній стан доступний [в історії Git](https://github.com/neverl1ke/palata404/tree/b48c82d72bc26ed8359ba84d878ecb862bdf239c). Підсумок очищення й контрольні суми — [cleanup-summary.json](docs/cleanup-summary.json).
