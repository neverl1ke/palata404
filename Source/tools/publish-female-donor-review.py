"""Publish only the verified review artifact tag; never push main or source branch."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[1];D=ROOT.parent/'Avatar-Female-Donor-Review';O=ROOT/'review/female-donor-arm-pass';REPO='neverl1ke/palata404'
def run(a,**kw):return subprocess.check_output(a,cwd=ROOT,text=True,**kw).strip()
pkg=json.loads((O/'package.json').read_text());proof=json.loads((O/'offline-package-check.json').read_text());source=pkg['source_commit'];tag='female-donor-'+source[:7]
assert proof['zip_sha256']==pkg['sha256'];assert len(proof['poses'])==16 and not proof['js_errors'] and not proof['network_requests']
main=run(['gh','api',f'repos/{REPO}/commits/main','--jq','.sha']);assert main=='f70b7e5be63f6b85d895c6d5b259adbc30577b86'
assert not run(['git','tag','-l',tag]),'Never overwrite a review tag';assert max(p.stat().st_size for p in D.rglob('*') if p.is_file())<100*1024*1024
with tempfile.TemporaryDirectory() as td:
 env=os.environ.copy();env['GIT_INDEX_FILE']=str(Path(td)/'review-index');run(['git','read-tree','--empty'],env=env)
 for p in sorted(D.rglob('*')):
  if p.is_file():
   name=str(p.relative_to(D));assert not name.startswith('.github/');oid=run(['git','hash-object','-w','--',str(p)]);run(['git','update-index','--add','--cacheinfo','100644',oid,name],env=env)
 tree=run(['git','write-tree'],env=env);commit=run(['git','commit-tree',tree,'-m','Female donor arm review: partial art, known pre-existing base PNG audit failure'])
run(['git','tag',tag,commit]);subprocess.run(['git','push','origin','refs/tags/'+tag],cwd=ROOT,check=True)
url=f'https://github.com/{REPO}/archive/refs/tags/{tag}.zip';notes=ROOT.parent/'independent-review-notes.md';notes.write_text('Жіночі руки з наданих референсів інтегровано тільки в Lab: idle, ніж, одноручний пістолет, автомат. Локальні чоловічі rifle-контури, цілісні жіночі wrist-поверхні, дихання4000мс.\n\nЦе версія для візуального приймання, не production-ready. Чоловічі pistol/melee та локальна фактура ще мають художні обмеження. Повний регресійний прогін містить відому попередню невдачу PNG-аудиту base_male.png:4234пікселі; оригінал і поріг не змінено.\n\nZIP: '+url+'\n\nРозпакуйте весь архів та відкрийте Report.html або Avatar-Lab.html. Є реальні рендери,1360кадрів контрольної матриці та20WebM відео. Main, гра, вихідні бази, інвентар і збереження не змінені.\n')
subprocess.run(['gh','release','create',tag,'--repo',REPO,'--verify-tag','--prerelease','--latest=false','--title','Avatar Core — жіночі донорські руки та огляд хватів','--notes-file',str(notes)],cwd=ROOT,check=True)
download=ROOT.parent/'Avatar-Female-Donor-Review-github-verified.zip';subprocess.run(['curl','--fail','--location','--retry','2','--silent','--show-error','--output',str(download),url],check=True)
expected={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file()}
with zipfile.ZipFile(download) as z:
 assert z.testzip() is None;actual={n.split('/',1)[1]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')};assert expected==actual
assert run(['gh','api',f'repos/{REPO}/commits/main','--jq','.sha'])==main
result={'download_url':url,'release_url':f'https://github.com/{REPO}/releases/tag/{tag}','artifact_commit':commit,'source_commit':source,'main_unchanged':main,'downloaded_files_verified':len(actual),'zip_bytes':download.stat().st_size,'zip_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'production_ready':False,'female_integrated_in_lab':True,'female_integrated_in_game':False};(O/'https-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
