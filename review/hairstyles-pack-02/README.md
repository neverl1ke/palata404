# Палата 404 — нові зачіски, комплект 02

**Гілка для погодження:** `feature/new-hairstyles-pack-02`. У `main` зміни не перенесено. Гілка каре `preview/bob-cheek-direction` не змінена.

Додано три предмети, чотири незмінені PNG та шість незалежних реєстрацій. Усі картинки нижче — реальні браузерні скриншоти гри. Крупний план є точною DOM-копією відрендереного компонента, пропорційно збільшеного цілком до 2×; новий арт не генерувався. Загальні плани зняті зі звичайної сцени гардероба.

Оновлено чотири посадки після перегляду. [Порівняння до/після та огляд чоловічої розкуйовдженої](../hairstyles-pack-02-fit2/README.md).

## Шість примірок — огляд

### Чоловік

![Три чоловічі зачіски](../hairstyles-pack-02-fit2/male-hairstyles-pack-02-overview.jpg)

### Жінка

![Три жіночі зачіски](../hairstyles-pack-02-fit2/female-hairstyles-pack-02-overview.jpg)

## Загальний вигляд і крупні плани

Натисніть на зображення, щоб переглянути його у повному розмірі. Крупні плани мають 800×700 px; світлий фон #faf8f0, темний #1c2023.

| Примірка | Загальний вигляд | Крупний план | Темний фон |
| --- | --- | --- | --- |
| Класична коротка стрижка — Чоловік | ![Загальний вигляд](../hairstyles-pack-02-fit2/male-hair-classic-short-wardrobe.jpg) | ![Голова](../hairstyles-pack-02-fit2/male-hair-classic-short-head.jpg) | [Відкрити](../hairstyles-pack-02-fit2/male-hair-classic-short-head-dark.jpg) |
| Класична коротка стрижка — Жінка | ![Загальний вигляд](../hairstyles-pack-02-fit2/female-hair-classic-short-wardrobe.jpg) | ![Голова](../hairstyles-pack-02-fit2/female-hair-classic-short-head.jpg) | [Відкрити](../hairstyles-pack-02-fit2/female-hair-classic-short-head-dark.jpg) |
| Коротка текстурована стрижка — Чоловік | ![Загальний вигляд](../hairstyles-pack-02-fit2/male-hair-textured-short-wardrobe.jpg) | ![Голова](../hairstyles-pack-02-fit2/male-hair-textured-short-head.jpg) | [Відкрити](../hairstyles-pack-02-fit2/male-hair-textured-short-head-dark.jpg) |
| Коротка текстурована стрижка — Жінка | ![Загальний вигляд](female-hair-textured-short-wardrobe.jpg) | ![Голова](female-hair-textured-short-head.jpg) | [Відкрити](female-hair-textured-short-head-dark.jpg) |
| Волосся до плечей — Чоловік | ![Загальний вигляд](male-hair-shoulder-length-wardrobe.jpg) | ![Голова](male-hair-shoulder-length-head.jpg) | [Відкрити](male-hair-shoulder-length-head-dark.jpg) |
| Волосся до плечей — Жінка | ![Загальний вигляд](../hairstyles-pack-02-fit2/female-hair-shoulder-length-wardrobe.jpg) | ![Голова](../hairstyles-pack-02-fit2/female-hair-shoulder-length-head.jpg) | [Відкрити](../hairstyles-pack-02-fit2/female-hair-shoulder-length-head-dark.jpg) |

## Залишковий дефект чоловічого волосся до плечей

На масштабі 0.21 залишився світлий проміжок зліва біля вуха й місцями читається контур маківки. Зменшення до 0.20 ще звужує отвори, але робить зачіску коротшою та сильніше відкриває верх базової голови. Початкові 0.225 дають більші отвори біля обох вух. У каталозі залишено 0.21 як пробний компроміс; альтернативи нижче — лише порівняння.

| 0.225 — початковий | 0.21 — у каталозі | 0.20 — діагностична проба |
| --- | --- | --- |
| ![0.225](male-hair-shoulder-length-fit-225.jpg) | ![0.21](male-hair-shoulder-length-fit-210.jpg) | ![0.20](male-hair-shoulder-length-fit-200.jpg) |

Повністю усунути дефект перевіреними пропорційними перетвореннями не вдалося. PNG не редагувався: маски шкіри, дублікати голови, домальовані пасма й сторонні шари не додавалися. Потрібне окреме рішення власника щодо цього ресурсу. Решта п’ять варіантів не мають виявлених великих просвітів, непрозорих фонів, помітних яскравих ореолів або перекриття обох очей; остаточна оцінка посадки належить власнику.

## Предмети та точні параметри

| Назва | ID | PNG |
| --- | --- | --- |
| Класична коротка стрижка | `hair-classic-short` | [`classic_short_unisex_style_A.png`](../../assets/wardrobe/hair/classic_short_unisex_style_A.png) |
| Коротка текстурована стрижка | `hair-textured-short` | [`classic_short_unisex_style_B.png`](../../assets/wardrobe/hair/classic_short_unisex_style_B.png) |
| Волосся до плечей | `hair-shoulder-length` | [`male_medium_shoulder_length.png`](../../assets/wardrobe/hair/male_medium_shoulder_length.png)<br>[`female_medium_shoulder_length.png`](../../assets/wardrobe/hair/female_medium_shoulder_length.png) |

Координати на полотні 941×1672; scale відносно вихідного PNG 1254×1254. Для обох осей однаковий коефіцієнт.

| ID | Стать | x | y | width | height | scale |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `hair-classic-short` | male | 373 | 0 | 200.64 | 200.64 | 0.16 |
| `hair-classic-short` | female | 375 | -5 | 196.878 | 196.878 | 0.157 |
| `hair-textured-short` | male | 363.1766 | -10.8282 | 218.9484 | 218.9484 | 0.1746 |
| `hair-textured-short` | female | 365 | -17 | 219.45 | 219.45 | 0.175 |
| `hair-shoulder-length` | male | 336.866667 | 22.5 | 263.34 | 263.34 | 0.21 |
| `hair-shoulder-length` | female | 313.5 | 11.7155 | 321.651 | 321.651 | 0.2565 |

## Перевірки та межі

[Браузерний прогін коду 501556f](https://github.com/neverl1ke/palata404/actions/runs/38788548344): 65 Node + 63 Python — усі **128** успішні. Серед них 8 перевірок PNG / SVG, точних байтів та альфа-каналів. Перевірено перемикання між новими й попередніми зачісками, «Без зачіски», обидві статі, «Пацієнт» / «Трип», головний HUD і гардероб, туніки, збереження вибору після перезавантаження та старі збереження. Перевірено 1280×800, 390×844 і 320×568 у Chromium; фізичний телефон не використовувався.

Чотири джерела скопійовані без зміни байтів, усі RGBA 1254×1254 з alpha 0–255. У style B та жіночому волоссі до плечей є поодинокі кутові alpha-1 пікселі, які не видалялися. Оригінальні бази з архіву збігаються з базами проєкту; приклади примірок не використовуються як накладки. Шість попередніх PNG, їхні placements, аватари, туніки, інші предмети та схема збережень незмінні.

Зміни: `paper-doll-data.js`, кеш каталогу в `index.html`, чотири PNG в `assets/wardrobe/hair/`, розширені наявні тести та маніфест нового пакета, [технічний опис](../../docs/HAIRSTYLES_PACK_02.md), ці матеріали перегляду. Система Paper Doll не переписувалася.

**Очікується особисте погодження всіх шести примірок. Злиття в main не виконано.**
