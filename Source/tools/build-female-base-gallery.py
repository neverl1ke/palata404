"""Build Ukrainian comparisons from native production Chromium screenshots."""
import html
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/female-base-replacement'
NAMES={'asian':'Азійське','young':'Молоде','exhausted':'Виснажене','elder':'Старше',
       'alternative':'Альтернативне','ginger-soft':'Світле ніжне','goth-septum':'Готичне із септумом',
       'goth-black-lips':'Готичне з чорними губами'}
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)


def pair(left,right,name):
    a,b=Image.open(left).convert('RGB'),Image.open(right).convert('RGB')
    out=Image.new('RGB',(a.width*2,a.height+26),'#dedbd4');d=ImageDraw.Draw(out)
    d.text((8,3),'ДО · b00712b',font=FONT,fill='black');d.text((a.width+8,3),'ПІСЛЯ',font=FONT,fill='black')
    out.paste(a,(0,26));out.paste(b,(a.width,26));out.save(REPORT/'details'/name,optimize=True)


def run():
    details=REPORT/'details';details.mkdir(exist_ok=True)
    before=REPORT/'before-chromium';after=REPORT/'after-chromium';native=REPORT/'native-base'
    pair(native/'before-full.png',native/'after-full.png','base-full.png')
    pair(native/'before-bare.png',native/'after-bare.png','base-head.png')
    result=json.loads((after/'result.json').read_text());hairs=result['hairs']
    geometries=[];sections=[]
    for kind,label in NAMES.items():
        face='face-'+kind;pair(before/(face+'-bare.png'),after/(face+'-bare.png'),face+'-join.png')
        a=np.array(Image.open(ROOT/f'assets/wardrobe/faces/female_{kind.replace("-","_")}_head.png'))[:218,:,3]
        y,x=np.where(a>=128);geometries.append({'face':face,'width_at_alpha128':int(np.ptp(x)+1),
            'height_above_y218':int(np.ptp(y)+1),'top':int(y.min()),'placement':{'x':0,'y':0,'scale':1}})
        source=next(after.glob(face+'-original.*'));sheet=Image.open(source).convert('RGB')
        # Original, short and long hairstyles: both ears, white and green
        # backgrounds, enlarged from the same 1:1 browser pixels, never repaint.
        checks=hairs
        ears=Image.new('RGB',(896,356*len(checks)),'#dedbd4');draw=ImageDraw.Draw(ears)
        for row,hair in enumerate(checks):
            offset=300*hairs.index(hair);draw.text((5,row*356+2),hair,font=FONT,fill='black')
            for col,(bg,box) in enumerate([(0,(16,108,70,190)),(0,(174,108,228,190)),(3,(16,108,70,190)),(3,(174,108,228,190))]):
                l,t,r,b=box;crop=sheet.crop((bg*240+l,offset+t,bg*240+r,offset+b))
                # 4x actual native pixels, with space between both ear crops.
                ears.paste(crop.resize((216,328),Image.Resampling.NEAREST),(col*224,row*356+24))
        ears.save(details/(face+'-ears.png'),optimize=True)
        links=[]
        for color in ['original','black','white']:
            p=next(after.glob(face+'-'+color+'.*'));links.append(f'<a href="{p.relative_to(REPORT)}">{color}: усі 8 зачісок × 4 фони</a>')
        sections.append(f'<section><h2>{html.escape(label)}</h2><p>x=0 · y=0 · scale=1. Контур вище y=218 не змінено.</p>'
            f'<a href="details/{face}-join.png"><img loading="lazy" src="details/{face}-join.png" alt="До і після: {label}"></a>'
            f'<h3>Вуха: короткі та довгі зачіски, біле й зелене тло, ×4</h3><a href="details/{face}-ears.png"><img loading="lazy" src="details/{face}-ears.png" alt="Крупні плани вух"></a>'
            f'<p>{" · ".join(links)}</p></section>')
    (REPORT/'head-geometry.json').write_text(json.dumps(geometries,ensure_ascii=False,indent=2)+'\n')
    document='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Палата 404 — нова жіноча база та вісім голів</title><style>body{background:#11151b;color:#eee;font:16px system-ui;max-width:1200px;margin:auto;padding:20px}a{color:#a5caff}img{max-width:100%;height:auto}section{border-top:1px solid #555;margin-top:32px;padding-top:12px}p{line-height:1.6}</style>
<h1>Нова жіноча база та перевірка восьми голів</h1><p><a href="README.md">Повний звіт</a>. Зображення отримані з фактичного compositor у index.html. ДО використовує збережені ресурси b00712b; ПІСЛЯ — нову базу. Збільшення крупних планів — nearest-neighbour, без генерації. Натисніть зображення для повного масштабу.</p>
<h2>Базовий аватар: однаковий масштаб 50%</h2><a href="details/base-full.png"><img src="details/base-full.png" alt="База до і після"></a>
<h2>Голова бази: білий, сірий, чорний, зелений</h2><a href="details/base-head.png"><img src="details/base-head.png" alt="Голова бази на чотирьох фонах"></a>
<p>Нова база з усіма зачісками: <a href="native-base/after-original.webp">original</a> · <a href="native-base/after-black.webp">black</a> · <a href="native-base/after-white.webp">white</a>.</p>
<p>Рядки матриць: без зачіски, каре з чубчиком, розкуйовджена, каре, два пучки, класична коротка, текстурована коротка, до плечей. Стовпці: білий, сірий, чорний, зелений фон.</p>
<p>Рудоволосе обличчя має вужчу форму й світліший/рожевіший тон у затвердженому джерелі; їх не змінювали. Проміжки між довгими пасмами збережені.</p>'''+''.join(sections)+'''
<section><h2>Лікарняна туніка на новій базі</h2><p><a href="clothing/result.json">Усі дев’ять варіантів перевірено</a>; одяг не змінено.</p><img loading="lazy" src="clothing/base-patient.png" alt="Нова база з тунікою"><img loading="lazy" src="clothing/face-alternative-patient.png" alt="Альтернативна голова з тунікою"></section>
<section><h2>Справжній гардероб</h2><p>Емуляція розміру вікна; фізичний телефон не використовувався.</p><a href="after-chromium/wardrobe-390.png"><img loading="lazy" src="after-chromium/wardrobe-390.png" alt="Гардероб 390 px"></a><a href="after-chromium/wardrobe-1440.png"><img loading="lazy" src="after-chromium/wardrobe-1440.png" alt="Гардероб 1440 px"></a></section></html>'''
    (REPORT/'gallery.html').write_text(document)


if __name__=='__main__':run()
