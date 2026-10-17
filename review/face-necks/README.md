# Палата 404 — індивідуальні переходи шиї

Виправлення інтеграції шести наявних голів від стану `38f5ba4`. Нові обличчя не генерувалися. Знімки зроблені Chromium через справжній `renderPaperDollAt`; галереї використовують ті самі PNG, маски й CSS, що й гра.

## Причина та виправлення

Колишня спільна маска тіла починалася на `y=245`, а всі накладки згасали до `y=263`. У чоловічих варіантів цей зріз проходив через підборіддя. У жіночих не відповідав індивідуальній щелепі та ширині шиї. Накладення відмінних контурів давало звуження, сходинки й різкий перехід фактури.

Для кожної голови відновлено нижню щелепу та шию з її початкового наданого PNG. Перехід до пікселів незміненого базового тіла тепер вигнутий та індивідуальний. Окрема маска тіла приховує старий силует і запобігає подвійним краям; нижче персональної зони стику повністю повертається оригінальний аватар. Згладжено лише контур нижньої зони інтеграції.

Допоміжна накладка **шкіри** жіночої горловини також могла повторно намалювати старий край шиї. До неї застосовується відповідна маска голови. PNG тканини туніки та допоміжної накладки не змінені.

Верх усіх шести накладок, рядки `0…220` включно, збережений побайтово. Контрольні SHA верхньої частини й центральних рис обличчя записані у `tests/fixtures/face-neck-transitions.json`. Положення голів лишилося `x=0, y=0`, полотно **941×1672**, масштаб **1:1**. Азійські голови, базові аватари, зачіски, їх посадка, кольори, одяг, UI та збереження не змінені.

Порядок шарів збережений: **тіло (0) → голова (1) → волосся (9)**. Раніше погоджені маски маківки не змінені.

## Точні профілі переходів

Координати наведені в оригінальному полотні. Бічна і центральна межі різні: `start(x)=startY−startArc×min(((x−center)/radius)²,1)`, аналогічно `end(x)`. Між ними застосовується плавна інтерполяція, а не спільний горизонтальний зріз.

| Голова | Центр X / радіус | Відновлення з Y | Початок: бік → центр | Кінець: бік → центр | Перекриття | Повне повернення тіла з Y |
|---|---|---|---|---|---|---|
| Молоде · чоловік | 474 / 70 | 224 | 232 → 258 | 260 → 282 | 10 | 292 |
| Молоде · жінка | 473 / 65 | 225 | 223 → 248 | 256 → 274 | 8 | 282 |
| Виснажене · чоловік | 474 / 69 | 223 | 234 → 261 | 265 → 287 | 9 | 296 |
| Виснажене · жінка | 473 / 62 | 224 | 227 → 240 | 258 → 272 | 9 | 281 |
| Старше · чоловік | 474 / 71 | 224 | 234 → 257 | 264 → 285 | 8 | 293 |
| Старше · жінка | 474 / 64 | 226 | 225 → 245 | 258 → 276 | 7 | 283 |

## Перевірки та межі результату

- 70 тестів JavaScript: логіка, вибір, видалення масок, збереження та незмінність погоджених налаштувань.
- 71 тест Python/Chromium: ресурси, індивідуальні маски, контури, незмінність верхніх частин голів і тіла нижче стику, гардероб, обидві статі, режими та перезавантаження.
- 24 перевірки без волосся: 6 голів × світлий / темно-сірий / чорний / яскраво-зелений фон.
- 48 комбінацій із волоссям: 6 голів × 4 зачіски × білий / чорний колір. Плюс 6 знімків реального гардероба в режимі «Пацієнт».
- У браузерній галереї помилок JavaScript не зафіксовано.

Важливе уточнення: оригінальні базові PNG мають альфа-значення **252–254** усередині шиї. Їх не змінювали. Тест перевіряє, що новий стик не додає прозорих дірок і нижче переходу точно відтворює початкове тіло; він не вимагає переробити затверджений аватар на альфа-255. Внутрішня зона самих облич лишається непрозорою.

Різкий колишній зріз підборіддя усунуто. На збільшенні ×4 ще можна розрізнити дрібні відмінності фактури та субпіксельні стики на бічній зоні переходу; це не нова генерація і не перемальований єдиний портрет. Нижче наведено знімки без приховування цих деталей, щоб оцінити результат у реальному масштабі та зі збільшенням.

## Змінені файли

- `assets/wardrobe/faces/{male,female}_{young,exhausted,elder}_head.png` — лише нижня зона інтеграції.
- `assets/wardrobe/faces/masks/{male,female}_{young,exhausted,elder}_body.png` — шість окремих масок.
- `paper-doll-data.js` — шляхи масок і кеш-хеші PNG; `paper-doll.js` — застосування відповідної маски; `index.html` — версії скриптів.
- `tools/repair-face-necks.py` — відтворювана обробка з початкових архівів і затверджених PNG; `tests/fixtures/face-neck-transitions.json` — профілі та контрольні суми.
- `tests/game-logic.test.cjs`, `tests/test_game.py` — перевірки нової інтеграції.
- Цей звіт і знімки у `review/face-necks/`; попередні звіти мають посилання сюди.

## Знімки для кожної голови

У кожному порівнянні **зліва ДО**, **справа ПІСЛЯ**. Верхній ряд ×2, нижній — стик шиї ×4. У чотирьох фонах порядок: світлий, сірий, чорний, зелений. У варіантах без волосся обрано порожній комплект «Трип», щоб одяг не приховував шию.

### Молоде · чоловік

**ДО / ПІСЛЯ**

![Молоде · чоловік: порівняння](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-male-before-after.png)

**Без волосся, чотири фони**

![Молоде · чоловік: чотири фони](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-male-four-backgrounds.jpg)

[Комбінації із зачісками](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-male-hair.jpg) · [Реальний гардероб, повний зріст](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-male-wardrobe.jpg)

### Молоде · жінка

**ДО / ПІСЛЯ**

![Молоде · жінка: порівняння](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-female-before-after.png)

**Без волосся, чотири фони**

![Молоде · жінка: чотири фони](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-female-four-backgrounds.jpg)

[Комбінації із зачісками](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-female-hair.jpg) · [Реальний гардероб, повний зріст](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/young-female-wardrobe.jpg)

### Виснажене · чоловік

**ДО / ПІСЛЯ**

![Виснажене · чоловік: порівняння](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-male-before-after.png)

**Без волосся, чотири фони**

![Виснажене · чоловік: чотири фони](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-male-four-backgrounds.jpg)

[Комбінації із зачісками](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-male-hair.jpg) · [Реальний гардероб, повний зріст](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-male-wardrobe.jpg)

### Виснажене · жінка

**ДО / ПІСЛЯ**

![Виснажене · жінка: порівняння](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-female-before-after.png)

**Без волосся, чотири фони**

![Виснажене · жінка: чотири фони](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-female-four-backgrounds.jpg)

[Комбінації із зачісками](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-female-hair.jpg) · [Реальний гардероб, повний зріст](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/exhausted-female-wardrobe.jpg)

### Старше · чоловік

**ДО / ПІСЛЯ**

![Старше · чоловік: порівняння](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-male-before-after.png)

**Без волосся, чотири фони**

![Старше · чоловік: чотири фони](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-male-four-backgrounds.jpg)

[Комбінації із зачісками](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-male-hair.jpg) · [Реальний гардероб, повний зріст](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-male-wardrobe.jpg)

### Старше · жінка

**ДО / ПІСЛЯ**

![Старше · жінка: порівняння](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-female-before-after.png)

**Без волосся, чотири фони**

![Старше · жінка: чотири фони](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-female-four-backgrounds.jpg)

[Комбінації із зачісками](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-female-hair.jpg) · [Реальний гардероб, повний зріст](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-necks/elder-female-wardrobe.jpg)
