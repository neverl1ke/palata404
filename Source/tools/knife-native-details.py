"""Native-pixel wrist/elbow snapshots from exact dense frame packs, not generated art."""
from pathlib import Path
from PIL import Image,ImageDraw
import struct,zlib,json,hashlib,numpy as np
R=Path(__file__).resolve().parents[1];G=R/'review/avatar-foundation-cleanup/Gallery';wanted=[0,30,60,120,180,240]
for gender in ['male','female']:
 crops={};box=(145,770,335,1045) if gender=='male' else (145,750,325,1020)
 for version in ['before','after']:
  path=G/f'Dense/{version}-{gender}-melee-True.avframes';data=path.read_bytes();n=struct.unpack('<I',data[7:11])[0];h=json.loads(data[11:11+n]);rgba=np.zeros((1672,941,4),dtype='uint8')
  for i,row in enumerate(h['frames']):
   at=11+n+row['offset'];rgba^=np.frombuffer(zlib.decompress(data[at:at+row['bytes']]),dtype='uint8').reshape(1672,941,4)
   if i in wanted:
    assert hashlib.sha256(rgba.tobytes()).hexdigest()==row['rgba_sha256'];im=Image.fromarray(rgba).crop(box);bg=Image.new('RGBA',im.size,'#f8f5ed');bg.alpha_composite(im);crops[version,i]=bg.convert('RGB')
 w,h=crops['before',0].size;sheet=Image.new('RGB',(w*len(wanted),2*(h+28)),'#eee9df');d=ImageDraw.Draw(sheet)
 for row,version in enumerate(['before','after']):
  for col,i in enumerate(wanted):sheet.paste(crops[version,i],(col*w,row*(h+28)+28));d.text((col*w+4,row*(h+28)+5),f'{version} {i*4000/240:.0f}ms',fill='black')
 sheet.save(G/f'{gender}-knife-native-phases.webp',lossless=True,method=0);print(gender,'6 native phases before/after',flush=True)
