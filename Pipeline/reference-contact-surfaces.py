"""Source-coordinate contact surfaces. These trace visible art, not new anatomy.
No source image is written. Coordinates are in the supplied 941x1672 references.
"""
import numpy as np
from PIL import Image,ImageDraw
from scipy.interpolate import CubicSpline
from scipy import ndimage as ndi

def curved_mask(points):
 p=np.asarray(points,float);p=np.vstack([p,p[0]]);length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];t=np.linspace(0,length[-1],max(100,int(length[-1]*3)));q=CubicSpline(length,p,bc_type='periodic')(t)
 im=Image.new('L',(941*4,1672*4));ImageDraw.Draw(im).polygon([tuple(v) for v in np.rint(q*4).astype(int)],fill=255);return np.asarray(im.resize((941,1672),Image.Resampling.LANCZOS))/255
RIGHT_FINGERS=[(315,544),(350,550),(390,551),(417,559),(442,573),(465,589),(484,606),(492,614),(493,622),(489,625),(484,624),(476,619),(462,607),(449,601),(444,603),(448,609),(449,615),(447,620),(442,625),(437,626),(433,624),(431,629),(428,634),(423,638),(418,639),(413,637),(410,641),(405,645),(399,646),(393,644),(383,639),(374,635),(365,630),(355,625),(345,618),(335,612),(325,606),(315,604)]
LEFT_FINGERS=[(623,704),(625,693),(631,683),(640,674),(646,673),(649,676),(652,673),(655,667),(662,665),(669,666),(674,670),(676,676),(679,673),(684,674),(690,679),(693,687),(695,694),(699,691),(704,694),(709,702),(712,713),(713,725),(710,735),(704,741),(695,746),(685,747),(676,743),(669,740),(660,739),(652,736),(645,733),(637,729),(630,723),(625,715)]
PISTOL_HANDLE=[(194,314),(205,312),(220,321),(234,318),(243,308),(249,305),(251,313),(243,331),(232,346),(218,351),(207,348),(199,341),(194,329)]
# The complete top and bottom of the wooden fore-end, around (not through)
# the supporting fingers. Visible wood is authoritative source paint.
RIFLE_FORE_END=[(612,602),(630,611),(649,624),(669,637),(690,648),(710,659),(729,669),(747,680),(762,693),(774,711),(773,723),(763,734),(749,736),(733,727),(715,717),(696,706),(679,694),(659,695),(640,686),(623,680),(610,676),(598,670),(588,662),(591,650),(606,642),(603,628)]
RIFLE_GRIP=[(359,628),(369,631),(383,636),(398,642),(408,645),(405,651),(399,657),(388,656),(375,651),(364,645),(356,638)]
MELEE_HANDLE=[(207,834),(215,833),(225,845),(237,863),(247,865),(249,871),(237,883),(219,901),(205,907),(190,905),(188,899),(199,883),(196,871),(195,854)]

def contact_masks(pose,src,subject,hand_masks,prop_alpha,mask):
 rgb=src[:,:,:3].astype(float)
 if pose=='rifle':
  hand_masks['right']=curved_mask(RIGHT_FINGERS)*subject
  hand_masks['left']=curved_mask(LEFT_FINGERS)*subject
  fore=curved_mask(RIFLE_FORE_END)*subject
  fraction=np.clip((40-(rgb[:,:,0]-rgb[:,:,2]))/18,0,1);fraction[rgb.max(2)<95]=1
  grip=curved_mask(RIFLE_GRIP)*subject*fraction
  repair=np.maximum.reduce([fore,grip,mask([(708,705),(790,705),(790,758),(708,758)])*subject])
 elif pose=='pistol':
  # An explicitly interior solid handle, not all enclosed dark areas globally.
  repair=np.maximum(mask(PISTOL_HANDLE),mask([(210,216),(259,208),(279,250),(285,291),(275,305),(256,300),(245,306),(220,281),(207,261)])*subject)
 else:
  visible_guard=mask([(234,859),(245,859),(249,863),(244,869),(237,870)])*subject*(rgb.max(2)>28)
  repair=np.maximum(mask([(200,840),(210,836),(223,848),(235,863),(236,871),(218,891),(205,900),(195,901),(195,889),(197,870)])*subject,visible_guard)
 # Cold exterior stencil crumbs are backdrop/metal, not new skin. Preserve
 # interior dark folds: only the outer 1.5px of each hand stencil is eligible.
 for side,h in hand_masks.items():
  inside=ndi.distance_transform_edt(h>.5)
  cold=(inside<=1.5)&(h>0)&(rgb.max(2)<110)&(rgb[:,:,0]-rgb[:,:,2]<=16)
  h[cold]=0
  hand_masks[side]=h
 # These small windows are wholly inside a photographed solid contact,
 # not a blanket fill of enclosed holes. Preserve the source RGB ownership:
 # warm exposed skin stays on the hand, neutral/dark material on the item.
 windows={'pistol':(195,315,240,355),'melee':(209,842,225,868)}
 if pose in windows:
  x0,y0,x1,y1=windows[pose];solid=np.zeros(subject.shape,bool);solid[y0:y1,x0:x1]=True
  warm=(rgb[:,:,0]>70)&(rgb[:,:,0]-rgb[:,:,2]>25)&(rgb[:,:,0]-rgb[:,:,1]>5)
  h=hand_masks['right'];skin=solid&(warm|(h>=.98));material=solid&~skin
  h[skin]=1;h[material]=0;hand_masks['right']=h;repair[solid]=1
 if pose=='rifle':
  # Restore native antialias coverage only at the real exterior of the left
  # hand. Opaque body pixels behind the right hand never enter this rule.
  h=hand_masks['left'];near=ndi.distance_transform_edt(h<=.5)<=1.5
  exterior=ndi.distance_transform_edt(subject>=.94)<=2
  skin=(rgb[:,:,0]>90)&(rgb[:,:,0]-rgb[:,:,2]>25)&(rgb[:,:,0]-rgb[:,:,1]>10)
  recover=near&exterior&skin&(subject>=.94)
  h[recover]=subject[recover];hand_masks['left']=h
  # At a fully opaque source pixel the antialias of an INTERNAL ownership
  # boundary must not reveal backdrop. Keep that exact source paint on the
  # majority owner; exterior source alpha and real negative space stay intact.
  q=np.zeros(subject.shape,bool);q[645:755,630:755]=True;q &= subject>=.94
  h=hand_masks['left'];hand_owner=q&(h>=.5)
  item_owner=q&(h<.5)&((repair>.01)|(prop_alpha>.01))
  h[hand_owner]=subject[hand_owner];h[item_owner]=0
  repair[item_owner]=subject[item_owner];hand_masks['left']=h
  # One dark material edge beside the little finger belongs to the wooden
  # fore-end, as shown by the supplied RGBA source (not exterior backdrop).
  small=np.zeros(subject.shape);small[675:688,629:636]=1
  repair=np.maximum(repair,small*subject*(rgb.max(2)<100)*(rgb[:,:,0]-rgb[:,:,2]<25))
 hands=np.maximum.reduce(list(hand_masks.values()))
 # Front fingers own their visible pixels. Repair independent object surfaces
 # behind them; do not multiply two complementary masks a second time.
 prop_alpha=np.maximum(prop_alpha*(1-hands),repair*(1-hands))
 return hand_masks,prop_alpha,repair

def unmatte_exterior(a,source_rgb,subject,pose=None):
 """Remove BLACK backdrop premultiplication at the exterior of RGB sources.
 Interior folds/contact boundaries do not enter this operation.
 """
 dist=ndi.distance_transform_edt(subject>.5);rgb=source_rgb.astype(float)
 reliable=(a[:,:,3]>=240)&(rgb.max(2)>120)&(rgb[:,:,0]-rgb[:,:,2]>25)&(dist>=3)
 if not reliable.any():return a
 distance,ix=ndi.distance_transform_edt(~reliable,return_indices=True);near=rgb[ix[0],ix[1]]
 outer=dist<=2
 if pose=='pistol':
  yy,xx=np.indices(dist.shape)
  # The reference has a narrow, partially antialiased negative space here.
  # Its backdrop is not uniformly <=8 RGB; use the arm's actual contour too.
  local=(xx>=225)&(xx<=280)&(yy>=315)&(yy<=430)
  outer|=local&(ndi.distance_transform_edt(a[:,:,3]>128)<=1.5)
 edge=(a[:,:,3]>0)&outer&(distance<=5)&(rgb.max(2)<150)
 fraction=np.clip((rgb*near).sum(2)/np.maximum(1,(near*near).sum(2)),.01,1)
 a[edge,:3]=np.rint(np.clip(rgb[edge]/fraction[edge,None],0,255));a[edge,3]=np.rint(a[edge,3]*fraction[edge]);a[a[:,:,3]==0]=0
 return a
