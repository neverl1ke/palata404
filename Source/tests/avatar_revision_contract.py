from tests.requested_source_contract import pre_integration_bytes
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
 if path=='avatar-core/rigs/female_rig.json':
  import json
  assert_female_donor_revision(t,json.loads(subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT)),json.loads((ROOT/path).read_text()))
 elif path in OWNERSHIP_PATHS:assert_ownership_only(t,path,revision)
 else:t.assertEqual(pre_integration_bytes(path),subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT),path)
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

def assert_female_donor_revision(t,old,new):
 """New donor pose art may change only authored pose fields, never the body rig."""
 allowed={'poses','pistolOneHand','poseArt','anatomyProjection','posePolicy'}
 t.assertEqual({k:v for k,v in old.items() if k not in allowed},{k:v for k,v in new.items() if k not in allowed})
 t.assertEqual(new['posePolicy'],{'instant':True,'oneHandPistol':True})
 t.assertEqual(set(new['poseArt']),{'melee','pistol','rifle'})
 t.assertEqual(set(new['poseArt']['pistol']),{'right'})
 t.assertEqual(set(new['poseArt']['rifle']),{'right','left'})


def assert_foundation_preview_revision(t,old,new):
 """Explicit approved derivative slots, preserving all skeletal/game controls.
 No archived golden image or resource hash is updated by this contract.
 """
 a=copy.deepcopy(old);b=copy.deepcopy(new)
 expected={f'{role}{p}-{side}':f'assets/male/foundation-cleanup/{p}-{side}-{kind}.png' for p,sides in [('rifle',['right','left']),('pistol',['right']),('melee',['right'])] for side in sides for role,kind in [('art-','arm'),('art-front-','front')]}
 t.assertEqual(b['poseArtSurfaces'],expected)
 t.assertEqual(b['meleeMotion'],{'mode':'forward-wrist','upperDegrees':.035,'foreDegrees':.12,'handDegrees':1.6,'cycleMs':4000})
 t.assertEqual(b.pop('poseCalibration',None),{'melee':{'right':[241,920]}})
 for k in ['runtimeSurfaces','runtimeSource','poseMeshExtensions','meleeMotion','poseArtCompleteSurfaces']:b.pop(k,None)
 b['poseArtSurfaces']=a.get('poseArtSurfaces',{})
 for pose in ['melee','pistol','rifle']:
  t.assertEqual(b['weapons'][pose]['primary'],a['weapons'][pose]['primary']);t.assertEqual(b['weapons'][pose]['support'],a['weapons'][pose]['support'])
  t.assertEqual(b['weapons'][pose]['image'],f'assets/male/foundation-cleanup/{pose}-weapon.png')
  for k in ['image','size','scale','angle','offset','art','stock','trigger']:
   if k in a['weapons'][pose]:b['weapons'][pose][k]=a['weapons'][pose][k]
   else:b['weapons'][pose].pop(k,None)
 t.assertEqual(a,b)

def assert_active_foundation_contacts(t,page,mode='coverage'):
 """Independent affine/raster probes for the explicitly different clean props.
 Old donor-photo pixel coordinates remain in the legacy branch and fixtures.
 Here expectations come from the registered material source and opaque authored
 hand cells, never from the actual output being asserted.
 """
 import json
 from PIL import ImageDraw
 from scipy import ndimage as ndi
 page.evaluate('()=>{let e=avatarLab.engine;e.time=0;e.setOptions({breathing:false,background:"transparent"});e.setLayerVisible("weapon",true)}')
 data=page.evaluate('()=>({g:avatarLab.engine.gender,pose:avatarLab.engine.pose,rig:avatarLab.engine.rig,cfg:avatarLab.engine.posePreview,f:avatarLab.engine.frame,png:avatarLab.engine.canvas.toDataURL().split(",")[1]})')
 import base64
 actual=np.array(Image.open(io.BytesIO(base64.b64decode(data.pop('png')))))
 def matrix(m):return np.array([[m[0],m[2],m[4]],[m[1],m[3],m[5]],[0,0,1.]])
 if mode=='material':
  definition=data['cfg']['weapons'][data['pose']];source=np.array(Image.open(ROOT/'avatar-core'/definition['image']));mask=ndi.minimum_filter(source[:,:,3],size=5)>=250
  ys,xs=np.where(mask);positions=np.stack([xs+.5,ys+.5,np.ones(len(xs))]);world=matrix(data['f']['weapon']['matrix'])@positions
  for side,art in data['rig']['poseArt'][data['pose']].items():
   front=np.array(Image.open(ROOT/'avatar-core'/data['cfg']['poseArtSurfaces']['art-front-'+data['pose']+'-'+side]));fy,fx=np.where(front[:,:,3]>=32);bx,by,_,_=art['mesh']['bounds'];native=np.stack([fx+bx+.5,fy+by+.5,np.ones(len(fx))]);delta=matrix(data['f']['arms'][side]['hand'])@np.linalg.inv(matrix(art['bind']['hand']));hand=delta@native;grip=np.array(data['f']['arms'][side]['grip']);radius=np.linalg.norm(hand[:2].T-grip,axis=1).max()+5;mask2=np.linalg.norm(world[:2].T-grip,axis=1)>radius;xs,ys,world=xs[mask2],ys[mask2],world[:,mask2]
  t.assertGreater(len(xs),30,'independent unoccluded material probes required')
  errors=[]
  for i in np.linspace(0,len(xs)-1,30).astype(int):
   x,y=np.floor(world[:2,i]).astype(int);t.assertGreaterEqual(int(actual[y,x,3]),235);uv=np.linalg.inv(matrix(data['f']['weapon']['matrix']))@np.array([x+.5,y+.5,1]);u,v=uv[:2]-.5;expected=np.array([ndi.map_coordinates(source[:,:,k].astype(float),[[v],[u]],order=1)[0] for k in range(3)]);error=float(np.abs(actual[y,x,:3].astype(float)-expected).max());errors.append(error);t.assertLessEqual(error,12,(data['g'],data['pose'],int(xs[i]),int(ys[i]),'new complete material source mismatch'))
  return {'material_probes':len(errors),'max_rgb_error':max(errors)}
 if mode=='forearm':page.evaluate('avatarLab.engine.setLayerVisible("weapon",false)');actual=np.array(Image.open(io.BytesIO(base64.b64decode(page.evaluate('avatarLab.engine.canvas.toDataURL().split(",")[1]')))))
 if mode=='forearm':
  samples=0
  for side,art in data['rig']['poseArt'][data['pose']].items():
   mesh=art['mesh'];bx,by,x1,y1=mesh['bounds'];source=np.array(Image.open(ROOT/'avatar-core'/data['cfg']['poseArtSurfaces']['art-'+data['pose']+'-'+side]));safe=ndi.distance_transform_edt(source[:,:,3]>=250)>4;el=np.array(art['anchors']['elbow']);wr=np.array(art['anchors']['wrist']);axis=wr-el;length=np.linalg.norm(axis);deltas={k:matrix(data['f']['transforms']['torso'] if k=='torso' else data['f']['arms'][side][k])@np.linalg.inv(matrix(art['bind'][k])) for k in ['torso','upper','fore','hand']}
   for tri in mesh['triangles']:
    vs=np.array([mesh['vertices'][i] for i in tri]);src=vs[:,:2];uv=src.mean(axis=0);along=np.dot(uv-el,axis)/(length*length)
    if not .25<along<.75:continue
    ix,iy=np.rint(uv-[bx,by]).astype(int)
    if not (2<=ix<source.shape[1]-2 and 2<=iy<source.shape[0]-2 and safe[iy,ix]):continue
    patch=source[iy-1:iy+2,ix-1:ix+2,:3].astype(int)
    if np.any(np.ptp(patch,axis=(0,1))>16):continue
    dst=[]
    for x,y,s,e,w in vs:
     q=np.array([x,y,1.]);v={k:mat@q for k,mat in deltas.items()};dst.append(((1-s)*v['torso']+s*((1-w)*((1-e)*v['upper']+e*v['fore'])+w*v['hand']))[:2])
    dst=np.array(dst);pixel=np.floor(dst.mean(axis=0)).astype(int);edges=np.column_stack([dst[1]-dst[0],dst[2]-dst[0]])
    if abs(np.linalg.det(edges))<1e-6:continue
    bary=np.linalg.solve(edges,pixel+.5-dst[0])
    if (bary<0).any() or bary.sum()>1:continue
    srcpoint=src[0]+bary[0]*(src[1]-src[0])+bary[1]*(src[2]-src[0]);u,v=srcpoint-[bx,by]-.5;expected=np.array([ndi.map_coordinates(source[:,:,k].astype(float),[[v],[u]],order=1)[0] for k in range(3)]);x,y=pixel;t.assertLessEqual(float(np.abs(actual[y,x,:3].astype(float)-expected).max()),12,(data['g'],data['pose'],side,'blended forearm UV colour mismatch'));samples+=1
    if samples>=30:break
  t.assertGreater(samples,10,'independent forearm interior samples must exist');return {'forearm_source_samples':samples}

 count=0
 for side,art in data['rig']['poseArt'][data['pose']].items():
  mesh=art['mesh'];bx,by,x1,y1=mesh['bounds'];kind='fore' if mode=='forearm' else 'hand';source=np.array(Image.open(ROOT/'avatar-core'/data['cfg']['poseArtSurfaces'][('art-' if kind=='fore' else 'art-front-')+data['pose']+'-'+side]));coverage=Image.new('L',(x1-bx,y1-by));dr=ImageDraw.Draw(coverage)
  for tri in mesh['triangles']:
   vs=[mesh['vertices'][i] for i in tri]
   if all(v[2]==1 and (v[4]==1 if kind=='hand' else v[3]==1 and v[4]==0) for v in vs):dr.polygon([(v[0]-bx,v[1]-by) for v in vs],fill=255)
  mask=(np.array(coverage)>0)&(source[:,:,3]>=250);mask=ndi.distance_transform_edt(mask)>2
  delta=matrix(data['f']['arms'][side][kind])@np.linalg.inv(matrix(art['bind'][kind]));local=delta.copy();local[:2,2]+=delta[:2,:2]@np.array([bx,by])
  if kind=='hand':
   expected=np.array(Image.fromarray((mask*255).astype('uint8')).transform((941,1672),Image.Transform.AFFINE,tuple(np.linalg.inv(local)[:2].ravel()),Image.Resampling.BILINEAR));valid=expected>=250;count+=int(valid.sum());t.assertTrue(np.all(actual[:,:,3][valid]>=235),(data['g'],data['pose'],side,'missing opaque distal hand paint'))
   if mode=='hand-color':
    py,px=np.where(valid);samples=0
    for i in np.linspace(0,len(px)-1,min(100,len(px))).astype(int):
     x,y=px[i],py[i];uv=np.linalg.inv(local)@np.array([x+.5,y+.5,1]);u,v=uv[:2]-.5;ix,iy=np.rint([u,v]).astype(int)
     if not (2<=ix<source.shape[1]-2 and 2<=iy<source.shape[0]-2):continue
     patch=source[iy-1:iy+2,ix-1:ix+2,:3].astype(int)
     if np.any(np.ptp(patch,axis=(0,1))>16):continue
     expected=np.array([ndi.map_coordinates(source[:,:,k].astype(float),[[v],[u]],order=1)[0] for k in range(3)]);t.assertLessEqual(float(np.abs(actual[y,x,:3].astype(float)-expected).max()),12,(data['g'],data['pose'],side,'active independent hand source RGB'));samples+=1
    t.assertGreater(samples,10,'hand colour probes must exist')
  else:
   ys,xs=np.where(mask)
   if len(xs)<20:continue
   count+=len(xs)
   for i in np.linspace(0,len(xs)-1,15).astype(int):
    point=local@np.array([xs[i],ys[i],1]);x,y=np.rint(point[:2]).astype(int);t.assertLessEqual(int(np.abs(actual[y,x,:3].astype(int)-source[ys[i],xs[i],:3].astype(int)).max()),12,(data['g'],data['pose'],side,'active forearm texture must survive registration'))
 if mode=='coverage' and count==0:
  # Female pistol has blended wrist weights, not fully rigid hand cells.
  # Project every safe source hand pixel through the independently evaluated UV mesh.
  for side,art in data['rig']['poseArt'][data['pose']].items():
   mesh=art['mesh'];bx,by,_,_=mesh['bounds'];source=np.array(Image.open(ROOT/'avatar-core'/data['cfg']['poseArtSurfaces']['art-front-'+data['pose']+'-'+side]));safe=ndi.distance_transform_edt(source[:,:,3]>=250)>3;ys,xs=np.where(safe);points=np.stack([xs+bx+.5,ys+by+.5]);deltas={k:matrix(data['f']['transforms']['torso'] if k=='torso' else data['f']['arms'][side][k])@np.linalg.inv(matrix(art['bind'][k])) for k in ['torso','upper','fore','hand']}
   for tri in mesh['triangles']:
    vs=np.array([mesh['vertices'][i] for i in tri]);src=vs[:,:2];edges=np.column_stack([src[1]-src[0],src[2]-src[0]])
    if abs(np.linalg.det(edges))<1e-6:continue
    uv=np.linalg.solve(edges,points-src[0,:,None]);inside=(uv[0]>.02)&(uv[1]>.02)&(uv.sum(axis=0)<.98)
    if not inside.any():continue
    dst=[]
    for x,y,weight,e,w in vs:
     q=np.array([x,y,1.]);v={k:m@q for k,m in deltas.items()};dst.append(((1-weight)*v['torso']+weight*((1-w)*((1-e)*v['upper']+e*v['fore'])+w*v['hand']))[:2])
    dst=np.array(dst);out=dst[0,:,None]+np.column_stack([dst[1]-dst[0],dst[2]-dst[0]])@uv[:,inside];px,py=np.floor(out).astype(int);count+=len(px);t.assertTrue(np.all(actual[py,px,3]>=235),(data['g'],data['pose'],side,'blended source hand coverage'))
 t.assertGreater(count,100,(data['g'],data['pose'],mode,'source-owned contact/forearm probes must exist'))
 if mode=='coverage':
  for side in ['right']+(['left'] if data['pose']=='rifle' else []):
   x,y=np.rint(data['f']['arms'][side]['grip']).astype(int);t.assertGreaterEqual(int(actual[y,x,3]),235,(data['g'],data['pose'],side,'grip aperture'))
 return {'opaque_source_contact_pixels':count}
