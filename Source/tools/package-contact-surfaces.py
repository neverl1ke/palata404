"""Build the new portable review; keep the returned package/history intact."""
from pathlib import Path
import base64,hashlib,html,json,shutil,subprocess,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-contact-surface-pass';G=OUT/'Gallery';DEST=ROOT.parent/'Male-Contact-Surface-Pass'
results=json.loads((OUT/'python-regression.json').read_text());capture=json.loads((OUT/'browser-capture.json').read_text());assert results['failures']==0 and results['errors']==0
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();baseline='c82fb9f';main=subprocess.check_output(['git','-C',str(ROOT.parent/'palata404'),'rev-parse','HEAD'],text=True).strip();assert main=='f70b7e5be63f6b85d895c6d5b259adbc30577b86'
issues=[
 ['Rifle1 · ліве передпліччя','Горизонтальна заміна маски на y655 обривала видиму руку.','Прибрано зріз; оригінальний контур продовжується до прихованого зап’ястя.','rifle-left-forearm-wrist.webp','Відновлено'],
 ['Rifle2 · зв’язок кисті','Окремі маски не покривали перехід навколо цівки.','Відновлено передпліччя та узгоджено контактні поверхні й прихований запас.','rifle-left-contact-item.webp; live-motion','Виправлено складання'],
 ['Rifle3 · отвори біля пальців','Подвійне віднімання кисті та недостатнє перекриття напівпрозорих масок.','Збережено нативне покриття суцільного джерела; кожний піксель належить руці або предмету.','whole-contact-coverage.json; transparent Canvas','Виправлено в перевіреній контактній області'],
 ['Rifle4 · рваний край цівки','GrabCut пропускав частини дерева й металу поруч із кистю.','Локально відновлено саме видимі матеріали з джерела; зовнішню альфу бере RGBA референсу.','rifle-left-contact-item.webp','Виправлено'],
 ['Rifle5 · зубець пахви','У ROI руки потрапив край референсного тулуба.','Внутрішню межу проведено вздовж кінцівки; оригінальний тулуб збережено.','rifle-left-axilla.webp','Зубець усунуто'],
 ['Rifle6 · чорна деталь','Рукоятка справжня, але її нижня частина відокремлювалася зубчасто.','Збережено деталь предмета й уточнено контур за джерельним матеріалом.','rifle-right-fingers-grip.webp','Контур скориговано; деталь не видалено'],
 ['Rifle7 · нижні краї пальців','Грубий полігон відсікав округлі завершення.','Локально перечерчено альфа-межу по джерелу плавними кривими; RGB пальців збережений.','rifle-right-fingers-grip.webp','Скориговано, потрібен художній перегляд'],
 ['Rifle8 · шов над прикладом','Жорсткі межі RGB-переходу та накладання плечового фрагмента.','Плавна локальна вага й градієнтне узгодження тільки спільного плеча/пахви.','rifle-stock-axilla.webp','Геометричний шов прибрано'],
 ['Rifle9 · фактура плеча','Референс і база мають різний локальний світлотіньовий малюнок.','Локальне seamlessClone з градієнтами джерела, без зміни анатомії/альфи/кистей.','rifle-right-shoulder.webp; harmonization masks','Узгоджено локально; художнє погодження потрібне'],
 ['Pistol1 · вертикальний проріз','Матеріал усередині рукоятки втрачався під час сегментації.','Відновлено джерельні пікселі металу/полімеру в перевіреній суцільній області.','pistol-handle-holes-thumb.webp','Виправлено'],
 ['Pistol2 · трикутний отвір','Маска кисті віднімалася з предмета двічі.','Узгоджено взаємне покриття; суцільний контакт не стає прозорим.','pistol-handle-holes-thumb.webp; whole-contact-coverage','Виправлено'],
 ['Pistol3 · дрібні отвори','Роздільні напівпрозорі межі не давали повної сумарної альфи.','Внутрішні суцільні пікселі мають одного власника; приховане перекриття з реального матеріалу.','pistol-handle-holes-thumb.webp','Виправлено в перевіреній області'],
 ['Pistol4 · чорний пунктир','Загальна маска руки залишала непрозоре тло під очищеним краєм долоні.','Синхронізовано край задньої руки та передньої кисті; очищено лише зовнішній fringe.','pistol-palm-outline-gap.webp; regression formerly-black pixels','Виправлено'],
 ['Pistol5 · природний просвіт','Вузький антіаліас джерела некоректно трактувався як непрозора шкіра.','Відновлено матування джерельного краю; сам просвіт не зафарбовано.','pistol-palm-outline-gap.webp; negative-space test','Збережено й очищено'],
 ['Pistol6 · плече','Постійна RGB-латка давала ефект монтажу.','Локальне градієнтне узгодження плеча; складене передпліччя виключено з обробки.','pistol-shoulder.webp; harmonization mask scope test','Узгоджено локально'],
 ['Pistol7 · лікоть','Порогова warm-RGB маска квантувала зовнішній антіаліас.','Відновлено нативний слабкий край і його матування від чорного тла.','pistol-elbow.webp','Згладжено край без розмиття руки'],
 ['Melee1 · щілина контакту','Втрачалися темні пікселі рукоятки та змішувались доповнювальні маски.','Відновлено реальну поверхню рукоятки; джерельні пальці залишено окремими.','melee-contact-handle.webp; coverage of416source pixels','Виправлено в перевіреній області'],
 ['Melee2 · пахва','ROI захоплював зайву смугу джерельного тулуба та мав діагональну RGB-межу.','Уточнено внутрішню межу руки й локально узгоджено стикову ділянку.','melee-axilla.webp','Перемичку й різку межу скориговано'],
 ['Melee3 · плече','Пороговий край джерела створював сходинки й темні fringe-пікселі.','Локальне відновлення нативного антіаліасу й очищення чорного тла.','melee-shoulder.webp','Технічно очищено'],
 ['Melee4 · активна / вільна рука','Надані референси та базова вільна рука мають різну фактуру.','Узгоджено плечовий тон і перехід. Деталі передпліччя не розмивали й не перемальовували.','melee-whole-active-arm.webp; after-melee.webp','Покращено локально; повна тотожність фактури не заявляється'],
 ['Melee5 · ніж / стегно','База ширша за референсний тулуб; лезо проєктується перед стегном.','Перевірено порядок: предмет перед тілом, пальці перед рукояткою. Положення й кисть не викручували.','melee-blade-thigh.webp; live-motion','Збережено як просторове перекриття; не приховано'],
 ['Вільні руки / idle','Зміна вихідного PNG сама не доводить справності зібраної руки.','Перевірено реальний runtime, покриття непрозорої шкіри та всі12прямих перемикань.','browser-capture.json; free-hand frame sheets','Без нових підтверджених обрізань'],
 ['Приховані запаси','Пошук сусіда міг вибрати темний матеріал предмета.','Запас береться лише з непрозорих теплих пікселів руки після відокремлення предмета.','hidden-wrist masks; warm-reserve source test','Виправлено'],
 ['Кадрування / рух','Один спільний crop обрізав підняті руки та показував стегна.','Вікна окремі для кожної пози: обидві руки, активні кисті, вільна кисть, плечі, повний персонаж. Записано справжній RAF WebM.','crop_windows; all-frames-*; *-live-motion.webm','Виправлено й перевірено'],
]
(OUT/'issues.json').write_text(json.dumps([dict(zip(['defect','cause','fix','check','status'],r)) for r in issues],ensure_ascii=False,indent=2)+'\n')
status={**results,'javascript_game':95,'javascript_core':22,'javascript_passed':117,'runtime_cycles':4,'frames_per_cycle':32,'cycle_ms':4000,'directed_instant_cuts':12,'js_errors':capture['js_errors'],'http_errors':capture['http_errors'],'artistic_approval':False,'prior_failure_logs_preserved':True};(OUT/'test-results.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
assets=[]
for folder in ['avatar-core/assets/male/reference-art','avatar-core/assets/weapons/reference-art']:
 for p in sorted((ROOT/folder).glob('*.png')):
  rel=str(p.relative_to(ROOT));old=subprocess.check_output(['git','show',baseline+':'+rel],cwd=ROOT);a=Image.open(p);assets.append({'path':rel,'size':a.size,'mode':a.mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(old).hexdigest(),'changed':p.read_bytes()!=old})
(OUT/'asset-manifest.json').write_text(json.dumps(assets,indent=2)+'\n')
changed=subprocess.check_output(['git','diff','--name-only',baseline],cwd=ROOT,text=True).splitlines();changed+=['review/male-contact-surface-pass/','tests/test_contact_surfaces.py','tools/review-contact-surfaces.py','tools/record-contact-motion.py','tools/reference-contact-surfaces.py','tools/package-contact-surfaces.py','tools/verify-contact-package.py'];(OUT/'changed-files.json').write_text(json.dumps(sorted(set(changed)),ensure_ascii=False,indent=2)+'\n')
coverage=json.loads((OUT/'whole-contact-coverage.json').read_text());motion=json.loads((OUT/'live-motion.json').read_text())
md=f'''# Чоловічий Avatar Core — контактні поверхні та залишкові стики

База: пакет `palata404-male-arm-contour-cleanup-e1f8e86.zip`, runtime `e1f8e86` / звіт `c82fb9f`. Робоча гілка `feature/avatar-core-2-weapon-transitions`. Відновлення: `avatar-core-before-contact-surface-pass-c82fb9f`. Нові ресурси: `{commit}`. Main `{main}` збережено.

## Незалежно підтверджені причини

Попередні зелені тести не перевіряли суцільне покриття кисті й предмета. Залишалися жорсткий зріз y655, подвійне віднімання масок, втрата темного матеріалу GrabCut, помилковий край тулуба в ROI руки, різкі RGB-межі та розсинхронізований край двох шарів долоні. У прихованому запасі знаходилися також темні пікселі предмета. Ці причини виправлено в підготовці ресурсів, не лише в готових PNG.

| Дефект | Причина | Виправлення | Доказ | Статус |
|---|---|---|---|---|
'''+''.join('| '+' | '.join(r)+' |\n' for r in issues)+f'''

## Параметри та захист

941×1672, реєстрація наданих зображень +10,+26, scale1. Кути, суглоби, inverse-bind і прив’язки предметів не змінені. Змінені11похідних PNG рук/пальців/предметів і лише poseArt-покриття `male_rig.json`; оригінальні бази, жіночі PNG/риг, engine, голова, ноги, гардероб, localStorage і правила гри не змінені. Дихання4000мс та instant cut збережені.

`tools/reference-contact-surfaces.py` містить локально простежені криві й суцільні області контактів. Усередині суцільної поверхні втрата сумарної альфи неприпустима: видимий піксель належить шкірі або матеріалу, RGB береться з джерела. Прихований запас предмета використовує сусідній реальний матеріал, не запечену кисть. Негативні простори не заповнюються глобально. Зовнішню альфу rifle бере нативний RGBA; RGB-референсам локально відновлено край від чорного тла. Глобального розмиття/erosion/dilation немає.

Плечі узгоджено лише в спільній області з незміненою базою методом NORMAL_CLONE та плавною локальною вагою; альфа й силует не переписуються цим RGB-кроком. Передпліччя pistol виключене з цієї області, щоб не створювати нової поперечної латки. Маски дії збережено окремо.

## Фактична перевірка

- JavaScript117/117 (95гра +22Core/anatomy).
- Python/Chromium **{results['passed']}/{results['python_total']}**, повний фінальний прогін. Є нові перевірки суцільних поверхонь, джерельного RGB матеріалів, справжнього просвіту, прихованої шкіри й меж локальної гармонізації.
- Контактні області: {sum(row['source_opaque_pixels'] for row in coverage)}непрозорих пікселів референсу,0втрачених у runtime. Окремо: rifle10077, pistol1800, melee416. Допуск альфи8рівнів враховує лише растеризацію; джерельна непрозорість має бути≥240. Це не перевірка всього персонажа за трьома точками.
- Чотири4-секундні цикли ×32кадри й контроль замикання; усі12напрямків миттєвого перемикання. Білі/сірі/чорні/зелені фони. 0JS/HTTP помилок. Збереження не змінені.
- Окремо записано **реальне безперервне RAF-відтворення** в WebM, не відеомонтаж контактних аркушів. Під час відтворення контролювалися контакти та матеріальні точки кожного спостереженого кадру; відео декодовано ffprobe. Частота захоплення змінна,60fpsне заявляється. WebP-цикли мають точну тривалість4000мс.
- Усі вікна кадрування окремі для пози; rifle-all-frames-hands тепер показує ОБИДВІ кисті, а не лише шорти. Є окремі повні руки, плечі/пахви, вільна кисть і повний персонаж.

Невдалі запуски збережені. Перший повний прогін дав85/88: два тести виявили невалідний холодний запас зап’ястя — виправлено алгоритм. Ще один вимагав незмінності5 крайових пікселів, які тепер навмисно очищені. Для цих пікселів перевіряється межа≤1.5px та зміна≤8RGB; внутрішній малюнок пальців і далі має допуск1RGB. Інші невдачі первинних контрольних координат стосувалися справжнього напівпрозорого краю джерела, а не відсутньої анатомії; джерельну перевірку≥240не послаблювали.

## Обмеження й оцінка

Повна художня тотожність фактури активного передпліччя та базової вільної руки **не заявляється**: виправлені локальні стики й тон плеча, але схвалений малюнок передпліч і пальців не перемальовувався. Melee4 залишається пунктом художнього погодження. Ніж залишено перед стегном за чинним порядком шарів; перекриття не видається за автоматичну анатомічну помилку й не приховується обрізанням леза.

Невидимі частини під предметами мають локальний запас, не повністю авторське перемальовування. Весь гардероб не сертифіковано цим проходом. Фізичний телефон і інші рушії не тестувалися. Наявні відео та покадрові матеріали є доказами для перегляду, а не заміною остаточного художнього приймання власником. Це runtime Avatar Core у Lab; основний index.html не змінено, у main/Pages нічого не публікувалося.

## Відкриття пакета

Розпакувати ВЕСЬ ZIP. `Report.html` відкрити браузером — фото, WebP та WebM вбудовані. `Avatar-Lab.html` — автономний справжній Lab. `Modules/Runtime` — точні cropped-PNG/JSON, `Modules/Arms` — повнорозмірні авторські експорти; не підміняти ними runtime-текстури. `Pipeline` запускається в початковому репозиторії, збережені джерела не змінювати. Точні файли, SHA, результати й маски входять у пакет.
''' 
(OUT/'README.md').write_text(md)
def pic(name,label):
 p=G/name;return '<figure><img loading="lazy" alt="'+html.escape(label,quote=True)+'" src="data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode()+'"><figcaption>'+html.escape(label)+'</figcaption></figure>'
blocks=[pic('four-current-poses.webp','Фактичний Core · idle / rifle / pistol / melee')]
for pose in ['rifle','pistol','melee']:
 blocks.append(pic('coverage-'+pose+'.webp','Суцільне покриття джерела: пропущені пікселі позначені ціаном. Поріг не змінено між версіями.'))
 blocks.append(pic(pose+'-comparison.webp','Референс / старий пакет / новий runtime. Плечі вирівняні, масштаб однаковий.'))
 for row in capture['panels']:
  name=row['path']
  if name.startswith(pose+'-') and not name.endswith('-comparison.webp'):blocks.append(pic(name,name.replace('.webp','')))
for pose in ['idle','rifle','pistol','melee']:
 for suffix,label in [('breathing','Анімований цикл4000мс'),('contact-cycle','Контактний цикл: активні кисті й предмет'),('all-frames-upper','Усі32кадри: ОБИДВІ ПОВНІ руки'),('all-frames-hands','Усі32кадри: активні кисті й предмет'),('all-frames-shoulders','Плечі й пахви'),('all-frames-full','Повний персонаж')]:blocks.append(pic(pose+'-'+suffix+'.webp',pose+' · '+label))
for pose in ['pistol','melee']:blocks.append(pic(pose+'-all-frames-free-hand.webp',pose+' · вільна рука в усіх32кадрах'))
for pose in ['idle','rifle','pistol','melee']:
 video=G/f'{pose}-live-motion.webm';blocks.append('<figure><video controls muted loop playsinline preload="metadata" style="max-width:100%;max-height:85vh" src="data:video/webm;base64,'+base64.b64encode(video.read_bytes()).decode()+'"></video><figcaption>'+pose+' · справжній RAF-запис руху, не монтаж кадрів</figcaption></figure>')
for n in ['all-twelve-cuts','all-twelve-cuts-frames']:blocks.append(pic(n+'.webp','Усі12миттєвих переходів, без morphing / напівпрозорих рук'))
for pose in ['rifle','pistol','melee']:
 for bg in ['fff','777','000','00ff00']:blocks.append(pic(pose+'-background-'+bg+'.webp',pose+' · фон #'+bg))
style='body{max-width:1450px;margin:auto;padding:16px;background:#182024;color:#eee7da;font:16px/1.5 system-ui}a{color:#a5dbf3}img{max-width:100%;height:auto}figure{margin:24px 0}figcaption{padding:7px;overflow-wrap:anywhere}table{display:block;overflow:auto;border-collapse:collapse}td,th{border:1px solid #687b81;padding:8px;min-width:155px;vertical-align:top}.notice{padding:14px;border:2px solid #d3b277}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
table='<table><tr>'+''.join('<th>'+x+'</th>' for x in ['Дефект','Причина','Виправлення','Доказ','Статус'])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in issues)+'</table>'
(OUT/'Report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата404 · повнота рук</title><style>'+style+'</style><h1>Чоловічий Avatar Core: контакти, прозорість і стики</h1><p class="notice">Відновлено поверхні контактів, краї кистей, передпліччя й локальні пахви. Пальці, постановка, базовий аватар, engine й жіночий риг збережені. Потрібне художнє погодження. Фактуру передпліччя Melee4 узгоджено лише локально; повне перемальовування не виконувалося.</p><p><a href="Avatar-Lab.html">Відкрити інтерактивний Lab</a> · <a href="README.md">Технічний звіт</a></p><p>117 JavaScript і '+str(results['passed'])+'/'+str(results['python_total'])+' Python/Chromium. 4цикли ×32кадри,12direct cuts,0JS/HTTP помилок. Main і гра не змінені.</p><p>Обмеження: приховані поверхні під предметами; проєкція ножа перед стегном; весь гардероб не сертифіковано. Physical-device testing не заявляється.</p>'+table+''.join(blocks)+'</html>')
DEST.mkdir(exist_ok=True)
for folder in ['Gallery','test-logs']:shutil.copytree(OUT/folder,DEST/folder,dirs_exist_ok=True)
shutil.copytree(ROOT/'review/male-reference-arm-art/Sources',DEST/'Sources',dirs_exist_ok=True)
(DEST/'Masks').mkdir(exist_ok=True)
for mask in OUT.glob('*-mask.png'):shutil.copyfile(mask,DEST/'Masks'/mask.name)
for name in ['source-map.json','pose-bindings.json']:shutil.copyfile(ROOT/'review/male-reference-arm-art'/name,DEST/name)
for p in OUT.glob('*.json'):
 if p.name not in ['https-verification.json','offline-package-check.json']:shutil.copyfile(p,DEST/p.name)
for name in ['README.md','Report.html','capture.log','capture-final.log','capture-delivery.log','live-motion.log','live-motion-final.log','live-motion-delivery.log','png-quality.log']:
 if (OUT/name).exists():shutil.copyfile(OUT/name,DEST/name)
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(DEST/'Avatar-Lab.html')],cwd=ROOT,check=True)
p=DEST/'Avatar-Lab.html';text=p.read_text()
for pose in ['idle','rifle','pistol','melee']:
 old=ROOT/'review/avatar-core-lobby-rework'/f'after-{pose}.webp';text=text.replace('data:image/webp;base64,'+base64.b64encode(old.read_bytes()).decode(),'data:image/webp;base64,'+base64.b64encode((G/f'before-{pose}.webp').read_bytes()).decode())
p.write_text(text.replace('<main>','<p style="padding:12px;border:2px solid #d3b277">Контактні поверхні · порівняння з пакетомe1f8e86/c82fb9f. Візуальне погодження очікується.</p><main>',1))
rig=json.loads((ROOT/'avatar-core/rigs/male_rig.json').read_text());cfg=json.loads((ROOT/'avatar-core/male-preview.json').read_text());exports=[]
for pose,sides in rig['poseArt'].items():
 for side,art in sides.items():
  for key in ['image','frontImage']:
   image=Image.new('RGBA',(941,1672));image.alpha_composite(Image.open(ROOT/'avatar-core'/art[key]),tuple(art['mesh']['bounds'][:2]));dest=DEST/'Modules/Arms'/f'{pose}-{side}-{key}.png';dest.parent.mkdir(parents=True,exist_ok=True);image.save(dest);exports.append({'file':str(dest.relative_to(DEST)),'runtime_crop':art[key],'bounds':art['mesh']['bounds'],'anchors':art['anchors']})
for side in ['right','left']:
 for part in ['Upper','Fore','Hand']:
  entry=rig['segments'][side+part];im=Image.new('RGBA',(941,1672));im.alpha_composite(Image.open(ROOT/'avatar-core'/entry['image']),tuple(entry['bounds'][:2]));im.save(DEST/'Modules/Arms'/f'idle-{side}-{part}.png')
for pose,w in cfg['weapons'].items():dest=DEST/'Modules/Weapons'/f'{pose}.png';dest.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/'avatar-core'/w['image'],dest)
for source in list((ROOT/'avatar-core/assets/male/reference-art').glob('*.png'))+list((ROOT/'avatar-core/assets/weapons/reference-art').glob('*.png'))+[ROOT/'avatar-core/rigs/male_rig.json',ROOT/'avatar-core/male-preview.json']:
 dest=DEST/'Modules/Runtime'/source.relative_to(ROOT/'avatar-core');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
(DEST/'Modules/Runtime/ПРОЧИТАЙ.txt').write_text('Точний overlay для початкового Avatar Core, не окрема гра. Runtime-crops відповідають UV-сіткам; не підміняти повнорозмірними Modules/Arms. Базові PNG незмінні.\n')
(DEST/'Modules/registration.json').write_text(json.dumps(exports,indent=2)+'\n')
(DEST/'Pipeline').mkdir(exist_ok=True)
for name in ['prepare-reference-arm-art.py','reference-contact-surfaces.py','review-contact-surfaces.py','record-contact-motion.py']:shutil.copyfile(ROOT/'tools'/name,DEST/'Pipeline'/name)
shutil.copyfile(ROOT/'tests/test_contact_surfaces.py',DEST/'Pipeline/test_contact_surfaces.py');shutil.copyfile(ROOT/'requirements-dev.txt',DEST/'Pipeline/requirements-dev.txt')
(DEST/'Pipeline/ПРОЧИТАЙ.txt').write_text('Запускати з початкового репозиторію: підготовка читає незмінні review/male-reference-arm-art/Sources, pose-bindings і base_male.png. Це відтворювані інструменти, не окрема збірка гри.\n')
(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('Розпакуй ВЕСЬ ZIP. Відкрий Report.html у браузері: галерея, порівняння й анімації вже вбудовані. Avatar-Lab.html — автономний інтерактивний Lab. Не відкривай HTML як вихідний текст на GitHub. Main та гра не змінені. Остаточне художнє погодження потрібне.\n')
(DEST/'Revision.txt').write_text(f'Runtime source:{commit}\nBaseline:c82fb9f /e1f8e86\nMain unchanged:{main}\nNo full-reference sprite replacement; no automatic production-ready approval.\n')
manifest=[{'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='Package-SHA256.json'];(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT.parent/'Male-Contact-Surface-Pass.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST.parent))
print(archive,archive.stat().st_size,'bytes;',len(manifest),'manifest files')
