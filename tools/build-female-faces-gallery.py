"""Build review navigation and enlarged crops from actual Chromium screenshots."""
import html
import json
from pathlib import Path

from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'review/female-faces-integration'
data=json.loads((OUT/'integration-manifest.json').read_text())
capture=json.loads((OUT/'after/capture.json').read_text())
names={'asian':'Азійське','young':'Молоде','exhausted':'Виснажене','elder':'Старше','alternative':'Альтернативне',
       'ginger_soft':'Світле ніжне','goth_septum':'Готичне із септумом','goth_black_lips':'Готичне з чорними губами'}
details=OUT/'details';details.mkdir(exist_ok=True)


def crop_game(path,box,scale=3):
    return Image.open(path).convert('RGB').crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST)


for e in data['files']:
    face=e['id'];old='before' if e['kind'] in ['asian','young','exhausted','elder','alternative'] else 'inputs'
    a=OUT/old/(face+'-bare.png');b=OUT/'after'/(face+'-bare.png')
    # Same first white-background panel, same actual renderer scale in both phases.
    sheets=[('portrait',(6,21,286,376),2),('left-ear',(22,135,100,255),4),
            ('right-ear',(190,135,278,255),4),('neck',(65,250,230,365),4)]
    for label,box,scale in sheets:
        before,after=crop_game(a,box,scale),crop_game(b,box,scale)
        sheet=Image.new('RGB',(before.width*2,before.height+24),'#d8d5cd');d=ImageDraw.Draw(sheet)
        d.text((8,5),'DO / BEFORE',fill='black');d.text((before.width+8,5),'PISLIA / AFTER',fill='black')
        sheet.paste(before,(0,24));sheet.paste(after,(before.width,24))
        sheet.save(details/(face+'-'+label+'.png'),optimize=True)
    source=Image.open(OUT/e['source']).convert('RGBA')
    alpha=source.getchannel('A').point(lambda a:255 if a>=128 else 0)
    preview=source.crop(alpha.getbbox());preview.thumbnail((340,440),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(360,460),'#e8e4db');canvas.alpha_composite(preview,((360-preview.width)//2,10));canvas.convert('RGB').save(details/(face+'-source.jpg'),quality=95)

# Dense contact sheets contain crops of renderer screenshots, not new artwork.
for color in ['original','white','black']:
    sheet=Image.new('RGB',(8*200,8*270),'#d8d5cd');draw=ImageDraw.Draw(sheet)
    for col,e in enumerate(data['files']):
        im=Image.open(OUT/'after'/(e['id']+'-'+color+'.png')).convert('RGB')
        for row in range(8):
            top=21+row*376
            tile=im.crop((6,top,286,top+355)).resize((200,254),Image.Resampling.LANCZOS)
            sheet.paste(tile,(col*200,row*270+16))
            draw.text((col*200+2,row*270+2),e['kind']+' / '+str(row+1),fill='black')
    sheet.save(OUT/('matrix-'+color+'.jpg'),quality=96)

sections=[]
for e in data['files']:
    face=e['id'];n=names[e['kind']];params=html.escape(json.dumps(e['registration'],ensure_ascii=False))
    sections.append(f'''<section id="{face}" data-face="{face}"><h2>{n} · {face}</h2>
      <p>Ігровий шар: x=0, y=0, scale=1, 941×1672 RGBA. Підготовка джерела: <code>{params}</code>.</p>
      <div class="three"><figure><a href="{e['source']}"><img loading="lazy" src="details/{face}-source.jpg" alt="Затверджене джерело: {n}"></a><figcaption>Затверджене джерело · без зміни рис</figcaption></figure>
      <figure><a href="../../{e['output']}"><img loading="lazy" src="after/{face}-full.png" alt="Фінальний ігровий шар і повний зріст"></a><figcaption>Реальний рендер · натисни для активного PNG</figcaption></figure>
      <figure class="mask"><a href="../../{e['mask']}"><img loading="lazy" src="../../{e['mask']}" alt="Маска базового тіла"></a><figcaption>Маска базового тіла</figcaption></figure></div>
      <h3>ДО / ПІСЛЯ · однаковий масштаб Chromium</h3>
      <a href="details/{face}-portrait.png"><img class="comparison" loading="lazy" src="details/{face}-portrait.png" alt="Порівняння портретів"></a>
      <details><summary>Збільшення обох вух та шиї</summary><div class="three">'''+''.join(f'<a href="details/{face}-{part}.png"><img loading="lazy" src="details/{face}-{part}.png" alt="{part}: до та після"></a>' for part in ['left-ear','right-ear','neck'])+f'''</div></details>
      <h3>П’ять фонів: білий, сірий, чорний, зелений, шаховий</h3><a href="after/{face}-bare.png"><img loading="lazy" src="after/{face}-bare.png" alt="Без волосся на п’яти фонах"></a>
      <details><summary>Усі 8 зачісок × 5 фонів: original / black / white</summary>
      <label>Колір волосся <select data-color><option value="original">Оригінальний</option><option value="black">Чорний</option><option value="white">Білий</option></select></label>
      <a data-matrix-link href="after/{face}-original.png"><img data-matrix loading="lazy" src="after/{face}-original.png" alt="Повна матриця зачісок"></a></details>
      <p>Технічні перевірки: файл/маска, реєстрація, збереження рис, незмінність тіла, відсутність відірваного слабкого альфа-шуму. <a href="integration-manifest.json">Точні SHA і параметри</a>.</p></section>''')
doc='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Палата 404 · 8 жіночих облич</title><style>
body{margin:0;background:#10151b;color:#e8e4db;font:16px/1.5 system-ui}main{max-width:1400px;margin:auto;padding:24px}a{color:#b8d8ff}img{max-width:100%;height:auto}figure{margin:0}section{border-top:1px solid #56616b;margin-top:35px;padding-top:16px}nav{display:flex;flex-wrap:wrap;gap:14px}.three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.three img{max-height:460px;object-fit:contain}.mask{background:repeating-conic-gradient(#bbb 0% 25%,#777 0% 50%) 0/20px 20px;color:#111}details{margin:16px 0;border:1px solid #56616b;padding:12px}summary,select{cursor:pointer;padding:10px}select{font:inherit}.comparison{max-width:1120px}code{overflow-wrap:anywhere}@media(max-width:700px){main{padding:12px}.three{grid-template-columns:1fr}}
</style><main><h1>8 жіночих облич · контроль інтеграції</h1>
<p>Фактичний main від 4046cac. П’ять старих ID збережено, три нові додано лише жінкам. Базове обличчя тіла також лишається доступним окремо. Без генерації, без зміни баз, одягу чи зачісок.</p>
<p>Фото примірок отримані з index.html і renderPaperDollAt у Chromium. Збільшення — точні кропи цих знімків. Для нових трьох «ДО» означає наданий PNG з його початковою маскою у тому самому рендері; для старих п’яти — попередній main.</p>
<p><a href="https://github.com/neverl1ke/palata404/blob/main/review/female-faces-integration/README_UA.md">Повний звіт українською</a> · <a href="after/capture.json">960 контрольних зразків</a> · <a href="png-quality.json">Аналіз RGBA</a></p><nav>'''+''.join(f'<a href="#{e["id"]}">{names[e["kind"]]}</a>' for e in data['files'])+'''</nav>
<details><summary>Зведена матриця 8 облич × 8 зачісок</summary>'''+''.join(f'<a href="matrix-{c}.jpg"><img loading="lazy" src="matrix-{c}.jpg" alt="Матриця {c}"></a>' for c in ['original','black','white'])+'''</details>'''+''.join(sections)+'''<section><h2>Справжній гардероб · телефон / планшет / desktop</h2>'''+''.join(f'<details><summary>{w} px</summary><img loading="lazy" src="after/wardrobe-{w}.png" alt="Гардероб {w}px"></details>' for w in [320,390,768,1440])+'''</section></main><script>
document.querySelectorAll('[data-color]').forEach(s=>s.addEventListener('change',()=>{const box=s.closest('[data-face]'),src='after/'+box.dataset.face+'-'+s.value+'.png';box.querySelector('[data-matrix]').src=src;box.querySelector('[data-matrix-link]').href=src}));
</script></html>'''
(OUT/'gallery.html').write_text(doc)
print('Gallery, 32 detail comparisons, 8 source previews and 3 real-render contact sheets created')
