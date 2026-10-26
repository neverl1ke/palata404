"""Clean dependency-scoped restore from actual52bfbca, not a full project test."""
from pathlib import Path
import subprocess,io,tarfile,json,hashlib,shutil,zipfile
R=Path(__file__).resolve().parents[1];D=R/'review/rifle-seams';T=R.parent/'rifle-seams-clean-restore';BASE='52bfbcaa2e72b9ec675b7f5da868e77aa90f4873'
assert not T.exists();T.mkdir()
paths=['avatar-core','avatar-lab','tools','tests','review/rifle-seams/Sources',':(exclude)*.png']
patch=subprocess.check_output(['git','diff','--cached',BASE,'--',*paths],cwd=R)
changed=subprocess.check_output(['git','diff','--cached','--name-only',BASE,'--',*paths],cwd=R,text=True).splitlines();tree=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=R,text=True).splitlines())
dependencies=['base_male.png','base_female.png','avatar-core/rigs/male_rig.json','avatar-core/rigs/female_rig.json','avatar-core/male-preview.json','avatar-core/female-preview.json','avatar-core/equipment-weapons.json','avatar-core/assets/male/rifle-arm-integrity/torso.png','avatar-core/assets/female/rifle-arm-integrity/torso.png','avatar-core/assets/weapons/user-ak47-20261026/ak47-master.png','tools/prepare-knife-perspective.py','review/rifle-arm-integrity/Sources']
selected=sorted(set([p for p in changed if p in tree]+dependencies));archive=subprocess.check_output(['git','archive',BASE,*selected],cwd=R)
with tarfile.open(fileobj=io.BytesIO(archive)) as tf:tf.extractall(T,filter='data')
baseline_zip=D/'Export-Base.zip'
with zipfile.ZipFile(baseline_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for file in sorted(T.rglob('*')):
  if file.is_file():z.write(file,str(file.relative_to(T)))
(T/'code.patch').write_bytes(patch);subprocess.run(['git','apply','--check','code.patch'],cwd=T,check=True);subprocess.run(['git','apply','code.patch'],cwd=T,check=True)
(T/'review/rifle-seams/Evidence').mkdir(parents=True,exist_ok=True)
for script in ['prepare-rifle-seams.py','prepare-ak47-opacity.py']:subprocess.run(['python','tools/'+script],cwd=T,check=True,capture_output=True)
outputs=[p for g in ['male','female'] for p in (R/f'avatar-core/assets/{g}/rifle-seams').glob('*.png')]+[R/'avatar-core/assets/weapons/user-ak47-20261026/ak47-runtime-opaque.png']+[R/f'avatar-core/{g}-preview.json' for g in ['male','female']]+[R/'avatar-core/equipment-weapons.json'];checks=[]
for p in outputs:
 q=T/p.relative_to(R);actual=hashlib.sha256(q.read_bytes()).hexdigest();expected=hashlib.sha256(p.read_bytes()).hexdigest();assert actual==expected,p;checks.append({'file':str(p.relative_to(R)),'sha256':actual,'restored_exact':True})
(D/'Evidence/clean-restore.json').write_text(json.dumps({'baseline':BASE,'directory':str(T),'selected_base_paths':selected,'baseline_export_snapshot':'Source/Export-Base.zip','baseline_export_snapshot_sha256':hashlib.sha256(baseline_zip.read_bytes()).hexdigest(),'patch_name':'Source/code.patch','exported_files':checks,'all_exported_bytes_exact':True,'scope':'clean dependency-scoped base extraction, NOT complete checkout or full historical suite','temporary_copy_removed_after_verification':True},indent=2)+'\n');shutil.rmtree(T);print('Clean baseline dependency restore: all',len(checks),'exported files exact')
