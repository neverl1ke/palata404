"""Build diagnostic plots from actual game screenshots and exact runtime alpha."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as ndi
import numpy as np,json,base64,re,mimetypes,html
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/female-five-fit-audit';P=ROOT/'review/female-five-hairstyles';FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
rows=json.loads((P/'registration.json').read_text());corrections=json.loads((R/'corrections.json').read_text())
def caption_pair(before,after,title,path):
 sheet=Image.new('RGB',(before.width+after.width,max(before.height,after.height)+42),'#e9e5dd');d=ImageDraw.Draw(sheet);d.text((10,9),'ДО · '+title,font=FONT,fill='black');d.text((before.width+10,9),'ПІСЛЯ',font=FONT,fill='black');sheet.paste(before,(0,42));sheet.paste(after,(before.width,42));sheet.save(path,lossless=True)
parts=[];measure=[]
for s in rows:
 key=s['key'];before=Image.open(R/'before/captures'/f'{key}-young.webp').convert('RGB');after=Image.open(P/f'{key}.png').convert('RGB');caption_pair(before,after,s['name'],R/f'{key}-before-after.webp');caption_pair(before.crop((130,80,380,330)).resize((500,500)),after.crop((130,80,380,330)).resize((500,500)),s['name']+' · 200%',R/f'{key}-detail.webp')
 a=np.array(Image.open(R/'before/assets'/f'{key}.png'))[:,:,3];b=np.array(Image.open(ROOT/s['path']))[:,:,3]
 def boundary(alpha):
  ink=alpha>=128;return ink&~ndi.binary_erosion(ink)
 old=Image.fromarray(boundary(a).astype('uint8')*255).crop((222,-20,722,500));new=Image.fromarray(boundary(b).astype('uint8')*255).crop((222,-20,722,500));old=np.array(old)>0;new=np.array(new)>0
 layer=np.zeros((520,500,4),dtype='uint8');layer[old&~new]=[35,130,234,255];layer[new&~old]=[238,138,48,255];layer[new&old]=[135,135,135,190]
 overlay=Image.alpha_composite(after.convert('RGBA'),Image.fromarray(layer));overlay.save(R/f'{key}-contours.png')
 c=next(x for x in corrections if x['key']==key);status='Локально виправлено' if c['changed_pixels'] else 'Геометрію збережено: підтвердженого дефекту не знайдено'
 parts.append(f'<section><h2>{html.escape(s["name"])}</h2><p>{status}. Змінено {c["changed_pixels"]}пікселів.</p><img src="{key}-before-after.webp" alt="До та після"><details><summary>Крупний план200% та контури</summary><img src="{key}-detail.webp" alt="200%"><p>Синій — тільки ДО, помаранчевий — тільки ПІСЛЯ, сірий — збіг контурів. Це діагностична накладка, не ігровий PNG.</p><img src="{key}-contours.png" alt="Контури"></details><h3>Усі17жіночих голів</h3><img src="../female-five-hairstyles/{key}-all-heads.webp" alt="17голів"><details><summary>Усі25кольорів</summary><img src="../female-five-hairstyles/{key}-all-colors.webp" alt="25кольорів"></details></section>')
 if key=='pixie':
  caption_pair(before.crop((150,100,350,180)).resize((800,320)),after.crop((150,100,350,180)).resize((800,320)),'Скроні та вуха · 400%',R/'pixie-400.webp')
  for y in [85,95,105,115,125,135,145,155]:
   x0=np.flatnonzero(a[y]>=128);x1=np.flatnonzero(b[y]>=128);measure.append({'y':y,'before':[int(x0[0]),int(x0[-1])],'after':[int(x1[0]),int(x1[-1])],'width_before':int(x0[-1]-x0[0]+1),'width_after':int(x1[-1]-x1[0]+1)})
(R/'pixie-widths.json').write_text(json.dumps(measure,ensure_ascii=False,indent=2)+'\n')
table='<table><tr><th>Y</th><th>X до</th><th>X після</th><th>Ширина до / після</th></tr>'+''.join(f'<tr><td>{m["y"]}</td><td>{m["before"]}</td><td>{m["after"]}</td><td>{m["width_before"]} / {m["width_after"]}px</td></tr>' for m in measure)+'</table>'
s='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата404 — посадка п’яти зачісок</title><style>body{margin:auto;padding:20px;max-width:1500px;background:#141a20;color:#eee;font:17px/1.5 system-ui}img{display:block;max-width:100%;height:auto;margin:15px 0}a{color:#abd9ff}section{border-top:1px solid #46505c;margin:36px 0;padding-top:20px}summary{cursor:pointer;padding:12px;background:#222b35}td,th{padding:8px;border:1px solid #46505c}table{border-collapse:collapse}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Посадка п’яти жіночих зачісок</h1><p>Реальні кадри index.html через ігровий renderPaperDollAt. Голова, тіло та старі зачіски не змінені. Локально виправлено піксі й пасмо довгих хвиль; інші три варіанти залишено піксельно незмінними.</p><p><a href="standalone.html" download>Завантажити автономний HTML</a> · <a href="README.md">Технічний звіт</a></p><img src="../female-five-hairstyles/five-comparison.png" alt="П’ять зачісок"><h2>Піксі: ширина за анатомічними зонами</h2>'''+table+'<img src="pixie-400.webp" alt="Піксі400%">'+''.join(parts)+'<section id="technical"><h2>Технічні параметри</h2><p>Полотно941×1672 RGBA, runtime x0/y0/scale1. Незмінні голова176px по вухах, X385…560, вісь472.5, маківка33. Локальна монотонна деформація премультиплікованого RGBA; без генерації, глобального розтягування й CSS-підгонки.</p><pre>'+html.escape(json.dumps(corrections,ensure_ascii=False,indent=2))+'</pre></section></html>'
(R/'index.html').write_text(s)
def embed(m):
 p=(R/m.group(2)).resolve()
 if not p.is_file() or p.suffix.lower() not in ['.png','.webp','.jpg','.jpeg']:return m.group(0)
 return m.group(1)+'data:'+mimetypes.guess_type(p.name)[0]+';base64,'+base64.b64encode(p.read_bytes()).decode()+m.group(3)
offline=s.replace('<a href="standalone.html" download>Завантажити автономний HTML</a> · ','').replace('href="README.md"','href="#technical"');offline=re.sub(r'((?:src|href)=")([^"]+)(")',embed,offline);(R/'standalone.html').write_text(offline);print('Standalone bytes',(R/'standalone.html').stat().st_size)
