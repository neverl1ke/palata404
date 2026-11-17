#!/usr/bin/env python3
"""Compose the fine weapon-paper material with unmodified source hardware.

No raster source is modified or resampled. Each SVG keeps its source viewBox,
replaces only explicitly listed paper faces, and uses uniform slice for material.
The player's original stat chart is intentionally excluded. Wardrobe-header
printed linework is isolated by luminosity, not regenerated. Its light paper
highlights adopt the new material, a deliberate limit recorded in manifest.
"""
from pathlib import Path
import base64
import hashlib
import json
import io
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/ui/documents/composed'

def uri(path):
    p=ROOT/path
    mime={'.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml'}[p.suffix]
    raw=p.read_bytes()
    if p.suffix=='.png':
        # Encoding only: keep source files and decoded native pixels unchanged.
        # Embedding an uncompressed large PNG in every SVG wastes megabytes.
        with Image.open(io.BytesIO(raw)) as original:
            image=original.convert('RGBA');encoded=io.BytesIO()
            image.save(encoded,format='WEBP',lossless=True,method=6,exact=True,icc_profile=original.info.get('icc_profile',b''))
            candidate=encoded.getvalue()
            with Image.open(io.BytesIO(candidate)) as restored:
                if restored.convert('RGBA').tobytes()!=image.tobytes():
                    raise ValueError('Lossless encoding changed source pixels: '+str(p))
            if len(candidate)<len(raw):raw=candidate;mime='image/webp'
    return 'data:'+mime+';base64,'+base64.b64encode(raw).decode()

CONFIG={
 'raid-frame':dict(source='assets/ui/raid/hud-frame.png',size=(1670,942),paper='<path fill-rule="evenodd" d="M50 697H376L391 716V868L370 897H51L40 874V716Z M302 727H396V845H302Z"/><path d="M1263 148L1407 135L1421 208L1273 221Z"/><path d="M1420 144H1638V198H1420Z"/><path d="M452 793H821Q835 793 835 809V889Q835 904 821 904H451Q441 904 441 891V811Z"/><path d="M882 793H1196Q1210 793 1210 810V890Q1210 903 1196 903H882Q869 903 869 890V809Z"/><ellipse cx="1464" cy="78" rx="58" ry="35"/>',protect='<path d="M303 728L373 719L383 705L396 701L406 709L402 733L400 842L311 850Z"/><path d="M448 810L487 768L502 780L464 824Z"/><path d="M874 810L913 768L928 780L890 824Z"/>'),
 'weapon-board':dict(source='assets/ui/wardrobe/clipboard-v2/board-original.png',size=(1054,1492),paper='<path d="M63 99H994L1014 132V1385L984 1431H76L44 1381V139Z"/>'),
 'weapon-slip':dict(source='assets/ui/wardrobe/clipboard-v2/slip-matched.webp',size=(1816,866),paper='<path d="M64 94H1751L1773 131V734L1729 790H87L48 743V135Z"/>',protect='<path d="M244 69H351V110H244Z"/><path d="M1440 72H1559V110H1440Z"/>'),
 'wardrobe-header':dict(source='assets/ui/wardrobe/paper-header-only.svg',size=(2090,443),paper='<path d="M29 40H2036L2072 78V377L2031 414H42L15 381V79Z"/>',ink=True),
 'map-hardware':dict(source='assets/quest-scenes/clipboard.webp',size=(1536,1024),paper='<path d="M64 79Q69 71 99 72H1424Q1461 73 1470 111L1488 152V912Q1481 970 1436 982H94Q40 974 35 930V151Q35 103 64 79Z"/>',material=False,protect='<path d="M510 151Q506 130 516 116L521 106Q521 74 541 56Q553 42 586 43H706Q709 11 724 0H808Q825 16 828 43H955Q986 44 1002 67Q1011 84 1013 110Q1028 126 1027 147Q1027 165 1012 170H524Q508 166 510 151Z"/>'),
}

# Rarity frames are distinct hardware; their inner paper is rendered separately
# in CSS so responsive cards never stretch the material with the metal border.
for rarity in ('common','improved','rare','experimental'):
    source=f'assets/ui/wardrobe/rarity-cards/{rarity}-blank.png'
    from PIL import Image
    with Image.open(ROOT/source) as im:w,h=im.size
    CONFIG[f'rarity-{rarity}-hardware']=dict(source=source,size=(w,h),paper=f'<rect x="65" y="50" width="{w-130}" height="{h-100}" rx="6"/>',material=False)

def build(name, c):
    w,h=c['size'];old=uri(c['source']);paper=c['paper'];protect=c.get('protect','')
    material=c.get('material',True)
    fine=uri('assets/ui/documents/weapon-paper-fine-portrait.webp' if h>w else 'assets/ui/documents/weapon-paper-fine-landscape.webp')
    # Hardware is the exact original outside the paper mask; protect explicitly
    # keeps metal, photo cut-outs, and leather plaques.
    defs=f'<filter id="soft" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="7"/></filter><mask id="paper-soft"><g fill="white" filter="url(#soft)">{paper}</g></mask><image id="original" href="{old}" width="{w}" height="{h}"/><clipPath id="paper">{paper}</clipPath><clipPath id="protected">{protect}</clipPath><mask id="hardware"><rect width="100%" height="100%" fill="white"/><g fill="black" filter="url(#soft)">{paper}</g><g fill="white">{protect}</g></mask>'
    ink='<filter id="ink" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  -1.45 -1.45 -1.45 0 3.55"/></filter>'
    layers='<use href="#original"/>' if material else '<use href="#original" mask="url(#hardware)"/>'
    if material:
        layers+=f'<g mask="url(#paper-soft)"><image href="{fine}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/>'
        if c.get('ink'):layers+='<use href="#original" filter="url(#ink)"/>'
        layers+='</g>'
        if protect:layers+='<use href="#original" clip-path="url(#protected)"/>'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="{"xMidYMid meet" if material else "none"}"><defs>{defs}{ink}</defs>{layers}</svg>\n'
    path=OUT/(name+'.svg');path.write_text(svg)
    return {'source':c['source'],'source_sha256':hashlib.sha256((ROOT/c['source']).read_bytes()).hexdigest(),'size':[w,h],'paper':paper,'protected':protect,'printed_ink_isolated':bool(c.get('ink')),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    files={name+'.svg':build(name,c) for name,c in CONFIG.items()}
    # This mask changes geometry only. Material behind it remains a uniform CSS
    # cover image; resizing a map never stretches its fine paper texture.
    (OUT/'map-paper-mask.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1536 1024" preserveAspectRatio="none"><g fill="white">'+CONFIG['map-hardware']['paper']+'</g></svg>\n')
    (OUT/'manifest.json').write_text(json.dumps({'version':1,'material':'../weapon-paper-fine-landscape.webp','scope':'Paper interiors only; source originals unchanged. Source-aligned masks keep hardware. The original player stat chart is excluded. Other printed shaded highlights adopt the new paper tone through luminance isolation, not pixel-identical preservation.','files':files},ensure_ascii=False,indent=2)+'\n')
    print('Composed',len(files),'paper surface SVGs; original assets preserved.')
if __name__=='__main__':main()
