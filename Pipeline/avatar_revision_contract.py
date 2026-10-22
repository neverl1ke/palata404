"""Explicit permitted changes in the hidden-surface/ownership follow-up.
Everything outside these narrowly named fields is still frozen.
"""
import copy,io,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OWNERSHIP_PATHS={'avatar-core/assets/male/'+n+'.png' for n in ['leftUpper','leftFore','leftHand','leftArmSkin','leftHandSkin','lower']}
def assert_rig_revision(t,old,new):
 a=copy.deepcopy(old);b=copy.deepcopy(new)
 t.assertEqual(b['anatomyProjection']['melee']['right'],[1,1]);t.assertEqual(b['poses']['melee']['right'],[241,906])
 a['anatomyProjection']['melee']['right']=b['anatomyProjection']['melee']['right'];a['poses']['melee']['right']=b['poses']['melee']['right']
 for k in ['leftUpper','leftFore','leftHand','lower']:a['segments'][k]['sha256']=b['segments'][k]['sha256']
 for k,n in [('image','leftArmSkin'),('handImage','leftHandSkin')]:
  t.assertEqual(b['skinMeshes']['left'][k],'assets/male/'+n+'.png');a['skinMeshes']['left'][k]=b['skinMeshes']['left'][k]
 a.pop('poseArt');b.pop('poseArt');t.assertEqual(a,b)
def assert_ownership_only(t,path,revision):
 old=np.array(Image.open(io.BytesIO(subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT))));new=np.array(Image.open(ROOT/path));t.assertEqual(old.shape,new.shape)
 # Exact localization of the demonstrated moving thigh edge, not a broad
 # allowance for changes elsewhere in an arm.
 import json
 rig=json.loads((ROOT/'avatar-core/rigs/male_rig.json').read_text());name=Path(path).stem
 bounds=rig['skinMeshes']['left']['bounds'] if name.endswith('Skin') else rig['segments'][name]['bounds'];x,y,x1,y1=bounds
 yy,xx=np.indices(old.shape[:2]);allowed=(xx+x>=660)&(xx+x<680)&(yy+y>=840)&(yy+y<1040)
 t.assertTrue(np.array_equal(old[~allowed],new[~allowed]),path)
 changed=np.any(old!=new,2)
 if name=='lower':
  base=np.array(Image.open(ROOT/'base_male.png'));t.assertTrue(np.array_equal(new[changed],base[y:y1,x:x1][changed]))
 else:t.assertTrue(np.all(new[changed]==0),path)

def assert_frozen_or_ownership(t,path,revision):
 if path in OWNERSHIP_PATHS:assert_ownership_only(t,path,revision)
 else:t.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT),path)
def runtime_point(page,pose,x,y,side='right',kind='hand',data=None):
 """Independently map fixed source probes after the authorized melee change.
 numpy affine inversion, no renderer utility imported. Non-melee stays exact.
 """
 p=np.array([x+10,y+26,1.])
 if pose!='melee':return tuple(np.rint(p[:2]).astype(int))
 data=data if data is not None else page.evaluate('()=>({rig:avatarLab.engine.rig,f:avatarLab.engine.frame})');f=data['f'];rig=data['rig']
 def mat(v):return np.array([[v[0],v[2],v[4]],[v[1],v[3],v[5]],[0,0,1.]])
 if kind=='item':q=mat(f['weapon']['matrix'])@p
 else:
  art=rig['poseArt'][pose][side]
  if kind=='hand':q=mat(f['arms'][side]['hand'])@np.linalg.inv(mat(art['bind']['hand']))@p
  else:
   vs=np.array(art['mesh']['vertices']);xs=np.unique(vs[:,0]);ys=np.unique(vs[:,1]);ix=np.clip(np.searchsorted(xs,p[0])-1,0,len(xs)-2);iy=np.clip(np.searchsorted(ys,p[1])-1,0,len(ys)-2);fx=(p[0]-xs[ix])/(xs[ix+1]-xs[ix]);fy=(p[1]-ys[iy])/(ys[iy+1]-ys[iy]);grid=vs.reshape(len(ys),len(xs),-1);weights=(grid[iy,ix,2:]*(1-fx)+grid[iy,ix+1,2:]*fx)*(1-fy)+(grid[iy+1,ix,2:]*(1-fx)+grid[iy+1,ix+1,2:]*fx)*fy;s,e,w=weights
   qs={k:mat(f['transforms']['torso'] if k=='torso' else f['arms'][side][k])@np.linalg.inv(mat(art['bind'][k]))@p for k in ['torso','upper','fore','hand']};q=(1-s)*qs['torso']+s*((1-w)*((1-e)*qs['upper']+e*qs['fore'])+w*qs['hand'])
 return tuple(np.rint(q[:2]).astype(int))
