"""Build the new portable review; keep the returned package/history intact."""
from pathlib import Path
import base64,hashlib,html,json,shutil,subprocess,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-arm-contour-cleanup';G=OUT/'Gallery';DEST=ROOT.parent/'Male-Arm-Contour-Cleanup'
results=json.loads((OUT/'python-regression.json').read_text());capture=json.loads((OUT/'browser-capture.json').read_text());assert results['failures']==0 and results['errors']==0
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();baseline='0392140';main=subprocess.check_output(['git','-C',str(ROOT.parent/'palata404'),'rev-parse','HEAD'],text=True).strip();assert main=='f70b7e5be63f6b85d895c6d5b259adbc30577b86'
issues=[
 ['Melee · зап’ястя','На y780 повна маска руки примусово замінювалась вузькою маскою кисті.','Прибрано горизонтальне відсікання; безперервна шкіра передпліччя й кисті.','melee-wrist.webp; тест контрольних пікселів','Виправлено'],
 ['Melee · повне передпліччя / пахва','Занадто вузький ручний POLYS зрізав потрібний малюнок з обох боків.','ROI винесено за справжній зовнішній контур; форму визначають видимі джерельні пікселі й окремий предмет.','melee-whole-right.webp; melee-forearm.webp; melee-axilla.webp','Виправлено'],
 ['Pistol · лікоть','Плоский нижній край полігона відрізав округлий низ ліктя.','Межа ROI тепер за ліктем; збережено повний видимий об’єм із джерела.','pistol-elbow.webp; контрольні перерізи y530/560/568','Виправлено'],
 ['Pistol · основа великого пальця','Верхня дуга hand stencil обрізала сім видимих теплих крайових пікселів.','Локально уточнено дугу великого пальця; постановка й пальці залишилися джерельними.','pistol-thumb-wrist.webp; точкові тести','Виправлено'],
 ['Плечі · темний фрагмент / шов','Внутрішня маска давала клин і зріз; старий cap перекривав референс. Додатково поріг .99 виключав базову альфу252/255.','Прибрано клин, референс над cap, змішування лише всередині спільного плеча/тулуба з коректним порогом .98. Темний зовнішній край, ставший внутрішнім, узгоджено з початковим плечем.','*-shoulder*.webp; source/Canvas tests; original base unchanged','Виправлено технічно; авторське погодження потрібне'],
 ['Rifle · праве передпліччя / пахва','Вузький polygon клином зрізав нижній край передпліччя та шкіру над прикладом.','Повернуто джерельні ширину й локальне перекриття пахви. Справжній просвіт під прикладом залишено.','rifle-whole-right.webp; rifle-right-axilla-stock.webp','Виправлено'],
 ['Rifle · ліві біцепс і передпліччя','Внутрішня межа ROI проходила крізь м’язи, а не вздовж референсного силуету.','ROI розширено по обидва боки, без масштабування кисті або зміни прив’язок.','rifle-left-bicep.webp; rifle-left-forearm.webp; source spans','Виправлено'],
 ['Rifle · фрагменти біля пальців','Край маски захоплював маленький фрагмент шкіри живота позаду середнього/безіменного пальців. Поряд є справжня чорна частина рукоятки.','Прибрано підтверджений захват живота; потрібна рукоятка залишилась окремим предметом. Видимий нижче пупок належить базовому тулубу, його не видаляли.','rifle-right-fingers-prop.webp; незалежність предметів','Локально виправлено, натуральні частини збережено'],
 ['Вільна ліва рука / idle','У runtime немає втрати непрозорої шкіри. Збирання split-текстур змінює альфу та дає округлення RGB≤2.','Руку не переробляли. Перевірено покриття всіх вихідних непрозорих пікселів і відсутність залишків попередньої пози.','browser-capture.json:free_arm_raster; cuts; all-frames-hands','Обрізання непрозорої шкіри не підтвердилося'],
 ['Bounds / UV / сітка','Втрата малюнка існувала вже в масках до обрізання й сітки. Нові ширші ресурси потребували нових bounds/трикутників.','Перебудовано лише poseArt-UV для змінених масок; усі видимі пікселі покриті трикутниками.','тест coverage; незмінені bind/anchors','Покриття перевірено'],
]
(OUT/'issues.json').write_text(json.dumps([dict(zip(['defect','cause','fix','check','status'],r)) for r in issues],ensure_ascii=False,indent=2)+'\n')
status={**results,'javascript_game':95,'javascript_core':22,'javascript_passed':117,'runtime_cycles':4,'frames_per_cycle':32,'cycle_ms':4000,'directed_instant_cuts':12,'js_errors':capture['js_errors'],'http_errors':capture['http_errors'],'artistic_approval':False,'prior_failure_logs_preserved':True};(OUT/'test-results.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
assets=[]
for folder in ['avatar-core/assets/male/reference-art','avatar-core/assets/weapons/reference-art']:
 for p in sorted((ROOT/folder).glob('*.png')):
  rel=str(p.relative_to(ROOT));old=subprocess.check_output(['git','show',baseline+':'+rel],cwd=ROOT);a=Image.open(p);assets.append({'path':rel,'size':a.size,'mode':a.mode,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(old).hexdigest(),'changed':p.read_bytes()!=old})
(OUT/'asset-manifest.json').write_text(json.dumps(assets,indent=2)+'\n')
changed=subprocess.check_output(['git','diff','--name-only',baseline],cwd=ROOT,text=True).splitlines();changed+=['review/male-arm-contour-cleanup/','tests/test_arm_contour_cleanup.py','tools/review-arm-contour-cleanup.py','tools/package-arm-contour-cleanup.py','tools/verify-arm-contour-package.py'];(OUT/'changed-files.json').write_text(json.dumps(sorted(set(changed)),ensure_ascii=False,indent=2)+'\n')
md=f'''# Повнота контурів чоловічих рук — повторний цільовий прохід

За основу взято локальний оригінал раніше виданого пакета `palata404-male-reference-arm-art-78d3c44.zip`, завантажений і перевірений через HTTPS; runtime тотожний `0392140`. Повторний upload у чаті перевищує ліміт перенесення32MiB, тому його байти окремо не прочитані. Походження доступного оригіналу й SHA — input-package-verification.json. Відновлення: `avatar-core-before-arm-contour-cleanup-0392140`. Робоча гілка `feature/avatar-core-2-weapon-transitions`, коміт ресурсів `{commit}`. Main `{main}` збережено.

Це виправлення масок по повній довжині рук, не нова генерація й не заміна аватара. Голова, оригінальний тулуб, ноги, жіночі PNG/риг, engine, дихання4000мс, параметри похитування, збереження та миттєве перемикання не змінені. Локально відновлено джерельні ділянки пахв поруч із новими руками. Жодного окремого патча всього тулуба або нового рига.

## Причини та виправлення

| Дефект | Причина | Виправлення | Перевірка | Статус |
|---|---|---|---|---|
'''+''.join('| '+' | '.join(r)+' |\n' for r in issues)+f'''
## Що реально змінено

Вісім похідних PNG `avatar-core/assets/male/reference-art/*-arm.png` і `*-front.png`; два похідні предмети rifle.png і pistol.png оновилися після уточнення відокремлення пальців. Melee-предмет не змінений. `male_rig.json`: тільки poseArt bounds/сітки; прив’язки, inverse-bind, суглоби й проєкції збережені. `prepare-reference-arm-art.py`: сталі правила підготовки, які відтворюють виправлення. Нові інструменти capture/package/verify та `tests/test_arm_contour_cleanup.py`. Точні шляхи й SHA — asset-manifest.json та changed-files.json.

Зовнішні ROI не є новими контурами анатомії: вони винесені за джерельні руки. Зовнішню альфу визначає джерело, внутрішні складки не розмиваються. Глобального erosion/dilation й розтягування кистей немає. Плечове RGB-змішування локальне, лише в спільному покритті базового плеча/тулуба; відкриті краї, пальці й решта бази не перефарбовуються.

## Перевірки цього проходу

- **117/117 JavaScript** (95 гра +22 Core/anatomy).
- **{results['passed']}/{results['python_total']} Python/Chromium**, повний узгоджений прогін, без пропущених тестів. Включає10 нових перевірок контурів; вихідний невдалий журнал також збережений.
- Незалежні контрольні перерізи: у старому пакеті не вистачало62 зразків melee,15 pistol,68 правої rifle,45 лівої rifle; після виправлення всі визначені видимі внутрішні пікселі мають альфу≥240. Напівпрозорий край референсу не видається за відсутню анатомію.
- Canvas:4 цикли по4000мс,32кадри кожний+замикання4000мс; усі12 напрямків instant-cut. Контакти пальців/предметів <1e−6, немає JS/HTTP помилок, localStorage не змінено.
- Вільна рука:0 втрачених непрозорих пікселів; RGB від джерела відрізняється щонайбільше на2 рівні через складання. Збіг лише вихідного PNG не використовувався як доказ.
- Білий, сірий, чорний, зелений фони; фото референсу / старий runtime / новий runtime в однакових координатах941×1672. Спільна реєстрація джерела +10,+26, scale1. У крупних планах однакові вікна, не різні центри для приховування різниці.
- PNG-діагностика11ресурсів: повний JSON з кандидатами, не обнулений для формального зеленого результату. Відокремлений палець у спусковій скобі й перекриті частини предметів — легітимні компоненти.

Початкові помилки нових тестів не приховано: один переріз помилково включав край джерела з alpha6; однорівневе округлення premultiplied RGB не є перемальовуванням; byte-equality neutral/split-raster замінено конкретною перевіркою покриття й кольору незміненої шкіри. Строгі тести ширини й видимих точок не послаблені. Початковий capture із неправильним фізичним розміром Canvas відхилено; остаточний capture використовує941×1672. Журнали збоїв збережено.

## Матеріали та межі

`Report.html` — автономна галерея із вбудованими крупними планами,4анімаціями дихання, покадровими аркушами та12прямими перемиканнями. `Avatar-Lab.html` — справжній автономний Lab. Відкривати браузером після повного розпакування, а не як текст на GitHub. `Modules/Runtime` — точні runtime-crops/JSON; `Modules/Arms` — повнорозмірні авторські експорти941×1672, їх не підміняти одне одним. Pipeline запускається з кореня початкового репозиторію.

Збережено попередні обмеження: приховані частини під предметами мають лише локальний запас; ніж частково проєктується перед стегном ширшої оригінальної бази; весь ігровий гардероб цим проходом не сертифікований. Короткі тести й поточні крупні плани не доводять ідеальність кожного художнього пікселя. Реально перевірено настільний Chromium, не фізичний телефон. Це експериментальний Avatar Core в Lab; main index.html його не підключає. Main/гра/GitHub Pages не публікувалися. Остаточне художнє затвердження — за власником.
'''
(OUT/'README.md').write_text(md)
def pic(name,label):
 p=G/name;return '<figure><img loading="lazy" alt="'+html.escape(label,quote=True)+'" src="data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode()+'"><figcaption>'+html.escape(label)+'</figcaption></figure>'
blocks=[pic('four-current-poses.webp','Фактичний Core · idle / rifle / pistol / melee')]
for pose in ['rifle','pistol','melee']:
 blocks.append(pic(pose+'-comparison.webp','Референс / старий пакет / новий runtime. Плечі вирівняні, масштаб однаковий.'))
 for row in capture['panels']:
  name=row['path']
  if name.startswith(pose+'-') and not name.endswith('-comparison.webp'):blocks.append(pic(name,name.replace('.webp','')))
for pose in ['idle','rifle','pistol','melee']:
 for suffix,label in [('breathing','Анімований цикл4000мс'),('all-frames-upper','Усі32кадри: плечі, біцепси, передпліччя'),('all-frames-hands','Усі32кадри: зап’ястя, активні та вільні кисті')]:blocks.append(pic(pose+'-'+suffix+'.webp',pose+' · '+label))
for n in ['all-twelve-cuts','all-twelve-cuts-frames']:blocks.append(pic(n+'.webp','Усі12миттєвих переходів, без morphing / напівпрозорих рук'))
for pose in ['rifle','pistol','melee']:
 for bg in ['fff','777','000','00ff00']:blocks.append(pic(pose+'-background-'+bg+'.webp',pose+' · фон #'+bg))
style='body{max-width:1450px;margin:auto;padding:16px;background:#182024;color:#eee7da;font:16px/1.5 system-ui}a{color:#a5dbf3}img{max-width:100%;height:auto}figure{margin:24px 0}figcaption{padding:7px;overflow-wrap:anywhere}table{display:block;overflow:auto;border-collapse:collapse}td,th{border:1px solid #687b81;padding:8px;min-width:155px;vertical-align:top}.notice{padding:14px;border:2px solid #d3b277}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
table='<table><tr>'+''.join('<th>'+x+'</th>' for x in ['Дефект','Причина','Виправлення','Доказ','Статус'])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in row)+'</tr>' for row in issues)+'</table>'
(OUT/'Report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата404 · повнота рук</title><style>'+style+'</style><h1>Чоловічі руки: контури та повнота</h1><p class="notice">Відновлено повну ширину, лікоть, зап’ястя та локальні пахви. Пальці, постановка, базовий аватар, engine й жіночий риг збережені. Потрібне художнє погодження.</p><p><a href="Avatar-Lab.html">Відкрити інтерактивний Lab</a> · <a href="README.md">Технічний звіт</a></p><p>117 JavaScript і '+str(results['passed'])+'/'+str(results['python_total'])+' Python/Chromium. 4цикли ×32кадри,12direct cuts,0JS/HTTP помилок. Main і гра не змінені.</p><p>Обмеження: приховані поверхні під предметами; проєкція ножа перед стегном; весь гардероб не сертифіковано. Physical-device testing не заявляється.</p>'+table+''.join(blocks)+'</html>')
DEST.mkdir(exist_ok=True)
for folder in ['Gallery','test-logs']:shutil.copytree(OUT/folder,DEST/folder,dirs_exist_ok=True)
shutil.copytree(ROOT/'review/male-reference-arm-art/Sources',DEST/'Sources',dirs_exist_ok=True)
(DEST/'Masks').mkdir(exist_ok=True)
for mask in OUT.glob('*-mask.png'):shutil.copyfile(mask,DEST/'Masks'/mask.name)
for name in ['source-map.json','pose-bindings.json']:shutil.copyfile(ROOT/'review/male-reference-arm-art'/name,DEST/name)
for p in OUT.glob('*.json'):
 if p.name not in ['https-verification.json','offline-package-check.json']:shutil.copyfile(p,DEST/p.name)
for name in ['README.md','Report.html','capture.log','capture-final.log','capture-verified.log','capture-final-serial.log','png-quality.log']:
 if (OUT/name).exists():shutil.copyfile(OUT/name,DEST/name)
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(DEST/'Avatar-Lab.html')],cwd=ROOT,check=True)
p=DEST/'Avatar-Lab.html';text=p.read_text()
for pose in ['idle','rifle','pistol','melee']:
 old=ROOT/'review/avatar-core-lobby-rework'/f'after-{pose}.webp';text=text.replace('data:image/webp;base64,'+base64.b64encode(old.read_bytes()).decode(),'data:image/webp;base64,'+base64.b64encode((G/f'before-{pose}.webp').read_bytes()).decode())
p.write_text(text.replace('<main>','<p style="padding:12px;border:2px solid #d3b277">Повнота рук · новий прохід масок. Порівняння — зі старим пакетом78d3c44/0392140. Візуальне погодження очікується.</p><main>',1))
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
for name in ['prepare-reference-arm-art.py','review-arm-contour-cleanup.py']:shutil.copyfile(ROOT/'tools'/name,DEST/'Pipeline'/name)
shutil.copyfile(ROOT/'tests/test_arm_contour_cleanup.py',DEST/'Pipeline/test_arm_contour_cleanup.py');shutil.copyfile(ROOT/'requirements-dev.txt',DEST/'Pipeline/requirements-dev.txt')
(DEST/'Pipeline/ПРОЧИТАЙ.txt').write_text('Запускати з початкового репозиторію: підготовка читає незмінні review/male-reference-arm-art/Sources, pose-bindings і base_male.png. Це відтворювані інструменти, не окрема збірка гри.\n')
(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('Розпакуй ВЕСЬ ZIP. Відкрий Report.html у браузері: галерея, порівняння й анімації вже вбудовані. Avatar-Lab.html — автономний інтерактивний Lab. Не відкривай HTML як вихідний текст на GitHub. Main та гра не змінені. Остаточне художнє погодження потрібне.\n')
(DEST/'Revision.txt').write_text(f'Runtime source:{commit}\nBaseline:0392140 /78d3c44\nMain unchanged:{main}\nNo full-reference sprite replacement; no automatic production-ready approval.\n')
manifest=[{'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='Package-SHA256.json'];(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT.parent/'Male-Arm-Contour-Cleanup.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST.parent))
print(archive,archive.stat().st_size,'bytes;',len(manifest),'manifest files')
