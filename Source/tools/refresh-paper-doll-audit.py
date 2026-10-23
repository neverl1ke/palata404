"""Refresh integrated hashes while retaining immutable pre-audit evidence."""
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit',ROOT/'tools/audit-paper-doll-png.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def blob(p):b=p.read_bytes();return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);a=p.parse_args();contracts=[]
for rel in audit.resources():
 dest=ROOT/rel;src=a.snapshot/rel
 if not src.exists():continue
 old=np.array(Image.open(src).convert('RGBA'));new=np.array(Image.open(dest).convert('RGBA'));record={'path':rel,'before_sha256':sha(src),'sha256':sha(dest),'size':list(Image.open(dest).size),'before_bbox128':audit.bbox(old[:,:,3]>=128),'before_area128':int((old[:,:,3]>=128).sum())}
 if '/hair/' in rel:
  record['protected_alpha17_sha256']=digest(np.where(old[:,:,3]>=17,old[:,:,3],0).astype('uint8').tobytes());record['protected_opaque_rgb_sha256']=digest(old[:,:,:3][old[:,:,3]>=240].tobytes())
 elif '/faces/' in rel and '/masks/' not in rel or rel.startswith('base_'):
  record['face_rgb_box']=[435,90,515,205];record['face_rgb_sha256']=digest(Image.open(src).convert('RGB').crop(record['face_rgb_box']).tobytes())
 contracts.append(record)
for file in ['hairstyles-pack-01.json','hairstyles-pack-02.json']:
 f=ROOT/'tests/fixtures'/file;d=json.loads(f.read_text())
 for name,e in d['files'].items():
  path=ROOT/'assets/wardrobe/hair'/name;e.setdefault('source_blob',e['blob']);e['blob']=blob(path);e['bytes']=path.stat().st_size;im=Image.open(path);e['bbox']=list(im.getchannel('A').point(lambda v:255 if v>=64 else 0).getbbox());e['transparent']=im.getchannel('A').histogram()[0]
 f.write_text(json.dumps(d,indent=2)+'\n')
for file in ['avatar-face-hair-update.json','face-neck-transitions.json']:
 f=ROOT/'tests/fixtures'/file;d=json.loads(f.read_text())
 for e in d['files']:
  path=ROOT/e['output'];e.setdefault('pre_edge_audit_sha256',e['sha256']);e['sha256']=sha(path);e['integrated_alpha_sha256']=digest(Image.open(path).getchannel('A').tobytes())
  if 'mask' in e:e['mask_sha256']=sha(ROOT/e['mask'])
  if 'protected_y' in e:
   e.setdefault('pre_edge_audit_protected_sha256',e['protected_sha256']);e['protected_sha256']=digest(Image.open(path).crop((0,0,941,e['protected_y'])).tobytes())
 d['edge_audit_reference']='dbbcddff2f79a3393271ac6afc4d261221d9b77e';f.write_text(json.dumps(d,indent=2)+'\n')
f=ROOT/'tests/fixtures/paper-doll-audit.json';f.write_text(json.dumps({'source_commit':'dbbcddff2f79a3393271ac6afc4d261221d9b77e','files':contracts},indent=2)+'\n')
paths=audit.resources()
for f in [ROOT/'paper-doll-data.js',ROOT/'index.html',*list((ROOT/'art').glob('*.html')),ROOT/'tests/test_game.py',ROOT/'tests/game-logic.test.cjs']:
 s=f.read_text()
 for rel in paths:s=re.sub(re.escape(rel)+r'\?v=[a-zA-Z0-9_-]+',rel+'?v='+sha(ROOT/rel)[:8],s)
 if f.name=='test_game.py':
  for rel in ['base_male.png','base_female.png','assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png']:
   s=re.sub("'"+re.escape(rel)+"': '[a-f0-9]{40}'","'"+rel+"': '"+blob(ROOT/rel)+"'",s)
  for g,oldhash in [('male','d9eb9e5445d22a2559f136acf8ed47c088dbb3b386c8699c57ab2e2ccad3c30b'),('female','bb36d987af092f4a60b5305d067bab3a3a89b963aff96af7f55d77b54ed843a7')]:s=s.replace(oldhash,sha(ROOT/f'assets/wardrobe/faces/{g}_asian_head.png'))
  s=s.replace("entry['reference_alpha_sha256']","entry['integrated_alpha_sha256']").replace("entry['source_alpha_sha256']","entry['integrated_alpha_sha256']")
 f.write_text(s)
for f in [ROOT/'index.html',ROOT/'art/patient-tunic.html']:
 s=f.read_text();s=re.sub(r'((?:style\.css|paper-doll-data\.js|paper-doll\.js|hair-color\.js|wardrobe\.js|script\.js)\?v=)[a-zA-Z0-9_-]+',r'\g<1>paper-audit-1',s);f.write_text(s)
print('Updated hash manifests and',len(contracts),'independent baseline contracts')
