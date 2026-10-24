"""Self-contained honest review and Lab delivery; never replaces reference sprites."""
from pathlib import Path
import base64,hashlib,html,json,shutil,subprocess,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-exact-reference-pass';DEST=ROOT.parent/'Male-Exact-Reference-Review';DEST.mkdir(exist_ok=True);G=OUT/'Gallery'
capture=json.loads((OUT/'browser-capture.json').read_text());rows=json.loads((OUT/'alpha-cleanup.json').read_text());panels=[]
def pic(name,label):
 p=G/name;mime='image/png' if p.suffix=='.png' else 'image/webp';return '<figure><img loading="lazy" src="data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()+'"><figcaption>'+html.escape(label)+'</figcaption></figure>'
overview=Image.new('RGB',(1880,836),'#f7f4ec')
for i,pose in enumerate(['idle','rifle','pistol','melee']):overview.paste(Image.open(G/(pose+'-actual.webp')).resize((470,836)),(470*i,0))
overview.save(G/'four-actual-poses.webp',lossless=True);panels.append(pic('four-actual-poses.webp','Фактичний модульний аватар: idle / rifle / pistol / melee. Художні обмеження хватів див. таблицю.'))
for pose in ['idle','rifle','pistol','melee']:panels.append(pic(pose+'-comparison.webp',pose+' · ліворуч лише референс, праворуч фактичний модульний Core. Однаковий масштаб, без деформації референсу.'))
for pose,sides in [('rifle',['right','left']),('pistol',['right']),('melee',['right'])]:
 for side in sides:
  for joint in ['grip','wrist','shoulder']:panels.append(pic(f'{pose}-{side}-{joint}.webp',f'{pose} / {side} / {joint} · ДО та ПІСЛЯ очищення альфи / окремий новий ніж; пальці не перемальовані.'))
for pose in ['idle','rifle','pistol','melee']:panels.append(pic(pose+'-breathing.webp',pose+' · чинний цикл 4000 мс / 32 кадри.'))
for p in sorted(G.glob('appearance-*.webp')):panels.append(pic(p.name,'Каталог чоловічих облич × дозволені зачіски; кадр melee. Усі чотири пози додатково пройшли технічну перевірку.'))
for pose in ['idle','rifle','pistol','melee']:
 for bg in ['fff','777','000','00ff00']:panels.append(pic(f'{pose}-background-{bg}.webp',pose+' · фон #'+bg))
issues=[
 {'file':'avatar-core/assets/male/exact-pass/pistol-right-frontImage.png','problem':'Окремий alpha=1 піксель біля передпліччя, поза основним 8-зв’язним силуетом','evidence':'alpha-cleanup.json / art-front-pistol-right','priority':'P2','fix':'Похідний PNG: видалено лише 1 слабкопрозорий піксель','status':'Виправлено технічно; хват не змінено'},
 {'file':'avatar-core/assets/male/exact-pass/rifle-left-image.png','problem':'Три окремі слабкопрозорі компоненти верхньої руки: 10+19+11 пікселів, alpha максимум 8','evidence':'alpha-cleanup.json / art-rifle-left','priority':'P2','fix':'Похідний PNG; решта байтів RGBA не змінені','status':'Виправлено технічно'},
 {'file':'avatar-core/assets/male/lobby/rifle-right-{arm,front}.png','problem':'Закритий кулак замість природного обхвату рукоятки, немає потрібної форми вказівного пальця та великого пальця','evidence':'rifle-right-grip.webp; rifle-comparison.webp','priority':'P0','fix':'Домалювати кисть у робочих копіях arm/front, залишити зап’ястя [324,631] та існуючий bind; уточнити контакт зі зброєю після малюнка','status':'НЕ виправлено: потрібна художня робота'},
 {'file':'avatar-core/assets/male/pose-art/pistol-right-{arm,front}.png','problem':'Одноручна поза збережена, але пальці та рукоятка не утворюють переконливого контакту','evidence':'pistol-right-grip.webp; pistol-comparison.webp','priority':'P0','fix':'Домалювати пальці/великий палець без зміни плеча/ліктя, зап’ястя [265.764,352.022]','status':'НЕ виправлено: потрібна художня робота'},
 {'file':'avatar-core/assets/male/lobby/rifle-left-{arm,front}.png','problem':'Підтримка знизу є, але контакт пальців з цівкою відрізняється від референсу','evidence':'rifle-left-grip.webp','priority':'P1','fix':'Локально уточнити пальці й передній thumb-шар; зап’ястя [658,725], цівка [619,755]','status':'Потрібне художнє доведення'},
 {'file':'avatar-core/assets/weapons/melee.png','problem':'У попередній версії ніж був схематичним','evidence':'melee-comparison.webp; melee-right-grip.webp','priority':'P1','fix':'Створено окремий ілюстративний PNG assets/weapons/male-exact/knife.png; прив’язано до чинної кисті, без референсних пікселів','status':'Замінено тестовим художнім предметом; потрібне візуальне затвердження'},
 {'file':'avatar-core/assets/male/hands/melee-right.png / melee-right-wrist-patch.png','problem':'Кисть виглядає надто блоковою відносно передпліччя, стик зап’ястя має помітний виступ','evidence':'melee-right-grip.webp; melee-right-wrist.webp','priority':'P1','fix':'Локально домалювати кисть й анатомічний стик у похідних ресурсах, не змінюючи позу опущеної руки','status':'НЕ виправлено художньо; новий ніж не приховує дефект'},
 {'file':'avatar-core/rigs/male_rig.json / poses','problem':'Висота обох кистей rifle та напрямок pistol відрізняються від референсів','evidence':'rifle-comparison.webp; pistol-comparison.webp','priority':'P1','fix':'Після нової анатомії кистей повторно зареєструвати зброю; не приховувати різницю підміною цілого спрайта','status':'Залишено чинну основу; точна відповідність НЕ досягнута'},
 {'file':'avatar-lab / equipment binding','problem':'Діагностичні рукави не доводять сумісність усього ігрового одягу з бойовими руками','evidence':'*-diagnostic-sleeves.webp / поточні браузерні тести','priority':'P1','fix':'Окреме припасування фактичного одягу після затвердження рук','status':'Повна сумісність НЕ підтверджена'},
]
(OUT/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n')
table='<table><tr>'+''.join('<th>'+x+'</th>' for x in ['Файл','Проблема','Доказ','Пріоритет','Спосіб виправлення','Статус'])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ['file','problem','evidence','priority','fix','status'])+'</tr>' for r in issues)+'</table>'
summary=f'''<h1>Male Avatar Core · перевірка точних референсів</h1><p class="warning">ЧАСТКОВИЙ РЕЗУЛЬТАТ. Нової анатомії кистей немає. Прийнятний хват rifle/pistol ще не готовий; новий окремий ніж потребує затвердження. Не production-ready.</p><p>Без зміни main, жіночого рига, вихідних PNG, геометрії рук, rifle/pistol та анімаційного механізму. Виправлення цього проходу: 41 відокремлений піксель з альфою ≤8 у двох похідних поверхнях; підключено окремим перевизначенням male-preview. Створено й підключено окремий художній ніж тільки для чоловічого melee; жіноча зброя не змінена. Цілі референсні персонажі використані лише в порівняннях.</p><p>Реальний Canvas-рендер Avatar Core з базою гри. Це не нова інтеграція в основний index.html. {len(capture['appearance_pose_cases'])} комбінацій зовнішності/поз завантажено й перевірено технічно; не незалежна художня оцінка кожної комбінації. Chromium {html.escape(capture['browser'])}. Фізичний телефон не перевірявся. Збереження гри не записувалися.</p><p>Дихання: 4000 мс, по32 кадри на кожну позу. Контактні похибки &lt;1e−6 — це збіг координат, а не доказ природності пальців. Діагностичні рукави працюють, повна сумісність ігрового одягу НЕ заявляється.</p><p>Спроби художнього редагування цих хватів раніше були відхилені інструментом зображень (violence). Нових схожих запитів в обхід відхилення не виконували. Новий незалежний запит на зображення самого ножа без людини успішний; це не нові кисті. Програмна маска не замінює необхідний малюнок.</p><p>Фінальна регресія:175/175 тестів (115 JavaScript,60 Python/Chromium). Перший прогін нового ножа:48/49 через старі жорсткі координати його кінчика; невдалий журнал збережено. Остаточні результати — test-logs та test-results.json.</p><p><a href="Avatar-Lab.html">Відкрити автономний інтерактивний Lab</a></p>'''
style='body{margin:auto;max-width:1250px;padding:20px;background:#182024;color:#eee7da;font:16px/1.5 system-ui}a{color:#9cd7ef}img{max-width:100%;height:auto}figure{margin:24px 0}figcaption{padding:8px}table{display:block;overflow:auto;border-collapse:collapse}td,th{border:1px solid #687273;padding:9px;min-width:120px;vertical-align:top;overflow-wrap:anywhere}.warning{border:2px solid #e5aa6b;padding:15px}code{overflow-wrap:anywhere}'
report='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Male Core · фактичний стан і референси</title><style>'+style+'</style>'+summary+table+''.join(panels)+'</html>'
(OUT/'Report.html').write_text(report)
readme='''# Male Avatar Core — часткове очищення та незалежна перевірка референсів

База до змін: `02cae62`. Точка відновлення: `avatar-core-before-exact-adaptation-02cae62`.
Робоча гілка: `feature/avatar-core-2-weapon-transitions`. Коміт технічної правки `a6f6433`. Main не змінено: `f70b7e5be63f6b85d895c6d5b259adbc30577b86`.

**Завдання художньої адаптації НЕ завершене.** Не замінено персонажа повними референсами. Порівняння показують відмінності, зокрема кулак rifle та неприродний контакт pistol. Очищення41 альфа-пікселя не виправляє ці проблеми.

Відкрити `Report.html` у браузері: усі зображення та анімовані цикли вбудовані. Інтерактивний `Avatar-Lab.html` автономний, із фактичним модульним аватаром. Референси не входять у runtime. Інструкція ZIP про показ повного спрайта суперечить прямому повідомленню користувача й не виконувалася.

## Реальні зміни

- `tools/prepare-male-alpha-surfaces.py`: відтворюваний вибір тільки8-зв’язних компонентів ≤20 пікселів, максимум альфи ≤8. Не erosion/blur, не зміна анатомії.
- `avatar-core/assets/male/exact-pass/`: дві похідні поверхні, 41 змінений піксель. Вихідні arm/front PNG залишено незмінними.
- `avatar-core/male-preview.json`: `poseArtSurfaces` лише для чоловічих поверхонь, окремий чоловічий melee-ніж; жіночий спільний ресурс не змінено.
- `tools/prepare-male-knife-prop.py` та `avatar-core/assets/weapons/male-exact/knife.png`: новий незалежний предмет, очищення слабкої зовнішньої альфи, реєстрація центра ручки та кута335° у чинній позі.
- `avatar-core/engine.mjs`: два fallback-посилання завантаження поверхонь, без змін координат рук, анімації, шарів, rifle/pistol.
- `tests/test_exact_reference_pass.py`: п’ять незалежних точні перевірки меж правки.
- `tests/test_avatar_polish.py`: старий тест кінчика ножа використовував жорсткі координати старого ресурсу; для нового чоловічого PNG кінчик визначається за непрозорими пікселями. Збережено перевірки напрямку вниз (>80px), відхилення вбік (>30px), відсутності перетину стегна; жіночий тест незмінений. Перший невдалий прогін (48/49) збережено у python-regression-before-knife-tip-update.log.
- `tests/test_grip_pass.py`: відокремлено нову поверхню від історичної перевірки chest-only; усі старі параметри досі порівнюються точно.
- `tests/test_male_hand_kit.py`: історичний комплект перевіряється за своїм комітом7854994, не заморожує назавжди поточний engine. Новий тест окремо перевіряє точний diff engine та конфігурації.
- `tools/review-male-exact-pass.py`: справжні Core-рендери, 4фони,4цикли, крупні плани, каталог зовнішності ×4пози, діагностичні рукави.
- `tools/package-male-exact-pass.py`: автономний звіт, Lab, поточні модулі та хеші.

## Межі перевірки

Немає нової інтеграції в основний index.html: основна гра не змінена. У Lab використовується її базовий аватар і каталог облич/волосся. Це не є підтвердженням сумісності всього одягу чи фізичного мобільного пристрою. До/після показує тільки альфа-очищення, не нові пальці. Створено окремий PNG ножа, відтворювана реєстрація у knife-registration.json; початкова генерація збережена у Sources/knife-working.png. Ніж потребує візуального погодження. Потрібно домалювати конкретні PNG з таблиці issues.json.

Попередні запити imagegen на виправлення rifle/pistol були відхилені інструментом (violence; IDs0d3c1b81-1738-4542-b497-c103de6c6607 та91d1ae3e-d503-4d64-9f64-564cbcc8994a). Нової генерації кистей немає. Окремий художній ніж згенеровано без людини та підключено як незалежний предмет; tools/prepare-male-knife-prop.py відтворює його очищення альфи та реєстрацію.

Чинна перевірка:115 JavaScript-тестів;49 Python/Chromium регресійних +11 перевірок альфи/комплекту. Підсумок175 успішних автоматичних тестів. Окремий capture:280 технічних комбінацій зовнішності/пози; це не280 художніх затверджень.

Перше offline-відкриття звіту чекало декодування всіх lazy-зображень і зависло; його перервано. Остаточна перевірка окремо декодує всі вбудовані зображення через Pillow, а в Chromium відкриває реальний file:// звіт і Lab. Це не заміна браузерної перевірки Lab. Перший тест восьми статичних поз помилково вимагав нульову похибку під час незавершеного жіночого переходу; журнал offline-before-freeze.log збережений. У фінальній перевірці статичних поз дихання/перехід зупинено, а всі анімовані чоловічі цикли перевірені окремо. Жіночий механізм не змінювався.

Точні результати поточних запусків: `test-logs/`; автоматичні результати не є художнім затвердженням. Галерея `Gallery/`, машинні спостереження `browser-capture.json`, точний альфа-diff `alpha-cleanup.json`.
'''
(OUT/'README.md').write_text(readme)
for name in ['Report.html','README.md','issues.json','alpha-cleanup.json','browser-capture.json','knife-registration.json','test-results.json','changed-files.json','reference-package.json']:shutil.copyfile(OUT/name,DEST/name)
for folder in ['Gallery','test-logs']:shutil.copytree(OUT/folder,DEST/folder,dirs_exist_ok=True)
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(DEST/'Avatar-Lab.html')],cwd=ROOT,check=True)
p=DEST/'Avatar-Lab.html';p.write_text(p.read_text().replace('<main>','<p style="padding:12px;border:2px solid orange">Частковий alpha-cleanup. Кисті rifle/pistol потребують художнього доведення; це не затверджена інтеграція.</p><main>',1))
shutil.copytree(OUT/'Sources',DEST/'Sources',dirs_exist_ok=True)
# Current actual arm modules, not empty artist placeholders or reference-derived limbs.
rig=json.loads((ROOT/'avatar-core/rigs/male_rig.json').read_text());cfg=json.loads((ROOT/'avatar-core/male-preview.json').read_text());modules=[]
for pose,sides in rig['poseArt'].items():
 for side,art in sides.items():
  for key in ['image','frontImage']:
   slot=('art-front-' if key=='frontImage' else 'art-')+pose+'-'+side;source=ROOT/'avatar-core'/cfg['poseArtSurfaces'].get(slot,art[key]);dest=DEST/'Modules'/f'{pose}-{side}-{key}.png';dest.parent.mkdir(exist_ok=True);canvas=Image.new('RGBA',(941,1672));canvas.alpha_composite(Image.open(source).convert('RGBA'),tuple(art['mesh']['bounds'][:2]));canvas.save(dest);modules.append({'path':str(dest.relative_to(DEST)),'source':str(source.relative_to(ROOT)),'bounds':art['mesh']['bounds'],'bind':art['bind'],'anchors':art['anchors'],'status':'existing arm anatomy, alpha cleanup only'})
weapon_dir=DEST/'Modules/Weapons';weapon_dir.mkdir(exist_ok=True)
for pose,weapon in cfg['weapons'].items():shutil.copyfile(ROOT/'avatar-core'/weapon['image'],weapon_dir/(pose+'.png'))
(DEST/'Modules/registration.json').write_text(json.dumps(modules,indent=2)+'\n');shutil.copyfile(ROOT/'avatar-core/male-preview.json',DEST/'Modules/male-preview.json')
(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('РозпакуйZIP. Відкрий Report.html у браузері: фото та анімації вбудовані. Avatar-Lab.html — автономний інтерактивний Core.\n\nРЕЗУЛЬТАТ ЧАСТКОВИЙ:41 альфа-піксель очищено. Нової анатомії кистей немає. Окремий новий ніж потребує затвердження. Деталі у звіті. Main не змінений.\n')
manifest=[{'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='Package-SHA256.json'];(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT.parent/'Male-Exact-Reference-Review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(archive,archive.stat().st_size,'bytes')
