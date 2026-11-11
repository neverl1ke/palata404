#!/usr/bin/env python3
"""Recovered final male artist sleeve extraction; one whole-pose similarity.

Raw art was recovered byte-for-byte. Code is reconstructed from the completed
pre-outage tool calls. Registration constants are the exact retained previous
fit, so lost target captures are not refitted and no arms are deformed.
"""
from pathlib import Path
import hashlib,json
import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'review/sleeves-artist-20261111/male'
OUT=ROOT/'review/artist-candidates'
ORIGINAL=ROOT/'review/pajamas-implementation-20261111/male'
REF=ROOT/'review/pajamas-implementation-20261111/references'
for p in [OUT,ART/'source-masks']:p.mkdir(parents=True,exist_ok=True)
MATRICES={
 'idle':[[1.0641614489557358,-0.00606711428228223,5.7113770525092455],[0.00606711428228223,1.0641614489557358,-2.9150610442806393]],
 'melee':[[1.0651856627555536,-0.0039200611353065575,4.412744583027249],[0.0039200611353065575,1.0651856627555536,-1.8014209204794718]],
 'rifle':[[1.0630342040946688,-0.0013910949339597375,32.135996975633475],[0.0013910949339597375,1.0630342040946688,-0.12844625514488864]],
}
QA={'idle':(117,1.0538981),'melee':(118,1.0699184),'rifle':(196,1.0065387)}
IDLE_LEFT=[(240,288),(263,299),(280,321),(295,351),(305,391),(307,432),(299,477),(289,509),(282,536),(272,562),(257,601),(243,648),(231,694),(223,738),(224,782),(209,791),(174,787),(143,783),(136,730),(138,664),(147,601),(158,554),(177,507),(190,457),(202,404),(212,359),(222,321)]
IDLE_RIGHT=[(619,292),(610,312),(601,344),(595,380),(591,421),(590,464),(592,500),(599,535),(609,570),(618,609),(632,659),(647,705),(658,750),(658,786),(687,792),(737,788),(742,730),(735,661),(725,597),(711,546),(692,505),(680,461),(668,412),(661,369),(649,328),(633,301)]
MELEE_LEFT=[(240,287),(264,298),(281,321),(295,352),(305,392),(306,433),(298,477),(288,508),(279,535),(268,565),(252,608),(239,655),(229,698),(225,739),(225,778),(210,786),(175,785),(148,781),(142,735),(140,684),(145,629),(153,582),(163,540),(176,507),(190,460),(202,405),(212,360),(222,321)]
RIFLE_LEFT_UPPER=[(250,281),(267,298),(281,322),(288,351),(287,381),(280,410),(247,407),(207,475),(173,482),(142,485),(159,454),(176,429),(184,399),(188,369),(199,337),(219,309)]
RIFLE_LEFT_FOREARM=[(110,489),(142,483),(165,486),(198,494),(230,503),(271,516),(301,524),(331,530),(326,557),(321,586),(317,610),(291,614),(255,613),(218,608),(179,602),(141,591),(117,580),(109,559),(107,533)]
RIFLE_RIGHT=[(599,292),(595,317),(587,345),(579,383),(575,424),(575,468),(580,503),(592,529),(608,542),(631,563),(655,581),(680,592),(695,597),(703,585),(701,560),(698,534),(690,508),(677,486),(666,461),(655,437),(647,400),(641,362),(636,331),(619,302)]
POLYGONS={'idle':{'left':[IDLE_LEFT],'right':[IDLE_RIGHT]},'melee':{'left':[MELEE_LEFT],'right':[IDLE_RIGHT]},'rifle':{'left':[RIFLE_LEFT_UPPER,RIFLE_LEFT_FOREARM],'right':[RIFLE_RIGHT]}}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def matte(size,polygons):
    scale=4;mask=Image.new('L',(size[0]*scale,size[1]*scale));draw=ImageDraw.Draw(mask)
    for polygon in polygons:draw.polygon([(round(x*scale),round(y*scale)) for x,y in polygon],fill=255)
    return np.asarray(mask.resize(size,Image.Resampling.LANCZOS))
def registered(pixels,matrix):
    work=pixels.astype(np.float32);work[:,:,:3]*=work[:,:,3:4]/255
    result=cv2.warpAffine(work,matrix,(941,1672),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_CONSTANT)
    alpha=np.clip(result[:,:,3],0,255);rgb=np.zeros_like(result[:,:,:3])
    np.divide(result[:,:,:3]*255,alpha[:,:,None],out=rgb,where=alpha[:,:,None]>.05)
    result=np.dstack([np.clip(rgb,0,255),alpha]).round().astype(np.uint8)
    result[result[:,:,3]==0,:3]=0;return Image.fromarray(result,'RGBA')
def coverage_underlay(sleeves,top,native,pose):
    pixels=np.array(sleeves);body=np.array(native)[:,:941];authored=np.array(top)
    yy,xx=np.mgrid[:1672,:941]
    if pose=='rifle':
        regions=[
         ('left-under-stock',(xx>175)&(xx<325)&(yy>400)&(yy<558),[(18,0),(-18,0),(36,0),(-36,0),(54,0),(72,0),(-18,36)]),
         ('right-under-receiver',(xx>638)&(xx<790)&(yy>520)&(yy<655),[(-18,0),(-36,0),(-18,36),(-36,36),(-18,54),(-54,54),(-72,54),(0,54)]),
        ]
    else:
        regions=[
         ('left-inner',(xx>220)&(xx<330)&(yy>545)&(yy<820),[(18,0),(36,0)]),
         ('right-outer-shoulder',(xx>675)&(xx<730)&(yy>310)&(yy<470),[(18,0),(36,0)]),
         ('right-inner',(xx>635)&(xx<720)&(yy>545)&(yy<820),[(-18,0),(-36,0)]),
        ]
    hand=np.zeros((1672,941),np.uint8)
    if pose=='rifle':hand=np.array(Image.open(ROOT/'review/pajamas-implementation-20261111/hand-masks/male-rifle.png').getchannel('A'))
    skin=(body[:,:,0].astype(int)-body[:,:,2].astype(int)>25)&(body[:,:,3]>32)
    result=np.zeros_like(pixels);notes=[]
    for name,roi,offsets in regions:
        gap=(roi&skin&(authored[:,:,3]<250)&(hand<16)).astype(np.uint8)*255
        overlap=cv2.dilate(gap,np.ones((7,7),np.uint8))>0
        wanted=overlap&roi&(body[:,:,3]>0)&(hand<16)
        alpha=np.where(wanted,body[:,:,3],0).astype(np.uint8);remaining=wanted.copy();used=[]
        for dx,dy in offsets:
            copy=Image.new('RGBA',(941,1672));copy.alpha_composite(sleeves,(dx,dy));donor=np.array(copy)
            take=remaining&(donor[:,:,3]>240)
            result[take,:3]=donor[take,:3];result[take,3]=np.maximum(result[take,3],alpha[take]);remaining[take]=False
            used.append({'translation':[dx,dy],'pixels':int(take.sum())})
        notes.append({'region':name,'uncoveredSkinPixels':int((gap>0).sum()),'remainingPixels':int((remaining&(gap>0)).sum()),'donors':used})
    return Image.fromarray(result,'RGBA'),notes

metadata={'method':'Recovered artist sleeve RGB + traced alpha; retained exact pre-outage whole-image similarities, no new fitting. No arm deformation or cloth texture transfer. Original canonical torso fixed. Candidate-only output.','recoveredFromHistory':True,'poses':{}}
for pose in ['idle','melee','rifle']:
    source=ART/f'male-{pose}-artist-raw.png';raw=np.array(Image.open(source).convert('RGBA'))
    matrix=np.array(MATRICES[pose],np.float64);sleeves=Image.new('RGBA',(941,1672))
    for side,polygons in POLYGONS[pose].items():
        mask=matte((raw.shape[1],raw.shape[0]),polygons)
        if pose!='rifle':
            mask=np.array(mask,copy=True)
            for y in range(520,801):
                occupied=raw[y,:,3]>16;delta=np.diff(np.r_[False,occupied,False].astype(int))
                spans=[(int(a),int(b)) for a,b in zip(np.where(delta==1)[0],np.where(delta==-1)[0]) if b-a>8]
                if side=='left' and len(spans)>=2 and spans[0][1]<320:
                    a,b=spans[0];mask[y,max(0,a-2):b+2]=255
                if side=='right' and len(spans)>=3 and spans[-1][0]>570:
                    a,b=spans[-1];mask[y,max(0,a-2):b+2]=255
        yy,xx=np.mgrid[:raw.shape[0],:raw.shape[1]]
        skin=raw[:,:,0].astype(int)-raw[:,:,2].astype(int)>28
        roi=(((xx>310)&(xx<405)&(yy>520)&(yy<625))|((xx>630)&(xx<720)&(yy>580)&(yy<700))) if pose=='rifle' else ((yy>770)&(yy<990))
        mask=np.array(mask,copy=True);mask[skin&roi]=0
        alpha=(raw[:,:,3].astype(np.uint16)*mask.astype(np.uint16)//255).astype(np.uint8)
        part=raw.copy();part[:,:,3]=alpha;part[alpha==0,:3]=0
        Image.fromarray(alpha).save(ART/'source-masks'/f'{pose}-{side}.png')
        layer=registered(part,matrix);layer.save(OUT/f'male-{pose}-sleeve-{side}.png',optimize=True);sleeves.alpha_composite(layer)
    torso_path=ORIGINAL/'overlap-layers'/f'{pose}-torso.png';torso=Image.open(torso_path).convert('RGBA')
    first=torso.copy();first.alpha_composite(sleeves)
    original=Image.open(REF/f'male-{pose}.png').convert('RGBA')
    underlay,notes=coverage_underlay(sleeves,first,original,pose)
    underlay.save(OUT/f'male-{pose}-underlay.png',optimize=True)
    top=underlay.copy();top.alpha_composite(torso);top.alpha_composite(sleeves)
    top.save(OUT/f'male-{pose}.png',optimize=True);sleeves.save(OUT/f'male-{pose}-sleeves.png',optimize=True)
    metadata['poses'][pose]={'matrix':matrix.tolist(),'inliers':QA[pose][0],'medianResidualPx':QA[pose][1],
     'source':str(source.relative_to(ROOT)),'sourceSha256':sha(source),
     'canonicalTorso':str(torso_path.relative_to(ROOT)),'canonicalTorsoSha256':sha(torso_path),
     'candidate':str((OUT/f'male-{pose}.png').relative_to(ROOT)),'candidateSha256':sha(OUT/f'male-{pose}.png'),
     'sourcePolygons':POLYGONS[pose],'underlay':notes}
    print(pose,metadata['poses'][pose]['candidateSha256'],notes,flush=True)
(OUT/'male-artist-extraction.json').write_text(json.dumps(metadata,indent=2)+'\n')
