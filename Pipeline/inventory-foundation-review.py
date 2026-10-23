"""Read-only independent resource and evidence inventory of the frozen baseline."""
from pathlib import Path
import json,hashlib,csv,io
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';B=R.parent/'avatar-foundation-baseline';G=R/'review/female-donor-arm-pass/Gallery'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
raw=(O/'Inputs/review-coverage.csv').read_text(encoding='utf-8-sig').replace('\\r\\n','\n');rows=list(csv.DictReader(io.StringIO(raw)));images=[r for r in rows if r['type']!='.webm'];coverage=[]
for page in range((len(images)+35)//36):
 sheet=Image.new('RGB',(1440,1500),'#444');d=ImageDraw.Draw(sheet)
 for i,row in enumerate(images[page*36:page*36+36]):
  p=G/row['file'];im=Image.open(p).convert('RGBA');im.thumbnail((235,215));x=i%6*240;y=i//6*250;sheet.paste(im,(x+(240-im.width)//2,y+25),im);d.text((x+2,y+2),row['file'][:36],font=font,fill='white');coverage.append({**row,'baseline':'c2822a7','evidence_sheet':f'contact-{page}.jpg','action':'overview; targeted defects individually tracked in audit register'})
 sheet.save(O/'Before'/f'contact-{page}.jpg',quality=88)
active=[]
for g in ['male','female']:
 rig=json.loads((B/f'avatar-core/rigs/{g}_rig.json').read_text());cfg=json.loads((B/f'avatar-core/{g}-preview.json').read_text())
 for pose,sides in rig['poseArt'].items():
  for side,a in sides.items():
   for key,slot in [('image','art-'),('frontImage','art-front-')]:
    path=cfg.get('poseArtSurfaces',{}).get(f'{slot}{pose}-{side}',a[key]);p=B/'avatar-core'/path;im=Image.open(p);active.append({'gender':g,'pose':pose,'side':side,'role':key,'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':im.size,'mesh_bounds':a['mesh']['bounds']})
 for pose,a in cfg['weapons'].items():
  p=B/'avatar-core'/a['image'];active.append({'gender':g,'pose':pose,'role':'weapon','path':a['image'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':Image.open(p).size,'primary':a['primary'],'support':a.get('support')})
(O/'Evidence/active-resource-map.json').write_text(json.dumps(active,indent=2)+'\n');(O/'Evidence/coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n');print(len(active),'active arm/front/weapon entries;',len(images),'image files on overview sheets')
