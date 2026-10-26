"""Register local artistic repair and extract only rifle arm material.

Original character PNGs, other poses, rigs, engine and knife grips unchanged.
Source is a local edit of the actual current no-weapon render; no replacement
character or substitute weapon is used. Preserve immutable before sources.
"""
from pathlib import Path
import ast,json,hashlib,copy
import numpy as np,cv2
from PIL import Image
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';D=R/'review/rifle-arm-integrity';W,H=941,1672;yy,xx=np.indices((H,W))
for node in ast.parse((R/'tools/prepare-knife-perspective.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ['matrix','authored_map','remap_rgba','full','smooth']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'rifle-utilities','exec'))
def load(p):return np.array(Image.open(p).convert('RGBA'))
REVIEW=R/'review/rifle-seams'

def full_grid(art):
 v=np.array(art['mesh']['vertices']);xs=np.unique(v[:,0]);ys=np.unique(v[:,1]);lookup={(x,y):i for i,(x,y,*_) in enumerate(v)};tri=[]
 for y0,y1 in zip(ys[:-1],ys[1:]):
  for x0,x1 in zip(xs[:-1],xs[1:]):
   keys=[(x0,y0),(x1,y0),(x0,y1),(x1,y1)]
   if all(p in lookup for p in keys):a,b,c,d=[lookup[p] for p in keys];tri.extend([[a,b,c],[b,d,c]])
 return tri
def register(src,target):
 sift=cv2.SIFT_create(nfeatures=5000)
 region=np.zeros((H,W),np.uint8);region[40:290,330:620]=255;region[950:1580,250:720]=255;region[730:900,320:630]=255
 a,da=sift.detectAndCompute(cv2.cvtColor(src[:,:,:3],cv2.COLOR_RGB2GRAY),region);b,db=sift.detectAndCompute(cv2.cvtColor(target[:,:,:3],cv2.COLOR_RGB2GRAY),region)
 matches=[x for x,y in cv2.BFMatcher().knnMatch(da,db,k=2) if x.distance<.7*y.distance]
 assert len(matches)>=12,'Insufficient unchanged-body features for source registration'
 p=np.float32([a[m.queryIdx].pt for m in matches]);q=np.float32([b[m.trainIdx].pt for m in matches]);m,mask=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=2)
 scale=float(np.hypot(m[0,0],m[1,0]));assert .97<scale<1.03 and int(mask.sum())>=10,(scale,int(mask.sum()))
 rgba=src.astype('float32');rgba[:,:,:3]*=rgba[:,:,3:4]/255;warped=cv2.warpAffine(rgba,m,(W,H),flags=cv2.INTER_CUBIC)
 warped[:,:,:3]=np.clip(warped[:,:,:3]*255/np.maximum(warped[:,:,3:4],1e-6),0,255);warped=np.rint(np.clip(warped,0,255)).astype('uint8')
 return warped,{'matrix':m.tolist(),'uniform_scale':scale,'inliers':int(mask.sum()),'matches':len(matches)}
def foreground(src):
 rgb=src[:,:,:3].astype(float);bg=np.median(np.concatenate([rgb[280:800,15:35].reshape(-1,3),rgb[280:800,905:925].reshape(-1,3)]),axis=0)
 distance=np.linalg.norm(rgb-bg,axis=2);solid=distance>45;_,near=ndi.distance_transform_edt(~solid,return_indices=True);f=rgb[near[0],near[1]];v=bg-f
 alpha=np.clip(np.sum((bg-rgb)*v,2)/np.maximum(np.sum(v*v,2),1),0,1);alpha[solid]=1;alpha[distance<12]=0
 out=src.copy();out[:,:,3]=np.rint(alpha*255);out[:,:,:3]=np.rint(np.clip((rgb-(1-alpha[:,:,None])*bg)/np.maximum(alpha[:,:,None],1e-6),0,255));out[alpha==0]=0
 strong=out[:,:,3]>=240;distance,nearest=ndi.distance_transform_edt(~strong,return_indices=True)
 fringe=(out[:,:,3]>0)&~strong
 color=out[nearest[0],nearest[1],:3];out[fringe,:3]=color[fringe]
 out[(out[:,:,3]>0)&(out[:,:,3]<32)&(distance>2)]=0
 return out
cases=json.loads((D/'Sources/baseline-rifle-frames.json').read_text())['cases'];records=[]
for gender in ['male','female']:
 path=D/f'Sources/{gender}-rifle-edit.png'
 if not path.exists():continue
 original=load(D/f'Sources/before-{gender}-no-weapon.png');raw=load(path);assert raw.shape==original.shape
 context,reg=register(raw,original);matte=foreground(context)
 # Match only the overall chromatic baseline measured on unchanged torso,
 # not the previously mismatched donor arms or arbitrary per-arm brightness.
 lab=cv2.cvtColor(context[:,:,:3],cv2.COLOR_RGB2LAB).astype(float);oldlab=cv2.cvtColor(original[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)
 skin=(original[:,:,0]>original[:,:,1]*1.08)&(original[:,:,0]>original[:,:,2]*1.15)&(xx>365)&(xx<590)&(yy>330)&(yy<680)
 shift=np.clip(np.median(oldlab[skin]-lab[skin],0),[-4,-3,-3],[4,3,3]);lab+=shift
 material_lab=cv2.cvtColor(matte[:,:,:3],cv2.COLOR_RGB2LAB).astype(float)+shift
 matte[:,:,:3]=cv2.cvtColor(np.rint(np.clip(material_lab,0,255)).astype('uint8'),cv2.COLOR_LAB2RGB)
 cfg=json.loads((C/f'{gender}-preview.json').read_text());baseline=json.loads((D/f'Sources/baseline-{gender}-preview.json').read_text());rig=json.loads((C/f'rigs/{gender}_rig.json').read_text())
 frame=next(r['frame']['frame'] for r in cases if r['gender']==gender and r['time']==0 and r['weapon'])
 for side in ['right','left']:
  art=rig['poseArt']['rifle'][side];bounds=art['mesh']['bounds']
  added=[]
  if gender=='female':
   vertices=art['mesh']['vertices'];top=min(v[1] for v in vertices)
   for v in [v for v in vertices if v[1]==top]:added.append([v[0],top-12,*v[2:]])
   art['mesh']['vertices']=vertices+added
  cfg.setdefault('poseMeshVertexExtensions',{})['rifle-'+side]=added
  edits={}
  if gender=='female' and side=='left':
   for index,v in enumerate(art['mesh']['vertices']):
    x,y,root,fore,hand=v
    active=float(smooth((y-370)/26)*(1-smooth((y-450)/30)))
    pin=float(1-smooth((x-594)/36)) if x<630 else 0
    if active*pin>0 and fore==0 and hand==0:
     edits[str(index)]=[x,y,root*(1-active*pin),fore,hand]
   art['mesh']['vertices']=[edits.get(str(i),v) for i,v in enumerate(art['mesh']['vertices'])]
  cfg.setdefault('poseMeshVertexOverrides',{})['rifle-'+side]=edits
  tri=full_grid(art);art['mesh']['triangles']=tri
  limb_frame=copy.deepcopy(frame);limb_frame['arms']['right']=frame['arms'][side]
  mapx,mapy=authored_map(art,limb_frame)
  limb_matte=matte.copy()
  if gender=='female':
   regions=json.loads((REVIEW/'Sources/female-native-arm-regions.json').read_text())
   mask=np.zeros((H*3,W*3),np.uint8);cv2.fillPoly(mask,[np.rint(np.array(regions[side])*3).astype('int32')],255)
   mask=cv2.resize(mask,(W,H),interpolation=cv2.INTER_AREA)
   limb_matte[:,:,3]=np.rint(limb_matte[:,:,3]*(mask/255)).astype('uint8')
   if side=='right':
    alpha=limb_matte[:,:,3].copy();dy,dx=np.mgrid[-4:5,-4:5];disk=dx*dx+dy*dy<=16
    opened=ndi.binary_opening(alpha>=128,structure=disk)
    signed=ndi.distance_transform_edt(opened)-ndi.distance_transform_edt(~opened)
    contour=np.rint(np.clip(.5+signed/2,0,1)*255).astype('uint8')
    zone=(xx>310)&(xx<355)&(yy>405)&(yy<455)
    limb_matte[zone,3]=np.minimum(alpha[zone],contour[zone])
    # Smooth only a few-pixel lower-forearm matte jitter; no skin blur.
    edge=[]
    for x in range(175,346):
     live=np.flatnonzero(alpha[530:600,x]>=128);edge.append(530+live.max() if len(live) else 570)
    edge=np.array(edge,dtype=float);target=ndi.gaussian_filter1d(ndi.median_filter(edge,5),.8)
    for x,e,t in zip(range(175,346),edge,target):
     low=max(530,int(min(e,t))-2);high=min(600,int(max(e,t))+3)
     coverage=np.rint(np.clip(t+.5-np.arange(low,high),0,1)*255).astype('uint8')
     limb_matte[low:high,x,3]=coverage
    opaque=alpha>=240;_,near=ndi.distance_transform_edt(~opaque,return_indices=True)
    expanded=limb_matte[:,:,3]>alpha;colors=limb_matte[near[0],near[1],:3];limb_matte[expanded,:3]=colors[expanded]
  painted=remap_rgba(limb_matte,mapx,mapy)
  if gender=='female':
   # Approved proximal shoulder exists in the base; restore only this
   # registered cap instead of extending the donor torso strip above it.
   approved=remap_rgba(load(R/'base_female.png'),mapx,mapy)
   cap=(1-smooth((mapy-325)/35))*((1-smooth((xx-330)/25)) if side=='right' else smooth((xx-605)/25))
   aa=painted[:,:,3]/255;ba=approved[:,:,3]/255;oa=aa*(1-cap)+ba*cap
   oldalpha=painted[:,:,3].copy()
   painted[:,:,:3]=np.rint(np.clip((painted[:,:,:3]*(aa*(1-cap))[:,:,None]+approved[:,:,:3]*(ba*cap)[:,:,None])/np.maximum(oa[:,:,None],1e-8),0,255));painted[:,:,3]=np.rint(oa*255)
   # Interpolate one outer contour, rather than cross-fading two silhouettes.
   # This removes the double cap/step caused by alpha-overlapping two edges.
   xa,xb=(210,360) if side=='right' else (610,740)
   for y in range(288,360):
    live=np.flatnonzero(oldalpha[y,xa:xb]>=128);base_live=np.flatnonzero(approved[y,xa:xb,3]>=128)
    if not len(live) or not len(base_live):continue
    oldedge=int(live.min() if side=='right' else live.max())+xa
    baseedge=int(base_live.min() if side=='right' else base_live.max())+xa
    w=float(cap[y,oldedge]);target=oldedge*(1-w)+baseedge*w
    lo=max(xa,int(min(oldedge,baseedge))-2);hi=min(xb,int(max(oldedge,baseedge))+3)
    coverage=np.clip((np.arange(lo,hi)-target+.5) if side=='right' else (target-np.arange(lo,hi)+.5),0,1)
    painted[y,lo:hi,3]=np.rint(coverage*255)
   opaque=painted[:,:,3]>=240;_,nearest=ndi.distance_transform_edt(~opaque,return_indices=True)
   fringe=(painted[:,:,3]>0)&(painted[:,:,3]<240)&(yy<360)
   colors=painted[nearest[0],nearest[1],:3];painted[fringe,:3]=colors[fringe]
  before_context=remap_rgba(original,mapx,mapy)
  old={role:full(load(D/f'Sources/{gender}-rifle-{side}-{role}.png'),bounds) for role in ['complete','arm','front']};source=old['complete'];out=source.copy()
  dist=ndi.distance_transform_edt(source[:,:,3]==0)
  bg=np.linalg.norm(before_context[:,:,:3].astype(float)-[248,245,237],axis=2)<24
  domain=(source[:,:,3]>0)|((dist<16)&bg)
  # Do not attach black swimsuit pixels to a moving arm.
  fabric=(painted[:,:,3]>128)&(painted[:,:,:3].mean(2)<75)&(painted[:,:,0].astype(float)-painted[:,:,2]<15)
  if gender=='female':painted[fabric]=0
  if gender=='female':weight=np.ones((H,W),float)
  else:
   sx,sy=art['anchors']['shoulder'];wx,wy=art['anchors']['wrist']
   root=1-smooth((np.hypot(xx-sx,yy-sy)-60)/28)
   wrist=(np.hypot(xx-wx,yy-wy)<48)&(source[:,:,3]<180)
   weight=np.maximum(root,wrist)*domain
  # Blend in premultiplied space. New skin is a real edited material, not
  # cloned neighboring torso or an opaque patch hiding a missing arm.
  sa=source[:,:,3]/255;pa=painted[:,:,3]/255;oa=sa*(1-weight)+pa*weight
  out[:,:,:3]=np.rint(np.clip((source[:,:,:3]*(sa*(1-weight))[:,:,None]+painted[:,:,:3]*(pa*weight)[:,:,None])/np.maximum(oa[:,:,None],1e-8),0,255));out[:,:,3]=np.rint(oa*255)
  # Keep unchanged source material wherever an edited finger would move out
  # of the actual old foreground profile; new rear skin may still fill gaps.
  foreground_old=old['front'][:,:,3]>0;fallback=foreground_old&(painted[:,:,3]<180)
  # No old foreground fallback: it reattached belly pixels under the edited fingers.
  fallback[:]=False
  # A proximal shared shoulder seam is a real surface overlap with the
  # pose-owned torso, not an opaque painted patch. Fade only where that
  # torso is already fully opaque; never fade free arm contours or hands.
  torso=np.zeros((H,W,4),np.uint8);tb=rig['segments']['torso']['bounds'];tx,ty,tx1,ty1=tb
  torso[ty:ty1,tx:tx1]=load(C/cfg.get('poseTorsoSurfaces',{}).get('rifle',cfg['runtimeSurfaces']['torso']))
  torso_uv=cv2.remap(torso[:,:,3],mapx,mapy,cv2.INTER_LINEAR)
  shoulder=np.array(art['anchors']['shoulder']);near_root=(np.hypot(xx-shoulder[0],yy-shoulder[1])<95)&(yy<470)
  shared=(torso_uv>=250)&near_root&(out[:,:,3]>0)
  depth=ndi.distance_transform_edt(out[:,:,3]>=128)
  # No static torso-dependent alpha cut: it opened the moving shared seam.
  # Keep actual registered material; any tone seam remains a separate art issue.
  labels,n=ndi.label(out[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labels.ravel());sizes[0]=0
  tiny=np.isin(labels,np.flatnonzero((sizes>0)&(sizes<80)))
  # A full arm including its digits is one large connected surface. These
  # are verified remote2–51px extraction crumbs, not finger separators.
  removed=int(np.count_nonzero(tiny));out[tiny]=0
  folder=C/f'assets/{gender}/rifle-seams';folder.mkdir(exist_ok=True)
  for role in ['complete','arm','front']:
   image=out.copy()
   if role=='front':
    profiles=json.loads((REVIEW/'Sources/rifle-foreground-profiles.json').read_text())[gender][side]
    mask=np.zeros((H*3,W*3),np.uint8)
    for polygon in profiles.values():cv2.fillPoly(mask,[np.rint(np.array(polygon)*3).astype('int32')],255)
    mask=cv2.resize(mask,(W,H),interpolation=cv2.INTER_AREA)
    image[:,:,3]=np.rint(out[:,:,3]*(mask/255)).astype('uint8')
   elif role=='arm':
    image[:,:,3]=np.minimum(out[:,:,3],np.maximum(old['arm'][:,:,3],np.rint(out[:,:,3]*(1-old['front'][:,:,3]/255))))
   image[image[:,:,3]==0]=0
   if gender=='male':image=image[bounds[1]:bounds[3],bounds[0]:bounds[2]]
   p=folder/f'rifle-{side}-{role}.png';Image.fromarray(image).save(p)
   if role=='complete':cfg['poseArtCompleteSurfaces']['rifle-'+side]=str(p.relative_to(C))
   else:cfg['poseArtSurfaces'][('art-front-' if role=='front' else 'art-')+'rifle-'+side]=str(p.relative_to(C))
  # Add only omitted cells of the same existing12px corrective grid when
  # reconstructed material occupies them. No new rig/bone/animation.
  oldtri=rig['poseArt']['rifle'][side]['mesh']['triangles']
  base_rig=json.loads((D/f'Sources/baseline-{gender}_rig.json').read_text());base_tri=base_rig['poseArt']['rifle'][side]['mesh']['triangles'];known={tuple(t) for t in base_tri};extra=list(baseline.get('poseMeshExtensions',{}).get('rifle-'+side,[]));known.update(tuple(t) for t in extra)
  vertices=np.array(art['mesh']['vertices'])
  for t in tri:
   if tuple(t) in known:continue
   uv=vertices[t,:2];x0,y0=np.floor(uv.min(0)).astype(int);x1,y1=np.ceil(uv.max(0)).astype(int)
   if out[y0:y1+1,x0:x1+1,3].max(initial=0)>64:extra.append(t)
  cfg.setdefault('poseMeshExtensions',{})['rifle-'+side]=extra
  records.append({'gender':gender,'side':side,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'registration':reg,'torso_LAB_match':shift.tolist(),'role':'local rifle arm edit only','new_mesh_triangles':len(extra)-len(baseline.get('poseMeshExtensions',{}).get('rifle-'+side,[])),'changed_pixels':int(np.count_nonzero(np.any(out!=source,axis=2))),'new_opaque_pixels':int(np.count_nonzero((out[:,:,3]>=200)&(source[:,:,3]<128))),'detached_extraction_pixels_removed':removed,'originals_changed':False})
 cfg['rifleForegroundMode']='opaque-core-cutout'
 (C/f'{gender}-preview.json').write_text(json.dumps(cfg,indent=2,sort_keys=True)+'\n')
(REVIEW/'Evidence/art-export.json').write_text(json.dumps(records,indent=2));print(records)
