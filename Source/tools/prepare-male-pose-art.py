"""Extract arm-only corrective art; originals, torso, face and female rig untouched.

The two edited pose images are working art, not replacement full-body avatars.
Only explicit arm masks enter the renderer. Gray test weapons are excluded.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'review/avatar-core-2'
CORE=ROOT/'avatar-core'
rigpath=CORE/'rigs/male_rig.json'
rig=json.loads(rigpath.read_text())
rig.update(json.loads((CORE/'rigs/male_anatomy.json').read_text()))
for mesh in rig['skinMeshes'].values():mesh.pop('preserveCrossSection',None)
bindings=json.loads((OUT/'pose-bindings.json').read_text())
polygons={
 ('rifle','right'):[(275,307),(316,313),(350,350),(352,390),(340,430),(335,463),(315,508),(301,537),(354,562),(407,552),(443,539),(482,540),(507,570),(510,622),(484,654),(421,651),(343,649),(277,657),(218,650),(182,642),(175,610),(178,567),(198,504),(221,453),(231,406),(231,369),(245,333)],
 ('rifle','left'):[(630,308),(671,310),(703,340),(720,382),(721,428),(744,481),(766,550),(769,613),(753,654),(705,676),(651,684),(605,678),(561,663),(539,633),(541,595),(562,571),(592,555),(626,556),(654,578),(657,551),(642,511),(623,468),(606,433),(600,387),(608,343)],
 ('pistol','right'):[(275,308),(317,314),(349,350),(352,398),(339,445),(324,498),(305,548),(284,590),(248,617),(211,616),(188,593),(176,551),(174,505),(187,449),(206,396),(211,362),(191,342),(182,315),(183,278),(202,262),(223,281),(243,296),(269,299),(285,329)],
}
def smooth(v):
    t=np.clip(v,0,1);return t*t*(3-2*t)
records=[]
rig['poseArt']={}
for (pose,side),poly in polygons.items():
    image=OUT/'sources'/f'{pose}-arm-edit.png'
    rgba=np.array(Image.open(image).convert('RGBA'))
    # Saturated warm skin against neutral gray. The weapon is achromatic.
    rgb=rgba[:,:,:3].astype(float)
    skin=smooth((rgb[:,:,0]-rgb[:,:,2]-16)/8)*smooth((rgb[:,:,0]-rgb[:,:,1]-5)/5)
    mask=Image.new('L',(941*4,1672*4));ImageDraw.Draw(mask).polygon([(x*4,y*4) for x,y in poly],fill=255)
    mask=np.array(mask.resize((941,1672),Image.Resampling.LANCZOS))/255
    yy,xx=np.indices(mask.shape)
    # Only the torso-facing part of the shoulder is feathered; silhouette
    # edges and elbow anatomy are not blurred. Overlap stays on original torso.
    if side=='right':
        shoulder=smooth((yy-309)/25)
        inner=1-smooth((xx-318)/29)*(1-smooth((yy-420)/60))
    else:
        shoulder=smooth((yy-309)/25)
        inner=smooth((xx-603)/28)+(1-smooth((xx-603)/28))*smooth((yy-430)/65)
    # Raised pistol hand lies above the shoulder; never fade its fingers.
    if pose=='pistol':shoulder=np.where(xx<285,1,shoulder)
    torso=np.zeros((1672,941));part=rig['segments']['torso'];tx,ty,tx1,ty1=part['bounds'];torso[ty:ty1,tx:tx1]=np.array(Image.open(CORE/part['image']))[:,:,3]/255
    # Feather only over existing opaque torso, never across its cut boundary.
    overlap=shoulder*inner
    alpha=mask*skin*np.where(torso>.99,overlap,1)
    alpha[alpha<1/255]=0
    rgba[:,:,3]=np.rint(alpha*255).astype('uint8');rgba[rgba[:,:,3]==0]=0
    labels,n=ndi.label(rgba[:,:,3]>0);sizes=np.bincount(labels.ravel());sizes[0]=0
    for i in range(1,n+1):
        if sizes[i]<6:rgba[labels==i]=0
    arm=bindings[pose]['arms'][side]
    s,e,w,g=[np.array(arm[k]) for k in ['shoulder','elbow','wrist','grip']]
    # Front hand is a local wrist half-plane; rear arm remains behind weapon.
    direction=g-w;direction/=np.linalg.norm(direction)
    along=(xx-w[0])*direction[0]+(yy-w[1])*direction[1]
    front=rgba.copy();front[:,:,3]=np.rint(front[:,:,3]*smooth((along+3)/12)).astype('uint8');front[front[:,:,3]==0]=0
    masks=OUT/'authoring-masks';masks.mkdir(exist_ok=True)
    Image.fromarray(rgba[:,:,3]).save(masks/f'{pose}-{side}-mask.png')
    bounds=Image.fromarray(rgba).getbbox();x0,y0,x1,y1=bounds
    folder=CORE/'assets/male/pose-art';folder.mkdir(parents=True,exist_ok=True)
    paths=[]
    for kind,pixels in [('arm',rgba),('front',front)]:
        path=folder/f'{pose}-{side}-{kind}.png';Image.fromarray(pixels).crop(bounds).save(path);paths.append(str(path.relative_to(CORE)))
    xs=list(range(x0,x1,12))+[x1];ys=list(range(y0,y1,12))+[y1]
    vertices=[]
    def line_distance(p,a,b):
        t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1)
        return np.linalg.norm(p-a-(b-a)*t)
    for y in ys:
        for x in xs:
            p=np.array([x,y]);du=line_distance(p,s,e);df=line_distance(p,e,w)
            # Rigid regions permit path batching; only joints interpolate.
            elbow=float(smooth((du-df+60)/120))
            wrist=float(smooth((np.dot(p-w,direction)+10)/40))
            wrist*=float(1-smooth((np.linalg.norm(p-g)-85)/70))
            shoulder=float(1-(1-smooth(np.linalg.norm(p-s)/80))*(1-elbow)*(1-wrist))
            vertices.append([x,y,shoulder,elbow,wrist])
    triangles=[];nx=len(xs)
    for iy in range(len(ys)-1):
        for ix in range(nx-1):
            a=iy*nx+ix;b=a+1;c=a+nx;d=c+1
            # Empty UV cells have no anatomy and need no triangles. Keep every
            # cell touching even alpha1; natural gaps are not filled.
            if np.any(rgba[ys[iy]:min(ys[iy+1]+1,1672),xs[ix]:min(xs[ix+1]+1,941),3]):
                triangles.extend([[a,b,c],[b,d,c]])
    mesh={'bounds':list(bounds),'vertices':vertices,'triangles':triangles,'handTriangles':triangles}
    entry={'image':paths[0],'frontImage':paths[1],'mesh':mesh,
        'bind':{**{k:arm[k] for k in ['upper','fore','hand']},'torso':bindings[pose]['transforms']['torso']},
        'anchors':{k:arm[k] for k in ['shoulder','elbow','wrist','grip']},
        'source':str(image.relative_to(ROOT)),'polygon':poly,
        'artStatus':'local generated arm edit, extracted within explicit masks; requires visual approval'}
    rig['poseArt'].setdefault(pose,{})[side]=entry
    records.append({'pose':pose,'side':side,'bounds':bounds,'source_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),
        'files':[{'path':p,'sha256':hashlib.sha256((CORE/p).read_bytes()).hexdigest()} for p in paths],
        'polygon':poly,'alpha_method':'warm skin matte inside supersampled arm polygon; shoulder overlap only'})
rigpath.write_text(json.dumps(rig,indent=2)+'\n')
(OUT/'arm-art-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
print('Extracted',len(records),'arm corrections; originals never written')
