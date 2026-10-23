"""Reproducible male lobby calibration and arm extraction. Original art is read-only."""
from pathlib import Path
import json,math,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';OUT=ROOT/'review/avatar-core-lobby-rework';OUT.mkdir(exist_ok=True)
RIG=CORE/'rigs/male_rig.json';rig=json.loads(RIG.read_text());config=json.loads((CORE/'male-preview.json').read_text())
anchors={'right':{'shoulder':[287,382],'elbow':[231,598],'wrist':[324,631],'grip':[364,668]},'left':{'shoulder':[657,381],'elbow':[711,620],'wrist':[658,725],'grip':[619,755]}}
if '--calibrate' in sys.argv:
    pose=rig['poses']['rifle'];pose.update(right=anchors['right']['grip'],left=anchors['left']['grip'],angle=0)
    for side,a in anchors.items():
        rest=rig['arms'][side];s,e,w,g=[np.array(a[k],float) for k in ['shoulder','elbow','wrist','grip']];rs,re,rw=[np.array(rest[k],float) for k in ['shoulder','elbow','wrist']]
        rig['anatomyProjection']['rifle'][side]=[float(np.linalg.norm(e-s)/np.linalg.norm(re-rs)),float(np.linalg.norm(w-e)/np.linalg.norm(rw-re))]
        rig['handCorrections']['rifle'][side]['grip']=[float(rw[0]),float(rw[1]+np.linalg.norm(g-w))]
        pose['handAngles'][side]=float(math.degrees(math.atan2(*(g-w)[::-1]))-90)
        cross=(w-s)[0]*(e-s)[1]-(w-s)[1]*(e-s)[0];pose['bend'][side]=1 if cross>0 else -1
    # The old rifle arm artwork and placeholder-specific contact patches are
    # intentionally replaced by a complete new, independently registered pair.
    rig['poseArt'].pop('rifle',None);config['contactRepairs']=[]
    RIG.write_text(json.dumps(rig,indent=2)+'\n');(CORE/'male-preview.json').write_text(json.dumps(config,indent=2)+'\n')
    (OUT/'calibration.json').write_text(json.dumps({'anchors':anchors,'poses':rig['poses'],'projection':rig['anatomyProjection'],'breathingProfiles':config['breathingProfiles']},indent=2)+'\n');sys.exit()
# Sources are working compositions only. Their head/torso/legs never enter art.
polygons={
'right':[(275,307),(316,313),(351,350),(356,404),(338,457),(320,502),(296,552),(321,572),(352,588),(386,615),(410,644),(416,681),(402,709),(370,714),(344,708),(328,699),(317,676),(281,660),(245,651),(214,640),(195,620),(194,592),(202,559),(217,500),(227,442),(230,399),(235,357),(252,326)],
'left':[(625,307),(672,313),(706,344),(725,382),(729,435),(746,489),(755,550),(752,608),(737,653),(711,690),(682,718),(674,749),(660,772),(639,790),(606,794),(577,780),(550,764),(547,748),(563,734),(580,733),(594,718),(615,700),(630,696),(644,665),(653,630),(657,590),(645,558),(627,516),(613,474),(599,431),(599,389),(605,349)]}
bindings=json.loads((OUT/'pose-bindings.json').read_text());src=OUT/'sources/rifle-arms-working.png';rgb=np.array(Image.open(src).convert('RGBA'));torso=np.zeros((1672,941));part=rig['segments']['torso'];x,y,x1,y1=part['bounds'];torso[y:y1,x:x1]=np.array(Image.open(CORE/part['image']))[:,:,3]/255
def smooth(v):t=np.clip(v,0,1);return t*t*(3-2*t)
yy,xx=np.indices((1672,941));records=[]
rig['poseArt']['rifle']={}
for side,poly in polygons.items():
    rgba=rgb.copy();v=rgba[:,:,:3].astype(float)
    skin=smooth((v[:,:,0]-v[:,:,2]-16)/8)*smooth((v[:,:,0]-v[:,:,1]-5)/5)
    m=Image.new('L',(941*4,1672*4));ImageDraw.Draw(m).polygon([(x*4,y*4) for x,y in poly],fill=255);mask=np.array(m.resize((941,1672),Image.Resampling.LANCZOS))/255
    shoulder=smooth((yy-309)/28)
    inner=(1-smooth((xx-318)/29)*(1-smooth((yy-430)/65))) if side=='right' else (smooth((xx-603)/28)+(1-smooth((xx-603)/28))*smooth((yy-440)/65))
    alpha=rgba[:,:,3]/255*mask*skin*np.where(torso>.99,shoulder*inner,1)
    alpha[alpha<1/255]=0;rgba[:,:,3]=np.rint(alpha*255).astype('uint8');rgba[rgba[:,:,3]==0]=0
    labels,n=ndi.label(rgba[:,:,3]>0);sizes=np.bincount(labels.ravel());sizes[0]=0
    for i in range(1,n+1):
        if sizes[i]<6:rgba[labels==i]=0
    a=bindings['arms'][side];s,e,w,g=[np.array(a[k]) for k in ['shoulder','elbow','wrist','grip']];direction=g-w;direction/=np.linalg.norm(direction)
    along=(xx-w[0])*direction[0]+(yy-w[1])*direction[1];front=rgba.copy();front[:,:,3]=np.rint(front[:,:,3]*smooth((along+3)/12)).astype('uint8');front[front[:,:,3]==0]=0
    bounds=Image.fromarray(rgba).getbbox();x0,y0,x1,y1=bounds;folder=CORE/'assets/male/lobby';folder.mkdir(parents=True,exist_ok=True);paths=[]
    for kind,pixels in [('arm',rgba),('front',front)]:
        p=folder/f'rifle-{side}-{kind}.png';Image.fromarray(pixels).crop(bounds).save(p);paths.append(str(p.relative_to(CORE)))
    xs=list(range(x0,x1,12))+[x1];ys=list(range(y0,y1,12))+[y1];vertices=[]
    def ld(p,a,b):t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1);return np.linalg.norm(p-a-(b-a)*t)
    for y in ys:
        for x in xs:
            p=np.array([x,y]);el=float(smooth((ld(p,s,e)-ld(p,e,w)+60)/120));wr=float(smooth((np.dot(p-w,direction)+10)/40))*float(1-smooth((np.linalg.norm(p-g)-85)/70));sh=float(1-(1-smooth(np.linalg.norm(p-s)/80))*(1-el)*(1-wr));vertices.append([x,y,sh,el,wr])
    tri=[];nx=len(xs)
    for iy in range(len(ys)-1):
        for ix in range(nx-1):
            if np.any(rgba[ys[iy]:min(ys[iy+1]+1,1672),xs[ix]:min(xs[ix+1]+1,941),3]):
                aa=iy*nx+ix;bb=aa+1;cc=aa+nx;dd=cc+1;tri.extend([[aa,bb,cc],[bb,dd,cc]])
    entry={'image':paths[0],'frontImage':paths[1],'mesh':{'bounds':list(bounds),'vertices':vertices,'triangles':tri,'handTriangles':tri},'bind':{**{k:a[k] for k in ['upper','fore','hand']},'torso':bindings['transforms']['torso']},'anchors':{k:a[k] for k in ['shoulder','elbow','wrist','grip']},'source':str(src.relative_to(ROOT)),'polygon':poly,'artStatus':'new male relaxed lobby arms; arm-only matte, requires approval'}
    rig['poseArt']['rifle'][side]=entry;records.append({'side':side,'bounds':bounds,'polygon':poly,'files':[{'path':p,'sha256':hashlib.sha256((CORE/p).read_bytes()).hexdigest()} for p in paths]})
RIG.write_text(json.dumps(rig,indent=2)+'\n');(OUT/'arm-art-manifest.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'parts':records},indent=2)+'\n')
print('Extracted two relaxed arm meshes, four RGBA PNGs; originals read-only')
