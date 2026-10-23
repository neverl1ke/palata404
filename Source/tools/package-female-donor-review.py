"""Bundle an honest, self-contained donor-arm review; never deploy the game."""
from pathlib import Path
import base64,hashlib,html,json,mimetypes,re,shutil,subprocess,zipfile
R=Path(__file__).resolve().parents[1];O=R/'review/female-donor-arm-pass';D=R.parent/'Avatar-Female-Donor-Review';D.mkdir(exist_ok=True)
old_quality=json.loads((O/'preexisting-png-audit.json').read_text());assert len(old_quality['failures'])==1;assert old_quality['failures'][0]['bytes_identical'];assert old_quality['failures'][0]['path']=='base_male.png'
proof=json.loads((O/'runtime-review.json').read_text());tests=json.loads((O/'final-acceptance/summary.json').read_text());motion=json.loads((O/'live-motion.json').read_text());source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
reg=json.loads((O/'regression-result.json').read_text());assert reg['remaining_failures']==['tests.test_paper_doll_audit.AuditAssetTests.test_no_remote_faint_haze_or_detached_low_alpha_specks'];assert reg['followup']['passed']==2 and reg['followup']['runtime_unchanged'];assert tests['ran']==tests['total'];assert len(motion['recordings'])==20;assert proof['rendered_frames']==1360
issues=[
['Жіночі чотири пози','Старі деформовані idle-атласи, геометричні предмети; попередня зйомка також зупиняла старий жіночий morph на старті','Нові донорські руки та окремі предмети; правильна зйомка завершених старих поз','Реалізовано; художнє приймання потрібне'],
['Жіночі пальці/матеріал зброї','Початкові маски втрачали кінчики пальців і лишали шкіру вPNG автомата; цівку звузили надміру','Уточнено власні контури пальців, розділено шкіру/метал/дерево, повернуто цілісний дерев’яний щиток; wrist-прив’язку встановлено в загоєному стику замість зони нігтів','Перевірено джерельні точки, шарову належність і фактичний рендер'],
['Прозорість жіночого rifle-зап’ястя','Цівка приховувала відсутній малюнок','Локально домальовано та зареєстровано тільки відсутню поверхню','Зв’язність перевірено, фактуру показано крупно'],
['Жіноче плече rifle','Приклад приховував край руки; груба колірна маска робила зубці','Локальна маска, збережений нативний плечовий перехід, вибіркова альфа','Потребує візуального приймання внутрішнього контуру'],
['Чоловічі rifle-краї','Геометричний запас під правою долонею, уламки біля лівого мізинця','Дві вузькі маски контуру; внутрішні непрозорі RGB пальців збережені','Локально покращено; загальна кисть не перемальована'],
['Композиція альфа-краю','Фон малювали до напівпрозорих трикутників:7рівнів RGB похибки у контрольній пробі, також у77199cd','Фон додано після прозорого персонажа через destination-over; джерела й геометрія незмінні','Окремий новий тест для8поз/статей і4фонів, незалежний контроль старого рендера'],
['Дихання/шия','Торс рухався відносно нерухомої голови','Існуючий pinned torso для обох статей, 4000 мс, збережені контакти','Перевірено замикання та контакти у всій матриці'],
['Чоловічі pistol/melee','Короткий вказівний pistol, світла смуга зап’ястя, різниця фактури/пахва melee','Перевірено та показано; повна нова художня переробка не виконувалася','Залишковий художній борг — не оголошено виправленим'],
['Інші розміри предметів','Масштабування навколо primary не змінює support','85/115% позначені як діагностика; 100% має власні контакти обох статей','Універсальна сумісність із будь-яким предметом не доведена'],
['Оригінальний base_male.png','4234віддалені альфа-пікселі1–16, присутні вже у77199cd','Не змінювали базу і не послаблювали тест; SHA-256 та кількість зафіксовано','Невиправлено через пряму заборону змінювати вихідні PNG'],
['Гардероб/production','Це лабораторний модульний етап','Гра, main, інвентар, збереження й затверджені бази не змінювалися','Production-інтеграція не виконувалася']]
md=f'''# Avatar Core — жіночі донорські руки та локальні контури

Гілка: feature/avatar-core-2-weapon-transitions. База: 77199cd. Точка відновлення: avatar-before-female-donors-77199cd. Runtime: {source}. Main f70b7e5 не змінено. Це лабораторна версія для візуального приймання, не production-ready.

База base_female.png із проєкту окремо підтверджена власником. Вихідні жіночі референси RGB 941×1672 з чорним фоном збережено без змін. Використано тільки руки та окремі маски предметів; жодне повне референсне тіло не накладається на гру. Оригінальні чоловічі/жіночі бази, білизна, голова, шия, торс, таз, ноги та стопи не перемальовані.

Нова жіноча арт-реєстрація використовує власні плечі/лікті/зап’ястя і контакти. Усі нові PNG RGBA на полотні941×1672 з масштабом1 і початком0,0. Верхні/нижні рухи контролює існуючий скелет та позові сітки; вихідний малюнок не розтягується для нової фігури. Нейтральний кадр точно збігається з браузерним рендером оригінальної бази. Pistol одноручний, вільна ліва рука вихідна. Моделі зброї окремі; передні пальці малюються після предмета. Show/hide не змінює час/матриці/шкіру. Авторські пози перемикаються без напівпрозорого подвоєння.

## Причини та результати

| Проблема | Причина | Зміна | Статус |
|---|---|---|---|
'''+''.join('| '+' | '.join(row)+' |\n' for row in issues)+f'''
## Поточні перевірки

- JavaScript:117/117 (95 ігрових +22 Core/anatomy).
- Python: **{tests['passed']}/{tests['total']} у повному прогоні**, потім **2/2** після корекції двох порівнянь захищених ділянок на точний вихідний прозорий Canvas замість старого сплющеного фону. Runtime між запуском та повторами не змінювався. Сукупно273/274унікальних сценарії; це НЕ один повністю зелений прогін. summary.json і журнали всіх shards додаються. Нових незалежних сценаріїв11. До цього фінального прогону виконано вибіркове очищення492слабких пікселів у4похіднихPNG та виправлення належності жіночих пальців/матеріалу цівки. Всі невдалі та проміжні прогони збережено окремо. Не приховано невдачу: старий тест знаходить4234слабкі віддалені пікселі в base_male.png. Той самий результат і SHA-256 підтверджено в77199cd; усі інші активні Paper Doll PNG пройшли цю перевірку. Базу й поріг тесту не змінено. Повністю зеленого прогону немає, тому критерій завершення з промпта виконано не повністю.
- Реальний Chromium/Lab:1360кадрів (2статі ×4пози ×2стани предмета ×5фонів ×17часів 0…4000мс),24прямі перемикання. Точне замикання циклу. Діагностика alpha_background_consistency_checks зберігає також невдалі порівняння композиції: до правки старий77199cdі новий рендер давали7рівнів RGB похибки. Причину виправлено локально: фон малюється destination-over після складання прозорого персонажа. Контрольний новий рендер має похибку0.416; фінальна матриця використовує суворіший поріг2. Старі невдалі журнали збережено. Стандартні100% контакти перевірено;85/115% — діагностична межа, не нові гарантовані моделі.
-20реальних RAF/MediaRecorder WebM (16циклів +4відео переходів), декодовані кадри та метрики. Змінна частота захоплення;60fps не заявляється. Не монтаж стоп-кадрів.
- Крупні плани100%/300%, джерело → маска → адаптована рука → фактичний рендер. Прозорість/слабка альфа, покриття сіткою, захист оригінальних файлів, базових сегментів і калібровки чоловічого melee перевіряються окремо.
- Фізичні пристрої та інші браузерні рушії не перевірялися. Реальна production-гра не отримувала ці руки; повна художня сумісність із кожним предметом одягу не сертифікована.

## Невдалі перевірки та незалежність

Перший повний прогін був діагностичним під час доопрацювання підготовки, не фінальним запуском одного замороженого runtime. Збережено initial-core-regression.log (39/47), donor-tests-first.log (8/10), core-regression-second.log (56/57) та початковий повний прогін. Жоден із них не видається за зелений. Нові тести виявили слабкі віддалені альфа-пікселі, які прибрано вибірково. Перша перевірка idle помилково порівнювала файл RGBA із браузерними непремультиплікованими RGB при альфі252: тепер порівнюються два справжні canvas-рендери, без послаблення рівності.

Старі вимоги повної незмінності жіночого rig змінено лише щодо дозволених полів poses/pistolOneHand/poseArt/anatomyProjection/posePolicy. Решта скелета, всі старі жіночі PNG, бази та гра залишаються захищені точно. Замість вимоги старого morph перевіряється єдиний непрозорий кінцевий кадр. Проби геометричного ножа/автомата читають фактичні параметри нового ресурсу. Критерії непрозорості, покриття, контактів і збереження пальців не послаблені. Перевірка чоловічих непрозорих пальців виявила зайве перефарбування у новій масці: виправлено підготовку, RGB затвердженої шкіри відновлено. Нові тести не є еталонними знімками після експорту: вони перевіряють окремі фізичні властивості та незалежно виміряні координатні вікна.

Попередні after-female з пакета2d28534 були зняті при скиданні часу на початок старого жіночого переходу. Вони не доводили, що у завершених старих позах зброя взагалі не відображалася. У новому ДО старий перехід завершено перед зйомкою. Історичні знімки не підмінені.

Окремий regression-result.json чесно розділяє повний прогін і2цільові повтори. Архівні знімки не підмінені. Зміни кольору старого фону через виправлену композицію не можна вважати зміною оригінальних пікселів персонажа; нові порівняння суворо перевіряють саме незмінний source на прозорому Canvas. Попередній повний прогін мав271/273та окремий успішний повтор після виправлення еталона торса; це історія попередньої версії, не фінальний результат. Сирий попередній summary дублював суфікси ID, що виправлено у runner. Фінальний запуск не використовує старих результатів і запускає кожен сценарій рівно один раз. Три тести відтворення ресурсів ізольовано перед паралельною фазою читання.

## Межі художнього результату

Жіночі руки не взяті з чоловічих і не є деформованим idle. Генератор використано лише для локальних відсутніх поверхонь rifle; ці джерела й точні маски збережено. Автоматично перенесено лише необхідні ділянки після вирівнювання, а не цілу згенеровану руку. Нові кисті та внутрішні контури плеча потребують вашого художнього приймання. Чоловічі pistol/melee та різниця фактури не оголошуються повністю виправленими. У чоловічої лівої rifle-долоні лишився грубий нижній край: спробу ширше обрізати його відхилено, бо вона втрачала справжню референсну поверхню пальців. Ручний прохід потрібен у avatar-core/assets/male/reference-art/rifle-left-arm.png та rifle-left-front.png (нижня/мізинцева межа), pistol-right-arm.png та pistol-right-front.png (вказівний і світла смуга), melee-right-arm.png (пахва/фактура) і melee-right-front.png (точне художнє приймання хвату). Для жіночих rifle-right-arm.png та rifle-left-arm.png у assets/female/donor-art потрібно прийняти локально домальовані бічні контури та шви фактури. Інші форми рукояток і цівок потребують окремих контактів/артефактів; діагностичне85/115% не замінює такої роботи.

## Відкриття

Розпакувати весь ZIP. Відкрити **Report.html** або **Avatar-Lab.html** у браузері; сервер не потрібен. У Lab вибрати стать та позу; перемикач показу предмета окремий, розміри85/100/115% доступні для перевірки. Галерея та відео — фактичні рендери Core. Sources — оригінальні донори; Retouch — локальні правки; Runtime — чинні модулі; Pipeline — відтворення у вихідному репозиторії, не окремий інсталятор гри.
'''
md=re.sub(r'^-(?=\S)', '- ',md,flags=re.M)
md=re.sub(r'(?<=[А-Яа-яІіЇїЄєҐґ])(?=[0-9A-Za-z])|(?<=[0-9A-Za-z])(?=[А-Яа-яІіЇїЄєҐґ])',' ',md)
(O/'README.md').write_text(md);(O/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n')
for name in ['Gallery','Sources','Retouch','Baseline','Masks','Runtime','Pipeline','Test-results']:
 p=D/name
 if p.exists():shutil.rmtree(p)
for name in ['Gallery','Sources','Retouch','Baseline','Masks']:shutil.copytree(O/name,D/name)
for gender in ['male','female']:shutil.copy2(R/f'base_{gender}.png',D/f'base_{gender}.png')
shutil.copytree(R/'avatar-core',D/'Runtime');(D/'Pipeline').mkdir();(D/'Test-results').mkdir()
for name in ['prepare-female-donor-arms.py','finish-male-contact-contours.py','prepare-independent-anatomy.py','capture-female-donor-pass.py','record-female-donor-motion.py','bundle-avatar-lab.py','diagnose-alpha-composition.py','inspect-donor-prop-components.py','audit-paper-doll-png.py','run-python-tests.py']:shutil.copy2(R/'tools'/name,D/'Pipeline'/name)
for p in [R/'tests/test_female_donor_arms.py',R/'tests/avatar_revision_contract.py']:shutil.copy2(p,D/'Pipeline'/p.name)
shutil.copytree(O/'final-acceptance',D/'Test-results/full-final');shutil.copytree(O/'release-regression',D/'Test-results/pre-background-interrupted');shutil.copytree(O/'full-regression',D/'Test-results/full-initial');shutil.copytree(O/'full-regression-final',D/'Test-results/earlier-full');shutil.copytree(O/'full-regression-release',D/'Test-results/interrupted')
for p in O.glob('*.log'):shutil.copy2(p,D/'Test-results'/p.name)
for p in O.glob('*.json'):
 if p.name not in ['package.json','offline-package-check.json','https-verification.json']:shutil.copy2(p,D/p.name)
(D/'README.md').write_text(md);shutil.copy2(R/'docs/avatar-core-female-donor-art.md',D/'Pipeline-guide.md');shutil.copy2(R/'docs/avatar-weapon-attachments.md',D/'Item-attachment-guide.md')
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(D/'Avatar-Lab.html')],cwd=R,check=True)
def embed(path):return 'data:'+mimetypes.guess_type(path.name)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()
selected=[f'female-{p}-visibility.webp' for p in ['idle','melee','pistol','rifle']]+[f'female-{p}-comparison.webp' for p in ['melee','pistol','rifle']]+[f'{n}-3x.webp' for n in ['female-rifle-wrist','female-rifle-right','female-rifle-shoulder','female-pistol-grip','female-melee-grip','male-rifle-right','male-rifle-left','male-pistol','male-melee','female-neck']]
style='body{font:16px system-ui;background:#12191e;color:#eee;margin:auto;max-width:1400px;padding:16px;overflow-wrap:anywhere}a{color:#90d2ff}img,video{max-width:100%;height:auto}pre{white-space:pre-wrap;line-height:1.6}figure{margin:20px 0}summary{cursor:pointer;padding:10px}'
def inline(text):
 text=html.escape(text);text=__import__('re').sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text);text=__import__('re').sub(r'`([^`]+)`',r'<code>\1</code>',text);return text
def markdown_report(text):
 lines=text.splitlines();out=[];i=0
 while i<len(lines):
  line=lines[i].strip()
  if not line:i+=1;continue
  if line.startswith('# '):i+=1;continue
  if line.startswith('## '):out.append('<h2>'+inline(line[3:])+'</h2>');i+=1;continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
    if not all(set(c)<=set('-: ') for c in cells):rows.append(cells)
    i+=1
   out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>'for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>'for c in row)+'</tr>'for row in rows[1:])+'</tbody></table></div>');continue
  if line.startswith('- '):
   out.append('<ul>')
   while i<len(lines) and lines[i].strip().startswith('- '):out.append('<li>'+inline(lines[i].strip()[2:])+'</li>');i+=1
   out.append('</ul>');continue
  para=[]
  while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('# ','## ','|','- ')):para.append(lines[i].strip());i+=1
  out.append('<p>'+inline(' '.join(para))+'</p>')
 return ''.join(out)
style+=' h1,h2{line-height:1.25}p,li{line-height:1.65}h2{margin-top:32px}.table-wrap{overflow:auto}table{border-collapse:collapse;min-width:660px;width:100%}th,td{border:1px solid #46505a;padding:10px;vertical-align:top;text-align:left}th{background:#25313a}code{overflow-wrap:anywhere}nav{display:flex;gap:20px;flex-wrap:wrap}figcaption{padding:8px 0;color:#c9d5df}summary{background:#25313a;margin:8px 0}video{display:block}'
body='<h1>Avatar Core — жіночі донорські руки</h1><nav><a href="Avatar-Lab.html">Відкрити інтерактивний Lab</a><a href="#images">Порівняння</a><a href="#videos">Реальні відео</a><a href="README.md">Текст звіту</a></nav>'+markdown_report(md)+'<h2 id="images">Фактичний результат і крупні плани</h2>'
body+='<figure><figcaption>Чотири жіночі пози на незміненій базі</figcaption><img alt="Чотири жіночі пози" src="'+embed(D/'Gallery/female-four-poses.webp')+'"></figure>'
for name in selected:body+='<figure><figcaption>'+html.escape(name)+'</figcaption><img src="'+embed(D/'Gallery'/name)+'"></figure>'
body+='<h2 id="videos">Записи живого RAF — 20 відео</h2>'
for rec in motion['recordings']:body+='<details><summary>'+html.escape(rec['path'])+'</summary><video controls loop muted preload="metadata" src="'+embed(D/'Gallery'/rec['path'])+'"></video></details>'
body+='<details><summary>Уся галерея та покадрова матриця</summary>'+''.join('<p><a href="Gallery/'+html.escape(p.name)+'">'+html.escape(p.name)+'</a></p>' for p in sorted((D/'Gallery').iterdir()))+'</details>'
(D/'Report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Avatar Core — донорські руки</title><style>'+style+'</style>'+body+'</html>')
manifest={str(p.relative_to(D)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='Package-SHA256.json'};(D/'Package-SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
z=D.with_suffix('.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as out:
 for p in sorted(D.rglob('*')):
  if p.is_file():out.write(p,D.name+'/'+str(p.relative_to(D)))
result={'source_commit':source,'path':str(z),'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'files':len(manifest)+1,'production_ready':False};(O/'package.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
