"""Build a small linked gallery from actual independent browser captures."""
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'review/female-faces-independent-audit'
KINDS=['asian','young','exhausted','elder','alternative',
       'ginger-soft','goth-septum','goth-black-lips']
NAMES=['Азійське','Молоде','Виснажене','Старше','Альтернативне',
       'Світле руде','Готичне із септумом','Готичне з чорними губами']
details=OUT/'details';details.mkdir(exist_ok=True)
font=ImageFont.truetype('DejaVuSans.ttf',13)
sections=[]
for kind,name in zip(KINDS,NAMES):
    face='face-'+kind
    before=Image.open(OUT/'before-chromium'/f'{face}-bare.png').convert('RGB')
    after=Image.open(OUT/'after-chromium'/f'{face}-bare.png').convert('RGB')
    for scale in [1,2,4]:
        # The white native render occupies the first 240px panel.
        pair=Image.new('RGB',(480*scale,300*scale+24),'#dedbd3')
        for j,im in enumerate([before,after]):
            crop=im.crop((0,0,240,300)).resize((240*scale,300*scale),Image.Resampling.NEAREST)
            pair.paste(crop,(240*scale*j,24))
        d=ImageDraw.Draw(pair);d.text((4,4),'ДО',fill='black',font=font);d.text((240*scale+4,4),'ПІСЛЯ',fill='black',font=font)
        pair.save(details/f'{face}-{scale}x.png',optimize=True)
    ears=Image.new('RGB',(800,688),'#dedbd3')
    ed=ImageDraw.Draw(ears)
    for row,(x0,label) in enumerate([(15,'Лівий край зображення'),(180,'Правий край зображення')]):
        ed.text((4,row*344+4),label+' · 400% · білий / сірий / чорний / зелений',font=font,fill='black')
        for column in range(4):
            crop=after.crop((240*column+x0,100,240*column+x0+40,180))
            ears.paste(crop.resize((160,320),Image.Resampling.NEAREST),(200*column,row*344+24))
    ears.save(details/f'{face}-ears-four-backgrounds.png',optimize=True)
    join=Image.new('RGB',(1120,296),'#dedbd3')
    jd=ImageDraw.Draw(join)
    for j,im in enumerate([before,after]):
        crop=im.crop((720+405-354,218,720+545-354,286)).resize((560,272),Image.Resampling.NEAREST)
        join.paste(crop,(560*j,24))
        jd.text((560*j+4,4),'ДО' if j==0 else 'ПІСЛЯ',font=font,fill='black')
    join.save(details/f'{face}-join-defect.png',optimize=True)
    if kind in ['ginger-soft','goth-septum']:
        # Right neck: native Paper Doll x=500..535, y=218..265, green panel.
        pair=Image.new('RGB',(280,212),'#dedbd3')
        for j,im in enumerate([before,after]):
            crop=im.crop((720+500-354,218,720+535-354,265)).resize((140,188),Image.Resampling.NEAREST)
            pair.paste(crop,(140*j,24))
        d=ImageDraw.Draw(pair);d.text((4,4),'ДО',fill='black',font=font);d.text((144,4),'ПІСЛЯ',fill='black',font=font)
        pair.save(details/f'{face}-neck-defect.png',optimize=True)
    links=[]
    for engine in ['chromium','firefox']:
        for color in ['original','black','white']:
            files=list((OUT/f'after-{engine}').glob(f'{face}-{color}.*'))
            if files:
                path=files[0].relative_to(OUT)
                links.append(f'<a href="{path}">{engine} · {color} · 8 зачісок × 4 фони</a>')
    neck=(f'<h3>Підтверджена смужка шиї · 400%</h3><img src="details/{face}-neck-defect.png" alt="Смужка шиї до та після">'
          if kind in ['ginger-soft','goth-septum'] else '')
    sections.append(f'''<section id="{face}"><h2>{name} · {face}</h2>
      {neck}<h3>Нижній стик шиї · 400%</h3><img loading="lazy" src="details/{face}-join-defect.png" alt="{name}: нижній стик до/після">
      <p>ДО: 6bac151; ПІСЛЯ: локальний технічний фікс. Однаковий ракурс і масштаб.</p>
      <a href="details/{face}-1x.png"><img loading="lazy" src="details/{face}-1x.png" alt="{name}: 100% до/після"></a>
      <details><summary>200% · вуха, щелепа, підборіддя, шия</summary><a href="details/{face}-2x.png"><img loading="lazy" src="details/{face}-2x.png" alt="{name}: 200%"></a></details>
      <details><summary>400% · той самий фактичний рендер</summary><a href="details/{face}-4x.png"><img loading="lazy" src="details/{face}-4x.png" alt="{name}: 400%"></a></details>
      <details><summary>Вуха та крайові RGB-кандидати · 4 фони · 400%</summary><a href="details/{face}-ears-four-backgrounds.png"><img loading="lazy" src="details/{face}-ears-four-backgrounds.png" alt="{name}: обидва вуха на чотирьох фонах"></a></details>
      <p><a href="before-chromium/{face}-bare.png">ДО · 4 фони</a> · <a href="after-chromium/{face}-bare.png">ПІСЛЯ · 4 фони</a> · <a href="after-chromium/{face}-game.png">Справжній розмір у гардеробі</a></p>
      <details><summary>Повна матриця зачісок і кольорів</summary><p>Колонки: білий / сірий / чорний / зелений. Рядки відповідають списку волосся у протоколі браузера.</p><nav>{''.join(links)}</nav></details></section>''')
doc='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Палата 404 · незалежна ревізія 8 облич</title><style>
body{margin:0;background:#10151b;color:#eee;font:16px/1.5 system-ui}main{max-width:1200px;margin:auto;padding:20px}a{color:#b7dcff}img{max-width:100%;height:auto}section{border-top:1px solid #667;padding:20px 0}nav{display:flex;gap:16px;flex-wrap:wrap}details{padding:12px;border:1px solid #667;margin:12px 0}summary{cursor:pointer}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #667;text-align:left}code{overflow-wrap:anywhere}
</style><main><h1>Незалежна ревізія 8 жіночих облич</h1>
<p>Ця галерея фіксує новий аудит після 6bac151. Контрольні кадри отримані з виробничого рендерера в index.html. Збільшення — найближчим сусідом, без нової генерації або домальовування.</p>
<p><a href="https://github.com/neverl1ke/palata404/blob/main/review/female-faces-independent-audit/README.md">Повний звіт і таблиця дефектів</a> · <a href="before-analysis.json">Вихідні кандидати контурів</a> · <a href="after-analysis.json">Повторний аналіз</a> · <a href="historical-inventory.json">Ревізія 75,8 МБ</a></p>
<p>Виправлені дві технічні смужки шиї та помилка distance field, яка спричиняла різкий нижній стик шести портретів. Вісім накладок скориговано тільки нижче щелепи, без зміни масок або верхніх портретів. Художні відмінності тону, форми вух та щелеп збережені й описані у звіті. Успішне завантаження матриці не є автоматичним підтвердженням художньої досконалості.</p>
<nav>'''+''.join(f'<a href="#face-{k}">{n}</a>' for k,n in zip(KINDS,NAMES))+'''</nav>'''+''.join(sections)+'''<section><h2>Справжній інтерфейс · емуляція розмірів</h2><nav>'''+''.join(f'<a href="after-{e}/wardrobe-{w}.png">{e} · {w}px</a>' for e in ['chromium','firefox'] for w in [320,360,390,430,768,1440])+'''</nav><p>Це настільні браузери з заданим viewport; фізичний телефон не використовувався. WebKit не запущений через відсутні системні бібліотеки.</p></section></main></html>'''
(OUT/'gallery.html').write_text(doc)
print('Independent real-render gallery built')
