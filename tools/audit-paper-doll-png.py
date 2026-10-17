"""RGBA quality diagnostics. Reports evidence, not a blanket pass/fail for artwork.
CLI: python tools/audit-paper-doll-png.py --output report.json [PNG ...]
Uses alpha=1 as well as strong-core thresholds. Hair strands/holes are not errors.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT=Path(__file__).resolve().parents[1]
def catalog():
 code="const fs=require('fs'),vm=require('vm');process.stdout.write(vm.runInNewContext(fs.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify({bodies:PAPER_DOLL_BODIES,items:PAPER_DOLL_ITEMS})'))"
 return json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT))
def resources():
 return sorted(set(re.findall(r'[A-Za-z0-9_./-]+\.png',json.dumps(catalog()))))
def bbox(mask):
 yy,xx=np.where(mask);return [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)] if len(xx) else None
def analyze(path):
 a=np.array(Image.open(path).convert('RGBA'));alpha=a[:,:,3];strong=alpha>=32;dist=ndi.distance_transform_edt(~strong);weak=(alpha>0)&(alpha<=16)
 labels,n=ndi.label(alpha>0,np.ones((3,3)));counts=np.bincount(labels.ravel());largest=counts[1:].argmax()+1 if n else 0
 detached=(labels!=largest)&(labels>0);remote=weak&(dist>4)
 core=alpha>=240;inside=ndi.distance_transform_edt(core);_,idx=ndi.distance_transform_edt(~core,return_indices=True)
 edge=(alpha>0)&(alpha<240)&(dist<=4);delta=np.mean(a[:,:,:3].astype(float)-a[idx[0],idx[1],:3].astype(float),axis=2)
 opaque=alpha>=128;opened=ndi.binary_opening(opaque,structure=ndi.generate_binary_structure(2,1));spurs=opaque&(~opened)
 return dict(path=str(path.relative_to(ROOT)),size=[a.shape[1],a.shape[0]],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),alpha_histogram=np.bincount(alpha.ravel(),minlength=256).tolist(),bounds={str(t):bbox(alpha>=t) for t in [1,8,16,32,128,240]},nonzero_components=int(n),detached_pixels=int(detached.sum()),detached_max_alpha=int(alpha[detached].max()) if detached.any() else 0,weak_remote_pixels=int(remote.sum()),weak_remote_bounds=bbox(remote),edge_dark_candidates=int((edge&(delta<-35)).sum()),edge_light_candidates=int((edge&(delta>35)).sum()),single_pixel_spur_candidates=int(spurs.sum()),notes='Candidates require visual review; natural hair strands, anatomical gaps and mask transitions are not automatic failures.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('paths',nargs='*');p.add_argument('--output',type=Path,required=True);a=p.parse_args();items=[ROOT/x for x in (a.paths or resources())];result={'thresholds':[1,8,16,32,128,240],'files':[analyze(x) for x in items]};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
 for e in result['files']:print(e['path'],e['size'],'weak far',e['weak_remote_pixels'],'detached',e['detached_pixels'],'dark/light',e['edge_dark_candidates'],e['edge_light_candidates'])
