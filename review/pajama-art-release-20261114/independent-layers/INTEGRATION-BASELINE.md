# Read-only аудит основи інтеграції

Main checkout залишено незмінним: `44f460f`, три dirty файли з точними SHA й patch збережено у `BASELINE-GIT.json` / `preserved-dirty-main.patch`. `ls-remote` підтвердив remote main `8cda2bd`. Локальне ahead3/behind1 походить із shallow/grafted історії й саме собою не доводить незалежність трьох комітів. Безпечна основа — актуальний origin у новій release branch, зі збереженням старого worktree.

Старий main tree не містить нових floor10/quest assets, docs/tests, script/config вставок і 12 approved shirt PNG. Його не можна накладати поверх origin. Dirty UI test уже дорівнює origin; dirty face exclusion функціонально вже є в origin, але старий main module не має back support. Із dirty asset tests потрібна семантика прозорої no-op footwear mask, без повернення застарілого WebP-only контракту чи видалення master guards.

Production candidate використовує 20 повнорозмірних lossless PNG одягу та 6 keep masks. Root pose-поля зберігають native шлях; declarative rear/front layers забезпечують static шлях, rear−1 перед тілом, top front3, footwear front0.5 під pants1. Нова multipart конфігурація створює `*-front` / `*-rear` DOM елементи; перевірки мають брати видимий front, а не прихований stable root. Item IDs, слоти, характеристики й saves залишаються тими самими.

Версії URL треба звіряти по всьому ланцюжку: PNG/thumbnail → pajama-data → index; pajamas module → game-preview import → index; paper-doll → index. Продакшн не має посилатися на локальні review candidate PNG. Історичні approved SHA залишаються перевіркою оригіналів; нові runtime bytes й exact alpha звіряються з окремим release manifest.

Поточні незмінні джерела й список необхідних actual/UI/CSS/стан-тестів наведено в `INTEGRATION-BASELINE.json`. Історичний 942 guard більше не використовується як заборона авторизованих похідних змін; base avatars, originals, історичні master й native resources залишаються захищеними. Комітів, push або merge я не виконував.
