"""Use the approved young female head as the shared, uniform hair fitting frame.

Approved source assets and the reference remain byte-identical. This prepares
registered derivatives and new complementary neck masks; no image generation.
"""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'review/female-head-standard';SIZE=(941,1672)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def distance(a):return ndi.distance_transform_edt(a>=.5)-ndi.distance_transform_edt(a<.5)
def register(im,p):
 s,tx,ty=p['scale'],p['x'],p['y'];scaled=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);sx,sy=scaled.width/im.width,scaled.height/im.height
 return scaled.transform(SIZE,Image.Transform.AFFINE,(sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC)
def metrics(a):
 a=a[:,:,3];y,x=np.where(a[:218]>=128);row=100+int(np.argmax((a[100:190]>=128).sum(axis=1)));xx=np.where(a[row]>=128)[0]
 return {'top_y':int(y.min()),'left_x':int(x.min()),'right_x':int(x.max()),'ear_span':int(xx.max()-xx.min()+1),'ear_row_y':row,'center_x':float((xx.min()+xx.max())/2)}
def pair(registered,body,c):
 h=registered[:380].copy();base=body[:380];alpha=h[:,:,3]
 remote=(alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>3);alpha[remote]=0
 yy,xx=np.mgrid[:380,:941];alpha[ndi.distance_transform_edt(alpha>=128)>2]=255
 ha,ba=alpha/255,base[:,:,3]/255;arc=np.minimum(((xx-c['center_x'])/c['radius'])**2,1)
 start=c['start_center_y']+(c['start_side_y']-c['start_center_y'])*arc;end=c['end_center_y']+(c['end_side_y']-c['end_center_y'])*arc;blend=smooth((yy-start)/(end-start))
 target=np.clip((1-blend)*distance(ha)+blend*distance(ba)+.5,0,1);target[blend==0]=ha[blend==0];target[blend==1]=ba[blend==1];target=np.minimum(target,np.maximum(ha,ba))
 opacity=np.minimum(ha,target*(1-smooth((yy-end)/6)))
 rgb=h[:,:,:3].astype(float);_,near=ndi.distance_transform_edt(alpha<128,return_indices=True);rgb=np.where((alpha>0)[:,:,None],rgb,rgb[near[0],near[1]])
 rgb=rgb*(1-blend[:,:,None])+base[:,:,:3]*blend[:,:,None]
 den=ba*(1-opacity);visible=np.divide(target-opacity,den,out=np.zeros_like(den),where=den>1e-8)
 visible[yy<240]=0;visible[yy>=c['body_restored_y']]=1;opacity[yy>=c['body_restored_y']]=0
 out=np.zeros_like(body);out[:380,:,:3]=np.rint(rgb).clip(0,255).astype('uint8');out[:380,:,3]=np.rint(opacity*255).astype('uint8')
 lab,n=ndi.label(out[:,:,3]>0,np.ones((3,3)));weak=np.isin(lab,np.flatnonzero(ndi.maximum(out[:,:,3],lab,np.arange(1,n+1))<=16)+1);out[weak]=0;out[out[:,:,3]==0]=0
 mask=np.full_like(body,255);mask[:380,:,3]=np.ceil(np.clip(visible,0,1)*255-1e-9).astype('uint8');return out,mask

def run():
 config=json.loads((D/'registration.json').read_text());base=np.array(Image.open(ROOT/'base_female.png').convert('RGBA'));entries=[]
 for item in config['heads']:
  assert sha(ROOT/item['source'])==item['source_sha256'];e=dict(item)
  if e['reference']:
   e.update(output=e['source'],mask=e['previous_mask'],sha256=e['source_sha256'],mask_sha256=sha(ROOT/e['previous_mask']),actual=metrics(np.array(Image.open(ROOT/e['source']).convert('RGBA'))));entries.append(e);continue
  im=Image.open(ROOT/e['source']).convert('RGBA');p=dict(e['registration'])
  # Adjust subpixel placement for the sampled alpha threshold, retaining a
  # single scale. One-pixel AA uncertainty is recorded, never hidden by warps.
  for _ in range(3):
   registered=np.array(register(im,p));m=metrics(registered);p['y']+=33-m['top_y'];p['x']+=472.5-m['center_x']
  registered=np.array(register(im,p));m=metrics(registered)
  if m['ear_span']!=176 or m['center_x']!=472.5:
   choices=[];nominal=e['registration']['scale']
   for factor in [1,.998,1.002,.996,1.004,.994,1.006]:
    q=dict(e['registration']);q['scale']=nominal*factor
    q['x']=472.5-e['source_metrics']['center_x']*q['scale'];q['y']=33-e['source_metrics']['top_y']*q['scale']
    for _ in range(3):
     a=np.array(register(im,q));v=metrics(a);q['x']+=472.5-v['center_x'];q['y']+=33-v['top_y']
    a=np.array(register(im,q));v=metrics(a);score=(abs(v['ear_span']-176)*20+abs(v['center_x']-472.5)*5+abs(v['top_y']-33)*10,abs(factor-1))
    choices.append((score,q,a))
   _,p,registered=min(choices,key=lambda c:c[0])
  head,mask=pair(registered,base,config['neck']);e['registration']=p
  for typ,array in [('head',head),('body',mask)]:
   rel='assets/wardrobe/faces/'+('masks/' if typ=='body' else '')+'standardized/'+e['kind']+'_'+typ+'.png';path=ROOT/rel;path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(array).save(path,optimize=True);e['output' if typ=='head' else 'mask']=rel;e['sha256' if typ=='head' else 'mask_sha256']=sha(path)
  e['actual']=metrics(head);entries.append(e)
 manifest={'baseline':config['baseline'],'reference_id':config['reference_id'],'target':config['target'],'neck':config['neck'],'heads':entries,'protected_sha256':config['protected_sha256']}
 (D/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print('Prepared',len(entries)-1,'uniform derivatives; reference and source artwork unchanged')
if __name__=='__main__':run()
