"""Local reviewed payload; do not publish. Final verification is a sidecar."""
from pathlib import Path
import json,hashlib,subprocess,zipfile,re
R=Path(__file__).resolve().parents[1];D=R/'review/rifle-seams';Z=R.parent/'Palata404-Rifle-Seams-Technical-PARTIAL-20261026.zip';OUT=R.parent/'rifle-seams-final-unpacked';BASE='52bfbcaa2e72b9ec675b7f5da868e77aa90f4873'
assert not Z.exists() and not OUT.exists(),'Preserve previous delivery'
files={n:D/n for n in ['README.md','Report.html','Review.pdf','Avatar-Lab.html']}
files['Source/Export-Base.zip']=D/'Export-Base.zip'
for folder in ['Sources','Art-Handoff','Evidence']:
 for p in (D/folder).rglob('*'):
  if p.is_file():files[str(p.relative_to(D))]=p
for path in re.findall(r'<img[^>]+src="([^"]+)"',(D/'Report.html').read_text()):files[path]=D/path
for pattern in ['native-phases-*.webp','phase-inspection-*.webp','before-*-isolate-*.webp','after-*-isolate-*.webp','PDF-contact-sheet.png','*body-view.png','diagnostic-*-root-before.png']:
 for p in (D/'Gallery').glob(pattern):files['Gallery/'+p.name]=p
for p in [R/'avatar-core/engine.mjs',R/'avatar-core/male-preview.json',R/'avatar-core/female-preview.json',R/'avatar-core/equipment-weapons.json']:
 files['Runtime/'+str(p.relative_to(R))]=p
for g in ['male','female']:
 for p in (R/f'avatar-core/assets/{g}/rifle-seams').glob('*.png'):files['Runtime/'+str(p.relative_to(R))]=p
 p=R/f'avatar-core/assets/{g}/rifle-arm-integrity/torso.png';files['Runtime/'+str(p.relative_to(R))]=p
for n in ['ak47-master.png','ak47-runtime-opaque.png']:
 p=R/'avatar-core/assets/weapons/user-ak47-20261026'/n;files['Runtime/'+str(p.relative_to(R))]=p
for p in (R/'tools').glob('*rifle-seams*.py'):files['Source/tools/'+p.name]=p
for n in ['prepare-ak47-opacity.py','prepare-knife-perspective.py','prepare-foundation-cleanup.py','bundle-avatar-lab.py']:
 files['Source/tools/'+n]=R/'tools'/n
files['Source/tests/test_rifle_seams.py']=R/'tests/test_rifle_seams.py'
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
extra={'Source/code.patch':subprocess.check_output(['git','diff',BASE+'..HEAD','--','avatar-core','avatar-lab','tools','tests','review/rifle-seams/Sources',':(exclude)*.png'],cwd=R)}
extra['Source/revision.json']=json.dumps({'base_commit':BASE,'source_commit':head,'branch':'feature/rifle-seams-52bfbca','status':'TECHNICAL CANDIDATE; R03/R04/R09 OPEN','published':False,'main_changed':False,'live_deployed':False},indent=2).encode()
extra['Source/RESTORE.txt']=(D/'README.md').read_bytes()
manifest={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()};manifest.update({n:hashlib.sha256(data).hexdigest() for n,data in extra.items()});extra['SHA256SUMS.json']=json.dumps(manifest,indent=2).encode()
print('Payload bytes',sum(p.stat().st_size for p in files.values())+sum(len(x) for x in extra.values()),flush=True)
with zipfile.ZipFile(Z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,p in files.items():z.write(p,n)
 for n,data in extra.items():z.writestr(n,data)
with zipfile.ZipFile(Z) as z:
 assert z.testzip() is None
 for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h,n
 # Remove only generated duplicate deliverable files after exact archive check.
 for n,p in files.items():
  if n.startswith('Gallery/') or n in ['Avatar-Lab.html','Review.pdf']:p.unlink(missing_ok=True)
 z.extractall(OUT)
for n,h in manifest.items():assert hashlib.sha256((OUT/n).read_bytes()).hexdigest()==h,n
record={'zip':str(Z),'zip_SHA256':hashlib.sha256(Z.read_bytes()).hexdigest(),'bytes':Z.stat().st_size,'payload_files':len(manifest),'unpacked_directory':str(OUT),'all_manifest_and_CRC_exact':True,'source_commit':head,'not_yet_browser_verified':'Run verify-rifle-seams-offline.py against this exact directory and ZIP; output external final receipt','published':False}
(R.parent/'Rifle-Seams-Archive-Integrity.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
