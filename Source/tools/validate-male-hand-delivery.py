"""Technical validation of returned hand layers; never approves anatomy or integrates art."""
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image

def validate(kit,delivery):
 contract=json.loads((kit/'hand-contract.json').read_text());errors=[];warnings=[];rows=[]
 for case in contract['cases']:
  allowed=np.array(Image.open(kit/'Hands'/case['id']/'edit-region.png'))>0
  for part,path in zip(['back','front','thumb'],case['candidate_paths']):
   p=delivery/path;entry={'hand':case['id'],'part':part,'path':path};rows.append(entry)
   if not p.is_file():errors.append(path+': missing');continue
   try:
    im=Image.open(p);im.load()
    if im.size!=(941,1672) or im.mode!='RGBA' or im.format!='PNG':errors.append(path+': expected full941x1672 RGBA PNG');continue
    a=np.array(im);visible=a[:,:,3]>0;entry['visible_pixels']=int(visible.sum())
    if part!='thumb' and not visible.any():errors.append(path+': empty placeholder; no new hand art')
    if (visible&~allowed).any():errors.append(path+': alpha outside approved edit region, including alpha1')
    if np.any(a[:,:,:3][~visible]):warnings.append(path+': nonzero hidden RGB; clean before integration')
   except (ValueError,OSError) as e:errors.append(path+': '+str(e))
 return {'technical_valid':not errors,'artistic_approval':False,'integration_allowed':False,'reason':'technical geometry/alpha checks only; anatomy and layer contact require visual approval','layers':rows,'errors':errors,'warnings':warnings}
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--kit',type=Path,default=Path(__file__).resolve().parents[1]/'review/male-hand-art-kit');parser.add_argument('--delivery',type=Path);args=parser.parse_args();result=validate(args.kit,args.delivery or args.kit);print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['technical_valid'] else 2)
