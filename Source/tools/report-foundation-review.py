"""Write factual delivery report from fresh machine evidence; no stale green totals."""
from pathlib import Path
import json,subprocess,hashlib,re
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';E=O/'Evidence'
def read(p):return json.loads((E/p).read_text())
results=read('final-tests/summary.json');dense=read('dense-cycles.json');raf=read('real-raf-motion.json');probes=read('browser-probes.json');motion=read('endpoint-motion.json')
js=(E/'final-javascript.log').read_text();jstotal=int(re.search(r'ℹ tests (\d+)',js)[1]);jspass=int(re.search(r'ℹ pass (\d+)',js)[1])
issues=[
('01','Білі смуги шиї / талії','Відтворено на CSS320/DPR1: α150 замість253 біля шиї; CSS391,5: α229 біля талії.','Native941×1672 compositor, один display resize; спільна pinned mesh торса/одягу.','Виправлено в перевіреній матриці DPR1/2.'),
('02','Жіноче rifle-плече','Зарубки та вузькі провали зовнішнього краю.','Локальний похідний rifle-right-complete.png; збережена проксимальна реєстрація.','Технічний край покращено; художнє приймання потрібне.'),
('03','Жіноче rifle-передпліччя','Трикутний виступ, обрізання знизу.','Локальна ретуш, повна поверхня і явне володіння переднім шаром.','Покращено; контур показано 1×/3×.'),
('04','Жіноча опорна кисть rifle','Коричневі клапті над нігтями та по боках.','Локально відновлено шкіру, прибрано чужий матеріал.','Виправлено видимі клапті у контрольному рендері.'),
('05','Чоловіча опорна кисть rifle','Чорні зубці й коричневі виступи.','Похідні rifle-left-arm/front/complete; чистий край пальців.','Виправлено видимі артефакти; хват потребує приймання.'),
('06','Чоловіча права кисть rifle','Зубчастий темний залишок під долонею.','Локальна ретуш і незалежний предмет.','Виправлено контрольний край.'),
('07','Чоловічий pistol-зап’ясток','Світла смуга, пунктирний край, чорний залишок.','Ретуш шва, відновлення справжнього негативного просвіту з оригіналу.','Покращено; крупний план збережено.'),
('08','Чоловічий pistol-вказівний','Сумнівні довжина/перехід пальця.','Без зміни кісток; локально уточнена поверхня.','Не оголошено повністю закритим: потрібне художнє рішення.'),
('09','Жіночий pistol-контур','Темна обводка, світлий клин і грубе зап’ястя.','Локальна ретуш лише похідної руки; природний просвіт збережений.','Покращено, показано без предмета.'),
('10','Фактура жіночих рук','Жили / об’єм відрізняються від idle.','Невелика тонова гармонізація, без розмиття тіла.','Частково покращено; художнє приймання відкрите.'),
('11','Чоловічий melee','Різка фактура й монтажний край кисті.','Ретуш похідного сегмента; базова анатомія та проєкція збережені.','Край покращено; фактура не сертифікована як фінальна.'),
('12','Жіночий melee','Східчастий хват, темні залишки.','Локально відновлена повна кисть і розділені шари.','Покращено; показано без ножа й із ножем.'),
('13','Шкіра в weapon PNG','Донорська шкіра й отвори в предметах.','Використані цілі наявні чисті props з точно збереженими афінними перетвореннями.','Виправлено розділення ресурсів; інші форми зброї не сертифіковані.'),
('14','Матові ореоли рук','Темні краї й слабкий шум.','Вибіркове очищення alpha≤16 поза2px від ядра; RGB fringe від найближчої непрозорої шкіри.','Активні ресурси пройшли критерії; не загальна ерозія.'),
('15','Різні деформації одягу','Torso affine проти pinned mesh, інші UV рук.','Спільна torso mesh; poseSources для діагностичних рукавів/рукавичок.','Перевірено діагностикою, старий довільний одяг не сертифіковано.'),
('16','85/115% предметів','Другий контакт не перекалібровується.','Залишено явно діагностичними розмірами;100% — калібрований профіль.','Обмеження задокументовано; універсальні хвати не реалізовані.'),
('17','Гардероб / майбутні скіни','Реального garment integration немає.','8 типів контрольного одягу,2 відтінки skin probe, обидві статі й пози.','Діагностика підтверджена; реальний гардероб не заявляється.'),
('18','Розріджені відео','Старі20відео повторно декодовані; не доказ60fps.','Точні241RGBAкадр на випадок + нові реальні RAF відео з PTS.','Покриття покращено; actual FPS див. JSON, не тест фізичного пристрою.'),
('19','Alpha-шум бази / регресія','Захищений base_male.png має слабкий шум; baseline273/274.','Похідні runtime-копії:4281піксель,α≤3, решта RGBA незмінні.','Runtime очищено; старий тест оригіналу навмисно залишається невдалим.'),
('20','Застаріла документація','Активні жіночі бойові руки вже підключені.','Оновлено актуальний опис формату і фактичну карту ресурсів.','Виправлено в поточному звіті; старі історичні звіти не підмінено.'),
('22','Приклади male/female foundation-cleanup/rifle-weapon.png','Male:38,74px до ліктя при межі35px; female:146,17px до плеча при межі60px.','Контакти обох кистей збережені; окремий контур/довжина приклада потребують адаптації.','Відкрито. Тест не послаблено.'),
('21','Ніж / надмірний рух ліктя','Pinned grip + IK: ніж майже нерухомий, female elbowspan8,98px.','Forward upper±0,035°,fore±0,12°,hand±1,6°; ніж успадковує кисть.','Виправлено обидві статі;4000ms, instant cuts, grip error<1e-6.')]
issues.sort(key=lambda r:int(r[0]))
files={
 '01':['avatar-core/engine.mjs'],
 '02':['avatar-core/assets/female/foundation-cleanup/rifle-right-complete.png'],
 '03':['avatar-core/assets/female/foundation-cleanup/rifle-right-complete.png'],
 '04':['avatar-core/assets/female/foundation-cleanup/rifle-left-complete.png'],
 '05':['avatar-core/assets/male/foundation-cleanup/rifle-left-complete.png'],
 '06':['avatar-core/assets/male/foundation-cleanup/rifle-right-complete.png'],
 '07':['avatar-core/assets/male/foundation-cleanup/pistol-right-complete.png'],
 '08':['avatar-core/assets/male/foundation-cleanup/pistol-right-complete.png'],
 '09':['avatar-core/assets/female/foundation-cleanup/pistol-right-complete.png'],
 '10':['review/avatar-foundation-cleanup/Evidence/art-export.json'],
 '11':['avatar-core/assets/male/foundation-cleanup/melee-right-complete.png'],
 '12':['avatar-core/assets/female/foundation-cleanup/melee-right-complete.png'],
 '13':['review/avatar-foundation-cleanup/Evidence/prop-export.json'],
 '14':['tools/prepare-foundation-cleanup.py'],
 '15':['avatar-core/engine.mjs','avatar-core/assets/diagnostics/config.json'],
 '16':['avatar-lab/index.html','docs/avatar-weapon-attachments.md'],
 '17':['avatar-core/assets/diagnostics/config.json'],
 '18':['tools/capture-foundation-dense.py','tools/record-foundation-raf.py'],
 '19':['base_male.png','avatar-core/assets/male/foundation-cleanup/base-runtime.png'],
 '20':['docs/avatar-weapon-attachments.md'],
 '21':['avatar-core/relaxed-melee.mjs','avatar-core/engine.mjs'],
 '22':['avatar-core/assets/male/foundation-cleanup/rifle-weapon.png','avatar-core/assets/female/foundation-cleanup/rifle-weapon.png']}
md='''# Avatar Foundation cleanup — кисті, ніж та модульні поверхні\n\nРобоча гілка: `feature/avatar-core-2-weapon-transitions`. ДО: `c2822a7`. Точка відновлення: `avatar-before-comprehensive-cleanup-c2822a7`.\n\nMain `f70b7e5be63f6b85d895c6d5b259adbc30577b86`, гра, обидва rig JSON, оригінальні бази, донори, голови, зачіски та збереження не змінені. Зміни виконані тільки в дослідному Core/Lab і похідних ресурсах. Це результат для візуального погодження, а не production-ready інтеграція.\n\n## Основний результат: рух ножа\n\nВідмовились від inverse solve нерухомого ножа саме в melee. Рух задається від авторських кутів; ніж і хват мають одну матрицю. При default2px повний розмах кисті/ножа3,2°. Повний розмах ліктя: male1,20×1,12px, female0,91×0,91px; було male2,54×0,54px та female8,98×2,67px. Період4000ms. Початкові/кінцеві RGBAкадри циклу збігаються. Instant cut збережено; старий morph не повернуто.\n\n`Gallery/male-knife-motion-before-after.webp` та `female-knife-motion-before-after.webp` — синхронне порівняння. Це зменшені20fpsпрев’ю, не вимірювання FPS.\n\n## Реєстр дефектів\n\n|№|Пріоритет|Файл|Проблема|Доказ / причина|Правка|Статус|\n|---|---|---|---|---|---|---|\n'''
for row in issues:md+='|'+'|'.join([row[0],('P2' if row[0] in ['18','19','20'] else 'P1'),'; '.join('`'+f+'`' for f in files[row[0]]),*row[1:]])+'|\n'
md+='''\n## Ресурси й відтворення\n\nВісім локальних ретушей рук збережено в Edits; точні джерельні crops у Before. Не генерувався новий цілий персонаж. Пайплайн `tools/prepare-foundation-cleanup.py` зберігає оригінальні реєстрації/риг, експортує arm/front/complete і чисті предмети. Жіночі накладки941×1672; чоловічі cropped PNG відповідають rig.mesh.bounds. Параметри/хеші: Evidence/art-export.json, prop-export.json, runtime-alpha-cleanup.json. Альфа переднього шару відокремлює дистальну кисть від передпліччя.\n\nЗавершена рука малюється один раз. Передні пальці застосовуються до окремого weapon-group через source-atop тільки в межах предмета; відкритий край шкіри не подвоюється. Тест порівнює всі RGBAбайти поза предметом при visible/hidden.\n\nНові runtime-матові копії чоловіка не змінюють жодного іншого RGBAбайта. Оригінальні PNG і суворий старий поріг збережено. Ресурс ножа взято з наявного clean prop, не з донорського повнокадрового зображення.\n\n## Поточна регресія\n\n'''
md+=f'JavaScript: **{jspass}/{jstotal}**. Python: див. точні поля `Evidence/final-tests/summary.json`: `{json.dumps({k:v for k,v in results.items() if k!="shards"},ensure_ascii=False)}`.\n\n'
md+=f'Нативні lossless: **{sum(x["logical_frames"] for x in dense["subject_frames"])}** кадрів у {len(dense["subject_frames"])} випадках. 241кадр включно0..4000ms з кроком1000/60ms. `.avframes` зберігає точні RGBAбайти кожного кадру, включно з невидимими RGB; кожний SHA перевірено після декодування. `ViewFrames.html` відкриває їх автономно; `tools/verify-foundation-frames.py` незалежно декодує/експортує PNG.\n\n'
md+=f'Нові живі записи: **{len(raf["recordings"])}** WebM, справжній requestAnimationFrame/MediaRecorder; actual timestamps та max_gap_seconds — `Evidence/real-raf-motion.json`. Не заявляється стабільні60fps. Прозорі dense-кадри перевіряються на5фонах через viewer; додаткові реальні direct-background перевірки окремо в browser-probes.json. Це не19280окремих Canvasрендерів.\n\n'
md+='''Старий пакет: усі288вхідних SHA звірені. 268зображень переглянуто оглядово з цільовими збільшеннями, не вручну кожний піксель.20відео незалежно повторно декодовані; PTS і кількість у old-videos-independent-decode.json. Проміжні невдалі/перервані запуски збережено в Evidence; вони не зараховані до фінального прогону. В одному ранньому тесті помилково вимагалиα255, хоча вихідна шкіраα252–253; критерій тепер відносний до незмінного джерела. Контактні тести мають незалежні вихідні RGBA/UV; стара female pistol мала blended weights і жодної rigidhandкомірки, тому тепер перевіряються також математично спроєктовані UVпікселі. Старі контрольні еталони не підмінені.\n\n## Обмеження\n\nЕксперимент пакетного переднього шару відхилено: виграшу часу не було, змінилися крайові RGBA. Початковий комітований compositor відновлено побайтно. Вимірювання під паралельним тестовим навантаженням збережені, це не FPS реального пристрою. Також raw-читання кадрів виявилось повільнішим за PNG; фінальна зйомка використовує PNG.\n\nСуворі перевірки rifle stock contact не проходять (male38,74px до ліктя при межі35px; female146,17px до плеча при межі60px). Female rifle stock contact не проходить для нового чистого предмета: відстань до плеча146,17px при порозі60px. Її не послаблено. Потрібен окремий адаптований female rifle-weapon.png із правильним контуром приклада; це відкрита проблема, незалежна від виправленого руху ножа.\n\nПотрібне художнє погодження пальців/фактури, особливо male pistol index та female бойових передпліч. Для ручного допрацювання використовувати `avatar-core/assets/{male,female}/foundation-cleanup/{pose}-{side}-complete.png` і відповідні front/arm через пайплайн; не малювати поверх оригінальної бази.\n\nПеревірено Chromium у Linux. Firefox/WebKit і фізичні пристрої недоступні; вузький viewport — емуляція. Реальний гардероб не інтегровано: перевірено лише діагностичні gridgarments та наявні compatibilityтести. Не доведена сумісність будь-якого майбутнього одягу/будь-якої зброї. Гру й GitHubPages не публікували й не змінювали. Опублікований буде лише автономний review-архів окремим tag.\n\n## Відкриття\n\nДля повторної зйомки у свіжому репозиторії підготуйте `../avatar-foundation-baseline` на `c2822a7` (окремий detached worktree). Великі generated Gallery/Evidence зберігаються у хешованому review-архіві, не дублюються в історії робочої гілки;8beforePNG для Lab і критичні маски/маніфести залишаються в Git. Невдалі перевірки не видалені: усі поточні логи і фактичні failure_ids включені в архів.\n\nPipeline/Source запускаються у вихідному репозиторії; Runtime — точні ресурси для ревізії, не окремий інсталятор гри. Повністю розпакувати ZIP. Відкрити Report.html браузером, Avatar-Lab.html — інтерактивний реальний Lab без сервера. Вибрати стать → melee → breathing. Передні пальці, ніж, діагностичний одяг і2skinprobeвідтінки перемикаються незалежно. Нативні кадри: ViewFrames.html → вибрати файл Gallery/Dense/*.avframes.\n'''
md=re.sub(r'(?<=[а-яА-ЯіІїЇєЄґҐ])(?=[0-9])',' ',md)
md=re.sub(r'(?<=[0-9])(?=[а-яА-ЯіІїЇєЄґҐ])',' ',md)
for a,b in [('default2px','стандартному параметрі 2 px'),('4000ms','4000 мс'),('1000/60ms','1000/60 мс'),('20fps','20 кадрів/с'),('RGBAкадр','RGBA-кадр'),('RGBAбайт','RGBA-байт'),('DPR1/2','DPR 1/2')]:md=md.replace(a,b)
(O/'README.md').write_text(md)
(O/'issue-register.json').write_text(json.dumps([dict(files=files[row[0]],priority=('P2' if row[0] in ['18','19','20'] else 'P1'),**dict(zip(['id','area','evidence','change','status'],row))) for row in issues],ensure_ascii=False,indent=2))
# This list identifies changed files and exact working bytes, independently of test success.
paths=sorted(set(subprocess.check_output(['git','diff','--name-only','c2822a7','HEAD'],cwd=R,text=True).splitlines()+subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard'],cwd=R,text=True).splitlines()));manifest=[]
for name in paths:
 p=R/name
 if p.is_file() and p!=E/'changed-files.json' and not name.startswith('review/avatar-foundation-cleanup/Evidence/interrupted'):
  manifest.append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
(E/'changed-files.json').write_text(json.dumps(manifest,indent=2));print('Wrote factual report and22-issue register')
