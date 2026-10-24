"""Create missing historical snapshots and verify every runtime byte against Git."""
from pathlib import Path
import subprocess,hashlib,tarfile,io,json
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-selective-merge/Evidence';rows=[]
for ref in ['184e392','766a71e','5532a93']:
 root=R.parent/('avatar-selective-'+ref);names=subprocess.check_output(['git','ls-tree','--name-only',ref],cwd=R,text=True).splitlines();names=[n for n in names if n in ['avatar-core','avatar-lab','assets'] or '.' in n and not n.startswith('.')]
 if not (root/'avatar-lab/index.html').exists():
  root.mkdir(exist_ok=True);data=subprocess.check_output(['git','archive',ref,'--',*names],cwd=R);tarfile.open(fileobj=io.BytesIO(data)).extractall(root,filter='data')
 files=[]
 for entry in subprocess.check_output(['git','ls-tree','-r','-z',ref,'--',*names],cwd=R).split(b'\0'):
  if not entry:continue
  info,path=entry.split(b'\t',1);expected=info.split()[-1].decode();name=path.decode();data=(root/name).read_bytes();actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert actual==expected,(ref,name,'snapshot modified');files.append({'path':name,'git_blob':expected,'sha256':hashlib.sha256(data).hexdigest()})
 rows.append({'ref':ref,'commit':subprocess.check_output(['git','rev-parse',ref],cwd=R,text=True).strip(),'root':str(root),'files':files});print(ref,len(files),'files exact')
D.mkdir(parents=True,exist_ok=True);(D/'snapshot-provenance.json').write_text(json.dumps(rows,indent=2)+'\n')
