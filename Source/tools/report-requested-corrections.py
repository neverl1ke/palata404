"""Render an honest local report; historical reports/fixtures remain unchanged."""
from pathlib import Path
import json,base64,html,mimetypes,subprocess,collections,re
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-requested-corrections';G=D/'Gallery'
subjects={1:['Плечі','Зріз грудей','Пропорції руки','Тон шкіри','Затверджений автомат'],2:['Поверхня за автоматом','Опорна кисть','Затверджений автомат'],3:['Плече','Затверджений пістолет'],4:['Зріз грудей','Затверджений пістолет','Тонка рука','Контур плеча'],5:['Світлі смуги на плечах'],6:['Зріз грудей'],7:['Зріз грудей','Довжина та об’єм руки','Затверджений ніж'],8:['Плече','Відведений лікоть','Затверджений ніж']}
status={1:['PARTIAL','FIXED','OPEN','OPEN','PARTIAL'],2:['PARTIAL','OPEN','PARTIAL'],3:['PARTIAL','PARTIAL'],4:['FIXED','PARTIAL','OPEN','PARTIAL'],5:['FIXED'],6:['FIXED'],7:['FIXED','PARTIAL','PARTIAL'],8:['PARTIAL','FIXED','PARTIAL']}
causes={'breast-ownership':('Латеральні пікселі білизни належали рухомим upper-arm сегментам.','896 оригінальних пікселів перенесено в runtime-тулуб; RGB не змінювався.','Source-owned ownership тест, Canvas ДО/ПІСЛЯ; оригінальна форма та матеріал збережені.'),'shoulder-seams':('Корені рук і тулуб використовували різні перетворення дихання; жорстка межа не мала внутрішнього резерву.','Спільний pinnedTorsoPoint для торса, skin і corrective art; внутрішній резерв 2 px з точного джерела.','Цільовий тест альфи >=240 усередині еродованого на 5 px силуету, 5 фаз, обидві статі.'),'shoulder':('Суміш геометричної межі, різного breathing-space та відмінного рисунка pose-specific плеча.','Усунено відмінність координат і додано source-owned резерв. Художня форма дельти ще не затверджена.','Canvas 1×/3×, без зброї; не позначено повним художнім виправленням.'),'original-rifle':('Попередній cleanup підмінив модель; старий затверджений шар має шкіру, отвори під пальцями та відсутню рукоятку.','Підготовлено незалежний visible-source PNG і спільний запис gear-aks із профілями обох статей. Відсутній матеріал не вигадувався.','Тест точного збереження всіх наявних RGBA-пікселів; artStatus=PARTIAL.'),'original-pistol':('Старий затверджений пістолет зберігся лише як частково вирізаний шар із прихованою рукояткою.','Збережено видиму модель без підміни; відокремлені залишки та маска пальців вилучені. Повна рукоятка відсутня.','PARTIAL, не готовий повний предмет; джерело і SHA-256 у original-weapons.json.'),'original-knife':('Був активований інший ніж; у старого шару частину рукоятки закриває рука.','Повернуто наявні видимі пікселі старої моделі як окремий частковий ресурс.','Ніж і кисть використовують спільну hand matrix; artStatus=PARTIAL.'),'arm-proportions':('Pose-specific проєкції відрізняються від довжин базової руки; це не лише масштаб цілого PNG.','Для female melee відновлено обидві довжини кісток 1:1 та target [230,895]. Для rifle/pistol пропорції й художній об’єм не переписані.','Фактичні довжини і цикл melee перевірено; товщина й рисунок інших поз залишаються OPEN.'),'skin-tone':('Pose-specific живопис і освітлення відрізняються від базового тулуба.','У цьому проході RGB рук не перемальовувався; source-owned резерв не є тоновою гармонізацією.','Потрібен контрольований художній прохід по похідних PNG; OPEN.'),'missing-surface':('Попередні дефектні back/front шари могли ховати нестачу поверхні предметом.','Збережено complete-arm compositing і source-atop лише всередині зброї; нових латок немає.','24 варіанти item/time/gender перевіряють точну незмінність усіх пікселів поза фактичним weapon alpha; форму прихованої анатомії не названо ідеальною.'),'support-hand':('Хват залежить від конкретного матеріалу цівки, якого в затвердженому шарі частково немає.','Контакт primary/support налаштовано для спільного PNG, але пальці художньо не домальовані.','Нульові числові помилки primary/support контакту не доводять анатомічну природність; OPEN.'),'elbow':('IK-target [241,906] при повних кістках відводив лікоть до X=191.45.','Melee target зміщено до [241,920] без зміни довжин кісток, хвату та forward breathing.','Лікоть X=238.74, стабільний цикл; базові плечі/тулуб/голова/стопи не перероблені.')}
rows=json.loads((D/'issues.json').read_text())
for row in rows:
 i=row['screenshot'];j=int(row['id'].split('-')[1])-1;row['problem']=subjects[i][j];row['status']=status[i][j];row['cause'],row['fix'],row['verification']=causes[row['issue']];row['evidence']=f'Gallery/issue-{i:02}-full.webp';row['closeup']=f'Gallery/issue-{i:02}-3x.webp'
(D/'issues.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
summary_path=D/'Evidence/full-run/summary.json';summary=json.loads(summary_path.read_text()) if summary_path.exists() else None
counts=collections.Counter(r['status'] for r in rows)
intro='''# Avatar Core — виправлення за «ПРАВКИ.zip»

Результат **частковий, не production-ready**. 22/22 зауваження зареєстровані; жодне не приховане. Для завершення потрібні повні окремі затверджені PNG зброї або погоджене ручне відновлення прихованих рукояток, а також локальний художній прохід по бойових плечах/кистях. Кодові тести не замінюють це погодження.

Робоча гілка `feature/avatar-core-2-weapon-transitions`. Початок: `37a73f75a88288b8327c26ae6b517d77ce3ce580`; recovery tag: `avatar-before-requested-corrections-37a73f7`. `main` та опублікована гра не змінювалися. Push, merge і публікація не виконувались.

Постановка автомата: **розслаблена, приклад біля ліктя** — за прямим уточненням власника, а не біля плеча.

## Реальні виправлення

- Спільний простір дихання тулуба й коренів рук; резерв 2 px тільки на внутрішніх стиках Y=300–530, з оригінального RGBA. Глобального erosion/dilation силуету немає.
- 896 пікселів латерального краю жіночої білизни перепризначено тулубу. Базовий PNG, тон і анатомія не змінені.
- Male melee: лікоть X=191.45 →238.74, target [241,920]. Female melee: довжини кісток відновлені до [1,1], target [230,895]. PNG не розтягувалися цілком; використано чинні кістки та corrective mesh.
- Дихання 4000 ms, 2 px та forward wrist sway збережені; ніж прив’язаний до hand matrix. Instant cut залишився.
- Точний нейтральний рендер використовує оригінальну поверхню, а голова — ту саму mask/crown текстуру, що й бойові пози. Це прибирає регресію крайових пікселів між позами.
- Виправлено повторний запуск female exporter: він зберігає runtime-маски та poseCalibration.

Невидимий гардероб зупиняє свій RAF і відновлює анімацію після відкривання; після fallback знімається застарілий маркер готовності. Це окремо перевірено після основного прогону.

## Оригінальна зброя і гардероб — межі реалізації

Шість повторно наданих референсів побайтово збігаються зі збереженими Sources. Це зображення людей зі зброєю, а не повні окремі предмети. У старих reference-art PNG є фрагменти пальців і відсутній матеріал під ними. Три `assets/weapons/original-visible/weapon_{rifle,pistol,knife}.png` містять лише збережені видимі пікселі старих моделей після видалення маски рук/відокремлених компонентів. Вони **PARTIAL**, а не вигадана повна реконструкція.

`equipment-weapons.json` використовує наявні `gear-aks`, `gear-pm`, `gear-knife`, одну модель на обидві статі й окремі attachment-профілі. `equipWeaponItem()` вибирає позу за типом предмета. Мініатюри — окремі crops лише зброї. У Lab є явний вибір часткових оригінальних ресурсів; попередні тестові моделі доступні для порівняння.

В основному `index.html?avatarCore=1` додано **режим перевірки**: наявний інвентар, картки, equip/unequip, обидва loadout та старі localStorage keys залишаються джерелом стану; центральна сцена й гардероб використовують той самий вибраний ID. Без параметра лишається чинний рендер. За наявності одягу з непідготовленими pose-specific рукавами режим зберігає чинний одяг і рендер, виставляє `data-avatar-core-blocked`; він не приховує одяг заради зброї. Це **не завершена інтеграція довільного одягу**.

## Перевірки

- JavaScript: 121/121 у поточному запуску.
- Нові Python/Chromium сценарії: 8/8; додаткові чотири перевірки виявлених регресій також пройшли.
- Повний прогін: 291/295. Після нього змінені лише game-preview.mjs (пауза прихованого гардероба та очищення маркера готовності) і цільовий тест; на фінальному стані окремо пройшли 8/8 сценаріїв. Решта 372 контрольних входів відповідають snapshot повного прогону. Див. Evidence/final-snapshot-delta.json.
- 100 затверджених base/face/hair PNG захищені SHA-256; попереднє очищення 4281 слабких alpha-пікселів у male runtime збережене.
- Нові source-contract перевірки допускають тільки п’ять точно перелічених текстових змін у старих frozen-файлах; решта байтів порівнюється з історичним Git/хешем. Старі еталони, пороги та PNG не підмінені. Старий donor-melee fixture збережено для архівного стану; для нової калібровки очікуються незалежно виміряні суглоби бази [306,367], [278,584], [215,825] з тим самим допуском 0.01 px.
- Анімовані WebP — реальні Canvas samples через 100 ms, 40 кадрів на цикл, не виміряні 60 FPS та не фізичний пристрій.
- Перевірки виконані в Chromium; фізичний телефон не використовувався.

Автономний пакет перевірено через file:// у Chromium: Report/Technical-report на 320, 390, 768, 1440 px без горизонтального переповнення; завантаження зображення працює; Lab — 8 комбінацій предмет/стать без зовнішніх запитів і JS-помилок. PDF має 8 сторінок; 8 анімацій — по 40 кадрів / 4000 ms. Машинний результат: Evidence/offline-verification.json.

## Відкриті технічні й художні питання

- Повні рукоятки/цівка затверджених предметів: **BLOCKED** відсутнім відкритим матеріалом у джерелах. Точні обрізи показані в галереї.
- Хват опорної руки, об’єм rifle/pistol рук, тон жіночої бойової руки та частина плечових переходів: **OPEN/PARTIAL**. Для художнього завершення потрібні похідні `foundation-cleanup/{rifle-right,rifle-left,pistol-right,melee-right}-{complete,front,arm}.png`; базові тіла не чіпати.
- Старий alpha-тест захищеного `base_male.png` і три старі stock-contact перевірки попередніх тестових моделей: відстежуються окремо; не послаблені.
- Сітки Binding API не доводять готовність реального одягу. Сумісність pose-specific рукавів лікарняної туніки не затверджена; наявний одяг у грі зберігається fallback-рендером.

## Реєстр усіх 22 правок

| ID | Проблема | Стать / поза | Першопричина | Виправлення | Доказ | Статус |
|---|---|---|---|---|---|---|
'''
for row in rows:intro+='| '+ ' | '.join([row['id'],row['problem'],row['gender']+' / '+row['pose'],row['cause'],row['fix'],f"[Canvas]({row['evidence']}) / [3×]({row['closeup']})",row['status']])+' |\n'
intro+='\nСтатуси: '+', '.join(f'{n} {s}' for s,n in sorted(counts.items()))+'.\n'
if summary:
 intro+=f"\n## Фактичний повний прогін\n\n{summary['ran']}/{summary['total']} виконано; {summary['passed']} успішно, {len(summary['failure_ids'])} невдалих, {summary['skipped']} пропущено.\n\n"+'\n'.join('- `'+x+'`' for x in summary['failure_ids'])+'\n'
else:intro+='\nПовний прогін ще триває; остаточні числа тут не заявлені.\n'
intro+='\n## Матеріали\n\nКодовий коміт: `2cd53c6` (локальний). Точні змінені шляхи та SHA-256: [changed-files.json](changed-files.json).\n\n[Автономний звіт](Report.html), [PDF](Review.pdf), [Lab](Avatar-Lab.html), [машинний реєстр](issues.json), [походження зброї](Evidence/original-weapons.json), [повторні референси](Evidence/repeated-references.json).\n\nКнопка попередніх рук у Lab показує історичний стан c2822a7; актуальні ДО/ПІСЛЯ цього проходу від 37a73f7 наведені у Report.html та PDF.\n\nHTML слід відкрити у звичайному браузері після розпакування; GitHub/редактор може показати HTML як текст. Для перевірки основного index.html з ES-модулями потрібен локальний HTTP-сервер; автономний Lab цього не потребує.\n'
(D/'README.md').write_text(intro)
def asset(p):return 'data:'+str(mimetypes.guess_type(p.name)[0])+';base64,'+base64.b64encode(p.read_bytes()).decode()
def img(p,label):return '<figure><img loading="lazy" src="'+asset(p)+'" alt="'+html.escape(label)+'"><figcaption>'+html.escape(label)+' <button data-file="'+html.escape(p.name)+'" onclick="downloadImage(this)">Завантажити зображення</button></figcaption></figure>'
body='<h1>Палата 404 · Avatar Core</h1><p class="warning">Частковий результат. Плечі/хвати й повні рукоятки ще не затверджені. Main не змінено.</p><p>Оригінальні бази з гри. Зброя незалежна. Для автомата залишено розслаблену постановку біля ліктя.</p><nav><a href="Avatar-Lab.html">Відкрити автономний Lab</a> · <a href="Technical-report.html">Технічний звіт</a> · <a href="Review.pdf">PDF без анімації</a></nav><p>Фон прозорих Canvas знімків: <select id="background"><option value="#f8f5ed">Світлий</option><option value="#777">Сірий</option><option value="#111">Чорний</option><option value="#0f0">Зелений</option></select></p>'
for i in range(1,9):
 group=[r for r in rows if r['screenshot']==i];body+=f'<section id="issue-{i}"><h2>{i}. {html.escape(group[0]["file"])}</h2><h3>Ваш вихідний скриншот</h3>'+img(D/'Inputs'/f'{i:02}.png','Оригінальне зауваження; червоні стрілки не додавались до runtime')
 body+='<table><tr><th>ID</th><th>Проблема</th><th>Що зроблено / межі</th><th>Статус</th></tr>'
 for row in group:body+='<tr>'+''.join('<td>'+html.escape(str(row[k]))+'</td>' for k in ['id','problem','fix','status'])+'</tr>'
 body+='</table>'+img(G/f'issue-{i:02}-full.webp','Однаковий масштаб: попередній рендер / оригінальні часткові предмети / без зброї')+img(G/f'issue-{i:02}-1x.webp','Нативний масштаб 1×, без зброї')+img(G/f'issue-{i:02}-3x.webp','Нативний кроп, збільшення 3×; колір тла не приховує дефектів')+'</section>'
body+='<section><h2>Повноростові пози</h2>'
for g in ['male','female']:body+=img(G/f'{g}-four-poses.webp',g+' · idle / melee / pistol / rifle')
body+='</section><section><h2>Оригінальні видимі матеріали зброї — PARTIAL</h2><p>Це не повні відновлені предмети. Відсутній матеріал під пальцями не домальовувався. Персонажі з референсів не замінюють аватар.</p>'
for name in ['rifle','pistol','knife']:body+=img(G/f'weapon_{name}-candidate.webp',name+' · наявний матеріал без підміни моделі')
body+='</section><section><h2>56 фактичних рендерів на контрастних фонах</h2>'
for p in sorted(G.glob('backgrounds-*.webp')):body+=img(p,p.stem+' · Canvas білий / сірий / чорний / зелений')
body+='</section><section><h2>Цикли 4000 ms</h2><p>40 реальних Canvas samples з кроком 100 ms; WebP не є вимірюванням FPS.</p>'
for g in ['male','female']:
 p=G/f'{g}-knife-before-after.webp'
 if p.exists():body+=img(p,g+' · синхронне ДО/ПІСЛЯ knife')
 for pose in ['idle','melee','pistol','rifle']:
  p=G/f'{g}-{pose}-cycle.webp'
  if p.exists():body+=img(p,g+' · '+pose+' · 4 s')
body+='</section><section><h2>Основна гра і гардероб</h2><p>Це браузерні рендери основного index.html?avatarCore=1. За непідготовленого одягу збережено звичайний рендер; це не готові анімовані рукави.</p>'
for p in sorted(G.glob('game-*.png')):body+=img(p,p.stem)
body+='</section><section><h2>Результати тестів і обмеження</h2><pre>'+html.escape(intro.split('## Перевірки')[1].split('## Реєстр')[0])+'</pre>'
if summary:body+='<pre>'+html.escape(json.dumps({k:summary[k] for k in ['total','ran','passed','failure_ids','skipped']},ensure_ascii=False,indent=2))+'</pre>'
body+='</section>'
page='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core — контроль правок</title><style>body{margin:auto;max-width:1480px;padding:18px;background:#161b20;color:#eee;font:16px/1.55 system-ui}a{color:#9fd7ee}section{border-top:1px solid #68717a;margin-top:35px}figure{margin:20px 0;overflow:auto}img{display:block;max-width:100%;height:auto;background:var(--preview-bg,#f8f5ed)}figcaption{color:#c6ccd1}table{border-collapse:collapse;width:100%}td,th{padding:9px;border:1px solid #69737d;vertical-align:top;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere}.warning{padding:15px;background:#6b421f}select{font:inherit;padding:9px}@media(max-width:600px){body{padding:10px}table{font-size:13px}td,th{padding:4px}}</style>'+body+'<script>function downloadImage(button){const a=document.createElement("a");a.href=button.closest("figure").querySelector("img").src;a.download=button.dataset.file;document.body.append(a);a.click();a.remove()}document.getElementById("background").onchange=e=>document.documentElement.style.setProperty("--preview-bg",e.target.value)</script></html>'
(D/'Report.html').write_text(page);print('Report:',len(rows),'issues;',dict(counts),'; HTML bytes',len(page.encode()))

# Render the technical document, rather than asking a browser to display Markdown.
def inline(text):
 text=html.escape(text)
 text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
 text=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text)
 return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
parts=[];lines=intro.splitlines();i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('#'):
  n=min(6,len(line)-len(line.lstrip('#')));parts.append(f'<h{n}>'+inline(line[n:].strip())+f'</h{n}>');i+=1
 elif line.startswith('|'):
  table=[]
  while i<len(lines) and lines[i].startswith('|'):
   cells=[c.strip() for c in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[-: ]+',c) for c in cells):table.append(cells)
   i+=1
  parts.append('<div class="table"><table>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in table)+'</table></div>')
 else:
  paragraph=[]
  while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')):paragraph.append(lines[i]);i+=1
  parts.append('<p>'+inline(' '.join(paragraph))+'</p>')
(D/'Technical-report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core — технічний звіт</title><style>body{font:16px/1.6 system-ui;max-width:1200px;margin:auto;padding:15px;overflow-wrap:anywhere}.table{overflow:auto}table{border-collapse:collapse;min-width:1100px}td{border:1px solid #aaa;padding:8px;vertical-align:top}code{background:#eee}</style><a href="Report.html">Галерея</a>'+''.join(parts)+'</html>')
