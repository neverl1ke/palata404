"""Decode/verify every native RGBA frame; optional PNG export for independent audit."""
import argparse,hashlib,json,struct,zlib
from pathlib import Path
import numpy as np
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('packs',nargs='+',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();total=0
for path in a.packs:
 data=path.read_bytes();assert data[:7]==b'P404F1\n';n=struct.unpack('<I',data[7:11])[0];h=json.loads(data[11:11+n]);w,hh=h['size'];rgba=np.zeros((hh,w,4),dtype='uint8');first=None;times=[]
 assert len(h['frames'])==241
 for i,entry in enumerate(h['frames']):
  start=11+n+entry['offset'];delta=zlib.decompress(data[start:start+entry['bytes']]);assert len(delta)==hh*w*4;rgba=np.bitwise_xor(rgba,np.frombuffer(delta,'uint8').reshape(hh,w,4));assert hashlib.sha256(rgba.tobytes()).hexdigest()==entry['rgba_sha256'],(path,i);assert abs(entry['time_ms']-i*4000/240)<1e-8
  if i==0:first=rgba.copy()
  if a.output:
   dest=a.output/path.stem;dest.mkdir(exist_ok=True,parents=True);Image.fromarray(rgba).save(dest/f'frame-{i:04d}.png')
  times.append(entry['time_ms'])
 assert np.array_equal(first,rgba),(path,'cycle closure');print(path.name,len(times),'frames; exact RGBA; 0..4000ms inclusive');total+=len(times)
 if a.output:(a.output/path.stem/'times.json').write_text(json.dumps(times,indent=2))
print('Verified',total,'native lossless samples')
