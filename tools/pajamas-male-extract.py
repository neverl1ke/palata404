#!/usr/bin/env python3
"""Recovered male source prep: unchanged approved torso, pants and slippers.

Reconstructed from pre-outage tool output. Obsolete procedural sleeve drafts
are deliberately not rebuilt; the following artist helper owns final sleeves.
No base/avatar/weapon/head pixels are edited.
"""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np
from PIL import Image,ImageFilter
from scipy.ndimage import binary_fill_holes
from scipy.spatial import Delaunay

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'review/pajamas-implementation-20261111/male/approved-male-concept.png'
REF=ROOT/'review/pajamas-implementation-20261111/references'
OUT=ROOT/'assets/wardrobe/clothing/patient/pajamas/male'
REVIEW=ROOT/'review/pajamas-implementation-20261111/male'
for p in [OUT,REVIEW/'registered',REVIEW/'source-masks',REVIEW/'overlap-layers']:
    p.mkdir(parents=True,exist_ok=True)
board=np.array(Image.open(SOURCE).convert('RGB'));H,W=board.shape[:2]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='1943dc7c37aa15bff0cda043d37d80845b92a894045b6ba720197a278c2c5885'
TOP_POLY=[(288,223),(302,210),(340,210),(362,226),(399,237),(425,252),(440,275),(450,311),(460,363),(469,416),(477,474),(481,526),(442,531),(432,490),(424,446),(419,405),(413,384),(413,444),(419,531),(229,535),(232,468),(235,411),(230,376),(217,425),(208,472),(203,524),(163,525),(165,486),(171,445),(180,397),(187,350),(196,305),(205,273),(219,252),(249,235)]
TORSO_POLY=[(288,225),(304,213),(343,213),(365,227),(402,243),(426,261),(414,319),(414,376),(413,432),(419,533),(229,533),(232,431),(234,376),(239,319),(217,261),(248,242)]
PANTS_POLY=[(215,526),(440,526),(440,905),(346,905),(326,600),(322,600),(286,905),(210,905)]
SHOE_POLYS=[[(225,895),(240,891),(255,896),(270,902),(275,915),(274,925),(267,933),(255,939),(237,941),(209,940),(201,935),(199,926),(203,917),(211,906)],[(358,894),(385,888),(408,894),(427,908),(449,918),(465,929),(463,942),(441,947),(411,944),(386,939),(366,933),(348,925),(347,909)]]

def local_image(shift):
    out=np.zeros_like(board);out[:,:W-shift]=board[:,shift:];return out
def poly_mask(poly):
    m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.array(poly,np.int32)],255);return m
def color_matte(rgb,poly,shoe=False):
    area=poly_mask(poly);values=rgb.astype(np.float32)
    cool=(values[:,:,0]-values[:,:,2])<(36 if shoe else 25)
    tone=values.mean(2)<(163 if shoe else 178)
    seed=(cool&tone&(area>0)).astype(np.uint8)*255
    seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(seed,8)
    if n<2:raise RuntimeError('No garment component')
    seed=(labels==(1+np.argmax(stats[1:,cv2.CC_STAT_AREA]))).astype(np.uint8)
    seed=binary_fill_holes(seed).astype(np.uint8)*255;seed=np.minimum(seed,area)
    alpha=np.array(Image.fromarray(seed).filter(ImageFilter.GaussianBlur(.35)))
    alpha[seed==255]=255;return alpha
def garment(rgb,alpha):return Image.fromarray(np.dstack([rgb,alpha]),'RGBA')
def premultiplied(im):
    a=np.array(im).astype(np.float32);a[:,:,:3]*=a[:,:,3:4]/255;return a
def finish_rgba(values):
    values=np.maximum(values,0);alpha=np.clip(values[:,:,3],0,255)
    color=np.zeros_like(values[:,:,:3]);np.divide(values[:,:,:3]*255,alpha[:,:,None],out=color,where=alpha[:,:,None]>.01)
    result=np.dstack([np.clip(color,0,255),alpha]).round().astype(np.uint8)
    result[result[:,:,3]==0,:3]=0;return Image.fromarray(result,'RGBA')
def mesh_warp(im,source,target):
    source=np.array(source,dtype=np.float32);target=np.array(target,dtype=np.float32)
    src=premultiplied(im);dest=np.zeros((1672,941,4),np.float32)
    for ids in Delaunay(source).simplices:
        st=source[ids];dt=target[ids]
        if cv2.contourArea(st,oriented=True)*cv2.contourArea(dt,oriented=True)<=0:continue
        x0=max(0,int(np.floor(dt[:,0].min()))-2);x1=min(941,int(np.ceil(dt[:,0].max()))+3)
        y0=max(0,int(np.floor(dt[:,1].min()))-2);y1=min(1672,int(np.ceil(dt[:,1].max()))+3)
        if x1<=x0 or y1<=y0:continue
        m=cv2.getAffineTransform(st,dt);m[:,2]-=[x0,y0]
        crop=cv2.warpAffine(src,m,(x1-x0,y1-y0),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT)
        mask=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillConvexPoly(mask,np.rint(dt-[x0,y0]).astype(np.int32),255)
        region=dest[y0:y1,x0:x1];region[mask>0]=crop[mask>0]
    return finish_rgba(dest)

middle=local_image(446);full_alpha=color_matte(middle,TOP_POLY)
torso=garment(middle,np.minimum(full_alpha,poly_mask(TORSO_POLY)))
scale=1628/832
matrix=np.array([[2.,0,474-325*2.],[0,scale,30-112*scale]],np.float32)
torso=finish_rgba(cv2.warpAffine(premultiplied(torso),matrix,(941,1672),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT))
for pose in ['idle','melee','rifle']:
    torso.save(REVIEW/'overlap-layers'/f'{pose}-torso.png')

rifle=local_image(886);lower=np.zeros_like(rifle);lower[:,:W-10]=rifle[:,10:]
pants_alpha=color_matte(lower,PANTS_POLY)
foot_alpha=np.zeros((H,W),np.uint8)
for polygon in SHOE_POLYS:
    a=color_matte(lower,polygon,True);a=cv2.erode(a,np.ones((3,3),np.uint8));foot_alpha=np.maximum(foot_alpha,a)
source=[(232,525),(325,525),(418,525),(225,600),(323,600),(328,600),(420,600),(228,700),(304,700),(341,700),(420,700),(218,800),(287,800),(349,800),(421,800),(215,895),(279,895),(357,895),(425,895)]
target=[(280,842),(474,842),(673,842),(274,985),(470,985),(490,985),(682,985),(260,1181),(448,1181),(494,1181),(683,1181),(273,1376),(419,1376),(517,1376),(667,1376),(277,1576),(402,1576),(526,1576),(669,1576)]
for x,y in [(190,510),(450,510),(190,915),(450,915)]:
    source.append((x,y));target.append((474+(x-325)*2.12,30+(y-112)*scale))
pants=mesh_warp(garment(lower,pants_alpha),source,target)
yy,xx=np.mgrid[:1672,:941].astype(np.float32)
extension=cv2.remap(premultiplied(pants),xx,850+(yy-700)*.64,cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT)
wm=np.zeros((1672,941),np.uint8)
cv2.fillPoly(wm,[np.array([(338,700),(636,700),(649,723),(664,781),(675,849),(279,849),(295,781),(313,727)],np.int32)],255)
extension[wm==0]=0;waist=finish_rgba(extension);waist.alpha_composite(pants);pants=waist
sx=2.12;matrix=np.array([[sx,0,474-325*sx],[0,scale,34-112*scale]],np.float32)
foot=cv2.warpAffine(premultiplied(garment(lower,foot_alpha)),matrix,(941,1672),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT)
shift=np.where(xx<474,25,-20).astype(np.float32)
footwear=finish_rgba(cv2.remap(foot,xx-shift,yy,cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT))
ref_alpha=np.array(Image.open(REF/'male-idle.png').getchannel('A'))[:,:941]
remove=np.zeros((1672,941),np.uint8);remove[1552:]=np.where(ref_alpha[1552:]>1,255,0).astype(np.uint8)
remove=cv2.dilate(remove,np.ones((3,3),np.uint8));remove[:1552]=0
mask=Image.new('RGBA',(941,1672),(255,255,255,0));mask.putalpha(Image.fromarray(remove))
mask.save(REVIEW/'registered/mask-footwear.png',optimize=True)
mask.save(OUT/'mask-footwear.webp',lossless=True,method=6,exact=True)
pieces={'pants':pants,'footwear':footwear}
# Intermediate top is canonical torso only. Final artist helper replaces it.
pieces.update({f'top-{pose}':torso for pose in ['idle','melee','rifle']})
records=[]
for name,im in pieces.items():
    png=REVIEW/'registered'/f'{name}.png';webp=OUT/f'{name}.webp'
    im.save(png,optimize=True);im.save(webp,quality=88,method=6,exact=True)
    records.append({'name':name,'png':str(png.relative_to(ROOT)),'pngSha256':hashlib.sha256(png.read_bytes()).hexdigest(),'webp':str(webp.relative_to(ROOT)),'webpBytes':webp.stat().st_size,'registeredBbox':im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()})
for name,donor in [('top','top-idle'),('pants','pants'),('footwear','footwear')]:
    im=pieces[donor];im=im.crop(im.getbbox());im.thumbnail((224,224),Image.Resampling.LANCZOS)
    thumb=Image.new('RGBA',(256,256));thumb.alpha_composite(im,((256-im.width)//2,(256-im.height)//2))
    thumb.save(OUT/f'thumb-{name}.webp',quality=91,method=6,exact=True)
metadata={'source':str(SOURCE.relative_to(ROOT)),'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'method':'Recovered source prep: exact approved canonical torso and unchanged lower pieces. Artist helper must follow for final sleeves.',
 'registeredSize':[941,1672],'runtimeSize':[941,1672],
 'mapping':{'sx':2.12,'sy':scale,'sourceCenterX':325,'targetCenterX':474,'sourceHeadTop':112,'targetHeadTop':30,'sourceSole':944,'targetSole':1658},
 'files':records,'readyForPublication':False}
(REVIEW/'extraction.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({'sourcePrepRecovered':True,'pieces':records},indent=2))
