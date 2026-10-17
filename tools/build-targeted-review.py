"""Assemble comparisons exclusively from captured game-render screenshots."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from html import escape
import json
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'review/paper-doll-targeted-fix';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
for file in sorted((P/'after').glob('*-detail.png')):
 old=P/'before'/file.name
 if not old.exists():continue
 parts=[]
 for f in [old,file]:
  im=Image.open(f);parts.append(im.crop((0,0,568,im.height)))
 out=Image.new('RGB',(1136,max(i.height for i in parts)+30),'#d6d2ca');d=ImageDraw.Draw(out);d.text((8,5),'ДО',fill='#111',font=font);d.text((576,5),'ПІСЛЯ',fill='#111',font=font)
 for j,i in enumerate(parts):out.paste(i,(j*568,30))
 out.save(P/(file.name.replace('-detail.png','-before-after.png')))
for gender in ['male','female']:
 for color in ['original','white']:
  haircount=7 if gender=='male' else 8;sheet=Image.new('RGB',(haircount*160,6*220),'#d6d2ca');d=ImageDraw.Draw(sheet)
  for row,kind in enumerate(['native','face-asian','face-young','face-exhausted','face-elder','face-alternative']):
   im=Image.open(P/'after'/f'{gender}-{kind}-{color}.jpg')
   for col in range(haircount):
    crop=im.crop((8,24+col*454,344,454+col*454));crop.thumbnail((152,194));sheet.paste(crop,(col*160,row*220+22));d.text((col*160+2,row*220+2),kind.replace('face-',''),fill='#111',font=font)
  sheet.save(P/f'matrix-{gender}-{color}.jpg',quality=95)
html=['<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата 404 — цільовий фікс Paper Doll</title><style>body{max-width:1400px;margin:auto;padding:20px;background:#111820;color:#ece8df;font:16px/1.5 system-ui}a{color:#c3d9ee}img{max-width:100%;height:auto}summary{cursor:pointer;padding:12px;background:#29313b}figure{margin:10px 0 25px}.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}@media(max-width:650px){.pair{grid-template-columns:1fr}}</style><h1>Палата 404 — цільовий фікс після аудиту</h1><p><a href="https://github.com/neverl1ke/palata404/blob/main/review/paper-doll-targeted-fix/README.md">Повний звіт українською</a> · <a href="../../index.html">Гра</a></p><p>ДО: main 8bcf183. ПІСЛЯ: цей фікс. Справжні знімки index.html у Chromium. Однакові камери та масштаб для обох фаз; білий, сірий, чорний, зелений фони. Ретушований портрет показано тільки через фактичне накладання в грі.</p>']
def pic(path,label):return '<figure><figcaption>'+escape(label)+'</figcaption><a href="'+escape(path)+'"><img loading="lazy" src="'+escape(path)+'" alt="'+escape(label)+'"></a></figure>'
labels={'male-asian-head':'Чоловіча азійська голова: масштаб і край','male-asian-neck':'Чоловіча азійська голова: шия','female-alternative-ear-left':'Жіноча альтернативна: лівий край вуха та шиї ×4','female-alternative-ear-right':'Жіноча альтернативна: правий край вуха та шиї ×4','female-exhausted-head':'Жіноча exhausted: голова','female-exhausted-neck':'Жіноча exhausted: стик шиї','female-inner-thighs':'Жіноче тіло: тон внутрішніх стегон','male-alternative-head':'Чоловіче альтернативне: тон і мальована ретуш','male-messy':'Чоловіча messy: вуха','male-shoulder':'Чоловіча shoulder-length: передні та задні пасма','female-alternative-head':'Жіноча альтернативна: легкий тон і очищений край','female-alternative-neck':'Жіноча альтернативна: шия'}
for name,label in labels.items():html+=[pic(name+'-before-after.png',label)]
html+=['<h2>Усі 90 комбінацій</h2>']
for g in ['male','female']:
 for c in ['original','white']:html+=[pic(f'matrix-{g}-{c}.jpg',f'{g} · {c} · усі обличчя та зачіски')]
html+=['<h2>Повні таблиці на чотирьох фонах</h2><p>Рядки: зачіски. Стовпці: білий, сірий, чорний, зелений.</p>']
for g in ['male','female']:
 for f in ['native','face-asian','face-young','face-exhausted','face-elder','face-alternative']:
  for c in ['original','white']:
   name=f'{g}-{f}-{c}.jpg';html+=['<details><summary>'+escape(f'{g} · {f} · {c}')+'</summary><div class="pair">',pic('before/'+name,'ДО'),pic('after/'+name,'ПІСЛЯ'),'</div></details>']
html+=['<h2>Збільшені оригінальні PNG на чотирьох фонах</h2>']
for f in sorted((P/'after').glob('*-detail.png')):html+=['<details><summary>'+escape(f.stem)+'</summary><div class="pair">',pic('before/'+f.name,'ДО'),pic('after/'+f.name,'ПІСЛЯ'),'</div></details>']
html+=['<h2>Гардероб і кольори</h2>']
for f in sorted((P/'after').glob('*target-palette*.jpg')):html+=['<details><summary>'+escape(f.stem)+'</summary>',pic('after/'+f.name,f.stem),'</details>']
for w in [320,360,390,430,768,1440]:html+=['<details><summary>'+str(w)+' px</summary>',pic(f'after/wardrobe-{w}-hair.jpg',str(w)+' px · поточний гардероб'),'</details>']
html+=['<p>Фізичний телефон недоступний; перевірки виконано в Chromium. Природні тіні під щелепою, складки вух і проміжки між пасмами навмисно не залито.</p></html>'];(P/'gallery.html').write_text('\n'.join(html)+'\n')
