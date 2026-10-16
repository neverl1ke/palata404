# Фінальне затемнення волосся — локальна перевірка

Базовий commit SHA: `d50a427a96d0bd1b61f71e10b2f8c2eff84948f3`. Гілка: `main`. Ігрові зміни підготовлені локально; commit у `main` і публікація гри ще не виконані. В окремій гілці розміщено лише звіт і зображення.

| Колір | До | Після | Примірка обох аватарів |
| --- | --- | --- | --- |
| Білий | `#D8D4CC` | `#C8C3BA` | [До / після](https://raw.githubusercontent.com/neverl1ke/palata404/review-asian-heads-report/review/hair-color-final/white-before-after.jpg) |
| Яскраво-червоний | `#B43A3F` | `#9E3137` | [До / після](https://raw.githubusercontent.com/neverl1ke/palata404/review-asian-heads-report/review/hair-color-final/red-before-after.jpg) |
| Електричний синій | `#3C6CC4` | `#335BA6` | [До / після](https://raw.githubusercontent.com/neverl1ke/palata404/review-asian-heads-report/review/hair-color-final/blue-before-after.jpg) |
| Бірюзовий | `#2E8B87` | `#28736F` | [До / після](https://raw.githubusercontent.com/neverl1ke/palata404/review-asian-heads-report/review/hair-color-final/turquoise-before-after.jpg) |
| Кислотно-зелений | `#8AA62F` | `#748C28` | [До / після](https://raw.githubusercontent.com/neverl1ke/palata404/review-asian-heads-report/review/hair-color-final/lime-before-after.jpg) |

У кожному скриншоті зліва «до», справа «після»; зверху чоловік, знизу жінка. Використано справжній `renderPaperDollAt`, ті самі затверджені PNG, масштаб та світлий фон. Для «до» використано незмінений модуль палітри з базового коміту.

Змінені лише п'ять значень у `hair-color.js` та кеш-версія його URL в `index.html`. Решта палітри й алгоритм ідентичні базовому коміту. PNG, бази, одяг та всі placement залишені незмінними.

Перевірки: 66 тестів Node успішні; примірка п'яти кольорів для обох статей успішна, без помилок JavaScript. У всіх 10 поєднаннях альфа-канал збережений піксель у піксель; є понад 450 різних непрозорих тонів, без пласкої заливки.

## Інтеграція нових голів

Оригінальні PNG отримані пізніше в `palata404_asian_heads_for_codex.zip` і локально підключені без змін. Браузерна перевірка нових голів і цих п’яти кольорів завершена: [результати та виявлений дефект маківки](https://github.com/neverl1ke/palata404/blob/review-asian-heads-report/review/asian-heads/README.md).

Commit і push ігрових змін у `main` не виконані: результати передані власнику до публікації.
