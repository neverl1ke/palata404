"""Readable online/offline review from actual captures; no synthesized avatars."""
from pathlib import Path
import json,base64,mimetypes,re,html,io
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/avatar-core-1'
status='Механічний прототип для перегляду. Не готовий до гри: на сильних згинах рук залишаються кутові фрагменти та різкі текстурні стики; пальці не утворюють природного хвату. У main не інтегровано.'
def image(path,alt):return f'<img src="{path}" alt="{html.escape(alt)}">'
def two(a,b,title):return f'<section><h2>{title}</h2><div class="grid">{image(a,"Чоловік · "+title)}{image(b,"Жінка · "+title)}</div></section>'
parts=[]
summary_path=R/'validation-summary.json'
if summary_path.is_file():
 summary=json.loads(summary_path.read_text())
 rows=''.join('<li>'+html.escape(v)+'</li>' for v in summary['statements'])
 parts.append('<section><h2>Фактичні результати перевірок</h2><ul>'+rows+'</ul><p>Кутові фрагменти рук і неправильний хват залишаються відкритими дефектами, незалежно від результатів автоматичних тестів.</p></section>')
for p,n in [('idle','01 · Спокій'),('melee','02 · Ніж'),('pistol','03 · Пістолет · поза з референсу'),('rifle','04 · Автомат')]:parts.append(two(f'male-{p}.png',f'female-{p}.png',n))
parts.append(two('male-pistol-supported.png','female-pistol-supported.png','Додаткова підтримка пістолета другою рукою'))
parts.append(two('male-breathing.webp','female-breathing.webp','Дихання · 4000 мс · 25 справжніх кадрів'))
parts.append(two('male-skeleton.png','female-skeleton.png','Скелети та точки хвату'))
parts.append('<section><h2>Оригінали й модульні тіла · однаковий масштаб</h2>'+image('male-original-vs-rig.webp','Оригінал та риг · чоловік')+image('female-original-vs-rig.webp','Оригінал та риг · жінка')+'</section>')
parts.append('<section><h2>Вдих / видих</h2><p>Чоловік, потім жінка. Ступні та обличчя не зсуваються.</p><div class="grid">'+''.join(image(f'{g}-{p}.png',g+' '+p) for g in ['male','female'] for p in ['inhale','exhale'])+'</div></section>')
for joint,name in [('shoulder','Плечі'),('elbow','Лікті'),('grip','Кисті та зброя')]:
 parts.append('<section><h2>'+name+' · 300%</h2><p>right — анатомічна права рука (зліва на зображенні). Не видаємо ці крупні плани за затверджений арт.</p><div class="grid">'+''.join(image(f'{g}-{side}-{joint}-300.webp',g+' '+side+' '+joint) for g in ['male','female'] for side in ['right','left'])+'</div></section>')
parts.append(two('male-test-sleeves.png','female-test-sleeves.png','Тестові накладки через Equipment Binding API'))
parts.append(two('male-all-current-faces.webp','female-all-current-faces.webp','Чинні обличчя · 9 чоловічих і 17 жіночих'))
parts.append('<section><h2>Інтерфейс лабораторії</h2>'+image('lab-desktop.png','Десктопний Avatar Lab')+'<div class="grid">'+''.join(image(f'lab-mobile-{w}.png',str(w)+' px · емуляція') for w in [320,390,768])+'</div></section>')
coords={g:{'landmarks':json.loads((ROOT/f'avatar-core/rigs/{g}_rig.json').read_text())['landmarks'],'arms':json.loads((ROOT/f'avatar-core/rigs/{g}_rig.json').read_text())['arms']} for g in ['male','female']}
text='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата 404 · Avatar Core 1.0 · перегляд</title><style>body{background:#151c1d;color:#d9d6ca;font:17px/1.55 system-ui;max-width:1500px;margin:auto;padding:24px}a{color:#9dd7d9}img{display:block;width:100%;height:auto;margin:16px 0;background:#d3cfc6}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}section{border-top:1px solid #59625b;margin-top:32px;padding-top:20px}.notice{padding:16px;border:1px solid #ae8763;background:#352e26}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#222c2c;padding:16px}h1{font:36px Georgia,serif}@media(max-width:600px){body{padding:14px}.grid{grid-template-columns:minmax(0,1fr)}h1{font-size:28px}}</style><h1>Avatar Core 1.0 · чоловічий і жіночий риги</h1><p class="notice">'''+status+'''</p><p>Кадри реального Avatar Lab, вихідне полотно 941×1672. Оригінальні PNG не перезаписані, надані приклади поз не використовуються як ігрові зображення. Зброя — окремі схематичні тестові ресурси.</p><p><a href="../../avatar-lab/">Відкрити Avatar Lab на локальному сервері</a> · <a href="README.md">Технічний звіт</a></p>'''+''.join(parts)+'<section id="parameters"><h2>Виміряні координати двох ригів</h2><pre>'+html.escape(json.dumps(coords,ensure_ascii=False,indent=2))+'</pre></section></html>'
(R/'index.html').write_text(text)
def embed(m):
 p=R/m[2]
 if not p.is_file() or p.suffix not in ['.png','.webp']:return m[0]
 if p.suffix=='.png':
  original=Image.open(p);buf=io.BytesIO();original.save(buf,format='WEBP',lossless=True);payload=buf.getvalue()
  import numpy as np
  assert np.array_equal(np.array(original.convert('RGBA')),np.array(Image.open(io.BytesIO(payload)).convert('RGBA')))
  mime='image/webp'
 else:payload=p.read_bytes();mime=mimetypes.guess_type(p.name)[0]
 return m[1]+'data:'+mime+';base64,'+base64.b64encode(payload).decode()+m[3]
off=re.sub(r'(src=")([^"]+)(")',embed,text.replace('href="../../avatar-lab/"','href="Avatar-Lab.html"').replace('href="README.md"','href="#parameters"'));(R/'avatar-report-offline.html').write_text(off);print('Report includes',off.count('<img '),'real images; offline bytes',len(off.encode()))
