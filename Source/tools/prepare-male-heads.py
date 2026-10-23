"""Register the supplied male portraits using only uniform transforms and masks.

No generated pixels, RGB repaint, tone correction or hairstyle edits. The body
is copied verbatim. Lower neck geometry is composited with complementary alpha
only; the original registered portrait RGB is retained even in the transition.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'review/male-heads-full-library'
spec=importlib.util.spec_from_file_location('neck_math',ROOT/'tools/prepare-female-faces.py')
math=importlib.util.module_from_spec(spec);spec.loader.exec_module(math)


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def register(im,config):
    s,tx,ty=config['scale'],config['x'],config['y']
    scaled=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
    sx,sy=scaled.width/im.width,scaled.height/im.height
    return scaled.transform((941,1672),Image.Transform.AFFINE,
        (sx/s,0,-tx*sx/s,0,sy/s,-ty*sy/s),Image.Resampling.BICUBIC)


def pair(registered,base):
    a=registered[:360].copy();body=base[:360]
    alpha=a[:,:,3];remote=(alpha>0)&(alpha<=16)&(ndi.distance_transform_edt(alpha<32)>3)
    alpha[remote]=0
    labels,n=ndi.label(alpha>0,np.ones((3,3)))
    alpha[np.isin(labels,np.flatnonzero(ndi.maximum(alpha,labels,np.arange(1,n+1))<=16)+1)]=0
    # Alpha mask correction only: never change a portrait's RGB, even at ears.
    alpha[ndi.distance_transform_edt(alpha>=128)>2]=255
    ha,ba=alpha/255,body[:,:,3]/255
    y,x=np.mgrid[:360,:941];arc=np.minimum(((x-474)/65)**2,1)
    start,end=245-20*arc,280-18*arc
    blend=math.smooth((y-start)/(end-start))
    target=np.clip((1-blend)*math.distance(ha)+blend*math.distance(ba)+.5,0,1)
    target[blend==0]=ha[blend==0];target[blend==1]=ba[blend==1]
    # No extension/painting outside the supplied portrait: the actual base
    # supplies any neck pixels missing from the source silhouette.
    target=np.minimum(target,np.maximum(ha,ba))
    opacity=np.minimum(ha,target*(1-math.smooth((y-end)/6)))
    den=ba*(1-opacity)
    visible=np.divide(target-opacity,den,out=np.zeros_like(den),where=den>1e-8)
    visible[y<210]=0;visible[y>=286]=1;opacity[y>=286]=0
    head=np.zeros_like(base);head[:360]=a;head[:360,:,3]=np.rint(opacity*255).astype('uint8')
    head[head[:,:,3]==0]=0
    mask=np.full_like(base,255);mask[:360,:,3]=np.rint(np.clip(visible,0,1)*255).astype('uint8')
    return head,mask,{'remote_weak_alpha_removed':int(remote.sum())}


def run():
    config=json.loads((REPORT/'registration.json').read_text())
    source=REPORT/config['base']['source'];assert sha(source)==config['base']['source_sha256']
    (ROOT/'base_male.png').write_bytes(source.read_bytes())
    base=np.array(Image.open(source).convert('RGBA'));assert base.shape==(1672,941,4)
    files=[]
    for entry in config['heads']:
        p=REPORT/entry['source'];assert sha(p)==entry['source_sha256']
        registered=np.array(register(Image.open(p).convert('RGBA'),entry['registration']))
        head,mask,cleanup=pair(registered,base)
        assert np.array_equal(head[:218,:,:3][head[:218,:,3]>0],registered[:218,:,:3][head[:218,:,3]>0])
        entry=dict(entry,cleanup=cleanup)
        for name,part in [('head',head),('body',mask)]:
            rel=f'assets/wardrobe/faces/{"masks/" if name=="body" else ""}male_{entry["kind"]}_{name}.png'
            Image.fromarray(part).save(ROOT/rel,optimize=True)
            entry['output' if name=='head' else 'mask']=rel
            entry['sha256' if name=='head' else 'mask_sha256']=sha(ROOT/rel)
        files.append(entry)
    (REPORT/'integration-manifest.json').write_text(json.dumps({'baseline':config['baseline'],
        'base_sha256':sha(ROOT/'base_male.png'),'files':files,'protected_sha256':config['protected_sha256']},ensure_ascii=False,indent=2)+'\n')
    print('Prepared',len(files),'male heads; female art/hair untouched')


if __name__=='__main__':run()
