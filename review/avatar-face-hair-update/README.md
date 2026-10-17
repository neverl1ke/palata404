# Palata 404 — нові аватари, обличчя та каре

Робоча гілка: **`feature/paper-doll-avatar-face-hair-update`**. Базовий коміт: `a85ccb4390dab37fa373b18d8515fbb803e31842`. `main` не змінювався; перенесення та злиття не виконувались.

## Результат

- Замінено обидва базові аватари на надані чорні варіанти.
- Додано два нові PNG облич як парний пункт **«Нове обличчя»**: чоловіча модель отримує чоловічий PNG, жіноча — жіночий. Попередні варіанти залишаються окремими пунктами.
- Додано **«Каре з чубчиком»** для обох статей. Воно використовує **один і той самий PNG**, побайтово тотожний наданому файлу. Початковий колір чорний; чинна палітра також працює.
- Шари збережено: **тіло (0) → голова (1) → волосся (9)**. Одяг зберігає свої попередні шари.
- UI, формат збережень, інвентар, бойові характеристики та незалежні комплекти «Пацієнт / Трип» залишилися чинними.

## Джерела та технічна реєстрація

Використано саме п'ять PNG з `palata404_assets_fixedd.zip`. Усі мають справжній альфа-канал з діапазоном 0…255. Генерація зображень не застосовувалася. Початкові та фінальні SHA-256, розміри й параметри записані у `tests/fixtures/avatar-face-hair-update.json`.

| Наданий PNG | Вихідне полотно | Ресурс у грі |
|---|---|---|
| `01_female_base_black.png` | 941×1672 | `base_female.png` |
| `02_male_base_black.png` | 941×1672 | `base_male.png` |
| `03_female_new_face.png` | 431×384 | `assets/wardrobe/faces/female_alternative_head.png` |
| `04_male_new_face.png` | 1261×1247 | `assets/wardrobe/faces/male_alternative_head.png` |
| `05_unisex_bob_hair.png` | 941×1672 | `assets/wardrobe/hair/unisex_bob_bangs.png` |

Бази залишилися **941×1672, X=0, Y=0, масштаб 1:1**. Використано текстуру нових тіл без деформації окремих частин. Альфа-контур узгоджено з попередніми затвердженими базами: його контрольні суми збігаються. Це зберігає зовнішню геометрію голови, плечей, тазу, рук і стоп. Відтінок відкритої шкіри локально узгоджено з попередніми моделями, особливо біля стиків шиї, щоб старі голови залишалися сумісними.

Нові обличчя технічно очищені від зайвих крайових пікселів і темного матового обідка. Внутрішні області зроблено непрозорими, зовнішній край залишено згладженим. Із жіночого портрета прибрано нижню частину із синім топом: у гру потрапляє саме голова/шия. Для кожної статі використано окремий вигнутий перехід шиї та окрему маску приховування базової голови.

| Накладка | Реєстрація вихідного PNG | Фінальне розміщення |
|---|---|---|
| Жіноче обличчя | Масштаб 1,02; X=254,7 → 255 px, Y=17 px | Запечено в полотно 941×1672; runtime X=0, Y=0, 1:1 |
| Чоловіче обличчя | Масштаб 0,275; X=300,5 → 300 px, Y=8 px | Запечено в полотно 941×1672; runtime X=0, Y=0, 1:1 |
| Каре, обидві статі | Масштаб **0,23** | **X=365,9; Y=−59,9; width=216,43; height=384,56** |

Від'ємний Y каре компенсує великі прозорі поля у вихідному PNG: видиме волосся починається всередині сцени, чубчик не обрізається. Старі параметри зачісок не змінені. Маска маківки тепер розпізнає будь-який активний предмет слота обличчя, включно з новим; контури раніше затверджених масок залишилися незмінними.

## Перевірки

- **71 тест JavaScript — пройдено.** Новий тест перевіряє реальні шляхи обох облич, масок і спільного PNG каре, порядок шарів та збереження вибору.
- **73 тести Python/Chromium — пройдено.** Перевірено нові ресурси, геометрію баз, попередні обличчя й зачіски, одяг, обидва режими, десктоп 1440 px, телефон 390 px, перемикання статі, вибір після перезавантаження, відсутність JS-помилок і відсутніх PNG.
- Перевірки старих баз оновлено під прямо запитану заміну. Порівняння туніки з погодженим еталоном продовжує перевіряти її непрозору тканину; геометрію й нові тіла окремо контролює новий тест ресурсів.
- **24 приклади на чотирьох фонах:** обидві бази, нові обличчя без волосся та нові обличчя з каре — білий, сірий, чорний, зелений.
- **24 примірки попередніх/нових голів із каре або без волосся** та **16 примірок нових облич з усіма зачісками**, включно з варіантом без волосся.
- У звіті **20 реальних скріншотів Chromium**: галереї побудовані тим самим `renderPaperDollAt`, повноростові кадри взяті з гардероба. Помилок JavaScript у галереях немає.

Базові азійські, молоді, виснажені та старші PNG, їхні маски, попередні PNG волосся, посадки, палітра й туніки не змінені. Остаточний художній вигляд нових елементів доступний нижче для погодження. У `main` цей варіант не опублікований.

## Файли

- `base_female.png`, `base_male.png`.
- `assets/wardrobe/faces/female_alternative_head.png`, `assets/wardrobe/faces/male_alternative_head.png`.
- `assets/wardrobe/faces/masks/female_alternative_body.png`, `assets/wardrobe/faces/masks/male_alternative_body.png`.
- `assets/wardrobe/hair/unisex_bob_bangs.png`.
- `paper-doll-data.js`, `paper-doll.js`, `index.html`.
- `art/hospital-shirt.html` — лише кеш-версії посилань на замінені бази.
- `tests/game-logic.test.cjs`, `tests/test_game.py`, `tests/fixtures/avatar-face-hair-update.json`.
- `tools/prepare-avatar-update.py`, `tools/review-avatar-update.py`.
- Цей звіт і 20 знімків у `review/avatar-face-hair-update/`.

Обробку можна відтворити через `tools/prepare-avatar-update.py`, надавши каталог вихідних п'яти PNG і попередні бази з коміту `a85ccb4` як `--reference-dir`. Залежності обробки: Pillow, NumPy, SciPy. Для повторних знімків: `python tools/review-avatar-update.py` з установленим Playwright Chromium.

## Повноростова примірка

### Жінка

| Нова база | Нове обличчя | Нове обличчя + каре |
|---|---|---|
| ![База](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-base-wardrobe.jpg) | ![Обличчя](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-face-wardrobe.jpg) | ![Каре](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-bob-wardrobe.jpg) |

**Нові обличчя з усіма зачісками**

![Усі зачіски — Жінка](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-all-hair-new-face.jpg)

**Старі та нові голови без волосся / з новим каре**

![Усі обличчя — Жінка](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-all-faces-bob.jpg)

**Нове обличчя: чотири фони, PNG без втрат**

![Чотири фони — Жінка](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-four-backgrounds.png)

[База у повний зріст на чотирьох фонах](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-base-four-backgrounds.jpg) · [Каре на чотирьох фонах](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-bob-four-backgrounds.jpg)

**Режим «Пацієнт» із чинною тунікою**

![Пацієнт — Жінка](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-patient-desktop.jpg)

[Сцена на телефоні, viewport 390×844](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/female-patient-phone.jpg)

### Чоловік

| Нова база | Нове обличчя | Нове обличчя + каре |
|---|---|---|
| ![База](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-base-wardrobe.jpg) | ![Обличчя](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-face-wardrobe.jpg) | ![Каре](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-bob-wardrobe.jpg) |

**Нові обличчя з усіма зачісками**

![Усі зачіски — Чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-all-hair-new-face.jpg)

**Старі та нові голови без волосся / з новим каре**

![Усі обличчя — Чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-all-faces-bob.jpg)

**Нове обличчя: чотири фони, PNG без втрат**

![Чотири фони — Чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-four-backgrounds.png)

[База у повний зріст на чотирьох фонах](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-base-four-backgrounds.jpg) · [Каре на чотирьох фонах](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-bob-four-backgrounds.jpg)

**Режим «Пацієнт» із чинною тунікою**

![Пацієнт — Чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-patient-desktop.jpg)

[Сцена на телефоні, viewport 390×844](https://raw.githubusercontent.com/neverl1ke/palata404/feature/paper-doll-avatar-face-hair-update/review/avatar-face-hair-update/male-patient-phone.jpg)
