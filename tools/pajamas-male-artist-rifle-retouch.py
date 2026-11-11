#!/usr/bin/env python3
"""Recovered two tiny artist-retouched rifle cloth joins and final promotion.

Uses exact recovered raw art and retained global similarity. Rebuild the v2
actual upper crop as target-upper.png using the unchanged native renderer;
it protects original gun/hands by exact actual-vs-shirt RGB comparison.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');ARGS=parser.parse_args()
REVIEW=ROOT/'review/sleeves-artist-20261111/male/rifle-seam-retouch'
OUT=ROOT/'review/artist-candidates/male-rifle.png'
REVIEW.mkdir(parents=True,exist_ok=True)
before_path=REVIEW/'top-before.png'
if not before_path.exists():shutil.copyfile(OUT,before_path)
raw=np.array(Image.open(REVIEW/'artist-retouch-raw.png').convert('RGBA'))
actual=np.array(Image.open(REVIEW/'target-upper.png').convert('RGBA'))
before=np.array(Image.open(before_path).convert('RGBA'))
assert actual.shape==(640,840,4)
matrix=np.array([[0.5754027812715363,-0.000821707340162799,-2.5840937904962926],[0.000821707340162799,0.5754027812715363,0.23076573603310693]],np.float64)
world=matrix.copy();world[:,2]+=[120,240]
work=raw.astype(np.float32);work[:,:,:3]*=work[:,:,3:4]/255
drawn=cv2.warpAffine(work,world,(941,1672),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT)
alpha=np.clip(drawn[:,:,3],0,255);rgb=np.zeros_like(drawn[:,:,:3])
np.divide(drawn[:,:,:3]*255,alpha[:,:,None],out=rgb,where=alpha[:,:,None]>.05);rgb=np.clip(rgb,0,255)
old_crop=np.zeros_like(actual);old_crop[:,:821]=before[240:880,120:941]
different=np.max(abs(actual[:,:,:3].astype(int)-old_crop[:,:,:3].astype(int)),axis=2)>4
protected=cv2.dilate(different.astype(np.uint8),np.ones((5,5),np.uint8))>0
cloth=(~protected)&(old_crop[:,:,3]>250)
regions={
 'below-left-stock':[(51,258),(104,257),(139,266),(151,276),(142,290),(110,295),(70,289),(52,280)],
 'above-right-receiver':[(525,310),(549,311),(568,325),(587,349),(587,375),(567,383),(543,365),(526,340)],
}
weight=np.zeros((1672,941),np.float32)
for name,polygon in regions.items():
    m=Image.new('L',(840,640));ImageDraw.Draw(m).polygon(polygon,fill=255)
    local=np.array(m.filter(ImageFilter.GaussianBlur(3.5))).astype(np.float32)/255;local*=cloth
    whole=np.zeros((1672,941),np.float32);whole[240:880,120:941]=local[:,:821]
    weight=np.maximum(weight,whole);Image.fromarray(np.rint(whole*255).astype(np.uint8)).save(REVIEW/f'mask-{name}.png')
weight*=alpha/255;after=before.copy()
after[:,:,:3]=np.rint(before[:,:,:3]*(1-weight[:,:,None])+rgb*weight[:,:,None]).astype(np.uint8)
after[after[:,:,3]==0,:3]=0;assert np.array_equal(before[:,:,3],after[:,:,3])
Image.fromarray(after,'RGBA').save(OUT,optimize=True)
Image.fromarray(after,'RGBA').save(REVIEW/'top-after.png',optimize=True)
patch=np.dstack([rgb,np.rint(weight*255)]).astype(np.uint8);patch[patch[:,:,3]==0,:3]=0
Image.fromarray(patch,'RGBA').save(REVIEW/'registered-cloth-patch.png',optimize=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data={'method':'Two local artist-painted cloth regions, retained exact global similarity. Original top alpha preserved; original actual gun/hand foreground excluded. No arm deformation or pattern transfer.',
 'recoveredFromHistory':True,'raw':str((REVIEW/'artist-retouch-raw.png').relative_to(ROOT)),
 'rawSha256':sha(REVIEW/'artist-retouch-raw.png'),'beforeSha256':sha(before_path),'candidateSha256':sha(OUT),
 'cropSimilarity':matrix.tolist(),'nativeSimilarity':world.tolist(),'inliers':375,'medianResidualPx':1.22028386592865,
 'regionCropPolygons':regions,'changedPixels':int(np.any(before!=after,axis=2).sum()),'alphaPreserved':True}
(REVIEW/'extraction.json').write_text(json.dumps(data,indent=2)+'\n')
parent=ROOT/'review/artist-candidates/male-artist-extraction.json'
metadata=json.loads(parent.read_text());metadata['poses']['rifle']['localArtistRetouch']=data
metadata['poses']['rifle']['candidateSha256']=data['candidateSha256'];parent.write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps(data,indent=2))

if ARGS.write:
    original=ROOT/'review/pajamas-implementation-20261111/male';runtime=ROOT/'assets/wardrobe/clothing/patient/pajamas/male'
    changes={f'top-{pose}.webp' for pose in ['idle','melee','rifle']}|{'thumb-top.webp'}
    preserved={p.name:sha(p) for p in runtime.glob('*.webp') if p.name not in changes}
    for pose in ['idle','melee','rifle']:
        candidate=ROOT/'review/artist-candidates'/f'male-{pose}.png'
        png=original/'registered'/f'top-{pose}.png';im=Image.open(candidate).convert('RGBA')
        assert im.size==(941,1672);shutil.copyfile(candidate,png)
        im.save(runtime/f'top-{pose}.webp',quality=88,method=6,exact=True)
    thumb=Image.open(original/'registered/top-idle.png').convert('RGBA');thumb=thumb.crop(thumb.getbbox())
    thumb.thumbnail((224,224),Image.Resampling.LANCZOS);thumbnail=Image.new('RGBA',(256,256))
    thumbnail.alpha_composite(thumb,((256-thumb.width)//2,(256-thumb.height)//2));thumbnail.save(runtime/'thumb-top.webp',quality=88,method=6,exact=True)
    assert preserved=={name:sha(runtime/name) for name in preserved}
    extraction_path=original/'extraction.json';extraction=json.loads(extraction_path.read_text())
    extraction['method']='Original approved canonical torso plus user-authorized artist sleeves. Retained exact whole-image similarities; tiny same-artist translated underlays fill native arm gaps. Two small rifle joins use the separately recovered local artist retouch. No final arm warp, UV texture transfer, native body/head/hand/weapon edit.'
    extraction['artistSleeveAuthorization']='художньо намалюй рукава а не викручуй їх; автомат також на шар вище'
    extraction['compositionOrder']=['minimal cloth-only underlay','unchanged canonical torso','artist sleeves and caps in front','original native weapon and hands above clothing']
    extraction['reproductionCommands']=['python tools/pajamas-male-extract.py','python tools/pajamas-male-artist-sleeves.py','python tools/pajamas-male-artist-rifle-retouch.py --write']
    extraction['registeredSize']=[941,1672];extraction['runtimeSize']=[941,1672]
    extraction['recoveredFromHistory']=True;extraction['readyForPublication']=False
    extraction['reproductionNote']='Recovered original artist raws and registration constants; no art regeneration. Native reference captures, exact native hand matte and v2 target-upper capture must first be rebuilt by unchanged approved runtime. Runtime visual QA required after recovery.'
    records=[]
    for name in ['top-idle','top-melee','top-rifle','pants','footwear']:
        png=original/'registered'/f'{name}.png';webp=runtime/f'{name}.webp';im=Image.open(png)
        records.append({'name':name,'png':str(png.relative_to(ROOT)),'pngSha256':sha(png),'webp':str(webp.relative_to(ROOT)),'webpSha256':sha(webp),'webpBytes':webp.stat().st_size,'registeredBbox':im.getchannel('A').point(lambda v:255 if v>=128 else 0).getbbox()})
    extraction['files']=records;files=[]
    for path in sorted(runtime.glob('*.webp')):
        im=Image.open(path).convert('RGBA');files.append({'name':path.name,'size':im.size,'bytes':path.stat().st_size,'alpha':im.getextrema()[3],'sha256':sha(path)})
    checkpoint={'assetsFrozenForVisualQa':True,'publicationReady':False,'recoveredFromHistory':True,
     'files':files,'runtimeBytes':sum(p.stat().st_size for p in runtime.glob('*.webp')),
     'compositionOrder':extraction['compositionOrder'],'reproductionCommands':extraction['reproductionCommands']}
    extraction['runtimeBytes']=checkpoint['runtimeBytes'];extraction_path.write_text(json.dumps(extraction,ensure_ascii=False,indent=2)+'\n')
    (original/'runtime-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(checkpoint,indent=2))
