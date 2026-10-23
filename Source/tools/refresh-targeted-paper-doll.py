"""Refresh release hashes while retaining earlier source contracts and local bounds."""
from pathlib import Path
import argparse,hashlib,json,importlib.util,re
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def blob(p):b=p.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
def read(p):return np.array(Image.open(p).convert('RGBA'))
def runs(mask):
 out=[]
 for y,row in enumerate(mask):
  change=np.diff(np.r_[False,row,False].astype(int));out.extend([y,int(l),int(r)] for l,r in zip(np.where(change==1)[0],np.where(change==-1)[0]))
 return out
p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);args=p.parse_args();snap=args.snapshot
spec=importlib.util.spec_from_file_location('audit',ROOT/'tools/audit-paper-doll-png.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
entries=[];cat=audit.catalog();changed={e['path'] for e in json.loads((ROOT/'review/paper-doll-targeted-fix/repairs.json').read_text())['files']}
for rel in audit.resources():
 before=read(snap/rel);after=read(ROOT/rel);y,x=np.mgrid[:before.shape[0],:before.shape[1]];aa=np.zeros(y.shape,dtype=bool);rgb=aa.copy()
 if rel in changed:
  if '/faces/masks/' in rel:aa=y<310
  elif rel=='base_female.png':rgb=(x>=340)&(x<605)&(y>=823)&(y<1105)
  elif '/hair/' in rel:
   item=next(i for i in cat['items'] if i.get('genderVariants',{}).get('male','').split('?')[0]==rel);place=item['placementByGender']['male'];fx=place['x']+(x+.5)*place['width']/before.shape[1];fy=place['y']+(y+.5)*place['height']/before.shape[0]
   aa=((fx<420)|(fx>528))&(fy>125) if item['id']=='hair-messy' else (((fx>393)&(fx<415)&(fy>133)&(fy<177))|((fx>531)&(fx<553)&(fy>131)&(fy<175)))
   rgb=aa.copy()
  else:
   m=before[:,:,3]>=128;band=(ndi.distance_transform_edt(m)<=7)&(ndi.distance_transform_edt(~m)<=7)
   aa=band&(y>=36)&(y<219);rgb=band&(y>=36)&(y<252)
   if rel.endswith('male_asian_head.png') and '/female_' not in rel:aa=y<280;rgb=y<280
   if rel.endswith('female_exhausted_head.png'):aa|=(y>=218)&(y<290);rgb|=(y>=218)&(y<290)
   if rel.endswith('alternative_head.png'):rgb|=(y>=20)&(y<251)&(x>=365)&(x<585)
 entry={'path':rel,'before_sha256':sha(snap/rel),'sha256':sha(ROOT/rel),'size':[before.shape[1],before.shape[0]],'changed':rel in changed,'allowed_alpha_runs':runs(aa),'allowed_rgb_runs':runs(rgb),'outside_alpha_sha256':digest(before[:,:,3][~aa].tobytes()),'outside_rgb_sha256':digest(before[:,:,:3][~rgb].tobytes())}
 if '/faces/' in rel and '/masks/' not in rel and Path(rel).name not in ['male_asian_head.png','male_alternative_head.png','female_alternative_head.png']:entry['core_rgb_sha256']=digest(before[90:205,435:515,:3].tobytes())
 if '/hair/' in rel and rel in changed:entry['retained_source_rgb_sha256']=digest(before[:,:,:3][after[:,:,3]>0].tobytes())
 entries.append(entry)
fixture=ROOT/'tests/fixtures/paper-doll-targeted-fix.json';fixture.write_text(json.dumps({'source_commit':'8bcf1830429008113c145e15c016a9bc709e35a1','files':entries},indent=2)+'\n')
geometry={i['id']:i.get('placementByGender') for i in cat['items'] if i['slot']=='hair'}
f=fixture;d=json.loads(f.read_text());d['hair_placements_before']=geometry;f.write_text(json.dumps(d,indent=2)+'\n')
# Keep independently checkable source face crops for landmark/tonal regressions.
folder=ROOT/'tests/fixtures/targeted-face-references';folder.mkdir(exist_ok=True)
for g,k in [('male','asian'),('male','alternative'),('female','alternative')]:Image.open(snap/f'assets/wardrobe/faces/{g}_{k}_head.png').crop((365,20,585,285)).save(folder/f'{g}_{k}.png')
for rel in changed:
 if '/hair/' in rel:Image.open(snap/rel).getchannel('A').save(folder/(Path(rel).stem+'-alpha.png'))
Image.open(snap/'base_female.png').crop((340,823,605,1105)).save(folder/'female_inner_thighs.png')
f=ROOT/'tests/fixtures/paper-doll-audit.json';d=json.loads(f.read_text())
for e in d['files']:
 if e['path'] not in changed:continue
 im=Image.open(ROOT/e['path']).convert('RGBA');a=np.array(im);e.setdefault('pre_targeted_fix_sha256',e['sha256']);e['sha256']=sha(ROOT/e['path'])
 for field,new in [('face_rgb_sha256',digest(im.convert('RGB').crop(e['face_rgb_box']).tobytes()) if 'face_rgb_box' in e else None),('protected_alpha17_sha256',digest(np.where(a[:,:,3]>=17,a[:,:,3],0).astype('uint8').tobytes())),('protected_opaque_rgb_sha256',digest(a[:,:,:3][a[:,:,3]>=240].tobytes()))]:
  if field in e:e.setdefault('pre_targeted_fix_'+field,e[field]);e[field]=new
 e['targeted_fix_contract']='paper-doll-targeted-fix.json'
f.write_text(json.dumps(d,indent=2)+'\n')
for name in ['hairstyles-pack-01.json','hairstyles-pack-02.json']:
 f=ROOT/'tests/fixtures'/name;d=json.loads(f.read_text())
 for name,e in d['files'].items():
  path=ROOT/'assets/wardrobe/hair'/name
  if str(path.relative_to(ROOT)) not in changed:continue
  e.setdefault('pre_targeted_fix_blob',e['blob']);e.update(blob=blob(path),bytes=path.stat().st_size);im=Image.open(path);e['bbox']=list(im.getchannel('A').point(lambda v:255 if v>=64 else 0).getbbox());e['transparent']=im.getchannel('A').histogram()[0]
 f.write_text(json.dumps(d,indent=2)+'\n')
for name in ['avatar-face-hair-update.json','face-neck-transitions.json']:
 f=ROOT/'tests/fixtures'/name;d=json.loads(f.read_text())
 for e in d['files']:
  if e['output'] not in changed:continue
  path=ROOT/e['output'];e.setdefault('pre_targeted_fix_sha256',e['sha256']);e['sha256']=sha(path);im=Image.open(path);e['integrated_alpha_sha256']=digest(im.getchannel('A').tobytes())
  if 'mask' in e:e['mask_sha256']=sha(ROOT/e['mask'])
  if 'protected_y' in e:e.setdefault('pre_targeted_fix_protected_sha256',e['protected_sha256']);e['protected_sha256']=digest(im.crop((0,0,941,e['protected_y'])).tobytes())
 f.write_text(json.dumps(d,indent=2)+'\n')
for f in [ROOT/'paper-doll-data.js',ROOT/'index.html',*list((ROOT/'art').glob('*.html')),ROOT/'tests/test_game.py',ROOT/'tests/game-logic.test.cjs']:
 s=f.read_text()
 for rel in audit.resources():s=re.sub(re.escape(rel)+r'\?v=[a-zA-Z0-9_-]+',rel+'?v='+sha(ROOT/rel)[:8],s)
 for rel in ['base_male.png','base_female.png','assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png']:s=re.sub("'"+re.escape(rel)+"': '[a-f0-9]{40}'","'"+rel+"': '"+blob(ROOT/rel)+"'",s)
 s=s.replace('paper-audit-1','paper-targeted-1');f.write_text(s)
text=fixture.read_text();fixture.write_text(re.sub(r'\[\s*\n\s*(\d+),\s*\n\s*(\d+),\s*\n\s*(\d+)\s*\n\s*\]',r'[\1,\2,\3]',text))
print('Updated local contracts for',len(changed),'PNG repairs;',len(entries),'resources checked')
