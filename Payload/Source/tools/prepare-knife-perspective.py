"""Local horizontal knife grasp, identical master/scale for both genders."""
from pathlib import Path
import hashlib,json
import cv2,numpy as np
from PIL import Image
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';D=R/'review/knife-perspective'
W,H=941,1672;yy,xx=np.indices((H,W))
def load(p):return np.array(Image.open(p).convert('RGBA'))

def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)

def matrix(v):return np.array([[v[0],v[2],v[4]],[v[1],v[3],v[5]],[0,0,1]])

def warp_rgba(a,m):
 a=a.astype('float32');a[:,:,:3]*=a[:,:,3:4]/255
 b=cv2.warpAffine(a,np.array(m),(W,H),flags=cv2.INTER_CUBIC);b[:,:,3]=np.clip(b[:,:,3],0,255)
 b[:,:,:3]=np.clip(b[:,:,:3]*255/np.maximum(b[:,:,3:4],1e-6),0,255)
 return np.rint(b).astype('uint8')

def authored_map(art,frame):
 delta={k:matrix(frame['transforms']['torso'] if k=='torso' else frame['arms']['right'][k])@np.linalg.inv(matrix(art['bind'][k])) for k in ['upper','fore','hand','torso']}
 v=np.array(art['mesh']['vertices']);native=[]
 for x,y,s,e,w in v:
  p=np.array([x,y,1]);t,u,f,h=[delta[k]@p for k in ['torso','upper','fore','hand']]
  native.append((t*(1-s)+s*((u*(1-e)+f*e)*(1-w)+h*w))[:2])
 mapx=np.zeros((H,W),dtype='float32');mapy=mapx.copy();native=np.array(native,dtype='float32')
 for ids in art['mesh']['triangles']:
  uv=v[ids,:2].astype('float32');m=cv2.getAffineTransform(uv,native[ids]);x0,y0=np.floor(uv.min(0)).astype(int);x1,y1=np.ceil(uv.max(0)).astype(int)
  yq,xq=np.mgrid[y0:y1+1,x0:x1+1];mask=np.zeros(xq.shape,dtype='uint8');cv2.fillConvexPoly(mask,np.rint(uv-[x0,y0]).astype('int32'),1)
  for out,row in [(mapx,m[0]),(mapy,m[1])]:
   region=out[y0:y1+1,x0:x1+1];region[mask>0]=(row[0]*xq+row[1]*yq+row[2])[mask>0]
 return mapx,mapy

def full(a,bounds):
 if a.shape[:2]==(H,W):return a.copy()
 out=np.zeros((H,W,4),dtype='uint8');x,y,x1,y1=bounds;out[y:y1,x:x1]=a;return out

def matte_hand(a):
 rgb=a[:,:,:3].astype(float);bg=np.median(np.concatenate([rgb[:12].reshape(-1,3),rgb[-12:].reshape(-1,3)]),axis=0)
 d=np.linalg.norm(rgb-bg,axis=2);core=d>40
 _,idx=ndi.distance_transform_edt(~core,return_indices=True);fg=rgb[idx[0],idx[1]];vec=bg-fg
 alpha=np.clip(np.sum((bg-rgb)*vec,axis=2)/np.maximum(np.sum(vec*vec,axis=2),1),0,1);alpha[d<7]=0;alpha[core]=1
 out=np.zeros_like(a);out[:,:,3]=np.rint(alpha*255);out[:,:,:3]=np.rint(np.clip((rgb-(1-alpha[:,:,None])*bg)/np.maximum(alpha[:,:,None],1e-6),0,255));out[alpha==0]=0
 # Bright painted nail/skin highlights are opaque material, not backdrop.
 # Keep exterior and natural grasp-hole antialiasing; restore only interior.
 interior=ndi.distance_transform_edt(alpha>=.5)>3
 out[interior,:3]=np.rint(rgb[interior]);out[interior,3]=255
 return out

def remap_rgba(a,mapx,mapy):
 a=a.astype('float32');a[:,:,:3]*=a[:,:,3:4]/255
 b=cv2.remap(a,mapx,mapy,cv2.INTER_CUBIC);b[:,:,3]=np.clip(b[:,:,3],0,255)
 b[:,:,:3]=np.clip(b[:,:,:3]*255/np.maximum(b[:,:,3:4],1e-6),0,255)
 return np.rint(b).astype('uint8')

def surface_binding(art,frame,target):
 delta={k:matrix(frame['transforms']['torso'] if k=='torso' else frame['arms']['right'][k])@np.linalg.inv(matrix(art['bind'][k])) for k in ['upper','fore','hand','torso']}
 vertices=np.array(art['mesh']['vertices']);native=[]
 for x,y,s,e,w in vertices:
  p=np.array([x,y,1]);t,u,f,h=[delta[k]@p for k in ['torso','upper','fore','hand']]
  native.append((t*(1-s)+s*((u*(1-e)+f*e)*(1-w)+h*w))[:2])
 native=np.array(native)
 for ids in art['mesh']['triangles']:
  a=np.vstack([native[ids].T,np.ones(3)])
  if abs(np.linalg.det(a))<1e-8:continue
  weights=np.linalg.solve(a,[*target,1])
  if np.min(weights)>=-1e-7:
   return {'indices':ids,'weights':weights.tolist(),'sourcePoint':(weights@vertices[ids,:2]).tolist()}
 raise ValueError('Real grasp lies outside the corrective mesh; do not use an invented anchor')

# Local arm restoration and reusable semantic grasp; approved knife view retained.
captures=json.loads((D/'Evidence/before-captures.json').read_text())['cases']
catalog=json.loads((C/'equipment-weapons.json').read_text());knife=next(i for i in catalog['items'] if i['id']=='gear-knife');records=[]
# A selected derived camera view need not be the calibration master itself.
reference_catalog=json.loads((D/'Sources/baseline-equipment-weapons.json').read_text())
reference_master=next(i for i in reference_catalog['items'] if i['id']=='gear-knife')['image']
assert hashlib.sha256((C/reference_master).read_bytes()).hexdigest()=='d977ed117aab103aa984ba55642c525869d2ae40ea167287d805d53d91f54fdf'
for gender in ['male','female']:
 baseline=json.loads((D/f'Sources/baseline-{gender}-preview.json').read_text());cfg=json.loads((C/f'{gender}-preview.json').read_text());rig=json.loads((C/f'rigs/{gender}_rig.json').read_text());art=rig['poseArt']['melee']['right'];bounds=art['mesh']['bounds']
 art['mesh']['triangles']+=baseline.get('poseMeshExtensions',{}).get('melee-right',[])
 frame=next(r['frame']['frame'] for r in captures if r['gender']==gender and r['pose']=='melee' and r['time']==0 and r['weapon'])
 mapx,mapy=authored_map(art,frame)
 reg=json.loads((D/f'Evidence/{gender}-art-registration.json').read_text());assert reg['inliers']>20 and .3<reg['uniform_scale']<.4
 context=warp_rgba(load(D/f'Sources/{gender}-local-edit.png'),reg['matrix_native']);native_context=context.copy()
 painted=remap_rgba(context,mapx,mapy)
 before=full(load(C/baseline['poseArtCompleteSurfaces']['melee-right']),bounds);out=before.copy()
 # The artist restores local material; retain original anatomy/scale and pixels
 # outside the authorized biceps/elbow/forearm range, including the shoulder.
 start=420 if gender=='male' else 350;end=835 if gender=='male' else 805
 weight=smooth((yy-start)/25)*(1-smooth((yy-end)/25))*(before[:,:,3]>0)
 # Matting extraction: edge RGB is sampled from actual opaque restored material,
 # not the light background; never globally blur the skin illustration.
 support=before[:,:,3]>=240
 skin=(painted[:,:,0]>1.07*painted[:,:,1])&(painted[:,:,0]>1.15*painted[:,:,2])
 valid_skin=support&skin;_,material=ndi.distance_transform_edt(~valid_skin,return_indices=True)
 contaminated=(before[:,:,3]>0)&~skin
 clean_rgb=painted[material[0],material[1],:3];painted[contaminated,:3]=clean_rgb[contaminated]
 _,nearest=ndi.distance_transform_edt(~support,return_indices=True)
 interior=painted[nearest[0],nearest[1],:3];fringe=before[:,:,3]<240
 painted[fringe,:3]=interior[fringe]
 oldlab=cv2.cvtColor(before[:,:,:3],cv2.COLOR_RGB2LAB).astype(float);lab=cv2.cvtColor(painted[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)
 match=support&(yy>start+20)&(yy<start+70)&(weight>.5)
 shift=np.clip(np.median(oldlab[match],axis=0)-np.median(lab[match],axis=0),[-7,-4,-4],[7,4,4]);painted[:,:,:3]=cv2.cvtColor(np.rint(np.clip(lab+shift,0,255)).astype('uint8'),cv2.COLOR_LAB2RGB)
 out[:,:,:3]=np.rint(before[:,:,:3]*(1-weight[:,:,None])+painted[:,:,:3]*weight[:,:,None])
 # Trace and antialias a single continuous source-material contour.
 # Median filtering removes isolated segmentation notches; RGB remains sharp.
 left=np.full(H,np.nan);right=left.copy()
 for row in range(H):
  xs=np.flatnonzero(before[row,:,3]>=128)
  if len(xs):left[row]=xs[0];right[row]=xs[-1]+1
 valid=np.flatnonzero(np.isfinite(left))
 left=np.interp(np.arange(H),valid,left[valid]);right=np.interp(np.arange(H),valid,right[valid])
 left=ndi.gaussian_filter1d(ndi.median_filter(left,size=7),1.1);right=ndi.gaussian_filter1d(ndi.median_filter(right,size=7),1.1)
 clean=np.clip(xx-left[:,None]+.5,0,1)*np.clip(right[:,None]-xx-.5,0,1)*255
 alpha_weight=smooth((yy-start-25)/18)*(1-smooth((yy-end+15)/18))
 out[:,:,3]=np.rint(before[:,:,3]*(1-alpha_weight)+clean*alpha_weight)
 # Extrapolate restored opaque material into its subpixel alpha fringe.
 core=(out[:,:,3]>=240)&(before[:,:,3]>=240);_,near=ndi.distance_transform_edt(~core,return_indices=True)
 edge=(out[:,:,3]>0)&(before[:,:,3]<240)&(alpha_weight>.5)
 rgb=out[near[0],near[1],:3];out[edge,:3]=rgb[edge]
 labels,n=ndi.label(out[:,:,3]>0,np.ones((3,3)))
 peaks=np.array(ndi.maximum(out[:,:,3],labels,range(n+1)))
 dust=np.isin(labels,np.flatnonzero(peaks<=8))&(labels>0);out[dust]=0
 out[out[:,:,3]==0]=0
 # Pose-owned torso: the restored arm never carries torso pixels into motion.
 tb=rig['segments']['torso']['bounds'];tx,ty,tx1,ty1=tb
 torso=load(C/baseline.get('poseTorsoSurfaces',{}).get('melee',baseline['runtimeSurfaces']['torso']));t=torso.copy();Y,X=np.indices(t.shape[:2]);Y+=ty;X+=tx
 native_torso=native_context[ty:ty1,tx:tx1,:3]
 if gender=='female':
  # Actual black-fabric boundary from the unchanged base, not a made-up breast
  # pasted over the moving arm. Recover that shape behind the arm's own layer.
  base=load(R/'base_female.png')[ty:ty1,tx:tx1]
  area=(X>=330)&(X<=370)&(Y>=375)&(Y<=515)
  blend=smooth((X-330)/7)*(1-smooth((X-360)/10))*smooth((Y-375)/20)*(1-smooth((Y-495)/20))
  skin=(base[:,:,:3].mean(2)>75)&(native_torso.mean(2)>75)
  t[:,:,:3]=np.rint(t[:,:,:3]*(1-(blend*skin)[:,:,None])+native_torso*(blend*skin)[:,:,None])
  # Reconstruct the actual registered outer material boundary, not an
  # old rectangular skin reserve or base-pose cloth dangling into the gap.
  row_left=np.array([np.flatnonzero(row>=128)[0]+tx if np.any(row>=128) else tx1 for row in torso[:,:,3]],float)
  reserve=4*np.maximum(0,1-((np.arange(ty,ty1)-412)/44)**2)**2
  line=ndi.gaussian_filter1d(row_left,1)-reserve
  for row,y in enumerate(range(ty,ty1)):
   if not 472<=y<=515:continue
   rgb=native_context[y,330:375,:3].astype(float)
   background=np.linalg.norm(rgb-[248,245,237],axis=1)<28
   gaps=np.flatnonzero(background)
   if len(gaps):line[row]=330+gaps[-1]+1
  line=ndi.gaussian_filter1d(line,.65)
  coverage=np.clip(X-line[:,None]+.5,0,1)*255
  fade=smooth((Y-378)/8)*(1-smooth((Y-505)/10))
  patch=(Y>=378)&(Y<=515)&(X>=330)&(X<line[:,None]+10)
  target=native_torso.copy()
  sample=np.clip(np.ceil(line+2).astype(int)-tx,0,t.shape[1]-1)
  safe=native_torso[np.arange(t.shape[0]),sample]
  fringe=X<line[:,None]+2
  target[fringe]=np.broadcast_to(safe[:,None,:],target.shape)[fringe]
  weight=fade*(1-smooth((X-line[:,None]-4)/6))*patch
  t[:,:,:3]=np.rint(t[:,:,:3]*(1-weight[:,:,None])+target*weight[:,:,None])
  t[:,:,3][patch]=np.rint(t[:,:,3][patch]*(1-fade[patch])+coverage[patch]*fade[patch])
 else:
  # The torso-side axilla fold is owned by this pose's torso, never by the arm.
  radius=((X-346)/22)**2+((Y-467)/64)**2;blend=smooth((1-radius)*2)*(t[:,:,3]>=250)
  t[:,:,:3]=np.rint(t[:,:,:3]*(1-blend[:,:,None])+native_torso*blend[:,:,None])
 folder=C/f'assets/{gender}/knife-perspective';folder.mkdir(exist_ok=True);outputs=[]
 # The grip profile is anatomical and reusable for this relaxed-wrap pose.
 # Its boundary is stored in scene pixels and inverse-registered to skin UVs.
 depth=json.loads((D/f'Sources/{gender}-grip-profile.json').read_text())
 arc=np.array(depth['contactArc'],float);us=np.linspace(0,1,65)[:,None]
 points=(1-us)**3*arc[0]+3*(1-us)**2*us*arc[1]+3*(1-us)*us**2*arc[2]+us**3*arc[3]
 # Curved inner-index boundary with subpixel antialiasing, not a hard polygon
 # slicing the back of the hand. Only item-covered pixels use this front mask.
 dx,dy=(0,0) if gender=='female' else (8,35)
 border=np.vstack([points,[[270+dx,907+dy],[278+dx,887+dy],[272+dx,863+dy],[250+dx,851+dy]]])
 high=np.zeros((H*3,W*3),dtype='uint8');cv2.fillPoly(high,[np.rint(border*3).astype('int32')],255)
 mask=cv2.resize(high,(W,H),interpolation=cv2.INTER_AREA);authored_mask=cv2.remap(mask,mapx,mapy,cv2.INTER_LINEAR)
 for role in ['complete','arm','front']:
  image=out.copy()
  if role=='arm':
   previous=full(load(C/baseline['poseArtSurfaces']['art-melee-right']),bounds);image[:,:,3]=np.minimum(out[:,:,3],previous[:,:,3])
  if role=='front':
   hand_only=smooth((yy-art['anchors']['wrist'][1]+6)/6)
   image[:,:,3]=np.rint(out[:,:,3].astype(float)*(1-authored_mask/255)*hand_only).astype('uint8')
  image[image[:,:,3]==0]=0
  if gender=='male':image=image[bounds[1]:bounds[3],bounds[0]:bounds[2]]
  path=folder/f'melee-right-{role}.png';Image.fromarray(image).save(path);outputs.append(str(path.relative_to(R)))
  cfg['poseArtCompleteSurfaces' if role=='complete' else 'poseArtSurfaces']['melee-right' if role=='complete' else ('art-front-' if role=='front' else 'art-')+'melee-right']=str(path.relative_to(C))
 tp=folder/'melee-torso.png';t[t[:,:,3]==0]=0;Image.fromarray(t).save(tp);cfg.setdefault('poseTorsoSurfaces',{})['melee']=str(tp.relative_to(C));outputs.append(str(tp.relative_to(R)))
 cfg.setdefault('gripProfiles',{})['relaxed-wrap']={'pose':'melee','side':'right','scope':'hand-only','frontImage':str((folder/'melee-right-front.png').relative_to(C)),'layerContract':['complete-hand','whole-item','front-fingers-and-dorsal-hand'],'rearPart':'thumb-side-of-contact-arc','completeHandImage':str((folder/'melee-right-complete.png').relative_to(C))}
 attachment=knife['attachmentByGender'][gender];attachment['gripProfile']='relaxed-wrap'
 if gender=='female':
  # Native inner-index contact arc midpoint, inspected on the actual unarmed hand.
  arc=np.array(depth['contactArc'],float);u=.5;target=((1-u)**3*arc[0]+3*(1-u)**2*u*arc[1]+3*(1-u)*u*u*arc[2]+u**3*arc[3]).tolist();attachment['surfaceGrip']=surface_binding(art,frame,target)
 cfg['weapons']['melee'].update(attachment);(C/f'{gender}-preview.json').write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
 records.append({'gender':gender,'outputs':outputs,'registration':reg,'tone_LAB_shift':shift.tolist(),'hand_scale_changed':False,'approved_master_changed':False,'knife_scale':attachment['scale'],'grasp':attachment['surfaceGrip'],'knife_view_status':'OPEN: image tool declined new view','only_pose':'melee','alpha_corridor':[start+25,end-5],'detached_weak_pixels_removed':int(dust.sum())})
(C/'equipment-weapons.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n');(D/'Evidence/export.json').write_text(json.dumps(records,indent=2)+'\n');print(records)
