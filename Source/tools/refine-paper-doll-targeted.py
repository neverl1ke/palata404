"""Targeted repairs from immutable 8bcf183 inputs, not a second global cleanup.
Pillow/NumPy/SciPy. Repaint RGB is registered separately; source alpha retained.
"""
from pathlib import Path
import argparse,hashlib,json,importlib.util
import numpy as np
from PIL import Image,ImageCms
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/paper-doll-targeted-fix'
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def read(p):return np.array(Image.open(p).convert('RGBA'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_module(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def clean_head(a,force=False):
 """Rebuild only broad outer AA rows; keep skull/ears within .55 px of iso-128."""
 out=a.copy();alpha=a[:,:,3]/255;rows=[];bounds=[]
 for y in range(38,218):
  xs=np.flatnonzero(alpha[y]>=.5)
  if len(xs)<20:continue
  l,r=xs[0],xs[-1];lf=l-1+(.5-alpha[y,l-1])/max(alpha[y,l]-alpha[y,l-1],1e-8);rf=r+(.5-alpha[y,r])/min(alpha[y,r+1]-alpha[y,r],-1e-8)
  rows.append(y);bounds.append([lf,rf])
 bounds=np.array(bounds);fit=ndi.gaussian_filter1d(ndi.median_filter(bounds,size=(3,1)),.65,axis=0);fit=np.clip(fit,bounds-.55,bounds+.55);x=np.arange(a.shape[1])
 changed_rows=0
 for i,y in enumerate(rows):
  l,r=bounds[i];li,ri=int(np.ceil(l)),int(np.floor(r));left=alpha[y,max(0,li-4):li+5];right=alpha[y,ri-4:ri+5]
  broad=max(np.count_nonzero((left>.06)&(left<.94)),np.count_nonzero((right>.06)&(right<.94)))>=3
  if force or broad:
   coverage=np.clip(x-fit[i,0]+.5,0,1)*np.clip(fit[i,1]-x+.5,0,1)
   out[y,:,3]=np.rint(coverage*255);changed_rows+=1
 # Sparse black matte is corrected from nearby shaded skin, not a flat paint fill.
 inside=ndi.distance_transform_edt(out[:,:,3]>=128);core=(inside>=4)&(out[:,:,3]>=248)&(out[:,:,0]>75)
 _,idx=ndi.distance_transform_edt(~core,return_indices=True);donor=out[idx[0],idx[1],:3].astype(float);rgb=out[:,:,:3].astype(float)
 y=np.arange(len(a))[:,None];lum=rgb@np.array([.2126,.7152,.0722]);dl=donor@np.array([.2126,.7152,.0722])
 band=(out[:,:,3]>0)&(inside<3)&(y>=65)&(y<251)
 bad=band&(lum<dl-24)&((out[:,:,0]<65)|(out[:,:,3]<200))
 # Keep a small natural edge shadow rather than introducing a pale skin rim.
 corrected=np.maximum(donor-8,rgb);out[bad,:3]=np.rint(corrected[bad]).clip(0,255)
 # New subpixel coverage needs valid RGB at formerly transparent edge positions.
 empty=(out[:,:,3]>0)&(a[:,:,3]==0);out[empty,:3]=donor[empty]
 region=out[:218,:,3];distance=ndi.distance_transform_edt(region<32);region[(region>0)&(region<=16)&(distance>4)]=0
 labels,n=ndi.label(region>0,np.ones((3,3)))
 if n:
  peaks=ndi.maximum(region,labels,np.arange(1,n+1));region[np.isin(labels,np.flatnonzero(peaks<=16)+1)]=0
 out[out[:,:,3]==0]=0
 return out,{'sharpened_rows':changed_rows,'dark_edge_pixels':int(bad.sum())}

def scale_asian(a):
 y,x=np.mgrid[:1672,:941];w=1-smooth((y-216)/40);scale=1+.035*w
 sx=474+(x-474)/scale;sy=30+(y-30)/scale
 pa=np.dstack((a[:,:,:3]*(a[:,:,3:4]/255),a[:,:,3]/255));out=np.stack([ndi.map_coordinates(pa[:,:,c],[sy,sx],order=1,mode='constant',cval=0) for c in range(4)],axis=2)
 rgb=np.divide(out[:,:,:3],out[:,:,3:4],out=np.zeros_like(out[:,:,:3]),where=out[:,:,3:4]>0)
 return np.dstack((np.rint(rgb),np.rint(out[:,:,3]*255))).clip(0,255).astype('uint8')

RGB=ImageCms.createProfile('sRGB');LAB=ImageCms.createProfile('LAB')
TO_LAB=ImageCms.buildTransform(RGB,LAB,'RGB','LAB');FROM_LAB=ImageCms.buildTransform(LAB,RGB,'LAB','RGB')
def lab(a):return np.array(ImageCms.applyTransform(Image.fromarray(a[:,:,:3].astype('uint8')),TO_LAB)).astype(float)
def skin_median(a):
 z=lab(a);y,x=np.mgrid[:a.shape[0],:a.shape[1]];m=(x>=426)&(x<522)&(y>=105)&(y<215)&(a[:,:,3]>240)&(a[:,:,0]>95)&(a[:,:,0]>a[:,:,1]*1.12)&(a[:,:,1]>a[:,:,2]*1.08)
 return np.median(z[m],axis=0)
def tone(a,base,gender):
 z=lab(a);before=skin_median(a);ref=skin_median(base);female=gender=='female'
 delta=np.clip((ref-before)*([.25,.5,.5] if female else [.7,.85,.85]),[-4,-2,-2] if female else [-14,-6,-8],[4,2,2] if female else [10,6,8])
 y,x=np.mgrid[:1672,:941];weight=smooth((y-55)/20)*(1-smooth((y-215)/25))
 mapped=np.array(ImageCms.applyTransform(Image.frombytes('LAB',(a.shape[1],a.shape[0]),np.rint(np.clip(z+delta,0,255)).astype('uint8').tobytes()),FROM_LAB))
 out=a.copy();out[:,:,:3]=np.rint(a[:,:,:3]*(1-weight[:,:,None])+mapped*weight[:,:,None]).clip(0,255);out[out[:,:,3]==0]=0
 return out,{'delta_lab8':delta.tolist(),'before_median_lab8':before.tolist(),'after_median_lab8':skin_median(out).tolist(),'body_reference_lab8':ref.tolist()}
def repaint(a):
 rgb=np.array(Image.open(REPORT/'sources/male-alternative-painted-rgb.png').convert('RGB'));old=a[20:285,365:585,:3].astype(float);yy,xx=np.mgrid[20:285,365:585]
 preserve=np.zeros(yy.shape)
 for cx,cy,rx,ry in [(442,138,18,10),(502,136,18,10),(441,121,23,7),(503,119,23,7),(474,175,14,18),(474,204,24,8)]:
  radius=((xx-cx)/rx)**2+((yy-cy)/ry)**2;preserve=np.maximum(preserve,(1-smooth((radius-.45)/.65))*.8)
 amount=(1-preserve)*(1-smooth((yy-215)/30))*.94
 out=a.copy();out[20:285,365:585,:3]=np.rint(old*(1-amount[:,:,None])+rgb*amount[:,:,None]).clip(0,255);out[out[:,:,3]==0]=0;return out

def thighs(a):
 out=a.copy();rows=[]
 for y in range(823,1105):
  fade=smooth((y-823)/24)*(1-smooth((y-1073)/32))
  for left in [True,False]:
   xs=np.flatnonzero((a[y,:,3]>=240)&((np.arange(941)>340)&(np.arange(941)<474) if left else ((a[y,:,3]>=240)&(np.arange(941)>474)&(np.arange(941)<605))))
   if not len(xs):continue
   edge=xs[-1] if left else xs[0];direction=-1 if left else 1
   # Add back excess transferred darkness with a broad, tapered correction;
   # the source gradient and skin texture remain in the RGB, not resampled.
   for d in range(0,21):
    x=edge+direction*d
    if a[y,x,3]==0 or not (a[y,x,0]>65 and a[y,x,0]>a[y,x,1]*1.12 and a[y,x,1]>a[y,x,2]*1.1):continue
    strength=fade*(1-smooth(d/21));delta=np.array([14,10,7])*strength
    out[y,x,:3]=np.rint(np.minimum(255,a[y,x,:3].astype(float)+delta))
 return out

def hair_ear_cut(a,kind,placement):
 y,x=np.mgrid[:a.shape[0],:a.shape[1]];fx=placement['x']+(x+.5)*placement['width']/a.shape[1];fy=placement['y']+(y+.5)*placement['height']/a.shape[0]
 if kind=='messy':
  d=np.abs(fx-474);cut=154-(d-58)*1.05;amount=smooth((d-55)/5)*smooth((fy-127)/3)*smooth((fy-cut)/1.4)
 else:
  # Front-only ear windows: the approved rear strands stay exactly as supplied.
  amount=np.zeros(fx.shape)
  for cx,cy,rx,ry in [(404,155,8,19),(542,153,8,19)]:
   distance=((fx-cx)/rx)**2+((fy-cy)/ry)**2;amount=np.maximum(amount,1-smooth((distance-.68)/.32))
 out=a.copy();out[:,:,3]=np.rint(a[:,:,3]*(1-amount))
 # Prune only faint fragments made remote by this local ear cut.
 distance=ndi.distance_transform_edt(out[:,:,3]<32);weak=(out[:,:,3]>0)&(out[:,:,3]<=16)
 out[:,:,3][weak&(distance>4)]=0
 labels,n=ndi.label(out[:,:,3]>0,np.ones((3,3)))
 if n:
  peaks=ndi.maximum(out[:,:,3],labels,np.arange(1,n+1));out[:,:,3][np.isin(labels,np.flatnonzero(peaks<=16)+1)]=0
 out[out[:,:,3]==0]=0
 return out

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);args=p.parse_args();snapshot=args.snapshot;records=[]
 audit=load_module('audit','tools/audit-paper-doll-png.py');prepare=load_module('prepare','tools/prepare-avatar-update.py');cat=audit.catalog();bases={g:read(snapshot/f'base_{g}.png') for g in ['male','female']}
 def save(rel,a,details):
  dest=ROOT/rel;Image.fromarray(a).save(dest,optimize=True);source=snapshot/rel
  old=read(source);records.append({'path':rel,'before_sha256':sha(source),'sha256':sha(dest),'alpha_changed':int((a[:,:,3]!=old[:,:,3]).sum()),'rgb_changed':int(np.any(a[:,:,:3]!=old[:,:,:3],axis=2).sum()),**details})
 for g in ['male','female']:
  for kind in ['asian','young','exhausted','elder','alternative']:
   rel=f'assets/wardrobe/faces/{g}_{kind}_head.png';a=read(snapshot/rel);details={}
   if g=='male' and kind=='asian':a=scale_asian(a);details['upper_head_scale']=1.035;details['anchor']=[474,30]
   if g=='male' and kind=='alternative':a=repaint(a);details['repaint']='registered painted RGB; original feature emphasis and alpha'
   if kind=='alternative':a,details['tone']=tone(a,bases[g],g)
   a,details['edge']=clean_head(a,force=g=='male' and kind=='asian')
   if (g,kind)==('female','alternative'):
    y,x=np.mgrid[:1672,:941];inside=ndi.distance_transform_edt(a[:,:,3]>=128)
    zone=(y>=225)&(y<251)&(inside<5)&(a[:,:,3]>0)&(bases[g][:,:,3]>=240)
    dark=(a[:,:,:3].astype(float)@np.array([.2126,.7152,.0722]))<(bases[g][:,:,:3].astype(float)@np.array([.2126,.7152,.0722]))-18
    weight=smooth((y-225)/6)*(1-smooth((y-243)/8))
    mix=zone&dark;target=np.maximum(a[:,:,:3].astype(float),bases[g][:,:,:3].astype(float)-9)
    rgb=np.rint(a[:,:,:3]*(1-weight[:,:,None])+target*weight[:,:,None]);a[mix,:3]=rgb[mix].clip(0,255);details['neck_matte_rgb_pixels']=int(mix.sum())
   if (g,kind) in [('male','asian'),('female','exhausted')]:
    profile=(474,72,234,262,10) if g=='male' else (473,63,234,260,11)
    protected=a[:218].copy();h,m=prepare.face(Image.fromarray(a),g,profile);a=np.array(h);a[:218]=protected;details['neck_profile']=profile;save(f'assets/wardrobe/faces/masks/{g}_{kind}_body.png',np.array(m),{'neck_profile':profile})
   save(rel,a,details)
 save('base_female.png',thighs(bases['female']),{'repair_box':[340,823,605,1105],'alpha_unchanged':True})
 for id,kind in [('hair-messy','messy'),('hair-shoulder-length','shoulder')]:
  item=next(i for i in cat['items'] if i['id']==id);rel=item['genderVariants']['male'].split('?')[0];a=read(snapshot/rel);save(rel,hair_ear_cut(a,kind,item['placementByGender']['male']),{'ear_clearance':kind,'placement_unchanged':True})
 (REPORT/'repairs.json').write_text(json.dumps({'source_commit':'8bcf1830429008113c145e15c016a9bc709e35a1','files':records},indent=2)+'\n');print('Repaired',len(records),'resources')
