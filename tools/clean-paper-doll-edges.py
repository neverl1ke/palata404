"""Selective, repeatable edge repair from an immutable pre-audit PNG snapshot.
No RGB blur, no global erosion, no filling hair gaps. A rear strand layer is
sampled from the approved male shoulder hair texture (not a flat-color patch).
"""
import argparse,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('audit',ROOT/'tools/audit-paper-doll-png.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def clean(arr,kind):
 a=arr.copy();alpha=a[:,:,3].astype(float);strong=alpha>=32;dist=ndi.distance_transform_edt(~strong)
 # Source hair is ~4-6x larger than its final rendering. Keep faint nearby
 # strands; remove only the remote 1..16-alpha export haze, feathering its end.
 radius=2
 fade=1-smooth((dist-radius)/1.5);weak=(alpha>0)&(alpha<=16)
 alpha[weak]=np.rint(alpha[weak]*fade[weak])
 # Selective antialiasing of solid skin only. Fine hair keeps its original AA.
 if kind in ['body','head']:
  support=alpha>=128;boundary=(ndi.distance_transform_edt(support)<=1.5)&(ndi.distance_transform_edt(~support)<=1.5)
  filtered=ndi.gaussian_filter(alpha,.42);zone=boundary
  if kind=='head':zone=zone&(np.arange(a.shape[0])[:,None]<215) # joins solved jointly below
  alpha[zone]=filtered[zone]
 a[:,:,3]=np.rint(alpha).clip(0,255)
 # Entire detached alpha<=16 specks are export ringing, not opaque strands,
 # fingers or ear detail. The alpha>=17 hair support is strictly protected.
 labels,n=ndi.label(a[:,:,3]>0,np.ones((3,3)))
 if n:
  peaks=ndi.maximum(a[:,:,3],labels,np.arange(1,n+1));bad=np.flatnonzero(peaks<=16)+1
  a[:,:,3][np.isin(labels,bad)]=0
 core=a[:,:,3]>=240;distance,idx=ndi.distance_transform_edt(~core,return_indices=True)
 donor=a[idx[0],idx[1],:3].astype(float);rgb=a[:,:,:3].astype(float)
 lum=rgb@np.array([.2126,.7152,.0722]);ref=donor@np.array([.2126,.7152,.0722]);ratio=np.divide(lum,ref,out=np.ones_like(lum),where=ref>10)
 # Correct only evidence of black premultiplication, not drawn outlines.
 edge=(a[:,:,3]>0)&(a[:,:,3]<220)&(distance<=3)&(ref>25)&(ratio<.8)&(np.abs(ratio-a[:,:,3]/255)<.16)
 corrected=rgb*255/np.maximum(a[:,:,3,None],1);corrected=np.minimum(np.maximum(corrected,donor-25),donor+25)
 a[edge,:3]=np.rint(corrected).clip(0,255)[edge]
 a[a[:,:,3]==0]=0
 return a,dict(weak_pixels_removed=int(((arr[:,:,3]>0)&(a[:,:,3]==0)).sum()),edge_rgb_corrected=int(edge.sum()),alpha_changed=int((a[:,:,3]!=arr[:,:,3]).sum()))
def joined_head(head,oldbase,newbase,mask):
 # Preserve existing head texture/fade while solving the new edge and mask
 # together; this prevents double AA outlines and disconnected mask specks.
 ba=oldbase[:,:,3]/255;ha=head[:,:,3]/255;mv=mask[:,:,3]/255;target=ha+ba*mv*(1-ha)
 support=target>=.5;boundary=(ndi.distance_transform_edt(support)<=1.5)&(ndi.distance_transform_edt(~support)<=1.5)
 filtered=ndi.gaussian_filter(target,.42);ys=np.arange(len(target))[:,None];zone=boundary&(ys>=215)&(ys<310)
 target[zone]=filtered[zone]
 nba=newbase[:,:,3]/255
 # Lower torso is exactly the newly cleaned base; do not extend the overlay.
 last=np.where(np.any(head[:,:,3]>0,axis=1))[0][-1]+1;target[ys[:,0]>=last]=nba[ys[:,0]>=last]
 target[250:288,445:505]=np.maximum(target[250:288,445:505],nba[250:288,445:505])
 target=np.clip(target,0,1);ha=np.minimum(ha,target)
 minimum=np.divide(target-nba,1-nba,out=np.zeros_like(target),where=nba<1)
 ha=np.maximum(ha,np.clip(minimum,0,1));ha[ys[:,0]>=last]=0
 # Retain the approved upper head AA (only the neck is solved here).
 ha[ys[:,0]<215]=head[ys[:,0]<215,:,3]/255
 visibility=np.divide(target-ha,nba*(1-ha),out=np.zeros_like(target),where=nba*(1-ha)>1e-8)
 visibility[ys[:,0]<215]=0;visibility[ys[:,0]>=last]=1
 result=head.copy();expanded=(ha*255>head[:,:,3]+.5)&(head[:,:,3]<64)
 _,idx=ndi.distance_transform_edt(head[:,:,3]<192,return_indices=True);result[expanded,:3]=head[idx[0],idx[1],:3][expanded]
 result[:,:,3]=np.rint(ha*255).clip(0,255);result[result[:,:,3]==0]=0
 m=np.full_like(mask,255);m[:,:,3]=np.ceil(np.clip(visibility,0,1)*255).astype('uint8')
 return result,m
def create_rear_layer():
 # Existing strand texture copied down behind the two inner ear openings.
 # The entire facial region remains in front of this rear-only layer.
 im=Image.open(ROOT/'assets/wardrobe/hair/male_medium_shoulder_length.png').convert('RGBA').resize((277,277),Image.Resampling.LANCZOS);front=Image.new('RGBA',(941,1672));front.paste(im,(331,22));f=np.array(front);back=np.zeros_like(f)
 ss=4;shape=Image.new('L',(941*ss,1672*ss));draw=ImageDraw.Draw(shape)
 for poly in [[(382,131),(420,131),(431,199),(420,216),(387,202),(375,160)],[(524,131),(561,130),(571,160),(560,204),(527,216),(515,199)]]:draw.polygon([(x*ss,y*ss) for x,y in poly],fill=255)
 shape=np.array(shape.resize((941,1672),Image.Resampling.LANCZOS))/255
 xx=np.arange(941);sample_x=np.clip(xx+np.where(xx<474,-22,22),0,940)
 for y in range(128,218):
  row1=f[max(0,y-23),sample_x];row2=f[max(0,y-36),sample_x];choose=row1[:,3]>=row2[:,3];row=np.where(choose[:,None],row1,row2);back[y]=row;back[y,:,3]=np.rint(row[:,3]*shape[y]).clip(0,255)
 back,_=clean(back,'underlay');back[:,:,3][back[:,:,3]>=240]=255;bp=ROOT/'assets/wardrobe/hair/male_medium_shoulder_length_rear.png';Image.fromarray(back).save(bp,optimize=True)
 return bp

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--snapshot',type=Path,required=True);a=p.parse_args();records=[]
 for rel in audit.resources():
  if '/masks/' in rel or 'patient_tunic_' in rel or rel.endswith('_rear.png'):continue
  kind='body' if rel.startswith('base_') else 'hair' if '/hair/' in rel else 'head' if '/faces/' in rel else 'underlay'
  source=a.snapshot/rel;old=np.array(Image.open(source).convert('RGBA'));new,stats=clean(old,kind)
  dest=ROOT/rel;Image.fromarray(new).save(dest,optimize=True);records.append(dict(path=rel,before_sha256=sha(source),sha256=sha(dest),kind=kind,**stats))
 cat=audit.catalog()
 for item in cat['items']:
  for g,maskpath in item.get('bodyMaskByGender',{}).items():
   rel=item['genderVariants'][g].split('?')[0];mp=maskpath.split('?')[0];head=np.array(Image.open(ROOT/rel).convert('RGBA'));oldbase=np.array(Image.open(a.snapshot/f'base_{g}.png').convert('RGBA'));newbase=np.array(Image.open(ROOT/f'base_{g}.png').convert('RGBA'))
   if (a.snapshot/mp).exists():
    mask=np.array(Image.open(a.snapshot/mp).convert('RGBA'));h,m=joined_head(head,oldbase,newbase,mask)
   else:
    # Asian overlays previously exposed 601/704 old-base pixels outside
    # their head silhouette. Give them a real registered neck/body join.
    spec=importlib.util.spec_from_file_location('prepare',ROOT/'tools/prepare-avatar-update.py');prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)
    profile=(474,72,230,252,10) if g=='male' else (474,65,230,252,10)
    hi,mi=prepare.face(Image.fromarray(head),g,profile);h=np.array(hi);m=np.array(mi)
   Image.fromarray(h).save(ROOT/rel,optimize=True);Image.fromarray(m).save(ROOT/mp,optimize=True)
   for r in records:
    if r['path']==rel:r['sha256']=sha(ROOT/rel)
   records.append(dict(path=mp,before_sha256=sha(a.snapshot/mp) if (a.snapshot/mp).exists() else None,sha256=sha(ROOT/mp),kind='joint-mask'))
 bp=create_rear_layer();records.append(dict(path=str(bp.relative_to(ROOT)),sha256=sha(bp),kind='rear-strands',source='male_medium_shoulder_length.png',render_order=-1))
 output=ROOT/'review/paper-doll-audit-2026-10/edge-repairs.json';output.write_text(json.dumps({'source_commit':'dbbcddff2f79a3393271ac6afc4d261221d9b77e','files':records},indent=2)+'\n');print('Processed',len(records),'resources')
