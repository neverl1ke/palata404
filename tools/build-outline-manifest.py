"""Select actual garment/hair resources. Never include heads, masks or palettes."""
from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
s=''.join(p.read_text()for p in [R/'paper-doll-data.js',*R.glob('*hair*data.js')])
paths=set(re.findall(r'[\"\x27]((?:assets/wardrobe/(?:hair|clothing)/)[^\"\x27?]+)',s))
paths.update(str(p.relative_to(R))for p in (R/'assets/wardrobe/clothing/patient/pajamas').glob('*/*.png'))
items={}
for rel in sorted(paths):
 p=R/rel
 if p.is_file()and p.suffix in ['.png','.webp']and not any(x in rel.lower()for x in ['mask','neckline','head.png','/palette/','/thumbnails/','thumb-','foreground-','keep-pants']):items[rel]=True
(R/'outline-manifest.js').write_text('window.PalataOutlineManifest='+json.dumps(items,separators=(',',':'))+';\n')
(R/'review/outline-release-20261114/sources.json').write_text(json.dumps({rel:hashlib.sha256((R/rel).read_bytes()).hexdigest()for rel in items},indent=2))
print(len(items),'unchanged source files selected')
