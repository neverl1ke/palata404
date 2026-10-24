"""Реєстрація п'яти наданих PNG; без генерації. Pillow, NumPy, SciPy.
Запуск: python tools/prepare-avatar-update.py --source-dir DIR --reference-dir DIR
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rgb_extend(a):
 _,idx=ndi.distance_transform_edt(a[:,:,3]<200,return_indices=True)
 return a[idx[0],idx[1],:3].astype(float)
def main_component(a):
 labels,_=ndi.label(a>127);ids,c=np.unique(labels,return_counts=True);c[ids==0]=0;return labels==ids[c.argmax()]
def body(raw,reference):
 src=np.array(Image.open(raw).convert('RGBA'));old=np.array(Image.open(reference).convert('RGBA'));assert src.shape==old.shape==(1672,941,4)
 y,x=np.mgrid[:1672,:941];warped=rgb_extend(src)
 # Local tone transfer from exposed skin only; neither black nor navy fabric is a donor.
 def skin(z):return (z[:,:,0]>65)&(z[:,:,0]>z[:,:,1]*1.12)&(z[:,:,1]>z[:,:,2]*1.1)
 valid=skin(old)&skin(warped)&(old[:,:,3]>240)
 weight=ndi.gaussian_filter(valid.astype(float),16);delta=np.stack([ndi.gaussian_filter((old[:,:,c]-warped[:,:,c])*valid,16)/np.maximum(weight,.001) for c in range(3)],axis=2)
 correction=delta*.8
 # Higher-resolution tone match only at the established old-head neck joins.
 neck=((y>=235)&(y<325)&(x>370)&(x<575)&valid)
 nw=ndi.gaussian_filter(neck.astype(float),2)
 nd=np.stack([ndi.gaussian_filter((old[:,:,c]-warped[:,:,c])*neck,2)/np.maximum(nw,.001) for c in range(3)],axis=2)
 mix=smooth((y-235)/10)*(1-smooth((y-310)/15))*smooth((x-370)/20)*(1-smooth((x-555)/20))
 correction=correction*(1-mix[:,:,None])+nd*mix[:,:,None]
 strength=skin(warped).astype(float);strength=ndi.gaussian_filter(strength,.6)
 # The new RGB and its own uploaded silhouette belong together. Reusing the old
 # alpha exposed stretched edge pixels, especially at the female trapezius.
 out=np.dstack((np.rint(warped+correction*strength[:,:,None]).clip(0,255),src[:,:,3])).astype('uint8');out[out[:,:,3]==0]=0
 return Image.fromarray(out)
def register(raw,scale,x,y):
 im=Image.open(raw).convert('RGBA');rgba=np.array(im);support=main_component(rgba[:,:,3]);near=ndi.distance_transform_edt(~support)<5
 rgba[:,:,3][~near]=0
 # Remove the dark matte at the exterior only, preserving interior eye/ear shadows.
 inside=ndi.distance_transform_edt(support);core=inside>=max(2.5,2.2/scale);rgba[:,:,3][core]=255
 _,idx=ndi.distance_transform_edt(~core,return_indices=True);edge=(rgba[:,:,3]>0)&(inside<max(2.5,2.2/scale))
 rgba[edge,:3]=rgba[idx[0],idx[1],:3][edge]
 signed=inside-ndi.distance_transform_edt(~support);rgba[:,:,3]=np.minimum(rgba[:,:,3],np.rint(np.clip((signed-.35/scale+.7)/1.4,0,1)*255)).astype('uint8')
 im=Image.fromarray(rgba);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 out=Image.new('RGBA',(941,1672));out.paste(im,(round(x),round(y)));return out

def finish_registered_head(image,gender):
 """Local edge cleanup and conservative, geometry-preserving painted retouch."""
 a=np.array(image);y,x=np.mgrid[:1672,:941];alpha=a[:,:,3]/255
 if gender=='female':
  # Remove single-pixel ear/scalp spurs, not the folds inside the ears.
  support=alpha>.5;opened=ndi.binary_opening(support,iterations=1)
  signed=ndi.distance_transform_edt(opened)-ndi.distance_transform_edt(~opened)
  zone=(y>108)&(y<192)&((x<415)|(x>535))
  a[:,:,3][zone]=np.minimum(a[:,:,3],np.clip((signed+.5)*255,0,255).astype('uint8'))[zone]
  rgb=rgb_extend(a);edge=zone&(a[:,:,3]>0)&(ndi.distance_transform_edt(a[:,:,3]>.5)<2)
  a[edge,:3]=rgb[edge]
  # The upload contains near-black matte patches at both ear attachments.
  # They are RGB paint, not holes or a second base head: repair just these
  # small boundary patches, retaining the normal internal ear shadows.
  patches=(y>=116)&(y<=136)&(((x>=391)&(x<=405))|((x>=539)&(x<=553)))&(a[:,:,3]>0)&(a[:,:,0]<75)
  donor=(a[:,:,3]>240)&(a[:,:,0]>95)
  _,idx=ndi.distance_transform_edt(~donor,return_indices=True)
  a[patches,:3]=a[idx[0],idx[1],:3][patches]
  # Remove the source neck's dark outer matte before its curved body join.
  core=ndi.distance_transform_edt(a[:,:,3]>127)>=4
  _,idx=ndi.distance_transform_edt(~core,return_indices=True)
  neckedge=(y>205)&(y<270)&(a[:,:,3]>0)&(~core)
  a[neckedge,:3]=a[idx[0],idx[1],:3][neckedge]
 else:
  # Bilateral retouch removes photographic microtexture without changing
  # the contour, landmarks, eyes, lips or the registered neck transition.
  rgb=a[:350,:,:3].astype(float);total=np.zeros_like(rgb);weights=np.zeros(rgb.shape[:2])
  padded=np.pad(rgb,((2,2),(2,2),(0,0)),mode='edge')
  for dy in range(-2,3):
   for dx in range(-2,3):
    sample=padded[2+dy:352+dy,2+dx:943+dx];d=np.mean((sample-rgb)**2,axis=2)
    w=np.exp(-(dx*dx+dy*dy)/3.2-d/(2*18**2));total+=sample*w[:,:,None];weights+=w
  painted=total/weights[:,:,None];painted=np.rint(painted/3)*3
  amount=(1-smooth((y[:350]-225)/35))*.82
  a[:350,:,:3]=np.rint(rgb*(1-amount[:,:,None])+painted*amount[:,:,None]).clip(0,255)
 a[a[:,:,3]==0]=0
 return Image.fromarray(a)

def face(registered,gender,profile):
 src=np.array(registered).astype(float);base=np.array(Image.open(ROOT/f'base_{gender}.png').convert('RGBA')).astype(float)
 y,x=np.mgrid[:1672,:941];center,radius,start,end,arc=profile
 curved=np.minimum(((x-center)/radius)**2,1);begin=start-arc*curved;finish=end-arc*.7*curved;b=smooth((y-begin)/(finish-begin))
 sa=src[:,:,3]/255;ba=base[:,:,3]/255
 def distance(a):
  m=a>=.5;d=ndi.distance_transform_edt(m)-ndi.distance_transform_edt(~m);edge=(a>0)&(a<1);d[edge]=a[edge]-.5;return d
 da=distance(sa);db=distance(ba);alpha=np.clip((1-b)*da+b*db+.5,0,1);alpha[b==0]=sa[b==0];alpha[b==1]=ba[b==1]
 # Smooth only the under-jaw contour into a continuous neck.
 rows=np.arange(218,301);lr=[]
 for yy in rows:
  xs=np.where(alpha[yy]> .5)[0];lr.append((xs[0],xs[-1]))
 lr=ndi.gaussian_filter1d(ndi.median_filter(np.array(lr,dtype=float),size=(3,1)),2,axis=0)
 left=np.interp(np.arange(1672),rows,lr[:,0])[:,None];right=np.interp(np.arange(1672),rows,lr[:,1])[:,None]
 nd=np.minimum(x-left,right-x);weight=smooth((y-222)/8)*(1-smooth((y-(end-8))/8))
 alpha=np.clip((1-weight)*distance(alpha)+weight*nd+.5,0,1)
 rgb=rgb_extend(src)*(1-b[:,:,None])+rgb_extend(base)*b[:,:,None]
 # Fully opaque inner head; preserve source edge AA and its natural face texture.
 fade=1-smooth((y-finish)/10);ha=alpha*fade
 out=np.dstack((np.rint(rgb),np.rint(ha*255))).clip(0,255).astype('uint8');out[out[:,:,3]==0]=0
 # Under the lower join keep the unchanged base present. Hide the replaced skull.
 visibility=np.ones_like(sa);visibility[y<np.ceil(begin)]=0
 partial=(y>=np.ceil(begin))&(y<end+10)
 visibility[partial]=np.divide(np.maximum(alpha-ha,0),ba*(1-ha),out=np.zeros_like(sa),where=(ba*(1-ha))>1e-8)[partial]
 # Avoid double AA borders; interior opaque skin may use the original body under it.
 visibility[(ha>.99)&(y<end)]=0
 mask=np.full((1672,941,4),255,dtype='uint8');mask[:,:,3]=np.rint(np.clip(visibility,0,1)*255).astype('uint8')
 return Image.fromarray(out),Image.fromarray(mask)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--reference-dir',type=Path,required=True);a=p.parse_args();entries=[]
 files={g:a.source_dir/f'{n}_{g}_base_black.png' for g,n in [('female','01'),('male','02')]}
 for g,path in files.items():
  dest=ROOT/f'base_{g}.png';body(path,a.reference_dir/f'base_{g}.png').save(dest,optimize=True);entries.append(dict(source=path.name,source_sha256=sha(path),output=str(dest.relative_to(ROOT)),sha256=sha(dest),reference_alpha_sha256=hashlib.sha256(Image.open(path).getchannel('A').tobytes()).hexdigest(),registration='1:1 uploaded RGB and uploaded alpha; local skin-tone transfer; no body-part warp'))
 for g,n,scale,x,y,profile in [('female','03',1.02,254.7,17,(474,65,242,270,14)),('male','04',.275,300.5,8,(474,72,258,288,23))]:
  path=a.source_dir/f'{n}_{g}_new_face.png';reg=finish_registered_head(register(path,scale,x,y),g);head,mask=face(reg,g,profile)
  dest=ROOT/f'assets/wardrobe/faces/{g}_alternative_head.png';mp=ROOT/f'assets/wardrobe/faces/masks/{g}_alternative_body.png';head.save(dest,optimize=True);mask.save(mp,optimize=True)
  entries.append(dict(source=path.name,source_sha256=sha(path),output=str(dest.relative_to(ROOT)),sha256=sha(dest),mask=str(mp.relative_to(ROOT)),mask_sha256=sha(mp),registration=dict(scale=scale,x=x,y=y),profile=profile))
 path=a.source_dir/'05_unisex_bob_hair.png';dest=ROOT/'assets/wardrobe/hair/unisex_bob_bangs.png'
 hair=np.array(Image.open(path).convert('RGBA'));lum=np.rint(hair[:,:,:3]@np.array([.2126,.7152,.0722]));median=np.median(lum[hair[:,:,3]>=192]);shade=(lum/max(median,1))**.85
 target=np.array([112,70,50]);rgb=np.where(shade[:,:,None]<=1,target*shade[:,:,None],target+(255-target)*np.minimum(.55,(shade[:,:,None]-1)*.3));hair[:,:,:3]=np.rint(rgb).clip(0,255);hair[hair[:,:,3]==0]=0
 Image.fromarray(hair).save(dest,optimize=True)
 entries.append(dict(source=path.name,source_sha256=sha(path),output=str(dest.relative_to(ROOT)),sha256=sha(dest),source_alpha_sha256=hashlib.sha256(Image.open(path).getchannel('A').tobytes()).hexdigest(),original_pigment='#704632',registration=dict(scale=.23,x=365.9,y=-59.9)))
 for e in entries:
  with Image.open(a.source_dir/e['source']) as im:e['source_size']=list(im.size);e['source_mode']=im.mode;e['source_alpha_extrema']=list(im.convert('RGBA').getchannel('A').getextrema())
 print(json.dumps(dict(source_archive='palata404_assets_fixedd.zip',reference_commit='a85ccb4390dab37fa373b18d8515fbb803e31842',files=entries),indent=2))
