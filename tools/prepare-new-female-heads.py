"""Uniform registration, measured skin tone, and individual head/body alpha pairs.

Only the eight new working copies are changed. The original sources, existing
portraits, bodies and hairstyle transforms remain untouched. No synthesis.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/female-heads-new-library'
SIZE=(941,1672)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def distance(a):return ndi.distance_transform_edt(a>=.5)-ndi.distance_transform_edt(a<.5)

def register(im,c):
 s,tx,ty=c['scale'],c['x'],c['y']
 scaled=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
 sx,sy=scaled.width/im.width,scaled.height/im.height
 return scaled.transform(SIZE,Image.Transform.AFFINE,(sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC)

def prepare(entry,base,apply_tone=True,blend_neck=True):
 source=np.array(Image.open(REPORT/entry['source']).convert('RGBA'))
 a=source[:,:,3]
 remote=(a>0)&(a<=16)&(ndi.distance_transform_edt(a<32)>3)
 labels,n=ndi.label(a>0,np.ones((3,3)))
 weak=np.isin(labels,np.flatnonzero(ndi.maximum(a,labels,np.arange(1,n+1))<=16)+1)
 a[remote|weak]=0;source[a==0]=0
 registered=np.array(register(Image.fromarray(source),entry['registration']))
 out=registered[:360].copy();body=base[:360];alpha=out[:,:,3]
 remote_after=(alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>3)
 alpha[remote_after]=0
 alpha[ndi.distance_transform_edt(alpha>=128)>2]=255
 yy,xx=np.mgrid[:360,:941]
 # Compare an opaque central neck patch, without eyes/lips/bikini or background.
 sample=(yy>=215)&(yy<240)&(xx>=450)&(xx<495)&(alpha>240)&(body[:,:,3]>240)
 src=np.median(out[:,:,:3][sample],axis=0);dst=np.median(body[:,:,:3][sample],axis=0)
 gain=np.clip(dst/np.maximum(src,1),.85,1.15) if apply_tone else np.ones(3)
 rgb=out[:,:,:3].astype(float)
 # Apply the measured gain with a smooth skin-colour selection. This limits
 # changes in dark piercings/makeup and cool irises, without flattening texture.
 r,g,b=np.moveaxis(rgb,-1,0)
 skin=smooth((r-g-2)/12)*smooth((g-b-1)/12)*smooth((g-45)/45)
 corrected=np.clip(rgb*(1+(gain-1)*skin[:,:,None]),0,255)
 c=entry['neck'];arc=np.minimum(((xx-c['center_x'])/c['radius'])**2,1)
 start=c['start_center_y']+(c['start_side_y']-c['start_center_y'])*arc
 end=c['end_center_y']+(c['end_side_y']-c['end_center_y'])*arc
 blend=smooth((yy-start)/(end-start))
 ha,ba=alpha/255,body[:,:,3]/255
 target=np.clip((1-blend)*distance(ha)+blend*distance(ba)+.5,0,1)
 target[blend==0]=ha[blend==0];target[blend==1]=ba[blend==1]
 target=np.minimum(target,np.maximum(ha,ba))
 opacity=target*(1-smooth((yy-end)/6))
 # Only where the neck silhouette transitions, nearest source RGB supplies the
 # edge. The body's actual RGB supplies the lower join; no texture is invented.
 _,near=ndi.distance_transform_edt(alpha<128,return_indices=True)
 extended=corrected[near[0],near[1]]
 head_rgb=np.where((alpha>0)[:,:,None],corrected,extended)
 if blend_neck:head_rgb=head_rgb*(1-blend[:,:,None])+body[:,:,:3]*blend[:,:,None]
 den=ba*(1-opacity)
 visible=np.divide(target-opacity,den,out=np.zeros_like(den),where=den>1e-8)
 visible[yy<205]=0;visible[yy>=277]=1;opacity[yy>=277]=0
 head=np.zeros_like(base);head[:360,:,:3]=np.rint(head_rgb).astype('uint8');head[:360,:,3]=np.rint(opacity*255).astype('uint8')
 # Remove only disconnected alpha<=16 remnants after the final join. Piercings
 # with opaque centres remain, as do connected antialiasing and natural holes.
 labels,n=ndi.label(head[:,:,3]>0,np.ones((3,3)))
 detach=np.isin(labels,np.flatnonzero(ndi.maximum(head[:,:,3],labels,np.arange(1,n+1))<=16)+1)
 head[detach]=0;head[head[:,:,3]==0]=0
 mask=np.full_like(base,255);mask[:360,:,3]=np.rint(np.clip(visible,0,1)*255).astype('uint8')
 return head,mask,{'skin_gain_rgb':gain.tolist(),'neck_sample_source_rgb':src.tolist(),'neck_sample_body_rgb':dst.tolist(),'source_weak_pixels_removed':int((remote|weak).sum()),'registered_weak_pixels_removed':int(remote_after.sum()),'final_detached_weak_pixels_removed':int(detach.sum())}

def run():
 config=json.loads((REPORT/'registration.json').read_text());base=np.array(Image.open(ROOT/'base_female.png').convert('RGBA'))
 assert sha(ROOT/'base_female.png')==config['base_sha256']
 entries=[]
 for e in config['heads']:
  assert sha(REPORT/e['source'])==e['source_sha256']
  head,mask,metrics=prepare(e,base);e=dict(e,metrics=metrics)
  for typ,im in [('head',head),('body',mask)]:
   path=f'assets/wardrobe/faces/{"masks/" if typ=="body" else ""}female_new_{e["kind"]}_{typ}.png'
   Image.fromarray(im).save(ROOT/path,optimize=True)
   e['output' if typ=='head' else 'mask']=path;e['sha256' if typ=='head' else 'mask_sha256']=sha(ROOT/path)
  entries.append(e)
 (REPORT/'integration-manifest.json').write_text(json.dumps(dict(baseline=config['baseline'],files=entries,protected_sha256=config['protected_sha256']),ensure_ascii=False,indent=2)+'\n')
 print('Prepared',len(entries),'new female heads; protected resources unchanged')

if __name__=='__main__':run()
