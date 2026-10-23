"""Package a local review; never push, merge or publish."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
R=Path(__file__).resolve().parents[1];D=R/'review/avatar-requested-corrections';OUT=R.parent/'Palata404-Avatar-Requested-Corrections.zip';files={}
for p in D.rglob('*'):
 if p.is_file() and p.name!='.gitignore':files[str(p.relative_to(D))]=p
for p in R.iterdir():
 if p.is_file() and p.suffix in {'.js','.mjs','.css','.html','.png','.json','.svg','.ico','.jpg','.jpeg','.webp','.gif','.woff','.woff2'}:files['Game/'+p.name]=p
for folder in ['assets','avatar-core','avatar-lab']:
 for p in (R/folder).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:files['Game/'+str(p.relative_to(R))]=p
for p in (R/'review/avatar-foundation-cleanup/Gallery').glob('before-*-True.png'):files['Game/'+str(p.relative_to(R))]=p
for folder in ['tools','tests','docs']:
 for name in subprocess.check_output(['git','ls-files','--',folder],cwd=R,text=True).splitlines():
  p=R/name
  if p.is_file():files['Source/'+name]=p
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
extras={'START-HERE.txt':'''ПАЛАТА 404 — ЛОКАЛЬНИЙ ЧАСТКОВИЙ REVIEW

1. Розпакуйте ZIP повністю.
2. Review.pdf — статичні порівняння без налаштувань браузера.
3. Report.html — повна галерея з анімаціями, відкривається у браузері.
4. Avatar-Lab.html — автономна примірка, відкривається у браузері.
5. Для справжньої гри запустіть python start-preview.py; потрібен Python 3.
   Гра: http://127.0.0.1:8044/Game/index.html?avatarCore=1
   Доступні тільки предмети, які вже є в інвентарі. Lab дозволяє переглянути всі.

УВАГА: 6 FIXED, 12 PARTIAL, 4 OPEN. Повні рукоятки зброї в джерелах відсутні.
Це не production-ready. Main і опублікована гра не змінені.
121/121 JS; 291/295 Python повного snapshot; окремо 8/8 фінальних цільових.
Повний набір історичних fixtures не включений; Source — матеріали для репозиторію.
'''.encode(),'start-preview.py':b"from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler\nfrom pathlib import Path\nimport os, webbrowser\nos.chdir(Path(__file__).resolve().parent)\nserver=ThreadingHTTPServer(('127.0.0.1',8044),SimpleHTTPRequestHandler)\nprint('http://127.0.0.1:8044/Game/index.html?avatarCore=1')\nwebbrowser.open('http://127.0.0.1:8044/Game/index.html?avatarCore=1')\nserver.serve_forever()\n",'Source/changes.patch':subprocess.check_output(['git','diff','--binary','37a73f7..HEAD'],cwd=R),'Source/revision.json':json.dumps({'source_commit':head,'base':'37a73f75a88288b8327c26ae6b517d77ce3ce580','branch':'feature/avatar-core-2-weapon-transitions','published':False},indent=2).encode()}
manifest={}
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,p in sorted(files.items()):
  data=p.read_bytes();z.writestr(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
 for name,data in extras.items():z.writestr(name,data);manifest[name]=hashlib.sha256(data).hexdigest()
 z.writestr('SHA256SUMS.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(OUT) as z:
 assert z.testzip() is None
 for name,h in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
print(json.dumps({'zip':str(OUT),'bytes':OUT.stat().st_size,'entries':len(manifest)+1,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'all_entry_hashes_verified':True,'source_commit':head},indent=2))
