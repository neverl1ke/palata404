"""Recovered exact final artist sleeve extraction; review-only unless --write.

The previous environment was lost. This reconstructs the recorded successful
recipe from history. Requires restored approved board, native references and
registered lower clothes. It never regenerates art or changes avatar anatomy.
"""
from pathlib import Path
import argparse,hashlib,json
import cv2
import numpy as np
from PIL import Image

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path('/workspace/palata404'))
parser.add_argument('--write',action='store_true')
ARGS=parser.parse_args();ROOT=ARGS.root
ART=ROOT/'review/sleeves-artist-20261111/female'
OLD=ROOT/'review/pajamas-implementation-20261111/female'
REF=ROOT/'review/pajamas-implementation-20261111/references'
OUT=ROOT/'review/artist-candidates';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=OLD/'approved-source.png'
rgb=np.array(Image.open(SOURCE).convert('RGB'));H,W=rgb.shape[:2]
R,G,B=[rgb[:,:,i].astype(float) for i in range(3)]
blue=((R-B<25)&(G-B<17)&((R+G+B)/3<183)).astype('uint8')*255
S=1.966;SX=1.98;DY=33-121*S

def source_poly(points):
 m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.array(points,np.int32)],255,lineType=cv2.LINE_AA);return m

def blue_shape(points,largest=False):
 roi=source_poly(points);seed=cv2.bitwise_and(blue,roi);seed=cv2.morphologyEx(seed,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
 cnts,_=cv2.findContours(seed,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);m=np.zeros_like(seed)
 if largest and cnts:cnts=[max(cnts,key=cv2.contourArea)]
 for c in cnts:
  if cv2.contourArea(c)>25:cv2.drawContours(m,[c],-1,255,-1)
 return cv2.bitwise_and(m,roi)

def cut(mask,colors=rgb):
 a=cv2.GaussianBlur(mask,(3,3),.35);im=np.dstack((colors,a));im[a==0,:3]=0;return im

def premul(im):
 a=im[:,:,3:4].astype('float32')/255;return np.concatenate((im[:,:,:3].astype('float32')*a,a*255),axis=2)

def unpremul(im):
 a=np.clip(im[:,:,3:4],0,255);c=np.divide(im[:,:,:3]*255,a,out=np.zeros_like(im[:,:,:3]),where=a>.01);return np.dstack((np.clip(c,0,255),a)).astype('uint8')

def register(im,cx):
 matrix=np.array([[SX,0,474-cx*SX],[0,S,DY]],np.float32)
 return unpremul(cv2.warpAffine(premul(im),matrix,(941,1672),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))

# This is exactly the earlier canonical torso preparation, held unchanged when
# user authorized new painted sleeves. It is not a new sleeve deformation.
full=blue_shape([(650,222),(850,222),(888,270),(916,470),(925,519),(862,519),(850,520),(680,520),(668,509),(605,510),(609,472),(641,370),(650,310)],True)
torso_region=source_poly([(694,222),(848,222),(853,304),(846,356),(837,394),(848,448),(873,520),(680,520),(700,451),(715,394),(705,357),(693,306)])
torso=register(cut(np.minimum(full,torso_region)),770)
yy,xx=np.mgrid[0:1672,0:941]
gain=np.interp(yy[:,0],[0,320,400,550,700,820,1671],[1,1,1.10,1.14,1.10,1.04,1])
torso=unpremul(cv2.remap(premul(torso),(474+(xx-474)/gain[:,None]).astype('float32'),yy.astype('float32'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
clean_approved_cloth=register(cut(full),770)

LEFT_IDLE=[(342,235),(319,245),(294,251),(271,261),(254,277),(241,302),(232,337),(228,377),(225,416),(215,449),(206,476),(201,506),(192,537),(185,566),(180,599),(173,632),(171,659),(169,683),(170,715),(184,719),(201,722),(219,727),(225,713),(230,682),(239,650),(250,615),(263,582),(274,549),(284,514),(294,480),(298,446),(299,409),(301,373),(306,331),(310,293),(327,260)]
RIGHT_IDLE=[(507,238),(544,250),(570,267),(589,290),(602,327),(608,373),(615,414),(625,450),(632,483),(639,511),(645,543),(650,580),(655,617),(662,658),(670,694),(672,720),(654,724),(635,728),(620,728),(615,706),(607,680),(599,651),(588,620),(577,586),(565,554),(555,522),(550,484),(552,447),(554,413),(556,375),(557,331),(553,292),(536,260)]
LEFT_MELEE=[(339,236),(316,245),(291,253),(268,264),(250,280),(236,310),(229,347),(225,387),(219,427),(209,463),(199,498),(190,532),(181,566),(174,600),(169,635),(163,672),(161,714),(180,719),(201,723),(217,726),(224,711),(230,680),(240,646),(251,612),(262,578),(274,543),(284,509),(293,473),(297,438),(299,400),(302,363),(306,324),(311,287),(327,257)]
RIGHT_MELEE=[(505,238),(544,250),(570,268),(587,291),(598,325),(605,367),(611,408),(620,448),(629,483),(637,518),(644,553),(650,588),(656,624),(663,662),(671,699),(673,722),(653,727),(635,729),(620,729),(615,706),(607,679),(597,648),(587,616),(575,580),(563,547),(555,514),(550,480),(551,444),(552,407),(554,370),(554,328),(549,290),(532,258)]
LEFT_RIFLE=[(337,237),(311,246),(286,254),(262,267),(243,285),(229,309),(214,337),(197,367),(176,397),(159,425),(145,451),(137,474),(138,490),(146,502),(168,511),(195,517),(229,519),(263,520),(295,524),(319,528),(328,525),(329,451),(303,450),(280,446),(259,438),(255,419),(268,395),(284,371),(298,345),(308,316),(316,287),(326,260)]
RIGHT_RIFLE=[(507,238),(544,250),(570,269),(589,293),(601,327),(608,366),(616,405),(628,441),(642,471),(651,493),(649,512),(637,533),(619,557),(609,578),(592,588),(572,580),(560,565),(553,547),(548,526),(549,503),(553,479),(555,452),(554,418),(554,381),(555,342),(552,305),(539,269)]

def poly(shape,points):
 m=np.zeros(shape,np.uint8);cv2.fillPoly(m,[np.array(points,np.int32)],255,lineType=cv2.LINE_AA);return m

def sleeve_art(pose):
 im=np.array(Image.open(ART/(pose+'-artist-raw.png')).convert('RGBA'));h,w=im.shape[:2]
 pts={'idle':(LEFT_IDLE,RIGHT_IDLE),'melee':(LEFT_MELEE,RIGHT_MELEE),'rifle':(LEFT_RIFLE,RIGHT_RIFLE)}[pose]
 roi=np.maximum(poly((h,w),pts[0]),poly((h,w),pts[1]));c=im[:,:,:3].astype('int16')
 gray=(c[:,:,0]-c[:,:,2]<22)&(c[:,:,1]-c[:,:,2]<15)
 if pose=='rifle':
  gun=[(238,365),(278,380),(326,397),(387,418),(416,421),(449,431),(478,444),(520,464),(559,482),(601,501),(647,519),(673,537),(711,557),(741,570),(764,582),(768,603),(744,609),(718,597),(696,584),(674,571),(652,561),(625,548),(599,538),(574,525),(548,516),(523,509),(506,504),(508,533),(527,577),(548,611),(549,642),(531,649),(513,639),(495,615),(481,588),(472,563),(467,534),(466,511),(439,499),(418,490),(391,480),(361,470),(331,457),(304,450),(278,443),(252,441),(231,437),(214,430),(217,409),(227,384)]
  hand1=[(328,455),(353,458),(377,469),(404,482),(421,491),(425,506),(408,526),(385,539),(365,535),(346,527),(329,518),(322,502),(323,479)]
  hand2=[(611,536),(625,529),(641,532),(654,545),(667,557),(677,575),(675,593),(655,603),(634,599),(615,588),(603,570)]
  exclude=np.maximum(poly((h,w),gun),np.maximum(poly((h,w),hand1),poly((h,w),hand2)));exclude=cv2.dilate(exclude,np.ones((3,3),np.uint8));roi[exclude>0]=0
 mask=np.minimum(roi,im[:,:,3]);mask[~gray]=0;im[:,:,3]=mask;im[mask==0,:3]=0
 scale=1672/1480;m=np.array([[scale,0,0],[0,scale,0]],np.float32)
 out=unpremul(cv2.warpAffine(premul(im),m,(941,1672),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT))
 return out,mask,m

meta={'stage':'RECOVERED_ARTIST_SLEEVE_RECIPE_REVIEW_PENDING','runtimeAssetsWritten':bool(ARGS.write),'poses':{},'recoveryNote':'Original final outputs were lost in environment replacement. These are reconstructed from recorded exact source pixels, polygons and math; compare expected final hashes before treating as identical.'}
Image.fromarray(torso).save(OUT/'female-canonical-torso.png')
expected={'idle':'48342a60235b6417ead097398a8c54b135b593afa58635bbd34bec0a4a566278','melee':'343d99ea0bbc918294b65d435f27a36df7e233b88aed23548e29fbbd80eaec44','rifle':'652be9234c57b805f188c2d2e5593866ff7ea331c6928608a1ec52d03a0a045b'}
for pose in ['idle','melee','rifle']:
 sleeve,mask,m=sleeve_art(pose);top=Image.fromarray(torso);top.alpha_composite(Image.fromarray(sleeve))
 native=np.array(Image.open(REF/('female-'+pose+'.png')).convert('RGBA'))[:1672,:941]
 rr,gg,bb=native[:,:,0].astype(int),native[:,:,1].astype(int),native[:,:,2].astype(int);skin=(rr-bb>25)&(rr-gg>5)&(native[:,:,3]>128)
 allowed=np.zeros((1672,941),np.uint8)
 cv2.fillPoly(allowed,[np.array([(255,288),(370,272),(375,352),(335,408),(257,403)],np.int32)],255)
 cv2.fillPoly(allowed,[np.array([(572,274),(678,296),(706,395),(631,414),(582,349)],np.int32)],255)
 if pose=='rifle':cv2.fillPoly(allowed,[np.array([(214,404),(274,394),(308,442),(283,472),(238,455)],np.int32)],255)
 a=np.array(top.getchannel('A'));visible=(skin&(a<245)&(allowed>0)).astype('uint8')*255;visible=cv2.dilate(visible,np.ones((3,3),np.uint8))
 under=clean_approved_cloth.copy();under[:,:,3]=np.minimum(under[:,:,3],visible)
 body_top=Image.fromarray(under);body_top.alpha_composite(Image.fromarray(torso));body_top.alpha_composite(Image.fromarray(sleeve));top=body_top
 Image.fromarray(under).save(OUT/('female-approved-cap-underlay-'+pose+'.png'))
 top.save(OUT/('female-top-'+pose+'.png'));Image.fromarray(sleeve).save(OUT/('female-sleeves-'+pose+'.png'));Image.fromarray(mask).save(OUT/('female-source-sleeve-mask-'+pose+'.png'))
 p=OUT/('female-top-'+pose+'.png');sha=hashlib.sha256(p.read_bytes()).hexdigest();src=ART/(pose+'-artist-raw.png')
 meta['poses'][pose]={'source':str(src.relative_to(ROOT)),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'canvasMatrix':m.tolist(),'candidate':str(p.relative_to(ROOT)),'candidateSha256':sha,'expectedOriginalFinalPngSha256':expected[pose],'matchesOriginalFinal':sha==expected[pose]}
 if ARGS.write:
  top.save(OLD/'registered'/('top-'+pose+'.png'));runtime=ROOT/'assets/wardrobe/clothing/patient/pajamas/female'/('top-'+pose+'.webp');runtime.parent.mkdir(parents=True,exist_ok=True);top.save(runtime,format='WEBP',quality=88,method=6)
  meta['poses'][pose]['runtime']={'path':str(runtime.relative_to(ROOT)),'bytes':runtime.stat().st_size,'sha256':hashlib.sha256(runtime.read_bytes()).hexdigest(),'dimensions':[941,1672],'quality':88}
if ARGS.write:
 im=Image.open(OUT/'female-top-idle.png').convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((232,232),Image.Resampling.LANCZOS);thumb=Image.new('RGBA',(256,256));thumb.alpha_composite(im,((256-im.width)//2,(256-im.height)//2));thumb.save(ROOT/'assets/wardrobe/clothing/patient/pajamas/female/thumb-top.webp',format='WEBP',quality=88,method=6)
(OUT/'female-artist-sleeves-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(meta,indent=2))
