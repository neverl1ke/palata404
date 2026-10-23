"""Review gallery from the production renderer captures; never synthetic portraits."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import base64,html,json,re,mimetypes
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'review/female-ear-fit';P=ROOT/'review/female-five-hairstyles'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
rows=json.loads((P/'registration.json').read_text());corrections=json.loads((R/'corrections.json').read_text())
def pair(a,b,title,path):
 out=Image.new('RGB',(a.width+b.width,a.height+42),'#e9e5dd');d=ImageDraw.Draw(out);d.text((10,9),'ДО · '+title,font=font,fill='black');d.text((a.width+10,9),'ПІСЛЯ',font=font,fill='black');out.paste(a,(0,42));out.paste(b,(a.width,42));out.save(path,lossless=True)
parts=[]
for s in rows:
 k=s['key'];a=Image.open(R/f'before/{k}.png').convert('RGB');b=Image.open(P/f'{k}.png').convert('RGB')
 if k in ['pixie','jaw-bob']:
  assert (R/f'before/assets/{k}.png').read_bytes()==(ROOT/s['path']).read_bytes()
  continue
 pair(a,b,s['name'],R/f'{k}-before-after.webp')
 box=(130,105,385,300);pair(a.crop(box).resize((765,585)),b.crop(box).resize((765,585)),s['name']+' · 300%',R/f'{k}-ears-detail.webp')
 parts.append(f'<section><h2>{html.escape(s["name"])}</h2><img src="{k}-before-after.webp" alt="До та після"><details open><summary>Вуха, щоки й бічний вузол · 300%</summary><img src="{k}-ears-detail.webp" alt="Крупний план до та після"></details><details><summary>Усі 17 жіночих облич</summary><img src="../female-five-hairstyles/{k}-all-heads.webp" alt="17 реальних примірок"></details><details><summary>25 кольорів</summary><img src="../female-five-hairstyles/{k}-all-colors.webp" alt="Палітра"></details><details><summary>Білий, сірий, чорний і зелений фони</summary>'+''.join(f'<img src="../female-five-hairstyles/captures/{k}-original-{bg}.webp" alt="{bg}">' for bg in ['light','gray','black','green'])+'</details></section>')
s='''<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Палата 404 — правки трьох зачісок біля вух</title><style>body{max-width:1500px;margin:auto;padding:20px;background:#141a20;color:#eee;font:17px/1.5 system-ui}img{display:block;max-width:100%;height:auto;margin:16px 0}a{color:#abd9ff}section{border-top:1px solid #46505c;margin:32px 0;padding-top:16px}summary{padding:12px;background:#222b35;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Три правки посадки біля вух</h1><p>Піксі та каре до щелепи збережені байт у байт. Довгі хвилі розширені біля вух; у хвоста припасований правий виріз; зібрана коса зменшена на 16% навколо маківки, бічний вузол піднятий і наближений до вуха. Полотно, runtime-посадка, голови, тіла та кольори не змінені.</p><p>Кадри справжнього index.html через renderPaperDollAt; однаковий масштаб і положення до/після.</p><p><a href="standalone.html" download>Завантажити автономний HTML</a> · <a href="https://github.com/neverl1ke/palata404/blob/main/review/female-ear-fit/README.md">Звіт</a> · <a href="../../">Відкрити гру</a></p><img src="../female-five-hairstyles/five-comparison.png" alt="Усі п’ять зачісок">'''+''.join(parts)+'<section id="technical"><h2>Параметри відтворюваної правки</h2><pre>'+html.escape(json.dumps(corrections,ensure_ascii=False,indent=2))+'</pre></section></html>'
(R/'index.html').write_text(s)
def embed(m):
 p=(R/m.group(2)).resolve()
 if p.suffix not in ['.webp','.png']:return m.group(0)
 return m.group(1)+'data:'+mimetypes.guess_type(p.name)[0]+';base64,'+base64.b64encode(p.read_bytes()).decode()+m.group(3)
off=re.sub(r'((?:src|href)=")([^"]+)(")',embed,s.replace('<a href="standalone.html" download>Завантажити автономний HTML</a> · ',''));(R/'standalone.html').write_text(off)
print('gallery',len(re.findall('<img ',off)),'embedded images; bytes',len(off.encode()))
