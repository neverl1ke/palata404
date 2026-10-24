"""Recover only visible approved material. Never invent the occluded handles.
Outputs are explicit PARTIAL candidates, not production-ready reconstructed art.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';folder=C/'assets/weapons/original-visible';folder.mkdir(exist_ok=True);records=[];items=[]
for pose,name,label,ident,primary,support in [('rifle','rifle','Автомат','gear-aks',[390,644],[675,708]),('pistol','pistol','Пістолет','gear-pm',[230,351],None),('melee','knife','Ніж','gear-knife',[227,880],None)]:
 p=C/f'assets/weapons/reference-art/{pose}.png';a=np.array(Image.open(p).convert('RGBA'));old=a.copy();labels,n=ndi.label(a[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(labels.ravel());main=labels==int(sizes[1:].argmax()+1);a[~main]=0
 y,x=np.indices(a.shape[:2]);rgb=a[:,:,:3].astype(int)
 if pose=='rifle':zone=(x>=640)&(x<=735)&(y>=660)&(y<=740)
 elif pose=='pistol':zone=(x>=202)&(x<=267)&(y>=250)&(y<=365)
 else:zone=(x>=195)&(x<=232)&(y>=860)&(y<=900)
 # Local skin remnants only, not a global brown-pixel threshold for wood.
 skin=zone&(rgb[:,:,0]>155)&(rgb[:,:,0]-rgb[:,:,1]>12)&(rgb[:,:,0]-rgb[:,:,2]>35)
 if pose=='pistol':skin|=zone&(rgb[:,:,0]-rgb[:,:,1]>4)&(rgb[:,:,0]-rgb[:,:,2]>16)
 a[skin]=0
 rig=json.loads((C/'rigs/male_rig.json').read_text())
 for art in rig['poseArt'][pose].values():
  front=np.array(Image.open(C/art['frontImage']).convert('RGBA'));x0,y0,x1,y1=art['mesh']['bounds'];fm=np.zeros(a.shape[:2],bool);fm[y0:y1,x0:x1]=front[:,:,3]>0;a[ndi.binary_dilation(fm,iterations=1)]=0
 a[a[:,:,3]==0]=0
 dest=folder/f'weapon_{name}.png';Image.fromarray(a).save(dest)
 Image.fromarray(a).crop(Image.fromarray(a).getbbox()).save(folder/f'weapon_{name}.thumb.png')
 profiles={}
 for g in ['male','female']:
  cfg=json.loads((C/f'{g}-preview.json').read_text());d=cfg['weapons'][pose];dst=np.array(d['primary']);z=1+0j
  if pose=='rifle':z=complex(*(np.array(d['support'])-dst))/complex(*(np.array(support)-primary))
  profiles[g]={'primary':primary,'support':support,'offset':[0,0],'scale':abs(z),'angle':float(np.degrees(np.angle(z))),'stock':[257,512] if pose=='rifle' else None,'order':30}
  if pose!='rifle':profiles[g]['offset']=[0,0] # hand-local primary attachment drives the source.
 record={'id':ident,'name':label,'type':pose,'pose':pose,'image':str(dest.relative_to(C)),'thumbnail':str((folder/f'weapon_{name}.thumb.png').relative_to(C)),'attachmentByGender':profiles,'artStatus':'PARTIAL','previewOnly':True,'limitation':'Occluded handle/fore-end pixels are absent from the approved source; no invented material or replacement model used.'}
 items.append(record);records.append({'id':ident,'source':str(p.relative_to(R)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'output':str(dest.relative_to(R)),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'unchanged_surviving_RGBA':bool(np.array_equal(a[a[:,:,3]>0],old[a[:,:,3]>0])),'removed_skin_pixels':int(skin.sum()),'status':'PARTIAL','missing':'Full material-only original including concealed grip is unavailable in checked source layers.'})
(C/'equipment-weapons.json').write_text(json.dumps({'version':1,'items':items},ensure_ascii=False,indent=2)+'\n');(R/'review/avatar-requested-corrections/Evidence/original-weapons.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('3 visible-source candidates, all marked PARTIAL; no invented concealed material')
