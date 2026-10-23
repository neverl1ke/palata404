"""Technical grid overlays only: no production garment, avatar or art generation."""
from pathlib import Path
from PIL import Image
import numpy as np,json
R=Path(__file__).resolve().parents[1];C=R/'avatar-core';D=C/'assets/diagnostics';D.mkdir(exist_ok=True);config={}
def grid(alpha,x0=0,y0=0):
 y,x=np.indices(alpha.shape);a=np.zeros((*alpha.shape,4),dtype='uint8');line=((x+x0)%16<2)|((y+y0)%16<2);a[:,:,:3]=[15,100,180];a[line,:3]=[255,225,0];a[:,:,3]=np.rint(np.where(alpha>=128,alpha,0).astype(float)*.84);return a
for g in ['male','female']:
 cfg=json.load(open(C/f'{g}-preview.json'));rig=json.load(open(C/f'rigs/{g}_rig.json'));base=np.array(Image.open(R/f'base_{g}.png'));Y,X=np.indices(base.shape[:2]);entries={}
 for kind in ['collar','waist-top','trousers','shoes']:
  mask={'collar':(Y>=278)&(Y<320),'waist-top':(Y>340)&(Y<790),'trousers':(Y>=740)&(Y<1300),'shoes':Y>1470}[kind];a=grid(base[:,:,3]*mask);name=f'{g}-{kind}.png';Image.fromarray(a).save(D/name);entries[kind]=[{'id':'diagnostic-'+kind,'segment':'torso' if kind in ['collar','waist-top'] else 'lower','source':'assets/diagnostics/'+name,'placement':{'x':0,'y':0,'width':941,'height':1672},'genders':[g]}]
 for kind in ['short-sleeve','long-sleeve','cuff','glove']:
  bindings=[]
  for side in ['right','left']:
   # Rest-space fallback really matches the approved idle geometry.
   skin=rig['skinMeshes'][side];bounds=skin['bounds'];x0,y0,x1,y1=bounds;image=np.array(Image.open(C/cfg.get('runtimeSurfaces',{}).get(side+'ArmSkin',skin['image'])));yy,xx=np.indices(image.shape[:2]);glob=np.stack([xx+x0,yy+y0],axis=-1);arm=rig['arms'][side];shoulder=np.array(arm['shoulder']);elbow=np.array(arm['elbow']);wrist=np.array(arm['wrist']);u=elbow-shoulder;v=wrist-elbow;dist=(glob-wrist)@v/np.linalg.norm(v)
   mask={'short-sleeve':(glob-shoulder)@u/np.linalg.norm(u)<np.linalg.norm(u)*.6,'long-sleeve':dist<0,'cuff':np.abs(dist)<7,'glove':dist>=-4}[kind];a=grid(image[:,:,3]*mask,x0,y0);name=f'{g}-{side}-{kind}-idle.png';Image.fromarray(a).save(D/name);poses={}
   for pose,sides in rig['poseArt'].items():
    if side not in sides:continue
    art=sides[side];x0,y0,x1,y1=art['mesh']['bounds'];path=cfg['poseArtSurfaces'][f'art-{pose}-{side}'];im=np.array(Image.open(C/path));fr=np.array(Image.open(C/cfg['poseArtSurfaces'][f'art-front-{pose}-{side}']));full=np.array(Image.open(C/cfg['poseArtCompleteSurfaces'][pose+'-'+side]));yy,xx=np.indices(im.shape[:2]);glob=np.stack([xx+x0,yy+y0],axis=-1);j=art['anchors'];s=np.array(j['shoulder']);e=np.array(j['elbow']);w=np.array(j['wrist']);u=e-s;v=w-e;dist=(glob-w)@v/np.linalg.norm(v)
    mask={'short-sleeve':(glob-s)@u/np.linalg.norm(u)<np.linalg.norm(u)*.6,'long-sleeve':dist<0,'cuff':np.abs(dist)<7,'glove':dist>=-4}[kind];a=grid(im[:,:,3]*mask,x0,y0);f=grid(fr[:,:,3]*mask,x0,y0);name=f'{g}-{pose}-{side}-{kind}';Image.fromarray(a).save(D/(name+'.png'));Image.fromarray(f).save(D/(name+'-front.png'));Image.fromarray(grid(full[:,:,3]*mask,x0,y0)).save(D/(name+'-complete.png'));poses[pose]={'image':f'assets/diagnostics/{name}.png','frontImage':f'assets/diagnostics/{name}-front.png','completeImage':f'assets/diagnostics/{name}-complete.png'}
   b=skin['bounds'];bindings.append({'id':f'diagnostic-{side}-{kind}','segment':side+'Hand' if kind=='glove' else side+'Upper','skinned':True,'source':f'assets/diagnostics/{g}-{side}-{kind}-idle.png','placement':{'x':b[0],'y':b[1],'width':b[2]-b[0],'height':b[3]-b[1]},'poseSources':poses,'genders':[g]})
  entries[kind]=bindings
 config[g]=entries
(D/'config.json').write_text(json.dumps(config,indent=2)+'\n');print('Diagnostic grid bindings prepared for both genders, all authored poses and native idle')
