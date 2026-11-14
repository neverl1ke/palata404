"""Show the actual production render and original/candidate cloth detail."""
from pathlib import Path
import json
import shutil
from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parents[1]
D = R / 'review/pajama-art-release-20261114'
A = Path('/workspace/artifacts/pajama-art-release-20261114')
A.mkdir(exist_ok=True)
C = json.loads((D / 'render-checks.json').read_text())
assert C['captureComplete'] and not C['artworkRoutesMocked']
old = json.loads((R / 'review/pajama-waist-occlusion-20261114/capture-checks.json').read_text())
before = {(r['gender'],r['pose']):r for r in old['records'] if r['stage']=='after' and r['kind']=='pair'}
index = {(r['kind'],r['gender'],r['pose']):r for r in C['records']}
BG = '#e8e2d3'; INK = '#362e26'
font = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
poses = [('idle','спокій'),('melee','ніж'),('rifle','автомат')]
def flat(im):
    out = Image.new('RGBA', im.size, BG); out.alpha_composite(im.convert('RGBA')); return out.convert('RGB')
def full(kind='full', previous=False):
    out = Image.new('RGB',(1560,1680),BG);dr=ImageDraw.Draw(out)
    title = 'Комплект до обробки тону' if previous else {'full':'Піжама — узгоджений тон і чіткість','shirt':'Сорочки — шість поз','pants':'Штани — шість поз','footwear':'Капці — шість поз'}[kind]
    dr.text((18,14),title,font=font(31),fill=INK)
    dr.text((18,55),'Фактичний рендер гри · незмінні аватари та прозорі контури',font=font(19),fill=INK)
    for row,g in enumerate(('male','female')):
        for col,(p,label) in enumerate(poses):
            x=col*520;y=92+row*788
            dr.text((x+16,y),('Чоловік' if g=='male' else 'Жінка')+' · '+label,font=font(24),fill=INK)
            path=before[g,p]['frames'][0]['fullFramePath'] if previous else index[kind,g,p]['frames'][0]['path']
            im=flat(Image.open(R/path).crop((100,0,1200,1672)));im.thumbnail((510,735),Image.Resampling.LANCZOS)
            out.paste(im,(x+(520-im.width)//2,y+39))
    return out
full(previous=True).save(A/'01-before-finish.png')
for n,kind in enumerate(('full','shirt','pants','footwear'),2):full(kind).save(A/f'{n:02d}-{kind}-six-poses.png')
# Native-resolution source detail, enlarged identically, no new artwork.
out=Image.new('RGB',(1280,1460),BG);dr=ImageDraw.Draw(out)
dr.text((18,12),'Матеріали — до / після, однакове збільшення',font=font(28),fill=INK)
patches=[('top-idle','сорочка',(380,430,620,620)),('pants','штани',(350,970,590,1160)),('footwear','капець',(500,1490,740,1680))]
for row,g in enumerate(('male','female')):
    for col,(part,label,box) in enumerate(patches):
        for k,stage in enumerate(('originals','candidate')):
            x=col*425+7;y=86+row*675+k*320
            dr.text((x,y-27),('Чоловік' if g=='male' else 'Жінка')+' · '+label+' · '+('до' if k==0 else 'після'),font=font(17),fill=INK)
            im=flat(Image.open(D/f'{stage}/{g}/{part}.png').crop(box));im.thumbnail((406,295),Image.Resampling.LANCZOS)
            # Enlarge the exact same crop equally; preserve its aspect ratio.
            im=im.resize((min(406,round(im.width*1.55)),min(295,round(im.height*1.55))),Image.Resampling.LANCZOS)
            out.paste(im,(x,y))
out.save(A/'06-materials-before-after.png')
frames=[]
for phase in range(16):
    out=Image.new('RGB',(990,1140),BG);dr=ImageDraw.Draw(out)
    dr.text((12,8),'Фактичний цикл дихання · 3,6 с',font=font(25),fill=INK)
    for row,g in enumerate(('male','female')):
        for col,(p,label) in enumerate(poses):
            x=col*330;y=50+row*540
            dr.text((x+7,y),('Чоловік' if g=='male' else 'Жінка')+' · '+label,font=font(18),fill=INK)
            out.paste(flat(Image.open(R/index['full',g,p]['frames'][phase]['thumb'])),(x,y+26))
    frames.append(out)
frames[0].save(A/'07-breathing-cycle.webp',save_all=True,append_images=frames[1:],duration=225,loop=0,lossless=True,method=4)
html='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Піжама — художнє завершення</title><style>body{margin:0;background:#e8e2d3;color:#362e26;font:17px/1.5 system-ui}main{max-width:1500px;margin:auto;padding:18px}img{display:block;max-width:100%;height:auto}section{border-top:1px solid #b5a18a;margin-top:24px}h1{font-size:28px}h2{font-size:23px}a{color:#3a5565}</style><main><h1>Піжама — художнє завершення та інтеграція</h1><p>Узгоджено сірий відтінок тканини сорочки, штанів і капців. Незначно посилено лише вже наявні деталі тканини; природне освітлення й різницю матеріалів збережено. Підошви залишилися теплими. Обробка походить від найкращих зареєстрованих PNG, без повторного розтягування, зміни прозорості чи нової генерації дизайну.</p><p>Це стримане покращення. Відсутню у вихіднику мікрофактуру не вигадували; слабкий мікроконтраст не означає відновлення втрачених ниток тканини. Чоловічі капці зберігають щільніший повстяний матеріал, жіночі — тонший тканий верх.</p><p>Перевірено 510 фактичних кадрів: комплект, кожен із трьох предметів окремо та аватар без одягу, по шість поз і 17 фаз на варіант. Полотно, alpha одягу, тіло, руки й пози незмінні. У повному комплекті характеристики, інвентар, екіпірування та save збіглися з попереднім контролем. Для маски пояса збережено точні погоджені контури; вона діє лише з цією сорочкою. Додано належні задні частини в змішаному legacy-режимі.</p><p>17 фаз покривають чинний спільний цикл дихання 3,6 с. Окремої ходьби чи анімації бойового замаху тут немає. Перевірки незалежних рецензентів і підсумок інтеграції наведено в матеріалах релізу.</p>'''
for name,title in [('01-before-finish.png','До обробки'),('02-full-six-poses.png','Після — весь комплект'),('06-materials-before-after.png','Зблизька: тон і фактура'),('03-shirt-six-poses.png','Сорочки окремо'),('04-pants-six-poses.png','Штани окремо'),('05-footwear-six-poses.png','Капці окремо'),('07-breathing-cycle.webp','У русі')]:
    html+=f'<section><h2>{title}</h2><a href="{name}"><img src="{name}" alt="{title}"></a></section>'
(A/'pajama-art-release.html').write_text(html+'</main></html>')
for name in ('finish-manifest.json','release-manifest.json','render-checks.json'):
    shutil.copy2(D/name,A/name)
print(A)
