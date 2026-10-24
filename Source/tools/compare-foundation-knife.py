"""Synchronized motion comparison from actual captured Canvas previews."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageSequence
R=Path(__file__).resolve().parents[1];G=R/'review/avatar-foundation-cleanup/Gallery'
for g in ['male','female']:
 if not (G/f'Dense/after-{g}-melee-True.webp').exists():continue
 outputs=[G/f'{g}-knife-motion-before-after.webp',G/f'{g}-knife-wrist-motion-before-after.webp']
 if all(p.exists() for p in outputs) and min(p.stat().st_mtime for p in outputs)>max((G/f'Dense/{v}-{g}-melee-True.webp').stat().st_mtime for v in ['before','after']):continue
 before=Image.open(G/f'Dense/before-{g}-melee-True.webp');after=Image.open(G/f'Dense/after-{g}-melee-True.webp');assert before.n_frames==after.n_frames==80
 full=[];close=[]
 for i in range(80):
  row=[];details=[]
  for src,label in [(before,'BEFORE c2822a7'),(after,'AFTER — wrist + knife')]:
   src.seek(i);im=src.convert('RGBA');bg=Image.new('RGBA',im.size,'#f8f5ed');bg.alpha_composite(im);tile=Image.new('RGB',(400,739),'#eee9df');tile.paste(bg.convert('RGB'),(0,28));ImageDraw.Draw(tile).text((8,7),label,fill='black');row.append(tile)
   # Same world-space crop, includes elbow, wrist and knife; resized for visibility.
   box=(45,210,150,465) if g=='male' else (45,200,150,450);part=bg.crop(box).resize((315,(box[3]-box[1])*3));detail=Image.new('RGB',(315,part.height+28),'#eee9df');detail.paste(part.convert('RGB'),(0,28));ImageDraw.Draw(detail).text((8,7),label,fill='black');details.append(detail)
  frame=Image.new('RGB',(800,739));frame.paste(row[0],(0,0));frame.paste(row[1],(400,0));full.append(frame);c=Image.new('RGB',(630,details[0].height));c.paste(details[0],(0,0));c.paste(details[1],(315,0));close.append(c)
 for name,frames in [('motion-before-after',full),('wrist-motion-before-after',close)]:frames[0].save(G/f'{g}-knife-{name}.webp',save_all=True,append_images=frames[1:],duration=[50]*80,loop=0,lossless=True,method=0)
 print(g,'80 synchronized before/after frames',flush=True)
