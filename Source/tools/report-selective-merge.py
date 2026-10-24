"""Self-contained, same-registration BEFORE/AFTER/FINAL evidence from real Canvas."""
from pathlib import Path
import json,base64,html,io,hashlib,subprocess
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-selective-merge';G=D/'Gallery';E=D/'Evidence';versions=['184e392','5532a93','final'];font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
labels=['ДО · 184e392 / 766a71e','ПІСЛЯ · 5532a93','ФІНАЛ · вибірковий RGB merge']
def raw(v,g,p,t=0,visible=True):return Image.open(G/f'{v}-{g}-{p}-{t}-{visible if p!="idle" else False}.png').convert('RGB')
def triple(g,p,t,vis,box=None):
 images=[raw(v,g,p,t,vis) for v in versions];box=box or (0,0,941,1672);w,h=box[2]-box[0],box[3]-box[1];sheet=Image.new('RGB',(w*3,h+30),'#ddd');d=ImageDraw.Draw(sheet)
 for i,im in enumerate(images):sheet.paste(im.crop(box),(i*w,30));d.text((i*w+4,4),labels[i] if w>=400 else ['ДО 184e392','ПІСЛЯ 5532a93','ФІНАЛ'][i],fill='black',font=font if w>=400 else ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12))
 return sheet
def save(im,name):
 p=G/name
 if not p.exists():im.save(p,lossless=True)
 return p
def embedded(p):return 'data:image/webp;base64,'+base64.b64encode(p.read_bytes()).decode()
def figure(p,caption):return '<figure><img loading="lazy" src="'+embedded(p)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>'
rows=[];body='''<h1>Палата 404 · вибіркове об’єднання Avatar Core</h1><p class="warning">Кандидат для перегляду. Не production-ready. Стики покращено локально; повні затверджені рукоятки відсутні. Main і публікацію не змінено.</p><p>ДО: 184e392 (runtime тотожний 766a71e). ПІСЛЯ: незмінений 5532a93. ФІНАЛ: похідні PNG. Усі Canvas 941×1672, тло #f8f5ed, незмінена реєстрація. Старі жіночі геометричні props показані як є. ПІСЛЯ та ФІНАЛ використовують original-visible, а не інші повні тестові моделі.</p><p>Історичні кінцеві пози знято з transitionMs=0, щоб не порівнювати кінцеву позу з випадковим проміжним кадром. У фінальній версії instant cut збережено; морфінг не додавався.</p><p>Масштабуйте сторінку для огляду 100–400%. Мініатюри лише CSS: вихідні пікселі вбудовані. Ця галерея працює без сервера та зовнішніх файлів.</p>'''
body+='<h2>Вибір основи до редагування</h2><div class="scroll"><table>'
first=True
for line in (D/'AUDIT-BEFORE-EDIT.md').read_text().splitlines():
 if not line.startswith('|') or set(line.replace('|','').replace(' ',''))<=set('-:'):continue
 tag='th' if first else 'td';first=False;body+='<tr>'+''.join('<'+tag+'>'+html.escape(c.strip())+'</'+tag+'>' for c in line.strip('|').split('|'))+'</tr>'
body+='</table></div>'
for gender in ['male','female']:
 for pose in ['idle','melee','pistol','rifle']:
  title={'male':'Чоловік','female':'Жінка'}[gender]+' · '+{'idle':'Нейтральна поза','melee':'Ніж','pistol':'Пістолет','rifle':'Автомат'}[pose];body+='<section><h2>'+title+'</h2>'
  assessment_path=D/'pose-assessment.json'
  if assessment_path.exists():
   assessment=next(r for r in json.loads(assessment_path.read_text()) if r['gender']==gender and r['pose']==pose);body+='<details><summary>Окрема візуальна оцінка — не автоматичне художнє затвердження</summary><dl>'
   for key,label in [('geometry','Геометрія'),('shoulders','Плечі'),('elbows','Лікті'),('wrists_hands','Кисті/зап’ястя'),('colour','Тон'),('detail','Деталізація'),('alpha','Альфа'),('grip','Хват'),('without_weapon','Без предмета'),('future_items','Майбутні предмети')]:body+='<dt><strong>'+label+'</strong></dt><dd>'+html.escape(assessment[key])+'</dd>'
   body+='</dl></details>'
  body+='<div class="phases">'
  for t in [0,1000,2000,3000]:
   p=save(triple(gender,pose,t,pose!='idle'),f'triple-{gender}-{pose}-{t}.webp');body+=f'<details {"open" if t==0 else ""}><summary>Фаза {t} ms · повний зріст</summary>'+figure(p,title+f', {t} ms; однаковий масштаб усіх трьох версій')+'</details>'
  body+='</div>'
  p=save(triple(gender,pose,0,False),f'triple-{gender}-{pose}-hidden.webp');body+='<details><summary>Без зброї</summary>'+figure(p,'Незалежне приховування предмета; руки не вимикаються')+'</details>'
  body+='<details><summary>Плечі, лікті, кисті — нативні крупні плани</summary>'
  snapshots=[]
  for v in versions:
   j=json.loads((E/f'{v}-captures.json').read_text());snap=next(r['snapshot'] for r in j['rows'] if r['gender']==gender and r['pose']==pose and r['time']==0 and r['snapshot']);snapshots.append(snap)
  for side in ['right','left']:
   for joint in ['shoulder','elbow','wrist']:
    points=[]
    for s in snapshots:
     frame=s.get('frame',s);arms=frame.get('arms',{});point=arms.get(side,{}).get(joint)
     if point:points.append(point)
    # Shoulder roots independently measured on immutable base; fallback windows
    # remain fixed world coordinates if an archived snapshot has no joint table.
    defaults={'right':{'shoulder':[300,375],'elbow':[240,590],'wrist':[280,780]},'left':{'shoulder':[650,375],'elbow':[700,590],'wrist':[710,760]}}
    if not points:points=[defaults[side][joint]]
    radius=75 if joint!='wrist' else 95;x0=max(0,int(min(p[0] for p in points)-radius));x1=min(941,int(max(p[0] for p in points)+radius));y0=max(0,int(min(p[1] for p in points)-radius));y1=min(1672,int(max(p[1] for p in points)+radius));p=save(triple(gender,pose,0,pose!='idle',(x0,y0,x1,y1)),f'close-{gender}-{pose}-{side}-{joint}.webp');body+=figure(p,f'{side} {joint}; той самий crop [{x0},{y0},{x1},{y1}]')
  body+='</details>'
  if pose!='idle':
   im=Image.new('RGB',(941*3,1702),'#ddd');d=ImageDraw.Draw(im)
   for i,scale in enumerate([.85,1,1.15]):im.paste(Image.open(G/f'final-{gender}-{pose}-scale-{scale}.png'),(941*i,30));d.text((941*i+10,4),str(round(scale*100))+'%',font=font,fill='black')
   p=save(im,f'sizes-{gender}-{pose}.webp');body+='<details><summary>Масштаби зброї 85% / 100% / 115%</summary>'+figure(p,'Primary grip збережено. Для rifle 85/115% опорна рука потребує окремого профілю; ці масштаби не затверджені.')+'</details>'
  body+='</section>'
body+='<section><h2>Повний цикл дихання 4000 ms</h2><p>Реальні Canvas кадри через 100 ms, 40 кадрів на цикл. Анімація — компактне WebP preview quality 95; статичні native порівняння lossless. Це не вимірювання FPS і не фізичний телефон.</p>'
for file in sorted(G.glob('*knife-triple-cycle.webp')):body+=figure(file,'ДО / ПІСЛЯ / ФІНАЛ — синхронізований цикл; default 100%')
body+='</section>'
body+='<section><h2>Походження зброї</h2><p>22 історичні weapon PNG + 37 додаткових кандидатів з усієї історії Git. reference-weapon-full у hand-art-kit містять інші тестові моделі, не потрібну затверджену модель. Назва full не є доказом відповідності дизайну. Маски й ілюстрації з пальцями не є незалежними повними предметами.</p>'+figure(G/'weapon-history.webp','Унікальні історичні PNG у каталозі weapons')+figure(G/'additional-weapons.webp','Додаткові ресурси: донорські шари, full тестові моделі, маски, атласи')
for file in sorted(G.glob('weapon-*-uncertain.webp')):body+=figure(file,'Малиновий — історично змінені solid pixels проти registered raw Sources. Це кандидати походження, не автоматична оцінка художньої якості. Сам runtime не змінено.')
body+='</section>'
export=json.loads((E/'selective-arm-export.json').read_text());body+='<section><h2>Порівняння вихідних PNG-сегментів</h2>'
for r in export:
 source=Image.open(R/'avatar-core'/r['source']).convert('RGBA');final=Image.open(R/'avatar-core'/r['output']).convert('RGBA');box=source.getbbox();source=source.crop(box);final=final.crop(box);w,h=source.size;im=Image.new('RGB',(w*2,h+30),'#ddd');d=ImageDraw.Draw(im)
 for i,a in enumerate([source,final]):im.paste(a,(i*w,30),a);d.text((i*w+2,2),['5532a93','ФІНАЛ'][i],font=font,fill='black')
 p=save(im,'source-'+r['gender']+'-'+r['pose']+'-'+r['side']+'.webp');body+='<details><summary>'+r['gender']+' '+r['pose']+' '+r['side']+'</summary>'+figure(p,'Однаковий crop вихідних complete PNG; alpha і кисті тотожні')+'</details>'
body+='</section>'
issues=[]
for row in export:
 g,p,s=row['gender'],row['pose'],row['side'];issues.append({'id':f'SM-{len(issues)+1:02}','location':f'{g}/{p}/{s}','problem':'Відмінна текстура/тон у зоні переходу плеча','cause':'Pose-specific живопис і його історична ретуш відрізняються від базового тіла; upper-arm alpha належить іншому шару.','change':'Старий надійний RGB чоловічої руки + current alpha/кисті; проксимальний RGB з точного base без зміни форми. Жінки: збережені current donor та корекція тільки зареєстрованого кореня.','status':'PARTIAL','evidence':f'Gallery/close-{g}-{p}-{s}-shoulder.webp','remaining':'У 100–400% частина відмінностей донорського рисунка/світлотіні залишається; це не повний repaint.'})
for item in ['AKS','PM','knife']:issues.append({'id':f'SM-{len(issues)+1:02}','location':item,'problem':'Немає доказово повного затвердженого незалежного PNG','cause':'У джерелах рукоятки закриті кистями; повні інші моделі не відповідають затвердженому дизайну.','change':'Збережено наявні достовірні пікселі original-visible без генерації/підміни.','status':'OPEN','evidence':'Gallery/weapon-history.webp','remaining':'Потрібен затверджений повний шар або окремо погоджене відновлення невидимого матеріалу.'})
issues.append({'id':f'SM-{len(issues)+1:02}','location':'rifle/85%-115%','problem':'Зміна довжини предмета змінює потрібне положення опорної кисті','cause':'Діагностичний scale зберігає primary pivot, але не перекалібровує support pose.','change':'Показано три розміри без приховування відстані; 100% профіль збережено.','status':'OPEN','evidence':'Gallery/sizes-male-rifle.webp','remaining':'Потрібні модельні support-профілі для цих розмірів; не змінено увесь аватар заради діагностики.'})
issues.append({'id':'SM-13','location':'Lab / ДО','problem':'Підпис 184e392/766a71e вів до знімків c2822a7','cause':'Старе посилання previousFrame залишилося після оновлення підпису.','change':'Посилання та offline embed тепер використовують справжні native 184e392 rerenders, фаза 0 ms явно вказана.','status':'FIXED','evidence':'Evidence/baseline-label-defect.json','remaining':'Історичні файли не замінювалися.'})
issues.append({'id':'SM-14','location':'melee / обидві статі','problem':'Регулятор 2 px фактично давав 7.5–7.9 px на ножі','cause':'Жорстка амплітуда 1.6° через важіль до кінця ножа давала понад 7 px; функція не читала опис meleeMotion з preview JSON.','change':'Один додатковий аргумент підключає наявний профіль: upper .008°, fore .025°, hand .35°. Цикл 4000 ms. Реальний hull усіх alpha>0: male 1.981 px, female 1.825 px при штатному масштабі 100%.','status':'FIXED','evidence':'Evidence/actual-weapon-motion.json','remaining':'Діагностичні 85/115% та більші значення регулятора не є затвердженими предметними профілями.'})
issues.append({'id':'SM-15','location':'Lab / вибір пози','problem':'Початковий режим міг показати інші повні тестові моделі після натискання пози','cause':'Кнопки викликали setPose без вибору original-visible ID.','change':'Кнопки за замовчуванням обирають gear-aks/gear-pm/gear-knife. Legacy доступний тільки після явного вибору режиму.','status':'FIXED','evidence':'Evidence/final-selective-tests.log','remaining':'Оригінальні моделі лишаються PARTIAL через джерела.'})
(D/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n');body+='<section><h2>Реєстр дефектів</h2><div class="scroll"><table><tr><th>ID</th><th>Місце</th><th>Проблема</th><th>Зміна</th><th>Статус</th></tr>'
for r in issues:body+='<tr>'+''.join('<td>'+html.escape(r[k])+'</td>' for k in ['id','location','problem','change','status'])+'</tr>'
body+='</table></div></section>'
summary=E/'full-run/summary.json';tests=json.loads(summary.read_text()) if summary.exists() else None
body+='<section><h2>Реальна гра та контрастні фони</h2>'
for file in sorted(G.glob('game-*.png')):
 p=save(Image.open(file).convert('RGB'),file.stem+'.webp');body+=figure(p,file.stem+' · фактичний index.html?avatarCore=1')
for file in sorted(G.glob('backgrounds-*.webp')):body+=figure(file,file.stem+' · чотири фони, фактичний Canvas')
body+='</section>'
body+='<section><h2>Перевірки та обмеження</h2><p>JavaScript 123/123. Фінальні цільові Python/Chromium 10/10; dropdown follow-up 1/1. Ці повтори не додаються до повного прогону.</p><p>'+ (f"Повний Python/Chromium: {tests['passed']}/{tests['ran']}; невдалих {len(tests['failure_ids'])}." if tests else 'Повний Python/Chromium ще виконується; підсумок не заявлено.')+'</p><p>Оригінальні PNG, риги, wardrobe, item IDs і save keys не змінені. Шари рук — RGB-only похідні зі збереженням alpha/кистей. У engine змінено один виклик для передачі існуючого motion-профілю; функція має сумісний optional argument, без перебудови рига. Дихання 4000 ms збережено; default melee тепер фізично вкладається в 2 px. У Lab виправлено джерело ДО і явний вибір оригінальних предметів. Усі результати Chromium — емуляція, фізичного пристрою не було.</p><p>Критерії завершення не виконані: рукоятки відсутні, painterly гармонізація рук часткова, rifle 85/115% не затверджено. Ця галерея є матеріалом для перевірки, а не заявою про production-ready.</p></section>'
css='body{background:#171b20;color:#ece6dc;font:16px system-ui;margin:0;padding:20px}section{border-top:1px solid #777;margin-top:35px;padding-top:15px}img{max-width:100%;height:auto}figure{margin:14px 0}figcaption{font-size:14px;color:#ccc}summary{cursor:pointer;padding:14px;background:#30343b;margin:5px 0}table{border-collapse:collapse;min-width:700px}td,th{padding:10px;border:1px solid #777;vertical-align:top}.scroll{overflow:auto}.warning{padding:15px;background:#5d352b}h1{font-size:27px}p{line-height:1.55}*{box-sizing:border-box}'
(D/'Report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core · ДО / ПІСЛЯ / ФІНАЛ</title><style>'+css+'</style><body>'+body+'</body></html>');print('Standalone gallery:',(D/'Report.html').stat().st_size,'bytes;',len(issues),'defects')
# Small static alternative. Each page has exactly the same actual Canvas triptych.
pages=[]
for g in ['male','female']:
 for p in ['idle','melee','pistol','rifle']:
  im=triple(g,p,0,p!='idle');im.thumbnail((1412,836));page=Image.new('RGB',(1480,940),'white');d=ImageDraw.Draw(page);d.text((20,8),g+' / '+p+' — 184e392 | 5532a93 | final',font=font,fill='black');page.paste(im,((1480-im.width)//2,45));d.text((20,900),'Кандидат: плечі частково узгоджені; рукоятки неповні. Для точних 100–400% дивіться lossless HTML.',font=font,fill='black');pages.append(page)
pages[0].save(D/'Review.pdf',save_all=True,append_images=pages[1:],resolution=120)

# Human-readable technical HTML, instead of displaying Markdown as source.
import re
def inline(text):
 text=html.escape(text);text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text);text=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text);return re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
parts=[];lines=(D/'README.md').read_text().splitlines();i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('#'):
  n=min(6,len(line)-len(line.lstrip('#')));parts.append(f'<h{n}>'+inline(line[n:].strip())+f'</h{n}>');i+=1
 elif line.startswith('- '):
  items=[]
  while i<len(lines) and lines[i].startswith('- '):items.append('<li>'+inline(lines[i][2:])+'</li>');i+=1
  parts.append('<ul>'+''.join(items)+'</ul>')
 else:parts.append('<p>'+inline(line)+'</p>');i+=1
(D/'Technical-report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core · технічний звіт</title><style>body{max-width:1100px;margin:auto;padding:18px;font:16px/1.6 system-ui;background:#171b20;color:#eee;overflow-wrap:anywhere}a{color:#9bd4eb}code{font-size:.9em}h1{font-size:26px}</style><body>'+''.join(parts)+'</body></html>')
