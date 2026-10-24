"""Readable local review pages built only from real game captures."""
import html,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'review/female-heads-new-library'
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
STYLE='body{margin:24px auto;padding:0 16px;max-width:1280px;background:#131820;color:#eee;font:17px/1.5 system-ui}a{color:#aaccff}img{max-width:100%;height:auto}nav{display:flex;flex-wrap:wrap;gap:15px}section{margin:28px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}figure{margin:0;background:#222a34;padding:10px}figcaption{padding:5px}button,select{font:inherit}h1{font-size:28px}'
def page(title,body):return '<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style><h1>'+html.escape(title)+'</h1><nav><a href="index.html">Усі обличчя</a><a href="README.md">Звіт</a><a href="SOURCE_MAPPING.md">Відповідність файлів</a></nav>'+body+'</html>'
def image(path,caption):return f'<figure><a href="{path}"><img loading="lazy" src="{path}" alt="{html.escape(caption)}"></a><figcaption>{html.escape(caption)}</figcaption></figure>'
def build():
 entries=json.loads((D/'integration-manifest.json').read_text())['files'];geometry=json.loads((D/'geometry/result.json').read_text());hairs=geometry['genders']['female']['hairs'];O=D/'overviews';O.mkdir(exist_ok=True);cards=[]
 records=[json.loads(l) for l in (D/'captures/records.jsonl').read_text().splitlines()] if (D/'captures/records.jsonl').exists() else []
 for e in entries:
  sheet=Image.new('RGB',(1600,848),'#dedbd4');draw=ImageDraw.Draw(sheet)
  for i,h in enumerate(hairs):
   path=D/'geometry/female'/e['id']/h/'original.webp';x=i%4*400;y=i//4*424;sheet.paste(Image.open(path),(x,y+24));draw.text((x+3,y+3),h,font=FONT,fill='black')
  sheet.save(O/(e['kind']+'-hairstyles.webp'),lossless=True)
  body='<p>Зображення отримано виробничим рендерером у справжньому index.html. Натисніть на зображення для оригінального розміру. ДО — реєстрація нового портрета до корекції тону та шийного RGB-стику.</p>'
  comp='review-captures/'+e['kind']+'-comparison.webp'
  if (D/comp).exists():body+='<section>'+image(comp,'ДО / ПІСЛЯ, однаковий масштаб')+'</section>'
  body+='<section>'+image('overviews/'+e['kind']+'-hairstyles.webp','Усі жіночі зачіски — оригінальний колір')+'</section>'
  detail='review-captures/'+e['kind']+'/full.webp'
  if (D/detail).exists():body+='<details><summary>Повний зріст</summary>'+image(detail,'Повний зріст')+'</details>'
  body+='<h2>Чотири фони — вуха, шия та світле волосся</h2><div class="grid">'
  for bg in ['white','gray','black','green']:
   for h in ['hair-none','hair-messy','hair-shoulder-length','hair-bob-bangs']:
    p='review-captures/'+e['kind']+'/'+bg+'-'+h+'.webp'
    if (D/p).exists():body+=image(p,bg+' / '+h)
  body+='</div><h2>Оригінальний, чорний і білий кольори</h2><div class="grid">'
  for r in records:
   if r['face']==e['id'] and r['path']:body+=image(r['path'],r['hair']+' / '+r['color'])
  body+='</div>'
  (D/(e['kind']+'.html')).write_text(page(e['name'],body))
  cards.append('<figure><a href="'+e['kind']+'.html"><img src="geometry/female/'+e['id']+'/hair-none/original.webp" alt="'+e['name']+'"><figcaption>'+e['name']+' — відкрити примірки</figcaption></a></figure>')
 body='<p>8 нових жіночих голів додано окремими варіантами. Чоловічі голови й затверджені жіночі обличчя збережено. Це локальна контрольна галерея, не опублікована гра.</p><div class="grid">'+''.join(cards)+'</div><h2>Вуха ×4 і шийні стики ×2</h2>'+image('ear-neck-details.webp','Крупні плани реальних ігрових рендерів')
 for p in sorted((D/'review-captures').glob('mobile-*.webp')):body+=image(str(p.relative_to(D)),p.stem)
 if (D/'review-captures/desktop-wardrobe.webp').exists():body+=image('review-captures/desktop-wardrobe.webp','Гардероб на комп’ютері')
 (D/'index.html').write_text(page('Палата 404 — нові жіночі обличчя',body))
 # Markdown remains readable in GitHub and editor previews, without JavaScript.
 md=['# Контрольна галерея','', '[Відкрити HTML у браузері](index.html). Натисніть на знімок для збільшення.','']
 for e in entries:md+=['## '+e['name'],'',f"![Усі зачіски](overviews/{e['kind']}-hairstyles.webp)",'']
 (D/'GALLERY.md').write_text('\n'.join(md).rstrip()+'\n')
 print('Built',len(entries),'face pages and index')
if __name__=='__main__':build()
