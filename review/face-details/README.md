# Палата 404 — точкові правки чотирьох голів

Порівняння зі станом `4a87c2c`. Знімки зроблено в Chromium справжнім рендерером гри; нова генерація зображень не використовувалася.

## Що змінено

| Варіант | Локальна правка |
|---|---|
| Молодий чоловік | Ослаблено неприродно чорну смугу на правому краї шиї: вузька смуга біля контуру, Y=220…257, з плавними кінцями. Згладжено виступ правого контуру черепа Y=82…122, край правого вуха Y=134…182 та підчищено темний піксельний стик над ним. |
| Молода жінка | Підчищено темну смугу правого краю шиї Y=222…253; локально згладжено нерівність лівої щоки/щелепи Y=183…218. |
| Виснажений чоловік | Лише чорні плями над вухами, 113 пікселів у межах Y=123…136. Шия й уся ділянка нижче Y=221 **побайтово незмінні**. |
| Виснажена жінка | Підчищено чорні плями над вухами. Голову пропорційно збільшено на **6%** відносно центру X=473 і верхнього якоря Y=26; нижня частина підборіддя опускається приблизно на 12 px, скорочуючи враження надто довгої шиї. У зоні Y=238…272 деформація плавно зводиться до нуля, нижня шия повертається до попереднього стику. Відповідно узгоджено лише її персональну маску тіла. |

Ліворуч/праворуч означає сторону на екрані. Риси не перемальовані: чорні дефектні пікселі заміщені інтерполяцією сусідньої наявної шкіри; центральні риси молодих облич і виснаженого чоловіка залишилися незмінними. Виснажена жінка — те саме зображення, пропорційно масштабоване в наявному полотні, із переходом лише по шиї.

**Старший чоловік і старша жінка не змінені**, включно з їхніми PNG, масками та параметрами. Базові аватари, азійські голови, всі зачіски й координати волосся, одяг, палітра, UI та збереження не змінені.

Положення усіх накладок лишилося **X=0, Y=0, 941×1672, 1:1**. Збільшення виснаженої жіночої голови виконано всередині її PNG без зміни canvas, тіла чи зачісок. Порядок **тіло → голова → волосся** збережено.

## Перевірки

- 70 тестів JavaScript.
- 13 цільових тестів Python/Chromium: персональні маски й шия, затверджені тіла та горловина, графічні ресурси, каталог облич і збереження після перезавантаження.
- 16 прикладів без волосся: 4 голови × 4 контрастні фони.
- 32 комбінації: 4 голови × 4 зачіски × біле/чорне волосся.
- 4 повноростові скріншоти гардероба. Браузерних помилок у галереї немає.

Природні темні складки всередині вух і тінь під щелепою збережено. Старі тонкі бічні відмінності фактури стику при великому збільшенні не приховані: нижче наведено реальні знімки ×2 та ×4.

## Файли

- Чотири PNG: `assets/wardrobe/faces/{male,female}_{young,exhausted}_head.png`.
- Тільки одна змінена маска: `assets/wardrobe/faces/masks/female_exhausted_body.png`.
- `paper-doll-data.js` — кеш-хеші цих п'яти ресурсів; `index.html` — кеш-версія даних.
- `tests/fixtures/face-neck-transitions.json` — актуальні контрольні суми після прямо запитаних змін.
- `tools/refine-face-details.py` — відтворювана локальна обробка; потребує Pillow, NumPy, SciPy і початкових PNG зі стану `4a87c2c` у `--before-dir`.
- Цей звіт, знімки й посилання з попереднього звіту.

## Порівняння

У кожному знімку зліва **ДО**, справа **ПІСЛЯ**; масштаб однаковий. Верх — голова ×2, низ — шия ×4. Фони: світлий, сірий, чорний, зелений.

### Молодий чоловік

![ДО / ПІСЛЯ — Молодий чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-male-before-after.png)

![Без волосся, чотири фони — Молодий чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-male-four-backgrounds.jpg)

[Примірка зачісок](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-male-hair.jpg) · [Повний зріст у гардеробі](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-male-wardrobe.jpg)

### Молода жінка

![ДО / ПІСЛЯ — Молода жінка](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-female-before-after.png)

![Без волосся, чотири фони — Молода жінка](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-female-four-backgrounds.jpg)

[Примірка зачісок](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-female-hair.jpg) · [Повний зріст у гардеробі](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/young-female-wardrobe.jpg)

### Виснажений чоловік

![ДО / ПІСЛЯ — Виснажений чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-male-before-after.png)

![Без волосся, чотири фони — Виснажений чоловік](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-male-four-backgrounds.jpg)

[Примірка зачісок](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-male-hair.jpg) · [Повний зріст у гардеробі](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-male-wardrobe.jpg)

### Виснажена жінка

![ДО / ПІСЛЯ — Виснажена жінка](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-female-before-after.png)

![Без волосся, чотири фони — Виснажена жінка](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-female-four-backgrounds.jpg)

[Примірка зачісок](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-female-hair.jpg) · [Повний зріст у гардеробі](https://raw.githubusercontent.com/neverl1ke/palata404/main/review/face-details/exhausted-female-wardrobe.jpg)
