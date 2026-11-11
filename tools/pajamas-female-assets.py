"""Reconstructed lower-pajama source extraction after environment replacement.

The exact old lower-clothes extractor tail was not retained in tool history.
This recovery therefore requires visual review and explicitly compares old
recorded hashes; it must not be represented as byte-identical unless verified.
Only approved original board cloth pixels are sampled. No image generation.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
import cv2,numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
P=argparse.ArgumentParser(description=__doc__);P.add_argument('--root',type=Path,default=Path('/workspace/palata404'));P.add_argument('--write',action='store_true');A=P.parse_args();ROOT=A.root
REVIEW=ROOT/'review/pajamas-implementation-20261111/female';REG=REVIEW/'registered';REF=ROOT/'review/pajamas-implementation-20261111/references';OUT=ROOT/'assets/wardrobe/clothing/patient/pajamas/female';TEMP=ROOT/'review/artist-candidates/female-lower-recovery'
for p in [REG,TEMP]:p.mkdir(parents=True,exist_ok=True)
SOURCE=REVIEW/'approved-source.png';rgb=np.array(Image.open(SOURCE).convert('RGB'));H,W=rgb.shape[:2];R,G,B=[rgb[:,:,i].astype(float) for i in range(3)];blue=((R-B<25)&(G-B<17)&((R+G+B)/3<183)).astype('uint8')*255
S=1.966;SX=1.98;DY=33-121*S

def poly(points):
 m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.array(points,np.int32)],255,lineType=cv2.LINE_AA);return m

def premul(im):
 a=im[:,:,3:4].astype('float32')/255;return np.concatenate((im[:,:,:3].astype('float32')*a,a*255),axis=2)

def unpremul(im):
 a=np.clip(im[:,:,3:4],0,255);c=np.divide(im[:,:,:3]*255,a,out=np.zeros_like(im[:,:,:3]),where=a>.01);return np.dstack((np.clip(c,0,255),a)).astype('uint8')

def cut(mask):
 a=cv2.GaussianBlur(mask,(3,3),.35);im=np.dstack((rgb,a));im[a==0,:3]=0;return im

def register(im,cx=1210):
 m=np.array([[SX,0,474-cx*SX],[0,S,DY]],np.float32);return unpremul(cv2.warpAffine(premul(im),m,(941,1672),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))

def over(*images):
 im=Image.new('RGBA',(941,1672))
 for item in images:im.alpha_composite(Image.fromarray(item))
 return np.array(im)

def fit_pants_rows(im):
 # This function is recovered exactly from the earlier readable source.
 base=np.array(Image.open(REF/'female-idle.png').convert('RGBA'))[:1672,:941,3]
 yy,xx=np.mgrid[0:1672,0:941];pieces=[]
 for side,(x0,x1) in enumerate([(0,474),(474,941)]):
  olo=np.full(1672,np.nan);ohi=np.full(1672,np.nan);nlo=np.full(1672,np.nan);nhi=np.full(1672,np.nan)
  for y in range(1672):
   xs=np.where(im[y,x0:x1,3]>30)[0]
   if len(xs)<2:continue
   lo,hi=int(xs.min()+x0),int(xs.max()+x0);olo[y]=lo;ohi[y]=hi
   vals=(base[y,x0:x1]>128).astype('uint8');runs=[];a=None
   for k,v in enumerate(vals):
    if v and a is None:a=k
    if a is not None and (not v or k==len(vals)-1):
     b=k if v else k-1
     if b-a>10:runs.append((a+x0,b+x0))
     a=None
   if runs:
    b0,b1=runs[-1] if side==0 else runs[0];width=max(hi-lo,b1-b0+24);center=(b0+b1)/2;nlo[y]=center-width/2;nhi[y]=center+width/2
   else:nlo[y]=lo;nhi[y]=hi
  valid=np.where(~np.isnan(olo))[0]
  for arr in [olo,ohi,nlo,nhi]:arr[:]=gaussian_filter1d(np.interp(np.arange(1672),valid,arr[valid]),8)
  sx=olo[:,None]+(xx-nlo[:,None])*(ohi-olo)[:,None]/np.maximum(1,(nhi-nlo))[:,None]
  # Preserve the curved cloth hem as a shape; never widen its partial last
  # scanlines to the original bare-foot width.
  fixed_sx=olo[1450]+(xx-nlo[1450])*(ohi[1450]-olo[1450])/max(1,nhi[1450]-nlo[1450])
  mix=np.clip((yy-1430)/70,0,1);sx=sx*(1-mix)+fixed_sx*mix
  out=unpremul(cv2.remap(premul(im),sx.astype('float32'),yy.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
  allowed=(((xx>=nlo[:,None])&(xx<=nhi[:,None]))|(yy>1500))&(xx>=x0)&(xx<x1)&(yy>=valid.min())&(yy<=valid.max());out[~allowed]=0;pieces.append(out)
 return over(*pieces)

# Source contour coordinates will be verified against the recovered immutable
# board before this recovery is promoted. These preserve the approved design.
PANTS_POLY=[(1104,527),(1312,527),(1320,553),(1317,612),(1308,675),(1304,734),(1309,800),(1320,874),(1314,904),(1254,905),(1246,875),(1234,817),(1220,747),(1207,659),(1198,730),(1183,809),(1173,866),(1168,905),(1106,902),(1101,868),(1100,815),(1095,758),(1096,709),(1104,648),(1101,585)]
roi=poly(PANTS_POLY);seed=np.minimum(blue,roi);seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8));cnts,_=cv2.findContours(seed,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);mask=np.zeros((H,W),np.uint8)
for c in cnts:
 if cv2.contourArea(c)>100:cv2.drawContours(mask,[c],-1,255,-1)
mask=np.minimum(mask,roi)
# Exact visible curved trouser hems exclude the touching slipper uppers.
for x in range(1080,1190):
 bottom=int(np.interp(x,[1095,1112,1136,1154,1174,1190],[890,892,889,895,903,903]));mask[bottom+1:,x]=0
for x in range(1240,1335):
 bottom=int(np.interp(x,[1240,1254,1272,1295,1314,1335],[906,906,898,889,895,895]));mask[bottom+1:,x]=0
pants=fit_pants_rows(register(cut(mask)))
yy0,xx0=np.mgrid[0:1672,0:941]
hem_y=np.where(yy0>1450,1450+(yy0-1450)/1.35,yy0).astype('float32')
pants=unpremul(cv2.remap(premul(pants),xx0.astype('float32'),hem_y,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
# The source shirt hem reaches below the first registered trouser rows.
# Keep only clean trouser weave below native847 before extending its waist.
pants[:847]=0
# Reconstruct the independently wearable waistband using approved upper-trouser
# weave. Its whole upper portion is hidden by the unchanged shirt in full sets.
native=np.array(Image.open(REF/'female-idle.png').convert('RGBA'))[:1672,:941]
yy,xx=np.mgrid[0:1672,0:941];top=min(np.where(pants[:,:,3].max(axis=1)>127)[0]);waist=pants.copy();sy=np.broadcast_to((top+np.maximum(0,top-yy)*.15).astype('float32'),(1672,941));upper=unpremul(cv2.remap(premul(pants),xx.astype('float32'),sy,cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
for y in range(650,top):
 row=native[y,275:675,3]>128
 d=np.diff(np.r_[False,row,False].astype(int));runs=[(int(a)+275,int(b)-1+275) for a,b in zip(np.where(d==1)[0],np.where(d==-1)[0]) if b-a>=30]
 if not runs:continue
 lo=min(a for a,b in runs)-12;hi=max(b for a,b in runs)+12
 upper[y,:lo]=0;upper[y,hi+1:]=0;upper[y,lo:hi+1,3]=255
waist[:650]=0;waist[650:top]=upper[650:top];pants=waist
cloth_color=pants[:,:,:3].astype('int16');pants[(yy>1450)&(cloth_color[:,:,0]-cloth_color[:,:,2]>30),3]=0
# Light antialias cleanup only at the last curved hems; the cloth UV and body
# remain unchanged. Premultiplication prevents dark fringes at new AA pixels.
coverage=(pants[:,:,3]>0).astype('uint8');edge=cv2.dilate(coverage,np.ones((3,3),np.uint8))!=cv2.erode(coverage,np.ones((3,3),np.uint8))
soft=unpremul(cv2.GaussianBlur(premul(pants),(3,3),.65));hem_edge=edge&(yy>1510);pants[hem_edge]=soft[hem_edge]
# Footwear contour placeholders are recorded explicitly and will be inspected.
SHOE_LEFT=[(1143,890),(1152,892),(1161,899),(1167,908),(1171,916),(1173,924),(1171,929),(1162,932),(1158,937),(1147,941),(1129,944),(1113,943),(1100,939),(1098,933),(1098,927),(1104,918),(1115,906),(1125,897),(1134,892)]
SHOE_RIGHT=[(1283,890),(1292,891),(1301,898),(1307,906),(1314,911),(1323,917),(1331,923),(1335,929),(1334,936),(1326,942),(1311,944),(1291,939),(1272,930),(1257,926),(1250,921),(1252,914),(1255,903),(1268,896)]
shoe_roi=np.maximum(poly(SHOE_LEFT),poly(SHOE_RIGHT));shoe_values=rgb.astype('int16')
shoe_seed=((shoe_values[:,:,0]-shoe_values[:,:,2]<45)&(shoe_values[:,:,1]-shoe_values[:,:,2]<28)&(shoe_values.mean(2)<155)&(shoe_roi>0)).astype('uint8')*255
shoe_seed=cv2.morphologyEx(shoe_seed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
cs,_=cv2.findContours(shoe_seed,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);shoe_mask=np.zeros((H,W),np.uint8)
for c in cs:
 if cv2.contourArea(c)>100:cv2.drawContours(shoe_mask,[c],-1,255,-1)
shoe_mask=np.minimum(shoe_mask,shoe_roi)
# Follow the painted slipper rim/sole, excluding touching striped trouser fabric
# and the cast floor shadow. All sampled pixels remain original approved art.
for x in range(1090,1180):
 top_edge=int(np.interp(x,[1090,1098,1105,1114,1124,1136,1144,1154,1163,1168,1172,1180],[932,925,915,904,897,893,894,898,905,915,925,935]))
 bottom_edge=int(np.interp(x,[1090,1098,1103,1114,1128,1141,1153,1161,1167,1169,1172,1180],[930,935,940,943,943,941,937,932,927,923,922,920]))
 shoe_mask[:top_edge+3,x]=0;shoe_mask[bottom_edge+1:,x]=0
for x in range(1240,1340):
 top_edge=int(np.interp(x,[1240,1256,1260,1270,1280,1288,1296,1304,1312,1321,1330,1335,1340],[914,906,902,897,894,894,898,905,912,919,926,932,938]))
 bottom_edge=int(np.interp(x,[1240,1256,1264,1274,1284,1295,1308,1319,1328,1334,1340],[914,919,923,929,935,940,943,943,940,935,930]))
 shoe_mask[:top_edge+3,x]=0;shoe_mask[bottom_edge+1:,x]=0
shoe_mask[:,:1098]=0;shoe_mask[:,1166:1240]=0;shoe_mask[:,1240:1256]=0
shoes=register(cut(shoe_mask))
# Register closed slippers to the native ankle centers without changing body.
xx1,yy1=np.meshgrid(np.arange(941),np.arange(1672));shift=np.where(xx1<474,22,-27)
footwear=unpremul(cv2.remap(premul(shoes),(xx1-shift).astype('float32'),yy1.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
# Only original native foot pixels below1578 are erased. Ankles stay intact.
footmask=np.zeros((1672,941,4),np.uint8);footmask[:,:,3]=np.where(native[:,:,3]>1,255,0).astype('uint8');footmask[:1578,:,3]=0
items={'pants':pants,'footwear':footwear,'mask-footwear':footmask}
expected={'pants':'1fac906116edb262dfa12cdb678f6ee34ec4146310635e8b7b17be4619e98a22','footwear':'aa65e2d2b352446286a895be2314f530204a6a452817b380863ab5b3e10fdb02','mask-footwear':'01d885ad746c7c711be967094c9c62371ade55eb6b64e1a7b40109b06154635e'}
meta={'stage':('RECOVERY_LOCAL_ASSET_FREEZE_RUNTIME_REVIEW_PENDING' if A.write else 'RECOVERY_DRAFT_REQUIRES_VISUAL_REVIEW'),'notes':'Full original lower extractor tail was lost. Recorded source-only method recreated; hash comparison must disclose differences. No new generation.','records':[]}
for name,im in items.items():
 p=TEMP/(name+'.png');Image.fromarray(im).save(p);sha=hashlib.sha256(p.read_bytes()).hexdigest();meta['records'].append({'name':name,'sha256':sha,'expectedOriginal':expected[name],'matchesOriginal':sha==expected[name]})
 if A.write:
  OUT.mkdir(parents=True,exist_ok=True);Image.fromarray(im).save(REG/(name+'.png'));Image.fromarray(im).save(OUT/(name+'.webp'),format='WEBP',lossless=(name=='mask-footwear'),quality=88,method=6)
  if name!='mask-footwear':
   thumb=Image.fromarray(im);thumb=thumb.crop(thumb.getbbox());thumb.thumbnail((232,232),Image.Resampling.LANCZOS);t=Image.new('RGBA',(256,256));t.alpha_composite(thumb,((256-thumb.width)//2,(256-thumb.height)//2));t.save(OUT/('thumb-'+name+'.webp'),format='WEBP',quality=88,method=6)
if A.write:
 for rec in meta['records']:
  runtime=OUT/(rec['name']+'.webp');rec['runtime']=str(runtime.relative_to(ROOT));rec['runtimeBytes']=runtime.stat().st_size;rec['runtimeSha256']=hashlib.sha256(runtime.read_bytes()).hexdigest()
 meta['sourceSha256']=hashlib.sha256(SOURCE.read_bytes()).hexdigest();meta['source']=str(SOURCE.relative_to(ROOT));meta['targetSize']=[941,1672];meta['bodyChanged']=False
(TEMP/'lower-recovery-metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
