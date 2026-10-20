"""Lossless ownership segmentation of approved bases; no synthesis or source overwrite.
Rig coordinates measured independently on the actual 941x1672 source PNGs.
Continuous skin weights reuse visible source pixels; missing surfaces are not invented.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
from scipy.ndimage import distance_transform_edt,binary_erosion
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'avatar-core';REVIEW=ROOT/'review/avatar-core-1';REVIEW.mkdir(parents=True,exist_ok=True)
DATA={
'male':{'head':[474,150],'neck':[474,285],'chest':[474,480],'pelvis':[474,800],
 'right':{'shoulder':[287,382],'elbow':[250,615],'wrist':[207,847],'grip':[217,920],'inner':[[283,311],[321,333],[334,369],[329,409],[318,443],[329,502],[333,550],[331,610],[310,730],[282,850],[283,1030]]},
 'left':{'shoulder':[657,381],'elbow':[697,615],'wrist':[747,847],'grip':[738,920],'inner':[[662,311],[624,333],[612,370],[618,411],[629,445],[618,502],[612,551],[614,610],[635,730],[663,850],[662,1030]]},
 'poses':{'melee':{'right':[225,912],'left':[738,920],'angle':150,'handAngles':{'right':0,'left':0},'bend':{'right':1,'left':-1}},'pistol':{'right':[230,300],'left':[738,920],'angle':-72,'handAngles':{'right':180,'left':0},'bend':{'right':-1,'left':-1}},'rifle':{'right':[460,580],'left':[644,635],'angle':30,'handAngles':{'right':-70,'left':170},'bend':{'right':1,'left':-1}}},'breathing':{'chestX':.0025,'chestY':.0012,'idleArmDegrees':.18}},
'female':{'head':[472.5,144],'neck':[472.5,280],'chest':[472.5,465],'pelvis':[472.5,795],
 'right':{'shoulder':[306,367],'elbow':[278,584],'wrist':[215,825],'grip':[222,890],'inner':[[318,300],[333,324],[342,355],[344,400],[345,440],[350,477],[342,530],[330,600],[299,715],[265,820],[263,991]]},
 'left':{'shoulder':[639,368],'elbow':[669,585],'wrist':[730,825],'grip':[724,891],'inner':[[626,301],[612,325],[603,356],[601,400],[600,440],[595,477],[604,531],[616,601],[645,716],[680,820],[682,991]]},
 'poses':{'melee':{'right':[230,888],'left':[724,891],'angle':150,'handAngles':{'right':0,'left':0},'bend':{'right':1,'left':-1}},'pistol':{'right':[246,300],'left':[724,891],'angle':-72,'handAngles':{'right':180,'left':0},'bend':{'right':-1,'left':-1}},'rifle':{'right':[450,560],'left':[634,615],'angle':30,'handAngles':{'right':-70,'left':170},'bend':{'right':1,'left':-1}}},'breathing':{'chestX':.002,'chestY':.001,'idleArmDegrees':.16}}
}
manifest={'version':1,'frame':[941,1672],'source_commit':'f70b7e5be63f6b85d895c6d5b259adbc30577b86','genders':{},'limitations':['Source hands have relaxed fingers, not authored trigger/support grips.','Continuous skinning cannot reconstruct hidden shoulder/elbow surfaces.']}
def savepart(a,mask,path):
 im=a.copy();im[~mask]=0;im[im[:,:,3]==0]=0;bb=Image.fromarray(im[:,:,3]).getbbox()
 if not bb:raise ValueError(path)
 Image.fromarray(im).crop(bb).save(path,optimize=True)
 return {'image':str(path.relative_to(OUT)),'bounds':list(bb),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
for gender,d in DATA.items():
 path=ROOT/f'base_{gender}.png';a=np.array(Image.open(path).convert('RGBA'));h,w=a.shape[:2];yy,xx=np.mgrid[:h,:w];labels=np.zeros((h,w),dtype='uint8');labels[yy<295]=1;labels[yy>=760]=2
 segs={};offset=3
 for side,edge in [('right',0),('left',941)]:
  arm=d[side];mask=Image.new('1',(w,h));poly=[(edge,arm['inner'][0][1]),*map(tuple,arm['inner']),(edge,arm['inner'][-1][1])];ImageDraw.Draw(mask).polygon(poly,fill=1);m=np.array(mask,dtype=bool)
  sh,el,wr=[np.array(arm[x]) for x in ['shoulder','elbow','wrist']]
  fore=(xx-el[0])*(el[0]-sh[0])+(yy-el[1])*(el[1]-sh[1])>=0
  hand=(xx-wr[0])*(wr[0]-el[0])+(yy-wr[1])*(wr[1]-el[1])>=0
  labels[m]=offset;labels[m&fore]=offset+1;labels[m&hand]=offset+2
  for n,code,pivot,parent in [('upper',offset,'shoulder','torso'),('fore',offset+1,'elbow',side+'Upper'),('hand',offset+2,'wrist',side+'Fore')]:
   sid=side+n.title();v=savepart(a,labels==code,OUT/'assets'/gender/(sid+'.png'));v.update({'pivot':arm[pivot],'parent':parent,'order':20+code});segs[sid]=v
  offset+=3
 for name,code,pivot,parent in [('torso',0,d['pelvis'],'root'),('head',1,d['neck'],'root'),('lower',2,d['pelvis'],'root')]:
  v=savepart(a,labels==code,OUT/'assets'/gender/(name+'.png'));v.update({'pivot':pivot,'parent':parent,'order':code});segs[name]=v
 # Simple diagnostic sleeves are derived from segment alpha, separate from anatomy.
 for sid in ['rightUpper','rightFore','leftUpper','leftFore']:
  seg=segs[sid];src=Image.open(OUT/seg['image']).convert('RGBA');v=np.array(src);alpha=v[:,:,3].copy();v[:,:,:3]=[52,122,128];v[:,:,3]=(alpha.astype(float)*.72).astype('uint8');v[v[:,:,3]==0]=0;Image.fromarray(v).save(OUT/'assets'/gender/(sid+'Sleeve.png'))
 # Every non-transparent source pixel belongs to exactly one regular segment.
 rebuilt=np.zeros_like(a)
 ids={0:'torso',1:'head',2:'lower',3:'rightUpper',4:'rightFore',5:'rightHand',6:'leftUpper',7:'leftFore',8:'leftHand'}
 for code,name in ids.items():rebuilt[labels==code]=a[labels==code]
 assert np.array_equal(rebuilt,a)
 rig={'id':gender+'_rig','gender':gender,'frame':[w,h],'source':'../base_'+gender+'.png','source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'landmarks':{k:v for k,v in d.items() if k not in ['right','left','poses','breathing']},'arms':{k:d[k] for k in ['right','left']},'poses':d['poses'],'breathing':d['breathing'],'segments':segs,'head_cut_y':295,'lower_cut_y':760,'partition_exact':True}

 # Continuous skin weights bridge rigid segment boundaries without inventing skin.
 meshes={};body=(labels==0)&(a[:,:,3]>=128);dist=distance_transform_edt(~body)
 def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
 for side,code in [('right',3),('left',6)]:
  amask=np.isin(labels,[code,code+1,code+2]);bb=Image.fromarray(np.where(amask,a[:,:,3],0).astype('uint8')).getbbox();x0,y0,x1,y1=bb
  for name,m in [(side+'ArmSkin',amask),(side+'HandSkin',labels==code+2)]:
   v=a.copy();v[~m]=0;v[v[:,:,3]==0]=0;Image.fromarray(v).crop(bb).save(OUT/'assets'/gender/(name+'.png'))
  xs=list(range(x0,x1,12))+[x1];ys=[y0];arm=d[side]
  while ys[-1]<y1:
   gy=ys[-1];step=8 if abs(gy-arm['elbow'][1])<65 or abs(gy-arm['wrist'][1])<40 else 16;ys.append(min(y1,gy+step))
  verts=[];sh,el,wr=[np.array(arm[k],float) for k in ['shoulder','elbow','wrist']];u=(el-sh)/np.linalg.norm(el-sh);v=(wr-el)/np.linalg.norm(wr-el)
  for gy in ys:
   for gx in xs:
    p=np.array([gx,gy]);ef=float(smooth(((p-el)@u+48)/96));hf=float(smooth(((p-wr)@v+18)/36));sw=float(smooth((dist[min(gy,h-1),min(gx,w-1)]-10)/45));sw*=float(smooth((gy-(sh[1]-25))/115));sw=max(sw,float(smooth((gy-500)/65)))
    verts.append([gx,gy,sw,ef,hf])
  triangles=[];handtri=[];nx=len(xs)
  for iy in range(len(ys)-1):
   for ix in range(nx-1):
    x,y,xn,yn=xs[ix],ys[iy],xs[ix+1],ys[iy+1]
    if not ((a[y:yn,x:xn,3]>0)&amask[y:yn,x:xn]).any():continue
    q=iy*nx+ix;pair=[[q,q+1,q+nx+1],[q,q+nx+1,q+nx]];triangles+=pair
    if ((a[y:yn,x:xn,3]>0)&(labels[y:yn,x:xn]==code+2)).any():handtri+=pair
  meshes[side]={'bounds':list(bb),'image':'assets/'+gender+'/'+side+'ArmSkin.png','handImage':'assets/'+gender+'/'+side+'HandSkin.png','vertices':verts,'triangles':triangles,'handTriangles':handtri,'grid_x_step':12,'joint_y_step':8,'interior_y_step':16}
 for sid,seg in segs.items():
  parent=segs.get(seg['parent']);parent_pivot=parent['pivot'] if parent else [0,0]
  seg['localPivot']=[seg['pivot'][0]-seg['bounds'][0],seg['pivot'][1]-seg['bounds'][1]]
  seg['bindOffset']=[seg['pivot'][0]-parent_pivot[0],seg['pivot'][1]-parent_pivot[1]]
 rig['skinMeshes']=meshes
 rp=OUT/'rigs'/(gender+'_rig.json');rp.write_text(json.dumps(rig,indent=2)+'\n');manifest['genders'][gender]={'rig':'rigs/'+rp.name,'source_sha256':rig['source_sha256'],'source_size':[w,h],'source_mode':'RGBA','alpha_bounds_1':list(Image.fromarray(a[:,:,3]).getbbox()),'alpha_bounds_128':list(Image.fromarray(np.where(a[:,:,3]>=128,255,0).astype('uint8')).getbbox()),'nonzero_alpha_pixels':int((a[:,:,3]>0).sum()),'weak_alpha_1_16':int(((a[:,:,3]>0)&(a[:,:,3]<=16)).sum()),'exact_partition':True}
 # Label/pivot evidence is a diagnostic of the real source, not a replacement portrait.
 bg=Image.new('RGBA',(w,h),'#b7b4ad');bg.alpha_composite(Image.fromarray(a));draw=ImageDraw.Draw(bg)
 for side in ['right','left']:
  points=[tuple(d[side][j]) for j in ['shoulder','elbow','wrist','grip']];draw.line(points,fill='#38bec4',width=3)
  for p,j in zip(points,['shoulder','elbow','wrist','grip']):draw.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill='#e9b94e');draw.text((p[0]+7,p[1]),side+' '+j,fill='white')
 bg.save(REVIEW/(gender+'-landmarks.png'))
manifest['note']='No original PNG overwritten; cropped lossless partitions, continuous arm skin weights copied from source geometry; no generated anatomy.'
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(REVIEW/'source-audit.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Deliberately schematic test weapons, shared by both rigs, not finished game art.
weapondefs={
 'melee':{'size':[140,300],'primary':[67,240],'support':None,'polygons':[[[64,12],[79,160],[71,210],[57,210],[49,160]],[[45,205],[88,205],[88,218],[45,218]],[[58,218],[76,218],[78,282],[56,282]]]},
 'pistol':{'size':[210,150],'primary':[65,107],'support':[83,118],'polygons':[[[20,22],[195,22],[195,61],[112,61],[100,85],[46,85],[20,68]],[[48,74],[100,74],[85,143],[41,143]]]},
 'rifle':{'size':[480,160],'primary':[175,120],'support':[313,87],'polygons':[[[12,40],[91,47],[123,66],[140,64],[140,96],[100,98],[25,108]],[[121,55],[315,55],[315,93],[121,93]],[[312,65],[466,65],[466,76],[312,76]],[[164,92],[190,92],[198,150],[168,150]],[[225,93],[266,93],[273,145],[230,151]]]},
}
for name,v in weapondefs.items():
 im=Image.new('RGBA',v['size']);dr=ImageDraw.Draw(im)
 for i,poly in enumerate(v['polygons']):dr.polygon(poly,fill=('#626968' if i%2==0 else '#393b3b'),outline='#202627',width=2)
 im.save(OUT/'assets/weapons'/(name+'.png'));v.pop('polygons');v.update({'id':'test-'+name,'class':name,'pose':name,'image':'assets/weapons/'+name+'.png','scale':1,'offset':[0,0],'angle':0,'order':30,'test_resource':True})
weapondefs['melee']['scale']=.8
weapondefs['rifle']['scale']=1.35
(OUT/'weapons.json').write_text(json.dumps(weapondefs,indent=2)+'\n')
print('Prepared male_rig and female_rig; original sources unchanged; exact pixel partition.')
