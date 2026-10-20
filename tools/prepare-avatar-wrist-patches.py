"""Bake local wrist retouches back into existing UVs; no skeleton/body edits.

Only the [-40,+35] source-pixel wrist band is eligible. The atlas was edited
from actual isolated Lab renders. Finger grips and incoming arm remain intact.
"""
from pathlib import Path
import gzip,hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core'
OUT=ROOT/'review/avatar-core-cleanup';OUT.mkdir(parents=True,exist_ok=True)
SOURCES=ROOT/'review/avatar-core-polish/sources'
reference=json.loads(gzip.open(SOURCES/'wrist-reference.json.gz','rt').read())
rigs={g:json.loads((CORE/'rigs'/f'{g}_rig.json').read_text()) for g in ['male','female']}
atlases={g:Image.open(SOURCES/f'{g}-wrist-edited.png').convert('RGBA') for g in rigs}
records=[]

def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)

def premultiply(a):
    a=np.asarray(a,dtype=float)/255
    a[:,:,:3]*=a[:,:,3,None];return a

def sample(a,x,y):
    """Bilinear sampling of premultiplied colors, zero outside actual artwork."""
    result=np.zeros((*x.shape,4));ix=np.floor(x).astype(int);iy=np.floor(y).astype(int)
    fx=x-ix;fy=y-iy
    for dx,dy,w in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
        xx=ix+dx;yy=iy+dy;valid=(xx>=0)&(yy>=0)&(xx<a.shape[1])&(yy<a.shape[0])
        result[valid]+=a[yy[valid],xx[valid]]*w[valid,None]
    return result

def signed_edge(alpha):
    """Distance to the silhouette, not a union of two translucent outlines."""
    inside=alpha>=.5
    return np.where(inside,ndi.distance_transform_edt(inside)-.5,
                    .5-ndi.distance_transform_edt(~inside))

for record in reference['records']:
    g,pose,side=record['gender'],record['pose'],record['side'];rig=rigs[g]
    mesh=rig['skinMeshes'][side];refmesh=record['mesh']
    if not np.array_equal(np.array(mesh['vertices']),np.array(refmesh['vertices'])):
        raise ValueError('Rig changed: recapture wrist references before baking')
    if mesh['bounds']!=refmesh['bounds']:raise ValueError('UV bounds changed')
    target=rig['poses'][pose]['right']
    if np.linalg.norm(np.array(record['frame']['arms']['right']['grip'])-target)>1e-6:
        raise ValueError('Pose calibration changed: recapture wrist references')
    for joint,bone in [('shoulder','upper'),('elbow','fore'),('wrist','hand')]:
        m=record['frame']['arms'][side][bone];p=rig['arms'][side][joint]
        mapped=[m[0]*p[0]+m[2]*p[1]+m[4],m[1]*p[0]+m[3]*p[1]+m[5]]
        if np.linalg.norm(np.array(mapped)-record['frame']['arms'][side][joint])>1e-6:
            raise ValueError('Source pivots changed')
    atlas=atlases[g];slot=record['slot'];cw=atlas.width//3;ch=atlas.height//2
    if abs(cw/ch-1)>0.01:raise ValueError('Retouched atlas must preserve square cells')
    cell=atlas.crop(((slot%3)*cw,(slot//3)*ch,(slot%3+1)*cw,(slot//3+1)*ch))
    a=np.array(cell);a[:,:,3]=np.clip((a[:,:,3].astype(float)-1)*255/249,0,255).astype('uint8');a[a[:,:,3]==0]=0
    cell=Image.fromarray(a).convert('RGBa').resize((200,200),Image.Resampling.LANCZOS).convert('RGBA')
    paint=premultiply(cell)
    x0,y0,x1,y1=mesh['bounds'];wy=rig['arms'][side]['wrist'][1]
    top=max(y0,wy-40);bottom=min(y1,wy+35)
    yy,xx=np.mgrid[top:bottom,x0:x1];qx=xx+.5;qy=yy+.5
    original_vertices=np.array(refmesh['vertices'],float);deformed=np.array(record['vertices'],float)
    xs=np.unique(original_vertices[:,0]);ys=np.unique(original_vertices[:,1]);nx=len(xs)
    ix=np.clip(np.searchsorted(xs,qx,side='right')-1,0,len(xs)-2)
    iy=np.clip(np.searchsorted(ys,qy,side='right')-1,0,len(ys)-2)
    tx=(qx-xs[ix])/(xs[ix+1]-xs[ix]);ty=(qy-ys[iy])/(ys[iy+1]-ys[iy])
    q=iy*nx+ix;d00=deformed[q];d10=deformed[q+1];d01=deformed[q+nx];d11=deformed[q+nx+1]
    first=(1-tx)[...,None]*d00+(tx-ty)[...,None]*d10+ty[...,None]*d11
    second=(1-ty)[...,None]*d00+tx[...,None]*d11+(ty-tx)[...,None]*d01
    world=np.where((tx>=ty)[...,None],first,second)
    box=record['world_crop']
    edited=sample(paint,world[:,:,0]-box[0]-.5,world[:,:,1]-box[1]-.5)
    base=Image.open(SOURCES/record['uv_source']).convert('RGBA')
    base=premultiply(base.crop((0,top-y0,x1-x0,bottom-y0)))
    weight=smooth((qy-(wy-40))/20)*smooth(((wy+35)-qy)/20)
    mixed=base*(1-weight[...,None])+edited*weight[...,None]
    coverage=mixed[:,:,3]
    rgb=np.divide(mixed[:,:,:3],coverage[:,:,None],out=np.zeros_like(mixed[:,:,:3]),where=coverage[:,:,None]>1e-8)
    # Blending coverage formed an alpha union: the old cuff's protruding edge
    # survived beside the retouched wrist. Interpolate the contour instead.
    edge=signed_edge(base[:,:,3])*(1-weight)+signed_edge(edited[:,:,3])*weight
    alpha=np.clip(edge+.5,0,1)
    alpha=np.where(weight<1e-7,base[:,:,3],np.where(weight>1-1e-7,edited[:,:,3],alpha))
    # The UV texture is wider than the wrist and contains faint original remote
    # pixels. Those are not this cleanup's subject; preserve their coverage.
    alpha=np.where(abs(qx-rig['arms'][side]['wrist'][0])<75,alpha,coverage)
    rgba=np.rint(np.clip(np.dstack([rgb,alpha]),0,1)*255).astype('uint8')
    remote=(rgba[:,:,3]>0)&(rgba[:,:,3]<=16)&(ndi.distance_transform_edt(rgba[:,:,3]<32)>4)
    rgba[remote]=0;rgba[rgba[:,:,3]==0]=0
    path=f'assets/{g}/hands/{pose}-{side}-wrist-clean.png';Image.fromarray(rgba).save(CORE/path)
    entry={'image':path,'bounds':[x0,top,x1,bottom],'sha256':hashlib.sha256((CORE/path).read_bytes()).hexdigest(),
           'source_band':[-40,-20,15,35],'source_atlas':f'review/avatar-core-polish/sources/{g}-wrist-edited.png',
           'edge_method':'signed-distance contour interpolation; exact original coverage at band limits'}
    rig['handCorrections'][pose][side]['wristPatch']=entry
    records.append({'gender':g,'pose':pose,'side':side,**entry})

for g,rig in rigs.items():(CORE/'rigs'/f'{g}_rig.json').write_text(json.dumps(rig,indent=2)+'\n')
(OUT/'wrist-patch-registration.json').write_text(json.dumps({'patches':records,
    'method':'Actual pose render -> local wrist edit -> inverse piecewise affine UV bake; only the source wrist band changes.'},indent=2)+'\n')
print('Baked10 local wrist bands; no body, face, bone or grip position changed.')
