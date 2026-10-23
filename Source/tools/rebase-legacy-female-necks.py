"""Keep approved faces above y=221; rebase only their neck joins onto new bodies.
Requires original young/remaining face uploads and SciPy. No generation.
"""
import argparse,importlib.util,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--young-dir',type=Path,required=True);p.add_argument('--remaining-dir',type=Path,required=True);p.add_argument('--approved-ref',default='41bf1d15d92d09cec4fae9ecbe39fde028a78c3d');a=p.parse_args()
spec=importlib.util.spec_from_file_location('neck_repair',ROOT/'tools/repair-face-necks.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
f=ROOT/'tests/fixtures/face-neck-transitions.json';manifest=json.loads(f.read_text());data=ROOT/'paper-doll-data.js';catalog=data.read_text()
for e in manifest['files']:
 if e['gender']!='female':continue
 kind=e['kind'];approved=subprocess.check_output(['git','show',f"{a.approved_ref}:{e['output']}"],cwd=ROOT)
 source=a.young_dir/'female_young_head_full_canvas.png' if kind=='young' else a.remaining_dir/f'{kind}_female_head_neck.png'
 e.update(m.repair(kind,'female',approved,source.read_bytes()));e['neck_rebase_reference_commit']=a.approved_ref
 for k,h in [('output','sha256'),('mask','mask_sha256')]:catalog=re.sub(re.escape(e[k])+r'\?v=[a-z0-9]+',e[k]+'?v='+e[h][:8],catalog)
f.write_text(json.dumps(manifest,indent=2)+'\n');data.write_text(catalog)
