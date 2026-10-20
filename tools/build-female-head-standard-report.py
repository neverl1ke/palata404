"""Build a portable review and downloadable hair template from actual captures."""
import html
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'review/female-head-standard'


def run():
    manifest = json.loads((D / 'manifest.json').read_text())
    records = [json.loads(line) for line in (D / 'geometry/records.jsonl').read_text().splitlines()]
    with zipfile.ZipFile(D / 'hair-generation-template.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((D / 'template').iterdir()):
            if path.is_file():
                archive.write(path, 'female-hair-template/' + path.name)
    rows = []
    cards = []
    for entry in manifest['heads']:
        p = entry['registration']
        rows.append(f"| {entry['name']} (`{entry['id'] or 'native/null'}`) | {p['scale']:.12g} | {p['x']:.12g} | {p['y']:.12g} | {entry['actual']['ear_row_y']} |")
        kind = entry['kind']
        thumbs = ''.join(f'<figure><a href="{r["path"]}"><img loading="lazy" src="{r["path"]}" alt="{html.escape(r["hair"])}"></a><figcaption>{html.escape(r["hair"])}</figcaption></figure>' for r in records if r['gender'] == 'female' and r['face'] == entry['id'])
        backgrounds = ''.join(f'<a href="captures/{kind}/{bg}-bare.webp"><img loading="lazy" src="captures/{kind}/{bg}-bare.webp" alt="{bg}"></a>' for bg in ['white', 'gray', 'black', 'green'])
        cards.append(f'<section><h2>{html.escape(entry["name"])}</h2><p>{html.escape(entry["id"] or "native/null")} · uniform scale {p["scale"]:.9g}</p><img class="comparison" loading="lazy" src="captures/{kind}-comparison.webp" alt="ДО / ПІСЛЯ"><div class="backgrounds">{backgrounds}</div><details><summary>Усі зачіски, оригінальний колір</summary><div class="hair-grid">{thumbs}</div></details></section>')
    report = '''# Єдина жіноча рамка для зачісок

Еталон — **«Молоде обличчя» / `face-young`**. Робота виконана в `main` від `fd20bc3`; точка відновлення — `backup/before-female-head-standard-20261019`. Вирівняно 17 жіночих варіантів, включно з оригінальним. Чоловічі голови, тіла, зачіски, одяг і палітра не змінені.

[Відкрити галерею](index.html) · [ZIP для генерації зачісок](hair-generation-template.zip) · [Чистий PNG голови](template/reference-head.png) · [Голова з тілом](template/reference-body.png) · [Розмітка](template/geometry-guide.png) · [Точні параметри JSON](template/hair-template.json) · [Готовий промпт](template/HAIR_GENERATION_PROMPT_UK.txt).

## Спільні параметри

| Параметр | Значення у натуральних пікселях Paper Doll |
| --- | --- |
| Полотно / формат | 941 × 1672, RGBA PNG, прозорий фон |
| Початок координат | верхній лівий кут |
| Межі голови з вухами | x=385…560 включно, ширина 176 |
| Вісь | x=472.5 |
| Верх шкіри маківки | y=33; волосся може бути вище |
| Верхній контур усіх голів до y=124 | x=394…549, загальна область 156 × 92 |
| Готова повнорозмірна зачіска | x=0, y=0, width=941, height=1672, scale=1 |
| Шари | заднє волосся −1 (за потреби), тіло 0, голова 1, переднє волосся 9 |

Геометрію виміряно за alpha≥128. Це **спільна монтажна рамка**, а не однакова анатомія: форма вух, довжина щелепи й підборіддя залишилися індивідуальними. Ряд максимальної ширини вух — y=133…148. Однакова рамка полегшує створення волосся, але не замінює примірку коротких пасом біля вух на всіх варіантах.

Орієнтири очей/скронь у JSON приблизні, визначені візуально. Чистий PNG — основний еталон. Не обрізайте прозорі поля. Для крупного генеративного редагування є crop 270×420 від (340,0), збільшений у 4 рази до 1080×1680; повернення — scale=0.25 і позиція (340,0). Сам текстовий промпт не гарантує точного суміщення.

## Реалізація

- Для 16 змінених варіантів створено окремі похідні PNG у `assets/wardrobe/faces/standardized/` та парні маски в `assets/wardrobe/faces/masks/standardized/`. Застосовано тільки рівномірний масштаб і перенесення; портретний RGB не перемальовувався й не перефарбовувався.
- Оригінальний `female_young_head.png` та його маска залишилися байт у байт незмінними. Збережено всі джерела й контрольні суми. Дані реєстрації — [registration.json](registration.json), кінцеві точні перетворення й хеші — [manifest.json](manifest.json).
- Нижню частину нових накладок зведено з незмінним тілом через взаємодоповнювальну пару голова/маска. Центр переходу x=472.5, радіус65; початок y=265 у центрі /245 збоку, завершення y=290/275; від y=300 тіло точно оригінальне. Непрозорість внутрішньої шкіри збережена; округлення альфи маски вгору усуває втрату непрозорості на стику.
- Базове жіноче обличчя вирівняно окремою внутрішньою накладкою `PAPER_DOLL_NATIVE_HEADS.female`; `base_female.png` не змінений. У сейві базовий вибір досі `null`, нового каталожного ID немає, формат збереження не змінений. Чоловічий native-рендер працює як раніше.
- Runtime placement усіх готових накладок: x=0, y=0, width=941, height=1672. У таблиці нижче — **перетворення підготовки вихідного PNG**, а не нові координати runtime.
- Версії PNG у каталозі — за SHA-256; `index.html` оновлює версії data/renderer.

## Реєстрація всіх жіночих варіантів

| Обличчя | uniform scale | tx | ty | Ряд ширини вух |
| --- | ---: | ---: | ---: | ---: |
''' + '\n'.join(rows) + '''

## Реальні контрольні зображення

![Усі жіночі голови після вирівнювання](overview.webp)

![Коротка текстурована, білий колір](hair-textured-short-overview.webp)

Повні контактні таблиці всіх зачісок: [варіанти1–6](hair-matrix-1.webp), [7–12](hair-matrix-2.webp), [13–17](hair-matrix-3.webp).

У галереї для кожного варіанта є ДО/ПІСЛЯ, чотири фони та всі вісім жіночих варіантів волосся. Зображення отримано з фактичного `index.html` через `renderPaperDollAt`, не з окремого імітатора. ДО використовує джерела й маски `fd20bc3`; ПІСЛЯ — поточні ресурси, з тим самим масштабом. Порівняння еталонного young ідентичне піксельно.

- [Результат матриці](geometry/result.json): 199 станів у Chromium, 136 жіночих і 63 чоловічих, оригінальний колір; 26 повноростових знімків і перевірок reload.
- [Окремі перевірки](captures/result.json): усі 17 жіночих голів на білому, сірому, чорному й зеленому фоні; classic/textured у black/white; туніка; desktop і емуляція ширин320/390/768. JS errors та HTTP errors — 0.
- Чоловічі 63 знімки ідентичні піксельно попередній опублікованій бібліотеці. Окремі тести перевіряють незмінні вихідні PNG, ресурси, маски, геометрію, RGB після рівномірного перетворення, непрозорість шиї, native/null і збереження всіх 17 виборів.
- [Аудит PNG](png-quality.json): 34 активні жіночі голови/маски. Кандидати на особливості контуру — діагностика, не автоматичний висновок про художній дефект.

### Межі перевірки

Спеціального повного прогону 17×8×25 кольорів не було: матриця знята в original, проблемні короткі зачіски додатково в black/white. Палітра й PNG волосся не змінювалися. Перевірено Chromium та емуляцію екранів, не фізичний телефон. Індивідуальна анатомія вух/щелеп збережена; майбутні дуже короткі зачіски потребують примірки на всій бібліотеці.

Початковий строгий тест альфа-шуму `base_male.png` фіксує 4234 віддалені слабкі пікселі в незмінному чоловічому джерелі. Це успадкована від `fd20bc3` відома проблема; заради поточного жіночого завдання чоловічий PNG не змінювався, поріг тесту не послаблений.

Діагностика незмінного еталона також бачить 4 слабкі пікселі в зоні згасання шиї y263…264, не на контурі черепа; відокремлених компонентів там немає. Похідні голови мають 0 віддалених слабких пікселів.

Поточні результати тестів і публікації наведено в [verification.json](verification.json); історичні звіти не замінено.

## Змінені файли

Каталог/рендер/кеш: `paper-doll-data.js`, `paper-doll.js`, `index.html`. Нові 16 голів +16 масок у підкаталогах `standardized/`. Інструменти: `tools/standardize-female-heads.py`, `tools/build-female-hair-template.py`, `tools/review-female-head-standard.py`, `tools/build-female-head-standard-report.py`; два аудитори враховують внутрішню native-накладку. Регресійні тести й runner доповнено; історичні перевірки незмінних оригіналів збережено, старі URL-контракти прив'язані до історичного `fd20bc3`, поточні похідні перевіряються окремо точними хешами. Навігацію README й документацію актуалізовано.
'''
    verification_path = D / 'verification.json'
    if verification_path.exists():
        verification = json.loads(verification_path.read_text())
        result = verification.get('python_final')
        if isinstance(result, dict):
            report += f"\nФінальний запуск: **89/89 JavaScript; {result['passed']}/{result['total']} Python/Chromium**. Єдиний збій — описаний вище незмінний чоловічий PNG. Сирі журнали збережено у `verification/final/`, початкові невдалі очікування — у `verification/initial/`; повторні запуски не підміняють початкових результатів.\n"
    (D / 'README.md').write_text(report)
    introduction = '<h1>Жіночі голови — єдиний шаблон</h1><p>Еталон: «Молоде обличчя». 17 жіночих варіантів; чоловічі незмінні. Рамка 176 px, x=385…560, вісь x=472.5, маківка y=33 на полотні 941×1672. Збережено індивідуальну анатомію вух і щелеп.</p><p><a href="hair-generation-template.zip" download>Завантажити ZIP для зачісок</a> · <a href="template/reference-head.png">Чистий еталон PNG</a> · <a href="template/geometry-guide.png">Розмітка</a> · <a href="template/HAIR_GENERATION_PROMPT_UK.txt">Промпт</a> · <a href="README.md">Повний звіт</a></p><p>ДО ліворуч, ПІСЛЯ праворуч. Реальний рендер index.html. Натисніть зображення зачіски для повного розміру.</p>'
    style = 'body{margin:0 auto;padding:20px;max-width:1100px;background:#11171d;color:#e6e7e8;font:16px system-ui}a{color:#9ed4ff}section{padding:16px 0;border-top:1px solid #48515b}img{max-width:100%;height:auto}.comparison{display:block;width:800px}.backgrounds,.hair-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.backgrounds{margin:12px 0}figure{margin:0}figcaption{overflow-wrap:anywhere}summary{padding:12px;cursor:pointer}@media(max-width:600px){.backgrounds,.hair-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}'
    (D / 'index.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата404 — жіночий шаблон</title><style>' + style + '</style><body>' + introduction + ''.join(cards) + '<section><h2>Гардероб</h2><img loading="lazy" src="captures/desktop.png" alt="Desktop"><img loading="lazy" src="captures/mobile-390.png" alt="Емуляція390"></section></body></html>')
    print('Built README, index.html and hair-generation-template.zip')


if __name__ == '__main__':
    run()
