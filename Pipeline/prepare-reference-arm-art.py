"""Extract authorized visible reference arm art, keeping the game's original body.
Only explicit limb/weapon ROIs enter the runtime. Original reference files are read-only.
"""
from pathlib import Path
import json,sys,hashlib,math
import numpy as np
import cv2
import importlib.util
_contact_spec=importlib.util.spec_from_file_location('contact_surfaces',Path(__file__).with_name('reference-contact-surfaces.py'));contact=importlib.util.module_from_spec(_contact_spec);_contact_spec.loader.exec_module(contact)
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
cv2.setNumThreads(1)
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';SOURCE_REVIEW=ROOT/'review/male-reference-arm-art';OUT=ROOT/'review/male-contact-surface-pass';OUT.mkdir(parents=True,exist_ok=True);RIG=CORE/'rigs/male_rig.json'
# Reference canvas941x1672 -> game canvas941x1672: no hand stretching.
SHIFT=[10,26]
POINTS={
 'rifle':{'right':{'shoulder':[277,356],'elbow':[203,553],'wrist':[331,575],'grip':[380,618]},'left':{'shoulder':[647,355],'elbow':[704,608],'wrist':[687,655],'grip':[665,682]}},
 'pistol':{'right':{'shoulder':[277,356],'elbow':[204,523],'wrist':[211,371],'grip':[220,325]}},
 'melee':{'right':{'shoulder':[277,356],'elbow':[232,548],'wrist':[185,781],'grip':[217,854]}},
}
POLYS={
 'rifle-right':[(277,302),(306,315),(323,347),(326,388),(311,426),(286,475),(264,505),(258,520),(300,531),(340,541),(368,552),(391,564),(411,582),(435,594),(447,611),(449,623),(440,630),(428,628),(417,618),(425,632),(417,640),(403,638),(391,630),(394,642),(382,647),(365,640),(352,632),(337,625),(327,610),(313,598),(294,593),(257,599),(218,605),(184,600),(162,589),(153,570),(155,544),(164,514),(179,479),(195,445),(216,416),(229,401),(233,369),(245,338),(263,316)],
 'rifle-left':[(624,302),(651,307),(673,326),(692,352),(705,389),(708,428),(704,459),(714,482),(722,523),(730,558),(737,594),(738,623),(728,645),(706,657),(690,664),(684,674),(686,687),(695,699),(701,716),(698,731),(686,740),(672,741),(660,734),(648,731),(635,722),(628,709),(624,693),(630,679),(635,671),(646,664),(651,660),(663,656),(669,642),(673,625),(671,603),(658,575),(648,552),(638,527),(629,504),(622,481),(610,453),(598,421),(594,387),(601,348)],
 'pistol-right':[(165,235),(276,235),(330,300),(340,385),(316,446),(273,520),(231,568),(187,570),(155,544),(148,490),(166,411),(180,368),(163,334),(158,306),(164,278)],
 'melee-right':[(277,302),(301,313),(316,344),(321,380),(316,413),(306,441),(299,468),(298,499),(290,531),(278,556),(280,580),(275,609),(264,643),(245,676),(234,708),(224,737),(217,761),(210,779),(221,791),(230,808),(236,831),(242,849),(237,861),(227,865),(218,858),(214,842),(209,829),(202,818),(195,822),(188,838),(190,855),(193,869),(184,879),(172,876),(164,862),(158,849),(151,836),(153,818),(160,794),(164,769),(166,737),(174,701),(183,667),(192,635),(198,608),(200,579),(204,547),(212,515),(219,488),(218,461),(218,434),(226,404),(231,373),(243,341),(259,317)],
}
# Side-specific inner seams may overlap only the adjacent axilla/torso. Exterior
# points are generous bounds, never a hand-traced substitute for source alpha.
POLYS.update({
 'melee-right':[(285,276),(324,285),(345,370),(340,433),(335,460),(323,485),(314,510),(307,530),(300,572),(293,620),(271,675),(248,730),(237,778),(253,810),(258,872),(213,908),(153,887),(133,847),(142,792),(143,744),(151,694),(168,629),(181,575),(187,525),(202,476),(206,423),(221,365),(245,321)],
 'pistol-right':[(155,233),(282,233),(346,285),(360,351),(331,418),(321,430),(320,440),(318,450),(316,460),(313,470),(310,480),(293,505),(270,537),(250,584),(204,590),(169,580),(143,555),(131,516),(133,469),(153,407),(165,371),(148,335),(147,300)],
 'rifle-right':[(285,276),(336,285),(350,356),(352,418),(353,470),(315,510),(323,530),(370,544),(394,555),(415,574),(444,600),(450,633),(415,659),(378,653),(342,636),(316,618),(264,618),(214,620),(172,613),(145,598),(137,574),(139,538),(156,493),(177,450),(212,404),(222,363),(243,325)],
 'rifle-left':[(605,276),(665,286),(701,328),(724,374),(728,424),(724,464),(742,502),(753,553),(765,598),(759,638),(737,661),(712,680),(721,713),(719,745),(681,759),(642,741),(615,713),(614,685),(640,663),(653,645),(655,619),(647,600),(635,575),(627,550),(621,530),(616,510),(613,490),(612,470),(613,450),(600,430),(581,419),(580,375),(590,337)],
})
# Explicit visible skin contours at the grips. These provide foreground fingers,
# not a rectangular pasted hand or a baked weapon on the arm.
HANDS={
 'rifle-right':[(315,544),(350,550),(390,551),(417,559),(442,573),(465,589),(484,606),(492,614),(494,622),(490,626),(484,626),(477,623),(462,607),(449,601),(444,603),(451,613),(453,620),(450,627),(445,631),(437,629),(430,625),(436,632),(436,637),(431,641),(422,640),(413,635),(420,642),(416,648),(407,650),(395,647),(381,641),(369,638),(355,629),(345,618),(335,612),(325,606),(315,604)],
 'rifle-left':[(621,704),(624,687),(632,677),(640,670),(647,668),(652,673),(652,682),(655,671),(659,666),(667,663),(674,666),(678,673),(679,679),(682,671),(691,671),(698,676),(701,687),(704,699),(711,706),(712,719),(712,733),(705,740),(695,746),(681,747),(669,740),(658,738),(644,735),(633,729),(625,718)],
 'pistol-right':[(215,263),(226,267),(236,275),(246,272),(253,274),(261,277),(267,280),(271,285),(273,297),(272,315),(264,334),(251,350),(236,362),(219,371),(204,373),(190,367),(181,358),(177,345),(172,332),(170,319),(169,310),(174,300),(180,291),(186,287),(192,278),(205,269)],
 'melee-right':[(169,774),(189,776),(210,786),(226,804),(236,823),(241,844),(242,860),(234,868),(227,865),(224,850),(217,843),(209,849),(207,863),(213,878),(204,885),(194,886),(181,880),(170,870),(161,859),(154,848),(152,837),(156,819),(163,800)],
}
WEAPONS={
 'rifle':[(275,418),(293,425),(352,462),(379,480),(403,499),(430,510),(447,518),(461,509),(481,507),(511,520),(609,580),(623,577),(628,588),(643,597),(669,610),(682,619),(691,624),(704,627),(719,635),(773,667),(785,679),(810,704),(814,717),(808,725),(839,749),(864,738),(874,744),(866,765),(881,791),(887,802),(879,811),(868,804),(856,804),(844,795),(812,776),(795,768),(765,752),(745,740),(726,729),(705,720),(680,712),(643,689),(623,678),(600,668),(591,665),(585,703),(581,742),(577,772),(553,785),(531,789),(514,786),(502,778),(493,762),(491,738),(491,700),(495,650),(479,643),(454,638),(438,629),(424,641),(403,640),(382,650),(365,642),(350,631),(351,612),(360,600),(351,578),(332,559),(296,542),(266,532),(247,522),(236,515),(237,502),(248,470),(262,438)],
 'pistol':[(220,150),(257,149),(261,174),(265,205),(270,225),(277,246),(282,268),(289,287),(288,301),(281,308),(270,302),(261,295),(249,304),(241,318),(230,346),(217,353),(204,348),(194,337),(198,319),(208,299),(216,283),(214,270),(207,258),(206,238),(216,223),(224,216),(221,197),(219,179)],
 'melee':[(205,830),(219,833),(240,858),(252,859),(258,867),(252,882),(255,896),(268,908),(283,929),(299,954),(311,980),(323,1009),(308,1003),(284,989),(266,970),(245,948),(229,924),(215,903),(199,909),(188,905),(185,895),(195,882),(186,869),(186,854)],
}
def smooth(v):t=np.clip(v,0,1);return t*t*(3-2*t)
def mask(poly):
 m=Image.new('L',(941*4,1672*4));ImageDraw.Draw(m).polygon([(round(x*4),round(y*4)) for x,y in poly],fill=255);return np.array(m.resize((941,1672),Image.Resampling.LANCZOS))/255
base_rgba=np.array(Image.open(ROOT/'base_male.png').convert('RGBA'));rig=json.loads(RIG.read_text());cfg=json.loads((CORE/'male-preview.json').read_text());anchors={p:{s:{k:[v[0]+SHIFT[0],v[1]+SHIFT[1]] for k,v in a.items()} for s,a in sides.items()} for p,sides in POINTS.items()}
if '--calibrate' in sys.argv:
 for pose,sides in anchors.items():
  target=rig['poses'][pose];target['angle']=0
  for side,a in sides.items():
   rest=rig['arms'][side];s,e,w,g=[np.array(a[k],float) for k in ['shoulder','elbow','wrist','grip']];rs,re,rw=[np.array(rest[k],float) for k in ['shoulder','elbow','wrist']]
   target[side]=a['grip'];rig['anatomyProjection'][pose][side]=[float(np.linalg.norm(e-s)/np.linalg.norm(re-rs)),float(np.linalg.norm(w-e)/np.linalg.norm(rw-re))];rig['handCorrections'][pose][side]['grip']=[float(rw[0]),float(rw[1]+np.linalg.norm(g-w))];target['handAngles'][side]=float(math.degrees(math.atan2(*(g-w)[::-1]))-90);cross=(w-s)[0]*(e-s)[1]-(w-s)[1]*(e-s)[0];target['bend'][side]=1 if cross>0 else -1
 rig['poseArt']={};cfg['poseArtSurfaces']={};cfg['contactRepairs']=[]
 for pose in anchors:
  cfg['weapons'][pose].update(image=f'assets/weapons/reference-art/{pose}.png',size=[941,1672],scale=1,primary=anchors[pose]['right']['grip'],support=anchors[pose].get('left',{}).get('grip'),angle=0,offset=[0,0],art='independent visible reference weapon art; hidden guard pixels padded locally')
  if pose=='rifle':cfg['weapons'][pose].update(stock=[257,512],trigger=[432,635])
  if pose=='pistol':cfg['weapons'][pose].update(stock=[216,370],trigger=[227,292])
 RIG.write_text(json.dumps(rig,indent=2)+'\n');(CORE/'male-preview.json').write_text(json.dumps(cfg,indent=2)+'\n');(OUT/'registration.json').write_text(json.dumps({'shift':SHIFT,'uniform_scale':1,'anchors':anchors,'source_anchors':POINTS,'polygons':POLYS,'hands':HANDS,'weapons':WEAPONS},indent=2)+'\n');sys.exit()
bindings=json.loads((SOURCE_REVIEW/'pose-bindings.json').read_text());records=[];yy,xx=np.indices((1672,941));torso_alpha=np.zeros((1672,941));tp=rig['segments']['torso'];tx,ty,tx1,ty1=tp['bounds'];torso_alpha[ty:ty1,tx:tx1]=np.array(Image.open(CORE/tp['image']))[:,:,3]/255
for pose,sides in anchors.items():
 source=SOURCE_REVIEW/'Sources'/f'{pose}.png';src=np.array(Image.open(source).convert('RGBA'));rgb=src[:,:,:3].astype(float);skin=(rgb[:,:,0]>45)&(rgb[:,:,0]-rgb[:,:,2]>12)&(rgb[:,:,0]-rgb[:,:,1]>5)
 # Fill enclosed dark wrinkles within the subject; never erase all dark pixels.
 holes=ndi.binary_fill_holes(skin)&(~skin);hl,hn=ndi.label(holes)
 for label in range(1,hn+1):
  sel=hl==label
  if sel.sum()<=12:skin[sel]=True
 signed=ndi.distance_transform_edt(skin)-ndi.distance_transform_edt(~skin);edge_alpha=np.clip((signed+.3)/1.3,0,1)
 # Segment the independent prop before extracting limbs: coarse ROI is only
 # a limit, never permission to keep skin/black background as weapon pixels.
 subject=src[:,:,3].astype(float)/255
 if Image.open(source).mode=='RGB':
  dark=rgb.max(axis=2)<=8;seed_bg=np.zeros(dark.shape,bool);seed_bg[0,:]=dark[0,:];seed_bg[-1,:]=dark[-1,:];seed_bg[:,0]=dark[:,0];seed_bg[:,-1]=dark[:,-1];outside=ndi.binary_propagation(seed_bg,mask=dark);subject*=~outside
 # Recover the source antialias fringe rather than quantizing the elbow to a
 # warm-RGB threshold. The source backdrop matte is reconstructed below; this
 # is a <=1.5px exterior fringe, not dilation of anatomical volume.
 near_skin=ndi.distance_transform_edt(~skin)
 fringe=(near_skin<=1.5)&(subject>0)&(rgb[:,:,0]>8)&(rgb[:,:,0]-rgb[:,:,2]>4)
 edge_alpha=np.maximum(edge_alpha,fringe.astype(float))
 hand_masks={side:mask(HANDS[pose+'-'+side])*subject for side in sides}
 if pose=='pistol':
  main=hand_masks['right'];main*=1-mask([(199,320),(207,321),(214,326),(222,327),(228,324),(234,320),(233,330),(226,346),(216,348),(204,342)])
  island=mask([(223,235),(228,237),(237,242),(240,248),(238,253),(232,256),(225,253),(221,247)])
  sliver=mask([(211,238),(216,240),(220,260),(214,266),(210,255)])
  hand_masks['right']=np.maximum.reduce([main,island*subject,sliver*subject])
 # Selective edge matting removes dark background/metal accidentally included
 # at a hand stencil's border. Interior dark folds and light nail detail stay.
 for side,hm in hand_masks.items():
  distance_inside=ndi.distance_transform_edt(hm>.5);warm=(rgb[:,:,0]-rgb[:,:,2]>16)&(hm>.5);distance,idx=ndi.distance_transform_edt(~warm,return_indices=True);cold_edge=(distance_inside<3)&(hm>0)&(rgb.max(axis=2)<110)&(rgb[:,:,0]-rgb[:,:,2]<=16)
  nearest=rgb[idx[0],idx[1]];fraction=np.clip((rgb*nearest).sum(axis=2)/np.maximum(1,(nearest*nearest).sum(axis=2)),0,1);hm[cold_edge]*=np.where(distance[cold_edge]<=1.5,fraction[cold_edge],0);hand_masks[side]=hm
 if pose=='rifle':
  # Below the middle/ring fingertips this was exposed BELLY, not another finger.
  # Original hand stencil reached x436,y637 although the fingertip ends x430,y628.
  cut=mask([(438,625),(448,633),(446,646),(423,652),(414,646),(421,638),(430,634)])
  hand_masks['right']*=1-cut
 hand_union=np.maximum.reduce(list(hand_masks.values()))
 roi=mask(WEAPONS[pose]);gc=np.full((1672,941),cv2.GC_BGD,dtype='uint8');gc[roi>.1]=cv2.GC_PR_FGD
 probable_skin=(rgb[:,:,0]>145)&(rgb[:,:,0]-rgb[:,:,2]>38)&(rgb[:,:,1]>85);gc[(roi>.1)&probable_skin]=cv2.GC_PR_BGD
 strokes={'rifle':[([(270,466),(423,525)],12), ([(464,540),(623,625)],10), ([(521,656),(542,765)],9), ([(654,648),(764,696)],7), ([(770,713),(873,797)],3)],'pistol':[([(241,167),(257,247),(276,287)],4), ([(211,337),(219,322)],4)],'melee':[([(213,849),(230,875)],4), ([(232,892),(305,989)],4)]}
 seed=Image.new('L',(941,1672));sd=ImageDraw.Draw(seed)
 for points,width in strokes[pose]:sd.line(points,fill=255,width=width)
 gc[(np.array(seed)>0)&(roi>.1)]=cv2.GC_FGD
 # Hands and exterior background are definite background for the PROP only.
 gc[hand_union>.4]=cv2.GC_BGD
 if Image.open(source).mode=='RGBA':gc[src[:,:,3]<16]=cv2.GC_BGD
 else:
  dark=rgb.max(axis=2)<=8;seed_bg=np.zeros(dark.shape,bool);seed_bg[0,:]=dark[0,:];seed_bg[-1,:]=dark[-1,:];seed_bg[:,0]=dark[:,0];seed_bg[:,-1]=dark[:,-1];outside=ndi.binary_propagation(seed_bg,mask=dark);gc[outside]=cv2.GC_BGD
 if pose=='rifle':
  for px,py in [(699,619),(706,630),(714,641),(722,648)]:cv2.circle(gc,(px,py),5,cv2.GC_BGD,-1)
 bgmodel=np.zeros((1,65));fgmodel=np.zeros((1,65));cv2.setRNGSeed(404);cv2.grabCut(src[:,:,:3].copy(),gc,None,bgmodel,fgmodel,3,cv2.GC_INIT_WITH_MASK)
 prop_binary=(gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD);prop_binary&=hand_union<.5
 pl,pn=ndi.label(prop_binary,structure=np.ones((3,3)));valid=np.unique(pl[(np.array(seed)>0)&prop_binary]);prop_binary=np.isin(pl,valid[valid>0])
 if pose=='rifle':prop_binary[(xx>755)&(yy>690)&(yy<850)]=src[:,:,3][(xx>755)&(yy>690)&(yy<850)]>=128
 signed_prop=ndi.distance_transform_edt(prop_binary)-ndi.distance_transform_edt(~prop_binary);prop_alpha=np.clip((signed_prop+.2)/1.2,0,1)*roi*(src[:,:,3]/255)
 hand_masks,prop_alpha,contact_repair=contact.contact_masks(pose,src,subject,hand_masks,prop_alpha,mask)
 hand_union=np.maximum.reduce(list(hand_masks.values()))
 Image.fromarray(np.rint(contact_repair*255).astype('uint8')).save(OUT/(pose+'-contact-repair-mask.png'))
 Image.fromarray(np.rint(prop_alpha*255).astype('uint8')).save(OUT/(pose+'-prop-mask.png'))
 visible={};fronts={}

 for side in sides:
  key=pose+'-'+side;alpha=np.maximum(mask(POLYS[key])*edge_alpha*subject,hand_masks[side])
  if pose=='rifle' and side=='right':
   zone=(xx>=315)&(yy>=535)
   alpha[zone]=hand_masks[side][zone]
  # Left forearm must continue to the occluded wrist: no horizontal y655 cut.
  # Melee: the arm matte continues through the wrist; no y=780 stencil cut.
  alpha*=1-prop_alpha*(1-hand_masks[side])
  # The only feather is inside the shoulder's overlap with the original torso.
  # Side borders and fingers are never globally feathered.
  # Do not punch an inner-shoulder polygon into the source. It produced the
  # dark triangular remnant and the horizontal y342 seam in every raised arm.
  # The sole blend below is restricted to overlap with the intact base torso.
  a=src.copy();a[:,:,3]=np.rint(alpha*255);a[a[:,:,3]==0]=0
  # Hidden wrist reserve: borrow neighboring skin only under opaque prop pixels,
  # never invent visible fingers or leave weapon RGB baked into the arm.
  wx,wy=POINTS[pose][side]['wrist'];solid_skin=(a[:,:,3]>=200)&(a[:,:,0].astype(int)-a[:,:,2].astype(int)>25)&(a[:,:,0]>80);dd,ii=ndi.distance_transform_edt(~solid_skin,return_indices=True);reserve=(prop_alpha>.99)&((xx-wx)**2+(yy-wy)**2<24**2)&(dd<=20)&(a[:,:,3]<128);a[reserve,:3]=a[ii[0][reserve],ii[1][reserve],:3];a[reserve,3]=255;Image.fromarray((reserve*255).astype('uint8')).save(OUT/(key+'-hidden-wrist-mask.png'))
  # Remove only truly disconnected <=8-alpha noise. Preserve finger separators.
  labels,n=ndi.label(a[:,:,3]>0,structure=np.ones((3,3)))
  for label in range(1,n+1):
   sel=labels==label
   if sel.sum()<20 and a[:,:,3][sel].max()<=8:a[sel]=0
  front=src.copy();front[:,:,3]=np.rint(hand_masks[side]*255);front[front[:,:,3]==0]=0
  if Image.open(source).mode=='RGB':
   a=contact.unmatte_exterior(a,rgb,subject,pose);front=contact.unmatte_exterior(front,rgb,subject,pose)
  if pose=='pistol':
   # The generic arm matte formerly kept opaque black backdrop pixels behind
   # the corrected palm fringe. Both passes must share the SAME boundary.
   h=hand_masks[side]>.5;inside=ndi.distance_transform_edt(h);outside=ndi.distance_transform_edt(~h)
   band=(inside<=2)&(outside<=2)&(xx>=225)&(xx<=280)&(yy>=260)&(yy<=360)
   a[band]=front[band]
  visible[side]=a;fronts[side]=front
 # Register once onto the existing canvas; original anatomy, no nonuniform warp.
 def shift(a):return np.array(Image.fromarray(a).transform((941,1672),Image.Transform.AFFINE,(1,0,-SHIFT[0],0,1,-SHIFT[1]),Image.Resampling.BICUBIC))
 def border_color(a):
  solid=a[:,:,3]>=128
  if not solid.any():return a
  distance,indices=ndi.distance_transform_edt(~solid,return_indices=True);a[(a[:,:,3]<128)&(distance>1.5)]=0;edge=(a[:,:,3]>0)&(a[:,:,3]<128);a[edge,:3]=a[indices[0][edge],indices[1][edge],:3];a[a[:,:,3]==0]=0;return a
 rig['poseArt'][pose]={}
 for side,a in visible.items():
  a=border_color(shift(a));front=border_color(shift(fronts[side]));roi_distance=ndi.distance_transform_edt(mask(POLYS[pose+'-'+side])>.5);roi_distance=np.array(Image.fromarray(roi_distance.astype('float32')).transform((941,1672),Image.Transform.AFFINE,(1,0,-SHIFT[0],0,1,-SHIFT[1]),Image.Resampling.BILINEAR));hm_registered=shift(np.dstack([np.zeros((1672,941,3),dtype='uint8'),np.rint(hand_masks[side]*255).astype('uint8')]))[:,:,3]/255;a[:,:,3]=np.rint(a[:,:,3]*np.where((torso_alpha>=.98)&(hm_registered<.01),smooth(roi_distance/32),1))
  # Original shoulder cap bridges the real torso partition without extrapolating
  # skin or shifting the body. Source paint fades into this cap only locally.
  segment=rig['segments'][side+'Upper'];bx,by,bx1,by1=segment['bounds'];cap=np.zeros_like(base_rgba);cap[by:by1,bx:bx1]=np.array(Image.open(CORE/segment['image']));cap=border_color(cap)
  # The old cap was alpha-overed ON TOP of the reference through y436,
  # leaving the old deltoid crease and a diagonal seam. Blend colour inside the
  # shared shoulder, but let the source silhouette take over below y365.
  ca=cap[:,:,3].astype(float)/255;sa=a[:,:,3].astype(float)/255
  # A reference silhouette edge can sit INSIDE the wider original shoulder.
  # Its dark antialias colour is then an internal double contour, not shading.
  # Mix only this shared shoulder boundary into original shoulder/torso paint;
  # never blur the image or alter an exposed arm silhouette / hand.
  edge_distance=ndi.distance_transform_edt(sa>.5)
  blend=smooth((yy-345)/45)*smooth(edge_distance/10)
  # Approved base skin alpha is 252/255, not 255. A .99 gate disables
  # ALL shoulder/torso blending and exposes reference exterior ink inside skin.
  overlap=(((ca>=.98)&(yy<436))|(torso_alpha>=.98))&(sa>0)&(yy<530)&(hm_registered<.01)
  blend=1-(1-blend)*(1-smooth((yy-430)/100))
  a[overlap,:3]=np.rint(base_rgba[overlap,:3]*(1-blend[overlap,None])+a[overlap,:3]*blend[overlap,None])
  # Harmonize only the shared shoulder/axilla paint using source gradients,
  # rather than leaving a rectangular RGB paste at the ROI boundary. Anatomy,
  # alpha, hands and the exposed arm remain outside this operation.
  shared=(((ca>=.98)&(yy<436))|(torso_alpha>=.98))&(sa>=.98)&(hm_registered<.001)&(yy>=335)&(yy<=535)
  shared &= ((xx>=235)&(xx<=380)) if side=='right' else ((xx>=580)&(xx<=700))
  if pose=='pistol':shared &= xx>=280
  shared=ndi.binary_erosion(shared,iterations=2)
  if shared.sum()>100:
   sy,sx=np.where(shared);center=(int((sx.min()+sx.max())//2),int((sy.min()+sy.max())//2))
   harmonized=cv2.seamlessClone(a[:,:,:3].copy(),base_rgba[:,:,:3].copy(),(shared*255).astype('uint8'),center,cv2.NORMAL_CLONE)
   strength=smooth(ndi.distance_transform_edt(shared)/5)
   a[:,:,:3]=np.rint(a[:,:,:3]*(1-strength[:,:,None])+harmonized*strength[:,:,None])
  Image.fromarray((shared*255).astype('uint8')).save(OUT/(pose+'-'+side+'-shoulder-harmonization-mask.png'))
  # Preserve the original upper shoulder only above the reference registration.
  ca*=1-smooth((yy-369)/67)
  sw=sa;cw=ca*(1-sa);oa=sw+cw
  mixed=np.zeros_like(a);mixed[:,:,:3]=np.rint((a[:,:,:3]*sw[:,:,None]+cap[:,:,:3]*cw[:,:,None])/np.maximum(oa[:,:,None],1e-9));mixed[:,:,3]=np.rint(oa*255);mixed[mixed[:,:,3]==0]=0;a=border_color(mixed)
  bounds=Image.fromarray(a).getbbox();x0,y0,x1,y1=bounds;folder=CORE/'assets/male/reference-art';folder.mkdir(exist_ok=True);paths=[]
  for kind,pixels in [('arm',a),('front',front)]:
   dest=folder/f'{pose}-{side}-{kind}.png';Image.fromarray(pixels).crop(bounds).save(dest);paths.append(str(dest.relative_to(CORE)))
  info=bindings[pose]['arms'][side];s,e,w,g=[np.array(info[k]) for k in ['shoulder','elbow','wrist','grip']];direction=(g-w)/np.linalg.norm(g-w)
  xs=list(range(x0,x1,12))+[x1];ys=list(range(y0,y1,12))+[y1];vertices=[]
  def ld(p,a,b):t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1);return np.linalg.norm(p-a-(b-a)*t)
  for y in ys:
   for x in xs:
    p=np.array([x,y]);el=float(smooth((ld(p,s,e)-ld(p,e,w)+60)/120));wr=float(smooth((np.dot(p-w,direction)+10)/40))*float(1-smooth((np.linalg.norm(p-g)-100)/70));sh=float(1-(1-smooth(np.linalg.norm(p-s)/80))*(1-el)*(1-wr));vertices.append([x,y,sh,el,wr])
  tris=[];nx=len(xs)
  for iy in range(len(ys)-1):
   for ix in range(nx-1):
    if a[ys[iy]:ys[iy+1]+1,xs[ix]:xs[ix+1]+1,3].any():
     v=iy*nx+ix;tris.extend([[v,v+1,v+nx],[v+1,v+nx+1,v+nx]])
  rig['poseArt'][pose][side]={'image':paths[0],'frontImage':paths[1],'mesh':{'bounds':list(bounds),'vertices':vertices,'triangles':tris,'handTriangles':tris},'bind':{**{k:info[k] for k in ['upper','fore','hand']},'torso':bindings[pose]['transforms']['torso']},'anchors':anchors[pose][side],'source':str(source.relative_to(ROOT)),'artStatus':'authorized reference arm extraction; local alpha/shoulder registration, no whole-character replacement'}
  records.append({'pose':pose,'side':side,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'bounds':bounds,'paths':paths})
 # Only the explicit weapon silhouette enters the weapon PNG. Remove all visible
 # hand pixels from it. Extend <=2px under opaque fingers for breathing tolerance.
 weapon_alpha=prop_alpha
 weapon=src.copy();weapon[:,:,3]=np.rint(weapon_alpha*255);weapon[weapon[:,:,3]==0]=0
 solid=weapon[:,:,3]>=128;distance,indices=ndi.distance_transform_edt(~solid,return_indices=True);pad=(distance<=4)&(hand_union>.01)&(~solid);weapon[pad,:3]=weapon[indices[0][pad],indices[1][pad],:3];weapon[pad,3]=255
 # Complementary alpha alone is insufficient at antialiased contact edges:
 # render real object material under those pixels, never background. Only the
 # explicitly traced solid contact surfaces may receive this hidden overlap.
 physical=(contact_repair>.98)&(ndi.distance_transform_edt(hand_union>.99)>=2)
 weapon[physical,:3]=weapon[indices[0][physical],indices[1][physical],:3]
 weapon[physical,3]=255
 # Infer only concealed contact pixels under the opaque fingers. These are
 # separate prop pixels and never visible painted anatomy.
 inside=ndi.distance_transform_edt(hand_union>.99)
 for point in [POINTS[pose]['right']['grip']]+([POINTS[pose]['left']['grip']] if 'left' in POINTS[pose] else []):
  gx,gy=point;hidden=((xx-gx)**2+(yy-gy)**2<9**2)&(inside>=3)&(~solid);weapon[hidden,:3]=weapon[indices[0][hidden],indices[1][hidden],:3];weapon[hidden,3]=255
 weapon=border_color(shift(weapon));folder=CORE/'assets/weapons/reference-art';folder.mkdir(exist_ok=True);Image.fromarray(weapon).save(folder/f'{pose}.png')
(OUT/'registration.json').write_text(json.dumps({'shift':SHIFT,'uniform_scale':1,'anchors':anchors,'source_anchors':POINTS,'polygons':POLYS,'hands':HANDS,'weapons':WEAPONS},indent=2)+'\n');RIG.write_text(json.dumps(rig,indent=2)+'\n');(OUT/'arm-art-manifest.json').write_text(json.dumps(records,indent=2)+'\n');print('Four reference-arm modules, eight limb surfaces, three independent props prepared')
