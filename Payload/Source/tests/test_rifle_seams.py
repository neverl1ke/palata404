"""Targeted source/alpha/restore guards; not an artistic acceptance."""
from pathlib import Path
import json,subprocess,hashlib,unittest
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';BASE='52bfbca'
def prior(p):return subprocess.check_output(['git','show',BASE+':'+p],cwd=R)
def read(p):return np.array(Image.open(p).convert('RGBA'))
class RifleSeamsTests(unittest.TestCase):
 def test_protected_base_rig_gameplay_and_other_weapons(self):
  for p in ['base_male.png','base_female.png','avatar-core/rigs/male_rig.json','avatar-core/rigs/female_rig.json','avatar-core/weapon-controller.mjs','avatar-core/relaxed-melee.mjs','avatar-core/skin.mjs','script.js','wardrobe.js','paper-doll-data.js']:
   self.assertEqual((R/p).read_bytes(),prior(p),p)
  a=json.loads(prior('avatar-core/equipment-weapons.json'));b=json.loads((C/'equipment-weapons.json').read_text());self.assertEqual(a['items'][1:],b['items'][1:]);self.assertEqual(a['items'][0]['attachmentByGender'],b['items'][0]['attachmentByGender'])
 def test_non_rifle_configuration_unchanged(self):
  for g in ['male','female']:
   a=json.loads(prior(f'avatar-core/{g}-preview.json'));b=json.loads((C/f'{g}-preview.json').read_text())
   for d in [a,b]:
    d.pop('rifleForegroundMode',None)
    for key in ['poseMeshVertexExtensions','poseMeshVertexOverrides','poseMeshExtensions','poseArtCompleteSurfaces','poseArtSurfaces']:
     if key in d:
      d[key]={k:v for k,v in d[key].items() if 'rifle-' not in k}
      if not d[key]:d.pop(key)
   self.assertEqual(a,b,g)
 def test_master_and_runtime_only_alpha(self):
  folder=C/'assets/weapons/user-ak47-20261026';self.assertEqual(hashlib.sha256((folder/'ak47-master.png').read_bytes()).hexdigest(),'891939f70b385def634c127f1999b22db92f55a3a6a80a99369fd01623b3104f');a=read(folder/'ak47-master.png');b=read(folder/'ak47-runtime-opaque.png');self.assertTrue(np.array_equal(a[:,:,:3],b[:,:,:3]));d=ndi.distance_transform_edt(a[:,:,3]>=128);self.assertTrue(np.array_equal(a[d<2.5],b[d<2.5]));self.assertTrue(np.all(b[d>=2.5,3]==255))
 def test_current_surface_topology_and_foreground_subset(self):
  for g in ['male','female']:
   c=json.loads((C/f'{g}-preview.json').read_text())
   for side in ['right','left']:
    complete=read(C/c['poseArtCompleteSurfaces']['rifle-'+side]);front=read(C/c['poseArtSurfaces']['art-front-rifle-'+side]);self.assertTrue(np.all(front[:,:,3]<=complete[:,:,3]),(g,side));self.assertTrue(np.array_equal(front[front[:,:,3]>0,:3],complete[front[:,:,3]>0,:3]))
    labels,n=ndi.label(complete[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labels.ravel());sizes[0]=0;self.assertLessEqual(int(sizes.sum()-sizes.max()),20,(g,side,'remote material'))
 def test_accepted_knife_reference(self):
  subprocess.run(['python','tools/check-approved-grips.py'],cwd=R,capture_output=True,check=True)
 def test_reexport_exact(self):
  paths=[C/f'{g}-preview.json' for g in ['male','female']]+[C/'equipment-weapons.json']+[p for g in ['male','female'] for p in (C/f'assets/{g}/rifle-seams').glob('*.png')]+[C/'assets/weapons/user-ak47-20261026/ak47-runtime-opaque.png']
  h=lambda:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
  before=h()
  for s in ['prepare-rifle-seams.py','prepare-ak47-opacity.py']:subprocess.run(['python','tools/'+s],cwd=R,capture_output=True,check=True)
  self.assertEqual(before,h())
