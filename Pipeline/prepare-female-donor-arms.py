"""Reproducible female-only donor limb extraction; never writes source/base PNGs.
Hand-painted polygon limits separate limb ownership from the unchanged torso.
Colour segmentation is confined to those limits; enclosed dark skin folds remain.
"""
from pathlib import Path
import json,hashlib,subprocess,math
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]; C=ROOT/'avatar-core'; O=ROOT/'review/female-donor-arm-pass'; (O/'Masks').mkdir(exist_ok=True)
W,H=941,1672; Y,X=np.indices((H,W)); base=np.array(Image.open(ROOT/'base_female.png').convert('RGBA'))
r=json.loads((O/'Baseline/female_rig.json').read_text());calibration_grips={}
POINTS={
'melee':{'right':{'shoulder':[306,367],'elbow':[260,570],'wrist':[205,787],'grip':[220,857]}},
'pistol':{'right':{'shoulder':[306,367],'elbow':[222,526],'wrist':[211,355],'grip':[217,303]}},
'rifle':{'right':{'shoulder':[306,367],'elbow':[190,522],'wrist':[350,544],'grip':[411,575]},'left':{'shoulder':[639,368],'elbow':[687,566],'wrist':[687,626],'grip':[665,666]}}}
POLYS={
'melee-right':[(303,294),(333,312),(345,360),(345,407),(337,442),(341,468),(327,522),(310,575),(300,619),(275,672),(250,726),(240,774),(248,806),(251,858),(233,884),(210,891),(188,869),(165,842),(166,819),(184,777),(188,732),(195,682),(208,629),(225,581),(239,545),(247,502),(252,465),(266,434),(263,398),(270,347),(284,316)],
'pistol-right':[(305,294),(332,310),(346,347),(346,400),(327,442),(308,476),(289,514),(268,543),(241,561),(215,571),(194,570),(179,555),(170,520),(165,482),(168,445),(177,407),(182,375),(179,352),(171,332),(166,308),(176,285),(196,267),(218,259),(242,266),(261,278),(273,295),(272,318),(252,342),(236,352),(237,382),(239,412),(245,440),(252,449),(263,428),(268,397),(269,364),(280,327)],
'rifle-right':[(303,294),(331,312),(345,350),(343,396),(330,431),(311,467),(291,495),(282,506),(315,507),(346,508),(371,517),(398,529),(419,541),(442,552),(464,569),(478,582),(476,593),(466,598),(455,591),(448,586),(449,598),(444,607),(435,607),(424,600),(423,609),(413,615),(399,611),(387,604),(377,598),(373,608),(362,611),(344,603),(328,591),(316,580),(309,566),(281,567),(249,573),(216,581),(182,579),(157,568),(150,552),(151,524),(163,495),(181,465),(199,440),(217,418),(235,399),(246,366),(264,332),(283,309)],
'rifle-left':[(627,295),(660,311),(681,343),(691,384),(690,425),(681,461),(686,488),(704,520),(715,554),(717,582),(704,608),(690,626),(692,642),(691,664),(686,684),(678,698),(661,699),(648,694),(635,688),(624,680),(619,666),(618,653),(624,636),(636,627),(647,619),(653,605),(653,586),(645,565),(632,541),(623,518),(617,496),(610,475),(602,453),(594,422),(595,385),(604,344)]}
HANDS={
'melee-right':[(186,784),(211,779),(231,793),(244,817),(249,846),(244,862),(233,873),(223,869),(221,849),(210,838),(204,850),(207,870),(197,883),(185,873),(174,858),(167,842),(171,823)],
'pistol-right':[(181,345),(173,330),(168,312),(172,295),(184,281),(199,270),(215,264),(235,266),(253,276),(266,287),(271,302),(267,320),(254,337),(239,346),(220,354),(199,356)],
'rifle-right':[(310,515),(335,509),(364,514),(392,527),(417,540),(443,554),(466,571),(478,583),(474,593),(465,597),(451,588),(450,599),(443,607),(435,606),(424,600),(422,609),(412,614),(399,611),(385,604),(377,598),(371,607),(359,609),(343,602),(329,591),(316,579),(307,561)],
'rifle-left':[(623,639),(635,627),(647,626),(657,631),(667,630),(678,633),(688,641),(692,659),(688,680),(680,695),(668,699),(654,696),(642,691),(631,685),(623,675),(618,659)]}
HANDS['rifle-right']=[(309,515),(340,515),(372,516),(399,525),(424,538),(451,551),(480,566),(498,578),(500,583),(497,588),(488,590),(478,584),(463,576),(448,570),(441,570),(444,577),(449,584),(449,590),(445,596),(439,598),(432,595),(423,588),(418,584),(423,590),(425,595),(424,601),(418,605),(411,606),(401,603),(393,598),(388,598),(391,603),(389,608),(382,610),(375,607),(367,601),(358,597),(349,592),(340,586),(332,577),(325,570),(313,567)]
HANDS['rifle-left']=[(622,644),(630,635),(639,628),(646,629),(651,636),(651,641),(652,630),(659,625),(665,625),(670,630),(671,635),(674,629),(680,628),(686,631),(689,640),(691,646),(696,646),(700,650),(704,660),(706,675),(705,686),(705,696),(701,703),(693,707),(685,705),(679,702),(672,705),(665,706),(657,703),(650,699),(642,699),(635,694),(630,687),(624,681),(621,670),(622,655)]
PROPS={
'melee':[(202,844),(218,839),(243,859),(255,872),(252,883),(271,911),(290,941),(308,979),(311,1005),(299,997),(275,978),(254,952),(234,922),(217,900),(202,906),(195,897),(201,882),(189,869)],
'pistol':[(207,145),(244,142),(251,177),(257,214),(263,237),(270,255),(276,274),(276,291),(263,294),(250,281),(235,298),(223,322),(213,337),(196,333),(187,319),(199,296),(204,277),(199,258),(201,240),(211,226),(216,215)],
'rifle':[(275,392),(303,404),(336,421),(370,439),(402,459),(427,476),(446,471),(467,479),(492,495),(563,537),(583,548),(600,546),(616,556),(639,569),(665,582),(682,588),(696,598),(712,612),(754,637),(776,654),(791,675),(824,696),(849,683),(861,690),(855,708),(875,734),(882,746),(874,753),(857,744),(832,732),(805,718),(774,699),(743,683),(718,671),(689,660),(655,644),(625,631),(591,612),(578,607),(574,646),(570,690),(562,732),(534,749),(512,754),(495,749),(492,733),(496,707),(501,676),(502,646),(506,615),(488,604),(471,597),(453,592),(431,600),(418,612),(400,610),(380,599),(366,592),(349,574),(349,558),(355,543),(333,529),(300,512),(269,502),(246,492),(241,481),(249,452),(262,417)]}
PROPS['rifle']=[(280,399),(291,402),(431,477),(444,472),(460,476),(562,538),(582,550),(594,548),(605,557),(638,578),(650,591),(667,593),(709,620),(727,640),(738,643),(752,655),(764,672),(771,691),(799,710),(825,729),(840,738),(849,715),(858,700),(867,706),(861,725),(852,745),(858,751),(872,762),(875,776),(869,783),(858,778),(842,768),(817,752),(789,736),(759,719),(739,709),(716,698),(693,685),(681,681),(676,692),(661,699),(646,697),(629,687),(620,677),(614,659),(607,646),(581,629),(566,619),(564,640),(560,675),(560,706),(571,734),(550,745),(529,754),(510,756),(500,746),(498,729),(498,704),(499,671),(504,639),(506,613),(492,608),(473,595),(457,586),(451,591),(442,601),(427,606),(415,613),(403,608),(390,604),(374,609),(364,610),(348,603),(331,590),(315,578),(304,564),(300,548),(314,538),(325,533),(322,522),(287,507),(257,497),(242,489),(243,477),(255,445),(267,416)]
STROKES={'melee':[([(223,876),(289,974)],5)],'pistol':[([(225,157),(243,243),(263,276)],5), ([(201,322),(213,305)],5)],'rifle':[([(279,439),(416,493)],12), ([(450,491),(610,580)],9), ([(531,620),(533,727)],8), ([(651,607),(770,675),(870,742)],4)]}
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def mask(poly):
 im=Image.new('L',(W*3,H*3));ImageDraw.Draw(im).polygon([(x*3,y*3) for x,y in poly],fill=255);return np.array(im.resize((W,H),Image.Resampling.LANCZOS))/255
cfg={'weapons':{},'breathingProfiles':{p:{'propSway':0,'gripX':0,'handDegrees':0,'idleArm':.12} for p in ['idle','melee','pistol','rifle']}}
r['posePolicy']={'instant':True,'oneHandPistol':True};r['anatomyProjection']={};r['poseArt']={}
r.pop('pistolOneHand',None)
records=[]
# Original torso alpha is used solely to blend the shared shoulder inside body.
torso=np.zeros((H,W));info=r['segments']['torso'];x0,y0,x1,y1=info['bounds'];torso[y0:y1,x0:x1]=np.array(Image.open(C/info['image']))[:,:,3]/255
for pose,sides in POINTS.items():
 src=np.array(Image.open(O/'Sources'/f'{pose}.png').convert('RGBA'));rgb=src[:,:,:3].astype(float)
 # Connected black outside is backdrop, not internal gun or finger shadow.
 dark=rgb.max(axis=2)<14;seed=np.zeros((H,W),bool);seed[0]=dark[0];seed[-1]=dark[-1];seed[:,0]=dark[:,0];seed[:,-1]=dark[:,-1];bg=ndi.binary_propagation(seed,mask=dark)
 warm=(rgb[:,:,0]>40)&(rgb[:,:,0]-rgb[:,:,1]>7)&(rgb[:,:,0]-rgb[:,:,2]>20)&~bg
 holes=ndi.binary_fill_holes(warm)&~warm;lab,n=ndi.label(holes);sizes=np.bincount(lab.ravel());warm|=holes&(sizes[lab]<24)
 hand={s:mask(HANDS[pose+'-'+s])*warm for s in sides}
 if pose=='rifle':
  wrong_body=mask([(346,598),(361,601),(375,614),(357,620)])
  hand['right']*=1-wrong_body
 union=np.maximum.reduce(list(hand.values()));roi=mask(PROPS[pose]);prop=(roi>.5)&~warm&~bg
 # Preserve wooden stock (warm RGB) through explicit safe material strokes.
 import cv2
 cv2.setNumThreads(1);cv2.setRNGSeed(404)
 gc=np.full((H,W),cv2.GC_BGD,np.uint8);gc[roi>.1]=cv2.GC_PR_FGD;gc[(roi>.1)&warm]=cv2.GC_PR_BGD
 line=Image.new('L',(W,H));d=ImageDraw.Draw(line)
 for pts,width in STROKES[pose]:d.line(pts,fill=255,width=width)
 gs=np.array(line)>0;gc[gs&(roi>.1)]=cv2.GC_FGD;gc[(union>.1)|bg]=cv2.GC_BGD
 cv2.grabCut(src[:,:,:3].copy(),gc,None,np.zeros((1,65)),np.zeros((1,65)),3,cv2.GC_INIT_WITH_MASK)
 prop=((gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD))&(roi>.1)&(union<.1)&~bg
 labels,n=ndi.label(prop,np.ones((3,3)));valid=np.unique(labels[gs&prop]);prop=np.isin(labels,valid[valid>0]);pa=prop.astype(float)*roi
 if pose=='rifle':
  pa=roi*(~bg)*(1-union);pa*=1-wrong_body*warm
  # Preserve warm WOOD only in actual stock/fore-end zones. Bright skin in
  # adjacent forearm/abdomen ROIs must never become a baked part of the item.
  wood=np.maximum.reduce([mask([(280,399),(435,477),(414,522),(241,488)]),mask([(610,590),(731,638),(717,667),(591,632)]),mask([(642,588),(737,640),(729,652),(627,603)])])
  flesh=warm
  pa*=1-flesh*(1-wood)
 # Remove external black matte only, retaining internal material detail.
 pa=np.clip(pa,0,1)
 # Anatomical source pixels may be foreground over metal. Do not paint the
 # weapon into hands or fill natural finger apertures with a rectangle.
 wp=src.copy();wp[:,:,3]=np.rint(pa*255)
 # Restore only concealed prop contact material under already opaque fingers.
 solid=pa>.9
 _,near=ndi.distance_transform_edt(~solid,return_indices=True)
 for pt in [sides['right']['grip']]+([sides['left']['grip']] if 'left' in sides else []):
  gx,gy=pt;hidden=((X-gx)**2+(Y-gy)**2<=10**2)&(union>.99)&(~solid)
  wp[hidden,:3]=wp[near[0][hidden],near[1][hidden],:3];wp[hidden,3]=255
 dist=ndi.distance_transform_edt(wp[:,:,3]<32);wp[(wp[:,:,3]>0)&(wp[:,:,3]<=16)&(dist>2)]=0
 labels,n=ndi.label(wp[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labels.ravel());peaks=ndi.maximum(wp[:,:,3],labels,range(n+1));weak_ids=np.flatnonzero(np.array(peaks)<=16);wp[np.isin(labels,weak_ids)&(labels>0)]=0
 wp[wp[:,:,3]==0]=0
 folder=C/'assets/female/donor-art';folder.mkdir(exist_ok=True)
 Image.fromarray(wp).save(folder/f'{pose}-weapon.png');Image.fromarray(np.rint(pa*255).astype('uint8')).save(O/'Masks'/f'{pose}-weapon.png')
 target=r['poses'][pose];target.update(angle=0,handAngles={'right':0,'left':0},bend={'right':1,'left':-1});r['anatomyProjection'][pose]={};calibration_grips[pose]={}
 for side,pts in sides.items():
  rest=r['arms'][side];s,e,w,g=[np.array(pts[k],float) for k in ['shoulder','elbow','wrist','grip']];rs,re,rw=[np.array(rest[k],float) for k in ['shoulder','elbow','wrist']]
  target[side]=pts['grip'];target['handAngles'][side]=math.degrees(math.atan2(*(g-w)[::-1]))-math.degrees(math.atan2(rest['grip'][1]-rest['wrist'][1],rest['grip'][0]-rest['wrist'][0]))
  # Use native grip vector length via a pose correction; source anatomy is
  # calibrated by projection only, never stretched in its painted raster.
  correction_grip=[float(rw[0]),float(rw[1]+np.linalg.norm(g-w))]
  target['handAngles'][side]=math.degrees(math.atan2(*(g-w)[::-1]))-90
  r['anatomyProjection'][pose][side]=[float(np.linalg.norm(e-s)/np.linalg.norm(re-rs)),float(np.linalg.norm(w-e)/np.linalg.norm(rw-re))]
  target['bend'][side]=1 if (w-s)[0]*(e-s)[1]-(w-s)[1]*(e-s)[0]>0 else -1
  # Existing correction texture fields are required by legacy atlas setup;
  # actual rendering uses poseArt and these exact native calibrated grips.
  calibration_grips[pose][side]=correction_grip
  a=src.copy();region=mask(POLYS[pose+'-'+side]);alpha=np.maximum(region*warm,hand[side]);alpha*=1-pa*(1-hand[side]);alpha[bg]=0
  if pose=='rifle' and side=='right':alpha*=1-wrong_body
  # Selective 0.55px alpha antialiasing; RGB texture is never blurred.
  signed=ndi.distance_transform_edt(alpha>.5)-ndi.distance_transform_edt(alpha<=.5)
  band=np.abs(signed)<=2
  soft=ndi.gaussian_filter((alpha>.5).astype(float),.55)
  alpha[band]=soft[band];alpha[bg & (ndi.distance_transform_edt(bg)>1)]=0
  # Only a shared shoulder seam is blended, never outer arm/hand contours.
  weight=smooth((Y-325)/65);shared=(torso>.98)&(alpha>.98)&(Y<440)&(hand[side]<.1)
  a[shared,:3]=np.rint(base[shared,:3]*(1-weight[shared,None])+a[shared,:3]*weight[shared,None])
  a[:,:,3]=np.rint(alpha*255)
  solid=(alpha>.9)&warm
  _,idx=ndi.distance_transform_edt(~solid,return_indices=True)
  fringe=(alpha>0)&(alpha<.9)
  a[fringe,:3]=a[idx[0][fringe],idx[1][fringe],:3]
  a[a[:,:,3]==0]=0
  # Restore only missing local source surfaces, not the generated full arm.
  if pose=='rifle':
   box=(140,280,485,630) if side=='right' else (585,280,735,715)
   editpath=O/'Retouch'/f'rifle-{side}-edited.png'
   if editpath.exists():
    edit=np.array(Image.open(editpath).convert('RGBA').resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS))
    if side=='left':edit=ndi.shift(edit,(13,1,0),order=1).astype('uint8')
    patch=np.zeros_like(a);patch[box[1]:box[3],box[0]:box[2]]=edit
    zone=mask([(610,570),(716,570),(716,657),(610,657)]) if side=='left' else np.maximum(mask([(245,370),(350,370),(350,505),(245,505)]),mask([(299,529),(325,531),(329,571),(305,575)]))
    # Keep all source foreground digits and texture. Add only gaps, blending
    # within 3px of their original edge for a continuous local seam.
    dist=ndi.distance_transform_edt(a[:,:,3]>128)
    mix=zone*(patch[:,:,3]/255)*(1-smooth(dist/3))
    if side=='right':
     inner=mask([(245,370),(350,370),(350,505),(245,505)]);local=smooth(ndi.distance_transform_edt(inner>.5)/7)
     oa=a[:,:,3]/255;pa2=patch[:,:,3]/255;new=oa*(1-local)+pa2*local
     a[:,:,:3]=np.rint((a[:,:,:3]*(oa*(1-local))[:,:,None]+patch[:,:,:3]*(pa2*local)[:,:,None])/np.maximum(new[:,:,None],1e-8));a[:,:,3]=np.rint(new*255);mix*=1-local
    if side=='left':
     local=zone*smooth((Y-575)/16)*(1-smooth((Y-628)/20))
     oa=a[:,:,3]/255;pa2=patch[:,:,3]/255;new=oa*(1-local)+pa2*local
     a[:,:,:3]=np.rint((a[:,:,:3]*(oa*(1-local))[:,:,None]+patch[:,:,:3]*(pa2*local)[:,:,None])/np.maximum(new[:,:,None],1e-8));a[:,:,3]=np.rint(new*255);mix*=1-local
    old=a[:,:,3]/255;new=mix+old*(1-mix)
    a[:,:,:3]=np.rint((patch[:,:,:3]*mix[:,:,None]+a[:,:,:3]*(old*(1-mix))[:,:,None])/np.maximum(new[:,:,None],1e-8));a[:,:,3]=np.rint(new*255);a[a[:,:,3]==0]=0
    Image.fromarray(np.rint(mix*255).astype('uint8')).save(O/'Masks'/f'{pose}-{side}-retouch.png')
  # Native shoulder cap bridges the partition. It is stationary above y365
  # and fades before y410, never carrying old idle arm down into a new pose.
  cap=np.zeros_like(a);seg=r['segments'][side+'Upper'];bx,by,bx1,by1=seg['bounds'];cap[by:by1,bx:bx1]=np.array(Image.open(C/seg['image']));ca=cap[:,:,3]/255*(1-smooth((Y-360)/48));aa=a[:,:,3]/255;new=aa+ca*(1-aa)
  a[:,:,:3]=np.rint((a[:,:,:3]*aa[:,:,None]+cap[:,:,:3]*(ca*(1-aa))[:,:,None])/np.maximum(new[:,:,None],1e-8));a[:,:,3]=np.rint(new*255);a[a[:,:,3]==0]=0
  front=src.copy();front[:,:,3]=np.rint(hand[side]*255);front[front[:,:,3]==0]=0
  for pix in [a,front]:
   if pose=='rifle' and side=='right':
    # Source is a whole figure: this small isolated warm fragment below the
    # black pistol-grip heel is BELLY, not a little finger. Preserve the real
    # connected hand and remove only that independently inspected island.
    labels,n=ndi.label(pix[:,:,3]>=128);sizes=np.bincount(labels.ravel());main=int(sizes[1:].argmax()+1);mainmask=labels==main
    for label in range(1,n+1):
     if label==main or sizes[label]>100:continue
     bys,bxs=np.where(labels==label)
     if len(bxs) and bxs.min()>=365 and bxs.max()<=390 and bys.min()>=598 and bys.max()<=615:
      removal=ndi.binary_dilation(labels==label,iterations=1)&~mainmask;pix[removal]=0
   dist=ndi.distance_transform_edt(pix[:,:,3]<128);remote=(pix[:,:,3]>0)&(pix[:,:,3]<=16)&(dist>2);pix[remote]=0
   labels,n=ndi.label(pix[:,:,3]>0,np.ones((3,3)));sz=np.bincount(labels.ravel());tiny=(sz[labels]<=2)&(labels>0);pix[tiny]=0
  for kind,pix in [('arm',a),('front',front)]:Image.fromarray(pix).save(folder/f'{pose}-{side}-{kind}.png')
  Image.fromarray(np.rint(alpha*255).astype('uint8')).save(O/'Masks'/f'{pose}-{side}-arm.png')
  records.append({'pose':pose,'side':side,'source_sha256':hashlib.sha256((O/'Sources'/f'{pose}.png').read_bytes()).hexdigest(),'anchors':pts,'arm_bbox':Image.fromarray(a).getbbox(),'rgba_canvas':[W,H],'source_registration':{'scale':1,'x':0,'y':0}})
 target.setdefault('left',r['arms']['left']['grip'])
 if pose!='rifle':target['left']=r['arms']['left']['grip']
 cfg['weapons'][pose]={'id':'female-donor-'+pose,'class':pose,'pose':pose,'image':f'assets/female/donor-art/{pose}-weapon.png','size':[W,H],'primary':sides['right']['grip'],'support':sides.get('left',{}).get('grip'),'scale':1,'angle':0,'offset':[0,0],'order':30,'test_resource':True}
cfg['weapons']['rifle']['stock']=[280,400]
# Compute inverse bind through the same documented skeleton primitives. Final
# tests independently compare authored shoulder/elbow/wrist points with runtime.
(C/'rigs/female_rig.json').write_text(json.dumps(r,indent=2)+'\n');(C/'female-preview.json').write_text(json.dumps(cfg,indent=2)+'\n')
js="""import fs from 'node:fs';import{solveArm,armMatrices,rad}from './avatar-core/math.mjs';let r=JSON.parse(fs.readFileSync('./avatar-core/rigs/female_rig.json'));let grips=GRIP_DATA;let out={};for(let [p,pts]of Object.entries(r.poses)){out[p]={};for(let side of ['right','left']){if(!grips[p]?.[side])continue;let a={...r.arms[side],projection:r.anatomyProjection[p][side],grip:grips[p][side]};let angles=solveArm(a,a.shoulder,pts[side],pts.bend[side],rad(pts.handAngles[side]));out[p][side]=armMatrices(a,a.shoulder,angles)}}console.log(JSON.stringify(out));"""
js=js.replace('GRIP_DATA',json.dumps(calibration_grips));binds=json.loads(subprocess.check_output(['node','--input-type=module','-e',js],cwd=ROOT,text=True))
for row in records:
 pose,side=row['pose'],row['side'];pts=POINTS[pose][side];a=np.array(Image.open(C/f'assets/female/donor-art/{pose}-{side}-arm.png'));s,e,w,g=[np.array(pts[k],float) for k in ['shoulder','elbow','wrist','grip']];x0,y0,x1,y1=Image.fromarray(a).getbbox();xs=list(range(x0,x1,12))+[x1];ys=list(range(y0,y1,12))+[y1];vertices=[]
 def ld(p,a,b):t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1);return np.linalg.norm(p-a-(b-a)*t)
 for y in ys:
  for x in xs:
   p=np.array([x,y]);el=float(smooth((ld(p,s,e)-ld(p,e,w)+40)/80));wr=float(smooth((np.dot(p-w,(g-w)/np.linalg.norm(g-w))+10)/35));sh=float(smooth((y-325)/65));vertices.append([x,y,sh,el,wr])
 nx=len(xs);tri=[]
 for iy in range(len(ys)-1):
  for ix in range(nx-1):
   if a[ys[iy]:ys[iy+1]+1,xs[ix]:xs[ix+1]+1,3].any():
    v=iy*nx+ix;tri.extend([[v,v+1,v+nx],[v+1,v+nx+1,v+nx]])
 bind={k:binds[pose][side][k] for k in ['upper','fore','hand']};bind['torso']=[1,0,0,1,0,0]
 r['poseArt'].setdefault(pose,{})[side]={'image':f'assets/female/donor-art/{pose}-{side}-arm.png','frontImage':f'assets/female/donor-art/{pose}-{side}-front.png','mesh':{'bounds':[0,0,W,H],'vertices':vertices,'triangles':tri,'handTriangles':tri},'bind':bind,'anchors':pts,'grip':calibration_grips[pose][side],'source':f'review/female-donor-arm-pass/Sources/{pose}.png','artStatus':'donor arm pixels only; no source torso or whole-character replacement'}
(C/'rigs/female_rig.json').write_text(json.dumps(r,indent=2)+'\n');(O/'registration.json').write_text(json.dumps({'records':records,'points':POINTS,'polygons':POLYS,'hands':HANDS,'weapons':PROPS,'base_sha256':hashlib.sha256((ROOT/'base_female.png').read_bytes()).hexdigest()},indent=2)+'\n');print('Prepared four female donor arms and three independent props; originals untouched')
