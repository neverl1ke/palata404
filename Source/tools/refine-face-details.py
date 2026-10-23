"""Локальні правки чотирьох голів від 4a87c2c, без генерації.
Потрібні Pillow, NumPy, SciPy та snapshots PNG/маски з --before-dir.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import argparse
p=argparse.ArgumentParser();p.add_argument('--before-dir',type=Path,required=True);args=p.parse_args()
r=Path(__file__).resolve().parents[1];before=args.before_dir
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def patch_dark(a,box):
 x0,y0,x1,y1=box;y,x=np.mgrid[:1672,:941];mask=(x>=x0)&(x<x1)&(y>=y0)&(y<y1)&(a[:,:,3]>128)&(a[:,:,:3].mean(2)<65)
 # Harmonic interpolation from adjacent existing skin, without transparent RGB donors.
 region=mask[y0-2:y1+2,x0-2:x1+2];rgb=a[y0-2:y1+2,x0-2:x1+2,:3].astype(float);valid=a[y0-2:y1+2,x0-2:x1+2,3]>128
 for _ in range(250):
  acc=np.zeros_like(rgb);weight=np.zeros(rgb.shape[:2])
  for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
   v=np.roll(valid,(dy,dx),(0,1));acc+=np.roll(rgb,(dy,dx),(0,1))*v[:,:,None];weight+=v
  mean=acc/np.maximum(weight[:,:,None],1);rgb[region]=mean[region]
 a[y0-2:y1+2,x0-2:x1+2,:3]=np.rint(rgb).clip(0,255).astype('uint8')
def neck_edge(a,start,end):
 for yy in range(start,end):
  points=np.where(a[yy,:,3]>=128)[0];edge=points[-1]
  # Three-pixel outer strip: copy the adjoining shaded neck, taper at both ends.
  strength=smooth((yy-start)/4)*(1-smooth((yy-(end-4))/4))
  for xx in range(edge-3,edge+2):
   if a[yy,xx,3]==0:continue
   w=strength*smooth((xx-(edge-4))/3)
   donor=np.mean(a[yy,edge-7:edge-4,:3],axis=0)
   a[yy,xx,:3]=np.rint(a[yy,xx,:3]*(1-w)+donor*w)
def contour(a,side,start,end,sigma):
 bounds=[]
 for yy in range(start-6,end+7):
  xs=np.where(a[yy,:,3]>=128)[0];bounds.append(xs[0] if side=='left' else xs[-1])
 original=np.array(bounds,dtype=float);fit=ndi.gaussian_filter1d(ndi.median_filter(original,size=5),sigma)
 for i,yy in enumerate(range(start,end)):
  j=i+6;w=smooth(i/4)*(1-smooth((yy-(end-4))/4));edge=original[j]*(1-w)+fit[j]*w
  if side=='left':
   for xx in range(int(original[j])-3,int(original[j])+4):a[yy,xx,3]=round(min(a[yy,xx,3]/255,np.clip(xx-edge+1,0,1))*255)
  else:
   for xx in range(int(original[j])-3,int(original[j])+4):a[yy,xx,3]=round(min(a[yy,xx,3]/255,np.clip(edge-xx+1,0,1))*255)
def warp(a):
 y,x=np.mgrid[:1672,:941];strength=1-smooth((y-238)/34);scale=1+.06*strength
 sx=473+(x-473)/scale;sy=y+strength*(26+(y-26)/1.06-y)
 alpha=a[:,:,3]/255;pa=np.dstack((a[:,:,:3]*alpha[:,:,None],alpha));out=np.empty_like(pa)
 for c in range(4):out[:,:,c]=ndi.map_coordinates(pa[:,:,c],[sy,sx],order=1,mode='constant',cval=0)
 rgb=np.divide(out[:,:,:3],out[:,:,3,None],out=np.zeros_like(out[:,:,:3]),where=out[:,:,3,None]>0)
 return np.dstack((np.rint(rgb),np.rint(out[:,:,3]*255))).clip(0,255).astype('uint8')
for kind in ['young','exhausted']:
 for g in ['male','female']:
  name=g+'_'+kind+'_head.png';a=np.array(Image.open(before/name).convert('RGBA'))
  if kind=='young':
   neck_edge(a,220 if g=='male' else 222,258 if g=='male' else 254)
   if g=='male':contour(a,'right',82,123,3);contour(a,'right',134,183,1.4);patch_dark(a,(541,124,549,133))
   else:contour(a,'left',183,219,2.5)
  else:
   boxes=[(398,128,408,137),(541,123,549,134)] if g=='male' else [(400,111,410,121),(538,112,547,123)]
   for b in boxes:patch_dark(a,b)
   if g=='female':
    a=warp(a)
    m=np.array(Image.open(before/'female_exhausted_body.png').convert('RGBA'));m=warp(m)
    # Retain original body beneath nearly opaque inner-neck pixels after resampling.
    ba=np.array(Image.open(r/'base_female.png').convert('RGBA'))[:,:,3];yy=np.arange(1672)[:,None]
    xx=np.arange(941)[None,:];inside=(yy>=244)&(yy<272)&(xx>=440)&(xx<=510)&(ba>=250);m[:,:,3][inside]=255
    Image.fromarray(m).save(r/'assets/wardrobe/faces/masks/female_exhausted_body.png',optimize=True)
  a[a[:,:,3]==0]=0
  Image.fromarray(a).save(r/'assets/wardrobe/faces'/name,optimize=True)
