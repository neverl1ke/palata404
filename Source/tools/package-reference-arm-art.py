"""Portable reference-arm adaptation review. No main/deployment mutations."""
from pathlib import Path
import base64,hashlib,html,json,shutil,subprocess,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-reference-arm-art';G=OUT/'Gallery';DEST=ROOT.parent/'Male-Reference-Arm-Art';DEST.mkdir(exist_ok=True)
capture=json.loads((OUT/'browser-capture.json').read_text());reg=json.loads((OUT/'registration.json').read_text());tests=json.loads((OUT/'test-results.json').read_text());quality=json.loads((OUT/'png-quality.json').read_text())
issues=[
 {'file':'avatar-core/assets/male/reference-art/rifle-{right,left}-{arm,front}.png','before':'Кулак під автоматом, неправильний малюнок пальців і посадка обох передпліч','fix':'Дві референсні руки, окремі передні пальці, нові лікті/зап’ястя/контакти. Без розтягування кистей.','evidence':'rifle-comparison.webp; rifle-{right,left}-grip.webp','status':'Адаптовано, передано на візуальне погодження'},
 {'file':'avatar-core/assets/male/reference-art/pistol-right-{arm,front}.png','before':'Неприродний контакт і орієнтація кисті','fix':'Піднята права рука й видимі пальці з референсу. Окремий кінчик пальця всередині спускової скоби; ліва рука лишилася оригінальною.','evidence':'pistol-comparison.webp; pistol-right-grip.webp','status':'Адаптовано; одноручну позу збережено'},
 {'file':'avatar-core/assets/male/reference-art/melee-right-{arm,front}.png','before':'Блокова кисть та виступ старого стику зап’ястя','fix':'Наданий малюнок передпліччя, зап’ястя та пальців замість старої кисті.','evidence':'melee-comparison.webp; melee-right-wrist.webp','status':'Адаптовано; опущену позу збережено'},
 {'file':'avatar-core/assets/weapons/reference-art/{rifle,pistol,melee}.png','before':'Предмети не відповідали новому малюнку пальців','fix':'Незалежні RGBA предмети з видимих референсних пікселів; прихований запас під пальцями; не запечені на руках.','evidence':'Modules/Weapons; png-quality.json; source/raster tests','status':'Підключено окремими ресурсами'},
 {'file':'avatar-core/rigs/male_rig.json; avatar-core/male-preview.json','before':'Старі контакти та inverse-bind не відповідали референсному малюнку','fix':'Нові pose-specific прив’язки й UV-меші. Плечі й основа лишились на старих місцях; оновлено проєкції кісток, зап’ястя та контакти.','evidence':'registration.json; pose-bindings.json; browser-capture.json','status':'Підключено; дихання4000мс та instant cut збережені'},
 {'file':'hidden wrist reserve / source masks','before':'При відокремленні предметів відкривались невідомі ділянки під кистями','fix':'Лише прихований запас сусідньої шкіри під непрозорими предметами. Нові видимі пальці не генерувалися.','evidence':'*-hidden-wrist-mask.png','status':'Запас для малого руху; не повністю домальована невидима анатомія'},
]
(OUT/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n')
readme='''# Референсна художня адаптація чоловічих рук

Робоча гілка `feature/avatar-core-2-weapon-transitions`. До змін: `dd61b2d`; точка відновлення `avatar-core-before-reference-arm-art-dd61b2d`. Коміт ресурсів: `78d3c44`. Main лишився `f70b7e5be63f6b85d895c6d5b259adbc30577b86`.

## Що виконано

Інтегровано чотири pose-specific модулі рук: обидві руки rifle, праву pistol, праву melee. Це новий видимий малюнок із наданих референсів, а не попереднє очищення41 пікселя чи заміна лише предмета. Вісім нових PNG рук/пальців і три окремі PNG предметів. Нейтральна поза та вільна ліва рука pistol/melee залишилися оригінальними.

Референси дозволено використати для виділення рук саме в поточному завданні. Цілого персонажа з референсу в runtime немає. Оригінальні файли збережені побайтово у Sources; відповідність початкових назв і SHA-256 у source-map.json, незмінність джерел перевіряється жорстко заданими SHA з отриманогоZIP. Основою рендера лишається оригінальний base_male.png із гри. Доданий inline-аватар переглянуто в чаті; окремого PNG для його побайтового порівняння не було.

## Припасування та маски

Усі референси941×1672. Вихідна реєстрація — рівномірний scale1, x+10, y+26, визначена за плечима. Обличчя, тулуб та ноги не масштабувалися. Плечі цільового рига лишилися праве[287,382], ліве[657,381]. Інші точки уточнені під наданий малюнок; повна таблиця в registration.json. Crop-ресурси використовують явні bounds, bind та sourceUV; у Modules додатково експортовані повнорозмірні941×1672 PNG.

Руки відокремлено вручну заданими контурами видимих ділянок; для предметів використано обмежену ROI сегментацію GrabCut з явними зразками. Чорний фон виділявся за зовнішньою зв’язністю, не видаленням усіх чорних пікселів. Деталі темних складок і нігтів усередині кисті збережені. На краях застосовано локальний matte та корекцію RGB напівпрозорої кайми. Додатково прибрано слабку віддалену альфу з робочих копій плечових фрагментів; оригінальний base не редагувався.

У переході до тулуба використано фрагмент оригінального плеча з комплементарним змішуванням альфи. Це прибирає щілини без подвійного напівпрозорого стику. Загального блюру або перегенерації рук немає. Колір видимих пальців збережений із джерел; контрольні пікселі перевірено також у фактичному Canvas.

Для невидимих ділянок під предметами додано невеликий запас сусідньої шкіри та приховані пікселі предмета під непрозорими пальцями. Це не нова авторська анатомія всіх закритих поверхонь. При повному видаленні предмета з тієї самої бойової пози ці ділянки не слід вважати окремо затвердженим порожнім хватом.

## Рендер та анімація

Порядок шарів збережений: оригінальні частини тіла/голови, задні ділянки рук, незалежний предмет, передні пальці й великий палець. Engine, math, skin, pose-art та controller не змінювалися. Змінені лише чоловічі дані й ресурси. Дихання4000мс, малий sway та непрозоре миттєве перемикання поз збережено. Кисті й предмети використовують узгоджені контакти та inverse-bind. По32 реальних кадри кожного4-секундного циклу знято з Lab.

## Фактичні перевірки

117 JavaScript-тестів пройшли:95 ігрових +22 Core/анатомії. У повному Python/Chromium прогоні69 тестів:68 пройшли,1 мала неправильну вимогу нерухомої світової точки приклада під час дихання. Після виправлення лише цієї перевірки її повтор пройшов1/1. Вона досі перевіряє точну локальну точку[257,512], рух менш2px та контакт із нижньою половиною руки. Зведено перевірені всі69 різних сценаріїв, але це не один повністю зелений повторний прогін; журнал початкової помилки збережено. Ще окремо повторено перевірку незмінності вихідних файлів із жорсткими SHA джерел.

До цього перший49-тестовий прогін дав40 успіхів,8 невдач та1 помилку. Виявлені застарілі обмеження й одна помилка шляху read-only історичного fixture задокументовані; журнал python-regression-initial.log збережено. Тести не вимагали перефарбувати темні контури заради червоного порога: тепер темні пікселі мають підтверджуване джерельне походження. Прихований скобою палець дозволений лише у точному прямокутнику референсу, а не як довільний другий компонент. Історичний alpha-only етап перевіряється за незмінним dd61b2d, поточні пози мають окремі перевірки джерельних пікселів, контактів та рендера. Старі еталонні PNG не підмінялися.

Реальний Chromium/Lab:280 комбінацій зовнішності й поз;4фони;4цикли дихання; крупні плани плечей, ліктів, зап’ясть і хватів. JS errors0, HTTP errors0, localStorage не змінено. Це технічна матриця, не280 незалежних художніх затверджень. Основний index.html не переводився на Avatar Core й не публікувався.

PNG-аналіз усіх11 нових ресурсів: слабких віддалених пікселів0. Окремі компоненти pistol — зокрема палець у скобі; у предметах — розділені видимі/приховані ділянки, перекриті руками. Кандидати темних/світлих країв у png-quality.json збережені для перегляду, не обнулені заради звіту. Наявність кандидата не означає автоматичний дефект і не доводить ідеальність малюнка.

## Обмеження

- Потрібне остаточне візуальне погодження власника; production-ready не заявляється автоматично.
- Приховані поверхні під предметами мають запас для малого руху, не повне авторське перемальовування.
- У ширшого оригінального тіла кінчик наданого ножа частково проєктується перед контуром стегна. Положення кисті не викручували заради старої умови тесту. Це видно у melee-comparison і крупних планах.
- Реально перевірені лише діагностичні прив’язані рукави; повна сумісність ігрових комплектів одягу не заявляється.
- Chromium — настільний браузер; фізичний телефон та інші рушії в цьому проході не перевірялися.
- Оригінальні PNG, жіночий риг, основна гра, збереження та баланс не змінені. Наявні джерельні особливості країв базового аватара не виправлялися під виглядом роботи над руками.

## Як відкрити

Report.html — автономна галерея з усіма вбудованими зображеннями й WebP-анімаціями. Avatar-Lab.html — автономний справжній Core з інтерактивними позами та шарами. Обидва HTML відкриваються у браузері після розпакування без сервера та Інтернету. HTML — не Markdown і не GitHub blob-перегляд. Modules/Runtime містить точні runtime-crops і JSON у відносних шляхах, Modules/Arms — додаткові повнорозмірні авторські експорти; їх не можна підміняти одне одним. Modules містить координати; Pipeline — код для запуску в початковому репозиторії, а не окрема збірка гри.
'''
(OUT/'README.md').write_text(readme)
def pic(name,label):
 p=G/name;return '<figure><img loading="lazy" alt="'+html.escape(label,quote=True)+'" src="data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode()+'"><figcaption>'+html.escape(label)+'</figcaption></figure>'
blocks=[pic('four-current-poses.webp','Фактичний модульний аватар: idle / rifle / pistol / melee.')]
for pose in ['rifle','pistol','melee']:blocks.append(pic(pose+'-comparison.webp','Референс / було / стало. Тулуби вирівняні за плечима; масштаб однаковий. Оригінальний фон RGB-референсу збережений.'))
for pose,sides in reg['anchors'].items():
 for side in sides:
  for joint in ['grip','wrist','elbow','shoulder']:blocks.append(pic(f'{pose}-{side}-{joint}.webp',f'{pose} · {side} · {joint} ×3. Крупні плани центровані за відповідними точками кожної версії.'))
for pose in ['idle','rifle','pistol','melee']:blocks.append(pic(pose+'-breathing.webp',pose+' · реальний4-секундний цикл,32кадри.'))
for pose in ['rifle','pistol','melee']:
 for bg in ['fff','777','000','00ff00']:blocks.append(pic(f'{pose}-background-{bg}.webp',pose+' · фон #'+bg))
for p in sorted(G.glob('appearance-*.webp')):blocks.append(pic(p.name,'Каталог чоловічих облич і зачісок; приклад показаний у melee. Усі4пози перевірені технічно.'))
for pose in ['idle','rifle','pistol','melee']:blocks.append(pic(pose+'-diagnostic-sleeves.webp',pose+' · лише діагностичні рукави, не сертифікація ігрового одягу.'))
style='body{max-width:1400px;margin:auto;padding:18px;background:#182024;color:#eee7da;font:16px/1.55 system-ui}a{color:#a5dbf3}img{max-width:100%;height:auto}figure{margin:22px 0}figcaption{padding:8px}table{display:block;overflow:auto;border-collapse:collapse}td,th{border:1px solid #758080;padding:10px;min-width:145px;vertical-align:top;overflow-wrap:anywhere}.notice{border:2px solid #d8b173;padding:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere}'
table='<table><tr>'+''.join('<th>'+s+'</th>' for s in ['Файл','Було','Виправлення','Доказ','Статус'])+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(row[k])+'</td>' for k in ['file','before','fix','evidence','status'])+'</tr>' for row in issues)+'</table>'
summary='''<h1>Чоловічі руки — адаптація наданого малюнка</h1><p class="notice">Нові видимі руки та пальці з референсів інтегровані модульно. Це не попередній alpha-only прохід і не підміна аватара цілим зображенням. Потрібне візуальне погодження; готовність усього гардероба не заявляється.</p><p><a href="Avatar-Lab.html">Відкрити автономний Lab</a> · <a href="README.md">Технічні подробиці</a></p><p>У цьому файлі всі зображення й анімації вбудовані. Інтернет для них не потрібен. Сам аватар, голова, тулуб і ноги — з гри. Змінено чоловічі pose-specific PNG та прив’язки; engine і жіночий риг збережено.</p><p>117 JavaScript-тестів пройшли. Python/Chromium:68/69 у повному прогоні; після уточнення єдиної перевірки приклада під час дихання її повтор пройшов1/1. Жоден невдалий журнал не приховано. Додатково280 технічних комбінацій каталогу,0JS/HTTP помилок. Це не автоматичне художнє затвердження.</p><p>Обмеження: приховані ділянки під предметами мають невеликий запас; лише діагностичні рукави перевірені на одяг; кінчик ножа частково проєктується перед стегном ширшої оригінальної бази. Main і опублікована гра не змінені.</p>'''
(OUT/'Report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата404 · референсні руки</title><style>'+style+'</style>'+summary+table+''.join(blocks)+'</html>')
for folder in ['Gallery','Sources','test-logs']:shutil.copytree(OUT/folder,DEST/folder,dirs_exist_ok=True)
for p in OUT.glob('*.json'):
 if p.name not in ['offline-package-check.json','https-verification.json']:shutil.copyfile(p,DEST/p.name)
for name in ['Report.html','README.md']:shutil.copyfile(OUT/name,DEST/name)
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(DEST/'Avatar-Lab.html')],cwd=ROOT,check=True)
p=DEST/'Avatar-Lab.html';lab_text=p.read_text()
# Export-only comparison uses the actual dd61b2d capture, not an older stage.
for pose in ['idle','rifle','pistol','melee']:
 old=ROOT/'review/avatar-core-lobby-rework'/f'after-{pose}.webp';new=G/f'before-{pose}.webp'
 lab_text=lab_text.replace('data:image/webp;base64,'+base64.b64encode(old.read_bytes()).decode(),'data:image/webp;base64,'+base64.b64encode(new.read_bytes()).decode())
p.write_text(lab_text.replace('<main>','<p style="padding:14px;border:2px solid #d8b173">Референсні модульні руки · нові прив’язки. Це Lab для погодження; повний одяг і production-ready статус не підтверджені.</p><main>',1))
rig=json.loads((ROOT/'avatar-core/rigs/male_rig.json').read_text());cfg=json.loads((ROOT/'avatar-core/male-preview.json').read_text());exports=[]
for pose,sides in rig['poseArt'].items():
 for side,art in sides.items():
  for key in ['image','frontImage']:
   im=Image.new('RGBA',(941,1672));im.alpha_composite(Image.open(ROOT/'avatar-core'/art[key]).convert('RGBA'),tuple(art['mesh']['bounds'][:2]));dest=DEST/'Modules/Arms'/f'{pose}-{side}-{key}.png';dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest);exports.append({'file':str(dest.relative_to(DEST)),'source':art[key],'bounds':art['mesh']['bounds'],'anchors':art['anchors'],'bind':art['bind']})
for side in ['right','left']:
 for part in ['Upper','Fore','Hand']:
  entry=rig['segments'][side+part];im=Image.new('RGBA',(941,1672));im.alpha_composite(Image.open(ROOT/'avatar-core'/entry['image']).convert('RGBA'),tuple(entry['bounds'][:2]));dest=DEST/'Modules/Arms'/f'idle-{side}-{part}.png';im.save(dest);exports.append({'file':str(dest.relative_to(DEST)),'source':entry['image'],'bounds':entry['bounds'],'status':'unchanged original neutral segment'})
for pose,w in cfg['weapons'].items():dest=DEST/'Modules/Weapons'/f'{pose}.png';dest.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/'avatar-core'/w['image'],dest)
# Also ship exact runtime crops and paths; full-frame authoring exports must
# never be mistaken for the cropped textures consumed by the existing UV mesh.
for source in list((ROOT/'avatar-core/assets/male/reference-art').glob('*.png'))+list((ROOT/'avatar-core/assets/weapons/reference-art').glob('*.png'))+[ROOT/'avatar-core/rigs/male_rig.json',ROOT/'avatar-core/male-preview.json']:
 dest=DEST/'Modules/Runtime'/source.relative_to(ROOT/'avatar-core');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
(DEST/'Modules/Runtime/ПРОЧИТАЙ.txt').write_text('Точні змінені файли Avatar Core у своїх відносних шляхах. Це overlay для початкового репозиторію, не повний окремий Core. Затверджені базові PNG та попередні сегменти не замінювати. Modules/Arms містить повнорозмірні авторські експорти, а не ці runtime-crops.\n')
(DEST/'Modules/registration.json').write_text(json.dumps(exports,indent=2)+'\n');shutil.copyfile(ROOT/'avatar-core/rigs/male_rig.json',DEST/'Modules/male_rig.json');shutil.copyfile(ROOT/'avatar-core/male-preview.json',DEST/'Modules/male-preview.json')
(DEST/'Pipeline').mkdir(exist_ok=True)
for name in ['prepare-reference-arm-art.py','review-reference-arm-art.py']:shutil.copyfile(ROOT/'tools'/name,DEST/'Pipeline'/name)
shutil.copyfile(ROOT/'requirements-dev.txt',DEST/'Pipeline/requirements-dev.txt');(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('Розпакуй весьZIP. Відкрий Report.html у браузері — галерея й4-секундні анімації вбудовані. Avatar-Lab.html — інтерактивний автономний Core.\n\nНові руки виділені з наданого малюнка, аватар не підмінений. Main не змінено. Є обмеження прихованих поверхонь та одягу; прочитай звіт.\n\nPipeline запускається з кореня початкового репозиторію, а не як окрема гра з цієї папки.\n')
(DEST/'Revision.txt').write_text('Runtime source commit:78d3c44\nBaseline:dd61b2d\nMain preserved:f70b7e5be63f6b85d895c6d5b259adbc30577b86\nNo full-reference sprite renderer. No automatic production-ready approval.\n')
manifest=[{'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='Package-SHA256.json'];(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT.parent/'Male-Reference-Arm-Art.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(archive,archive.stat().st_size,'bytes;',len(manifest),'files')
