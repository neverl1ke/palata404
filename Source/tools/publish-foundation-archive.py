"""Fallback for hosts that reject uploads.github.com credentials: a new artifact-only tag."""
from pathlib import Path
import subprocess,json,hashlib,tempfile,os,zipfile
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';D=R.parent/'Avatar-Foundation-Cleanup';repo='neverl1ke/palata404';pkg=json.loads((O/'package.json').read_text());proof=json.loads((O/'offline-package-check.json').read_text());assert proof['zip_sha256']==pkg['sha256'];assert len(proof['poses'])==16 and not proof['js_errors'] and not proof['network_requests']
def run(a,**kw):return subprocess.check_output(a,cwd=R,text=True,**kw).strip()
source=pkg['source_commit'];tag='avatar-foundation-verified-'+source[:7];assert not run(['git','tag','-l',tag]);main=run(['gh','api',f'repos/{repo}/commits/main','--jq','.sha']);assert main=='f70b7e5be63f6b85d895c6d5b259adbc30577b86';assert max(p.stat().st_size for p in D.rglob('*') if p.is_file())<100*1024*1024
with tempfile.TemporaryDirectory() as td:
 env=os.environ.copy();env['GIT_INDEX_FILE']=str(Path(td)/'artifact-index');run(['git','read-tree','--empty'],env=env)
 for p in sorted(D.rglob('*')):
  if p.is_file():
   name=str(p.relative_to(D));assert not name.startswith('.github/');oid=run(['git','hash-object','--no-filters','-w','--',str(p)]);run(['git','update-index','--add','--cacheinfo','100644',oid,name],env=env)
 tree=run(['git','write-tree'],env=env);commit=run(['git','commit-tree',tree,'-m','Avatar Foundation offline review: relaxed knife; unresolved rifle checks documented'])
run(['git','tag',tag,commit]);print('Created independent archive tree',commit,flush=True);subprocess.run(['git','-c','pack.threads=2','-c','pack.windowMemory=128m','push','origin','refs/tags/'+tag],cwd=R,check=True)
url=f'https://github.com/{repo}/archive/refs/tags/{tag}.zip';notes=R.parent/'foundation-archive-release-notes.md';notes.write_text('Виправлено рух кисті з ножем для обох аватарів. Період4000мс, стабільний лікоть, без ковзання хвату. Main та гра не змінені.\n\n[Завантажити повний ZIP]('+url+'). Розпакуйте ВЕСЬ архів, відкрийте Report.html або Avatar-Lab.html у браузері. Report містить вбудовані анімації та відео.\n\n119/119JavaScript;284/288Python/Chromium. Чотири невдалі перевірки не приховані: шум захищеної оригінальної бази та контакт прикладівrifle. Художнє затвердження потрібне; це не production-ready.\n\nEndpoint файлів Release повертає401, тому повний пакет розміщено в окремому parentless artifact tag. Source code(zip) для цього тегу є повним перевіреним пакетом.\n')
subprocess.run(['gh','release','create',tag,'--repo',repo,'--verify-tag','--prerelease','--latest=false','--title','Avatar Core — рух ножа, Lab та контрольні цикли','--notes-file',str(notes)],cwd=R,check=True)
download=R.parent/'Avatar-Foundation-Cleanup-github-verified.zip';subprocess.run(['curl','--fail','--location','--retry','2','--silent','--show-error','--output',str(download),url],check=True)
expected={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file()}
with zipfile.ZipFile(download) as z:
 assert z.testzip() is None;actual={n.split('/',1)[1]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')};assert expected==actual
assert run(['gh','api',f'repos/{repo}/commits/main','--jq','.sha'])==main
result={'download_url':url,'release_url':f'https://github.com/{repo}/releases/tag/{tag}','artifact_commit':commit,'source_commit':source,'main_unchanged':main,'downloaded_files_verified':len(actual),'zip_bytes':download.stat().st_size,'zip_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'production_ready':False,'publication_transport':'artifact tag archive; release uploads endpoint401; no force push','motion_urls':{g:f'https://raw.githubusercontent.com/{repo}/{tag}/Gallery/{g}-knife-motion-before-after.webp' for g in ['male','female']}};(O/'https-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
