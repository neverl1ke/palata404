"""Portable review of current results, explicitly distinguishing unfinished art."""
from pathlib import Path
import base64,hashlib,html,json,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'review/weapon-independent-anatomy';D=ROOT.parent/'Avatar-Weapon-Independent-Review';D.mkdir(exist_ok=True)
r=json.loads((O/'python-regression.json').read_text());capture=json.loads((O/'runtime-review.json').read_text());motion=json.loads((O/'live-motion.json').read_text());assert r['failures']==0 and r['errors']==0
issues=json.loads((O/'issues.json').read_text());sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();table='| Дефект | Причина | Правка | Доказ | Стан |\n|---|---|---|---|---|\n'+''.join('| '+' | '.join(row)+' |\n' for row in issues)
md=f'''# Avatar Core — прихована анатомія та незалежні предмети

Робоча гілка: feature/avatar-core-2-weapon-transitions. База: 184e392 (пакет 766a71e). Точка відновлення: avatar-core-before-hidden-anatomy-184e392. Код поточного результату: {sha}. Main f70b7e5 збережено; гра/Pages не змінені.

## Результат і межа готовності

Це перевірений технічний прохід із частковим художнім результатом, **не завершена універсальна основа**. Приховування предметів і діагностичні варіанти доступні в Lab. Виправлено рухомий край стегна, щілину шиї, покриття нових поверхонь сіткою й неприродне скорочення melee-руки. Чотири локальні генерації застосовані тільки до проблемних задніх поверхонь чоловічих кистей; вихідні бази й референси не змінено. Прийняті передні пальці збережено, крім пошкодженого фрагмента pistol та помилково віднесеного до пальців матеріалу rifle.

Ліва/права — з погляду персонажа. Порівняння використовують однакові світові координати, не незалежно центровані руки. Melee тепер довша навмисно за додатковим проханням власника: upper projection 0.8358908853 → 1, fore 1.007382089 → 1; хват [227,880] → [241,906]. Базові довжини й ширина кисті не змінені. Плечова шапка локально прив’язана до торса, щоб зміна довжини не тягнула її за плечовою кісткою.

{table}
## Що перевірено цього разу

- JavaScript: 95 ігрових +22 Core/anatomy = **117/117**, фактичні журнали в пакеті.
- Python/Chromium: **{r['passed']}/{r['python_total']} сценаріїв сукупно**:102/103у повному прогоні та1/1цільово після виправлення застарілих координат проби ножа. Runtime не змінювався між цими запусками; це НЕ один повністю зелений прогін. Помилок {r['errors']}, пропущено {r['skipped']}. Після фінальної локальної правки контуру додатково пройшли36/36цільових перевірок. Нових перевірок —12: незалежне приховування, три розміри, повні кістки melee, шия, власність стегна, зв’язність pistol, повторюваність експорту та захист оригіналів.
- Вісім чоловічих циклів (кожна поза з предметом/без), 4000мс,16контрольних фаз, точне замикання.24прямі перемикання поз (12напрямків ×2стани предмета).
- Вісім WebM повних циклів та два WebM перемикань — справжній RAF/MediaRecorder, не монтаж статичних кадрів. Частота захоплення змінна; 60fps не заявляється. Контакти перевірені на кожному спостереженому RAF.
- Чотири фони, правильні вікна обох повних рук. Локальні крупні плани, повний персонаж, ізоляція реальних пікселів рук та кольорова карта їх покриття.
- Усі чотири попередні жіночі рендери порівняно попіксельно з 184e392. Голова/стопи обох персонажів захищені. Фізичний пристрій та інші браузерні рушії не перевірено. Це перевірка справжнього Core у Lab, не інтеграція у production index.html.
- Немає JS/HTTP-помилок у контрольному запуску; localStorage не змінено. Main і збереження не зачіпалися.

## Невдалі перевірки й зміни тестів

Початковий повний прогін:85/103,18невдач; журнал і JSON збережені. Частина стосувалася старої вимоги незмінності похідних PNG/координат, які тепер явно дозволено змінити. Їх замінено точними перевірками дозволеної передачі RGBA у вузькій зоні x660–679,y840–1039; поза нею пікселі мають бути незмінними, нові lower-пікселі — точно з бази, решта вихідних файлів усе ще заморожені. Проби melee тепер переводяться через незалежне NumPy affine/inverse-bind обчислення; альфа/RGB-допуски не послаблено. Нові тести перевіряють запитану повну довжину кісток і відсутність відірваного пальця.

Справжні технічні дефекти, виявлені новими перевірками: читання старого arm-source атласу, відсутні клітини сітки, втрата темного матеріалу при виправленні його власника, десатурація нового краю після RGB-корекції, зміна історичних кешів при повторному експорті. Виправлено причини, а не тільки очікування тестів. Попередні звіти й результати не видаються за поточні. Один проміжний прогін перервано через надмірне повторне завантаження великого rig-JSON для кожного пікселя; спільні дані проб тепер кешуються без зміни критеріїв. Першу паралельну зйомку зупинено, бо історичний тест відтворення переписує ресурси; фінальна зйомка виконана окремо після регресії.

## Жіночий етап — незавершено

Повноростовий генераторний запит відхилений сервісом. За окремими жіночими вихідними руками створено ізольований кандидат rifle: Sources/female-rifle-arms-candidate-not-integrated.png. Це новий жіночий малюнок, не зменшені чоловічі руки. Але хват не відповідає наявній рукоятці, полотно1536×1024ще не зареєстровано, навколо рук є14997слабких альфа-пікселів1–16 і широкий ореол. Кандидат не пройшов приймання й не інтегрований. Нових жіночих pistol/melee немає. Чинні жіночі PNG/риг залишилися попереднім прототипом; не заявляємо завершення цього етапу.

## Відкриті художні питання

Ліве зап’ястя rifle стало суцільним, але контур долоні біля мізинця ще потребує ручного проходу. Геометричний край під правою долонею rifle не закрито. Потрібне візуальне приймання локально домальованого лівого зап’ястя rifle та короткого пальця pistol; різниця фактури активної й вільної рук усунута не повністю. Складні внутрішні контури пахв і допустимий діапазон інших рукояток не оголошені універсально готовими. При85/115% rifle цівка може розійтися з підтримувальною кистю: це чесна діагностика потреби іншого контакту/хвату, а не гарантія сумісності. Не слід переносити незатверджені поверхні у жіночий риг як еталон.

## Відкриття й відтворення

Розпакувати ВЕСЬ ZIP і відкрити Report.html або Avatar-Lab.html у браузері. Вони працюють без сервера. У Lab вибрати позу, перемикач «Показувати предмет» та тест розміру; приховування не змінює позу/час/кисті. Галерея містить додаткові крупні плани й анімації. Runtime — точні робочі модулі; Sources — окремі вихідні локальні правки та неприйнятий жіночий кандидат. Pipeline запускається в початковому репозиторії з історією Git184e392, не самостійно в ZIP. Існуюча підготовка викликає новий фінальний етап; повторний запуск не генерує картинки й не має повертати дефекти.

Інструкція предметів: docs/avatar-weapon-attachments.md у репозиторії та Item-attachment-guide.md у пакеті. Поля primary/support, scale/angle/offset та окремі bind/mesh/пальці використовують чинний спільний контролер. Нова система автоматичного вибору будь-якого хвату не додавалася.
'''
(O/'README.md').write_text(md)
# Keep portable output deterministic; never alter historical review packages.
for dirname in ['Gallery','Sources','Runtime','Pipeline']:
 p=D/dirname
 if p.exists():shutil.rmtree(p)
maskdir=D/'Masks';maskdir.mkdir(exist_ok=True)
for p in O.glob('*mask.png'):shutil.copy2(p,maskdir/p.name)
shutil.copytree(O/'Gallery',D/'Gallery');shutil.copytree(O/'Sources',D/'Sources');shutil.copytree(ROOT/'avatar-core',D/'Runtime')
P=D/'Pipeline';P.mkdir()
for name in ['prepare-independent-anatomy.py','prepare-reference-arm-art.py','reference-contact-surfaces.py','review-independent-anatomy.py','record-independent-motion.py','bundle-avatar-lab.py'] :shutil.copy2(ROOT/'tools'/name,P/name)
for name in ['test_independent_anatomy.py','avatar_revision_contract.py']:shutil.copy2(ROOT/'tests'/name,P/name)
shutil.copy2(ROOT/'docs/avatar-weapon-attachments.md',D/'Item-attachment-guide.md');(D/'README.md').write_text(md)
for p in O.glob('*.json'):shutil.copy2(p,D/p.name)
logs=D/'Test-logs';logs.mkdir(exist_ok=True)
for p in O.glob('*.log'):shutil.copy2(p,logs/p.name)
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(D/'Avatar-Lab.html')],cwd=ROOT,check=True)
def uri(p):return 'data:'+('video/webm' if p.suffix=='.webm' else 'image/webp')+';base64,'+base64.b64encode(p.read_bytes()).decode()
body='<h1>Avatar Core · зброя та прихована анатомія</h1><p><strong>Технічно перевірений огляд; чоловічі художні правки часткові. Жіночий етап незавершено. Production-ready статус не заявляється.</strong></p><p><a href="Avatar-Lab.html">Відкрити автономний Lab</a> · <a href="Item-attachment-guide.md">Схема предметів</a> · <a href="README.md">Повний текст звіту</a></p>'
body+='<h2>Дефекти та статус</h2><div class="scroll"><table><thead><tr>'+''.join('<th>'+html.escape(s)+'</th>' for s in ['Дефект','Причина','Правка','Доказ','Статус'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in row)+'</tr>' for row in issues)+'</tbody></table></div>'
body+=f'<p>Повний Python-прогін:102/103; повторна координатна проба:1/1. Це сукупне покриття, не один зелений прогін. JavaScript:117/117; {r["passed"]}/{r["python_total"]}Python/Chromium. Початкові85/103і18невдач збережені в журналах. Main не змінено.</p>'
for name in ['melee-before-after.webp','melee-current.webp','rifle-before-after.webp','rifle-current.webp','pistol-before-after.webp','pistol-current.webp','idle-current.webp','neck-exhale-comparison.webp','rifle-left-hand-comparison.webp','rifle-right-hand-comparison.webp','pistol-hand-comparison.webp','melee-hand-comparison.webp','melee-axilla-comparison.webp','idle-ownership.webp','rifle-variants.webp','pistol-variants.webp','melee-variants.webp']:
 p=O/'Gallery'/name;body+='<figure><figcaption>'+html.escape(name)+'</figcaption><img loading="lazy" src="'+uri(p)+'"></figure>'
body+='<h2>Реальне безперервне відтворення</h2><p>WebM — запис RAF, не склеєні нерухомі картинки. Частота захоплення змінна.</p>'
for row in motion['recordings']:
 p=O/'Gallery'/row['path'];body+='<figure><figcaption>'+html.escape(p.name)+'</figcaption><video controls loop muted playsinline preload="metadata" src="'+uri(p)+'"></video></figure>'
body+='<h2>Усі контрольні матеріали</h2><ul>'+''.join('<li><a href="Gallery/'+html.escape(p.name)+'">'+html.escape(p.name)+'</a></li>' for p in sorted((O/'Gallery').iterdir()) if p.is_file())+'</ul><h2>Незавершений жіночий етап</h2><p>Див. female-stage.json. Нові руки не інтегровано: непридатний хват та альфа-ореол. Це не попередня жіноча система, видана за новий результат.</p>'
report='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core — незалежні предмети</title><style>body{overflow-wrap:anywhere;font:16px system-ui;line-height:1.5;max-width:1400px;margin:auto;padding:16px;background:#151c20;color:#eee}a{color:#9bdcff}img,video{max-width:100%;height:auto}video{max-height:80vh}figure{margin:24px 0;padding:8px;background:#242d31}td,th{border:1px solid #687278;padding:8px;vertical-align:top}table{border-collapse:collapse;min-width:900px}.scroll{overflow:auto}</style>'+body+'</html>'
(D/'Report.html').write_text(report)
manifest={str(p.relative_to(D)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in D.rglob('*') if p.is_file() and p.name!='Package-SHA256.json'};(D/'Package-SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
z=D.with_suffix('.zip')
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
 for p in D.rglob('*'):
  if p.is_file():archive.write(p,D.name+'/'+str(p.relative_to(D)))
(O/'package.json').write_text(json.dumps({'zip':str(z),'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest(),'files':len(manifest)+1,'source_commit':sha,'production_ready':False,'female_integrated':False},indent=2)+'\n');print(z,z.stat().st_size)
