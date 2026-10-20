"""Register locally redrawn pose hands; original bodies/segments stay unchanged.

Run after prepare-avatar-core.py. Source atlases are preserved, not regenerated.
Only uniform scale/rotation/translation and technical alpha/tone registration.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'avatar-core'
REVIEW=ROOT/'review/avatar-core-polish'
SLOTS=[('melee','right',0,0),('pistol','right',1,0),('rifle','right',2,0),
       ('pistol','left',0,1),('rifle','left',1,1)]
records=[]
for gender in ['male','female']:
    rigpath=CORE/'rigs'/f'{gender}_rig.json'
    rig=json.loads(rigpath.read_text())
    base=np.array(Image.open(ROOT/f'base_{gender}.png').convert('RGBA'))
    source=REVIEW/'sources'/f'{gender}-hands-generated.png'
    atlas=Image.open(source).convert('RGBA')
    rig['handCorrections']={}
    rig['wristProfiles']={}
    for side,arm in rig['arms'].items():
        u=np.array(arm['wrist'],float)-np.array(arm['elbow'],float);u/=np.linalg.norm(u);n=np.array([-u[1],u[0]])
        offsets=np.arange(-90,91);points=np.array(arm['wrist'])-20*u+offsets[:,None]*n
        coords=np.rint(points).astype(int);valid=base[coords[:,1],coords[:,0],3]>=128
        component=valid.copy();centre=90
        lo=centre;hi=centre
        while lo>0 and valid[lo-1]:lo-=1
        while hi<180 and valid[hi+1]:hi+=1
        rig['wristProfiles'][side]={'halfWidth':float((hi-lo+1)/2),'sampleOffset':-20}
    for pose,side,col,row in SLOTS:
        cell=atlas.crop((col*atlas.width//3,row*atlas.height//2,
                         (col+1)*atlas.width//3,(row+1)*atlas.height//2))
        a=np.array(cell)
        # Remove only almost-invisible alpha noise, restore opaque skin. No blur.
        a[:,:,3]=np.clip((a[:,:,3].astype(float)-1)*255/249,0,255).astype('uint8')
        a[a[:,:,3]==0]=0
        bb=Image.fromarray(a[:,:,3]).getbbox()
        if not bb:raise ValueError((gender,pose,side))
        a=a[bb[1]:bb[3],bb[0]:bb[2]].copy();h,w=a.shape[:2]
        wrist=np.array([w*.48,h*.78])
        grip=np.array([w*.51,h*.45])
        # Wider cupped hands have an angled, off-centre wrist.
        if side=='left':wrist=np.array([w*.64,h*.78])
        row_alpha=a[round(h*.78),:,3];xs=np.flatnonzero(row_alpha>=128)
        if len(xs):wrist[0]=(xs[0]+xs[-1])/2
        arm=rig['arms'][side];wr=np.array(arm['wrist'],float)
        closed_grip=wr+np.array([0,42 if gender=='male' else 38])
        target=closed_grip-wr
        v=grip-wrist;scale=np.linalg.norm(target)/np.linalg.norm(v)
        rotation=math.atan2(target[1],target[0])-math.atan2(v[1],v[0])
        c,s=math.cos(rotation)*scale,math.sin(rotation)*scale
        matrix=np.array([[c,-s,wr[0]-c*wrist[0]+s*wrist[1]],
                         [s,c,wr[1]-s*wrist[0]-c*wrist[1]],[0,0,1]])
        wx,wy=map(int,wr);body=base[wy-12:wy+13,wx-12:wx+13]
        target_tone=np.median(body[:,:,:3][body[:,:,3]>=240],axis=0)
        band=a[round(h*.76):round(h*.93)]
        tone=np.median(band[:,:,:3][band[:,:,3]>=250],axis=0)
        delta=np.clip(target_tone-tone,-22,22)
        a[:,:,:3]=np.clip(a[:,:,:3].astype(float)+delta,0,255).astype('uint8')
        a[a[:,:,3]==0]=0
        # Feather only the proximal cut INSIDE the source-wrist overlap.
        fade=np.clip((h-1-np.arange(h))/(h*.055),0,1)
        a[:,:,3]=(a[:,:,3].astype(float)*fade[:,None]).astype('uint8')
        inv=np.linalg.inv(matrix)
        full=Image.fromarray(a).transform((941,1672),Image.Transform.AFFINE,
                  tuple(inv[:2].ravel()),Image.Resampling.BICUBIC)
        # Hide the authored stump cut only inside the original wrist overlap.
        # This is a local alpha join, not blur or a change to the source forearm.
        pixels=np.array(full);yy=np.arange(1672)[:,None];t=(yy-wr[1])/18
        t=np.clip(t,0,1);fade=t*t*(3-2*t)
        alpha=pixels[:,:,3].astype(float)*fade
        alpha=np.where(yy<wr[1],alpha*base[:,:,3]/255,alpha)
        pixels[:,:,3]=np.rint(alpha).astype('uint8')
        labels,num=ndi.label(pixels[:,:,3]>0);sizes=np.bincount(labels.ravel());sizes[0]=0
        main=int(sizes.argmax())
        for component in range(1,num+1):
            if component==main:continue
            if sizes[component]>8:raise ValueError(('Unexpected detached hand detail',gender,pose,side,int(sizes[component])))
            pixels[labels==component]=0
        pixels[pixels[:,:,3]==0]=0
        full=Image.fromarray(pixels)
        bounds=full.getbbox();image=f'assets/{gender}/hands/{pose}-{side}.png'
        p=CORE/image;p.parent.mkdir(parents=True,exist_ok=True)
        full.crop(bounds).save(p)
        entry={'image':image,'bounds':list(bounds),'pivot':list(wr),'grip':list(closed_grip),
               'atlas_to_rest_rotation_deg':math.degrees(rotation),
               'scale':float(scale),'tone_delta_rgb':list(delta),
               'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        rig['handCorrections'].setdefault(pose,{})[side]=entry
        records.append({'gender':gender,'pose':pose,'side':side,**entry,
                        'source':str(source.relative_to(ROOT)),
                        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    # Extend distal topology/texture bounds to the union of authored hands.
    # Keep the prototype arm PNGs intact: padded source copies have new paths.
    for side,mesh in rig['skinMeshes'].items():
        oldbounds=mesh['bounds'];x0,y0,x1,y1=oldbounds
        entries=[hands[side] for hands in rig['handCorrections'].values() if side in hands]
        nx0=min([x0]+[e['bounds'][0]-2 for e in entries]);nx1=max([x1]+[e['bounds'][2]+2 for e in entries])
        newbounds=[nx0,y0,nx1,y1]
        oldverts=mesh['vertices'];oldxs=sorted({v[0] for v in oldverts});ys=sorted({v[1] for v in oldverts})
        xs=sorted(set(oldxs+[nx0,nx1]));lookup={(v[0],v[1]):v for v in oldverts};nx=len(xs)
        wr=np.array(rig['arms'][side]['wrist']);el=np.array(rig['arms'][side]['elbow']);u=(wr-el)/np.linalg.norm(wr-el)
        vertices=[]
        for y in ys:
            for x in xs:
                if (x,y) in lookup:vertices.append(lookup[x,y]);continue
                near=lookup[min(oldxs,key=lambda z:abs(z-x)),y]
                t=np.clip(((np.array([x,y])-wr)@u+18)/36,0,1);hf=float(t*t*(3-2*t))
                vertices.append([x,y,near[2],near[3],hf])
        index={(v[0],v[1]):i for i,v in enumerate(vertices)}
        triangles={tuple(index[tuple(oldverts[i][:2])] for i in tri) for tri in mesh['triangles']}
        for iy in range(len(ys)-1):
            if ys[iy+1]<wr[1]-55:continue
            for ix in range(nx-1):
                q=iy*nx+ix;triangles.add((q,q+1,q+nx+1));triangles.add((q,q+nx+1,q+nx))
        mesh['vertices']=vertices;mesh['bounds']=newbounds
        mesh['triangles']=[list(t) for t in sorted(triangles,key=lambda t:(min(t),t[1]))]
        mesh['handTriangles']=[t for t in mesh['triangles'] if max(vertices[i][1] for i in t)>=wr[1]-55]
        for key,suffix in [('image','arm'),('handImage','open-hand')]:
            # Always start from the unchanged prototype source, making reruns stable.
            original=CORE/f'assets/{gender}/{side}{"ArmSkin" if key=="image" else "HandSkin"}.png'
            image=Image.open(original).convert('RGBA');original_bounds=rig.get('sourceSkinBounds',{}).get(side,oldbounds)
            padded=Image.new('RGBA',(nx1-nx0,y1-y0));padded.alpha_composite(image,(original_bounds[0]-nx0,0))
            path=f'assets/{gender}/hands/{side}-{suffix}-source.png';padded.save(CORE/path);mesh[key]=path
        rig.setdefault('sourceSkinBounds',{})[side]=rig.get('sourceSkinBounds',{}).get(side,oldbounds)
    # Neutral hand art is registered in source coordinates; orient its painted
    # fingers along the actual weapon instead of twisting open source palms.
    def angle(pose,side,world):
        return world-rig['handCorrections'][pose][side]['atlas_to_rest_rotation_deg']
    old=rig.get('pistolOneHand',rig['poses']['pistol'])
    rig['pistolOneHand']={**old,'handAngles':{'right':angle('pistol','right',-72),'left':0}}
    rig['poses']['melee']['angle']=210
    rig['poses']['melee']['right']=[225,875] if gender=='male' else [230,850]
    rig['poses']['melee']['handAngles']['right']=angle('melee','right',180)
    rig['poses']['pistol']={'right':[465,505] if gender=='male' else [465,495],
        'left':[484,515],'angle':20,'handAngles':{
        'right':angle('pistol','right',35),'left':angle('pistol','left',-35)},
        'bend':{'right':1,'left':-1}}
    rig['poses']['rifle']['right']=[465,590] if gender=='male' else [455,575]
    rig['poses']['rifle']['handAngles']={'right':angle('rifle','right',45),'left':angle('rifle','left',-110)}
    rigpath.write_text(json.dumps(rig,indent=2)+'\n')
weapons=json.loads((CORE/'weapons.json').read_text())
weapons['pistol']['primary']=[45,110] # Contact at the rear edge of the actual grip.
weapons['rifle']['support']=[285,82] # Receiver fore-end, before the barrel.
(CORE/'weapons.json').write_text(json.dumps(weapons,indent=2)+'\n')
(REVIEW/'hand-registration.json').write_text(json.dumps({'hands':records,
    'note':'Local corrective hand sprites only. Original base/face PNGs untouched.'},indent=2)+'\n')
print('Prepared10 registered pose-specific hands; no original PNG changed.')
