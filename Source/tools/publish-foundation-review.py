"""Publish an isolated artifact tag, never the source branch/main; verify downloaded ZIP."""
from pathlib import Path
import json,subprocess,os,tempfile,hashlib,zipfile
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';D=R.parent/'Avatar-Foundation-Cleanup';repo='neverl1ke/palata404'
def run(a,**kw):return subprocess.check_output(a,cwd=R,text=True,**kw).strip()
pkg=json.loads((O/'package.json').read_text());proof=json.loads((O/'offline-package-check.json').read_text());assert proof['zip_sha256']==pkg['sha256'];assert len(proof['poses'])==16 and not proof['js_errors'] and not proof['network_requests'];source=pkg['source_commit'];tag='avatar-foundation-'+source[:7];main=run(['gh','api',f'repos/{repo}/commits/main','--jq','.sha']);assert main=='f70b7e5be63f6b85d895c6d5b259adbc30577b86';assert not run(['git','tag','-l',tag]);assert max(p.stat().st_size for p in D.rglob('*') if p.is_file())<100*1024*1024
url=f'https://github.com/{repo}/releases/download/{tag}/Avatar-Foundation-Cleanup.zip'
readme=R.parent/'foundation-tag-README.md'
readme.write_text('# Avatar Foundation — preview tag\n\nПовний ZIP зі звітом, Lab та нативними кадрами: '+url+'\n\nКнопка Source code (zip) містить тільки цей README і прев’ю. Завантажуйте файл релізу Avatar-Foundation-Cleanup.zip. Main та гра не змінені. Це review для художнього погодження.\n\nSHA-256 повного ZIP: '+pkg['sha256']+'\n')
with tempfile.TemporaryDirectory() as td:
 env=os.environ.copy();env['GIT_INDEX_FILE']=str(Path(td)/'artifact-index');run(['git','read-tree','--empty'],env=env)
 previews=[('README.md',readme)]+[(str(p.relative_to(D)),p) for g in ['male','female'] for kind in ['motion','wrist-motion'] for p in [D/'Gallery'/f'{g}-knife-{kind}-before-after.webp']]
 for name,p in previews:
  assert p.is_file();oid=run(['git','hash-object','-w','--',str(p)]);run(['git','update-index','--add','--cacheinfo','100644',oid,name],env=env)
 tree=run(['git','write-tree'],env=env);commit=run(['git','commit-tree',tree,'-m','Avatar Foundation previews; full review is a release ZIP asset'])
run(['git','tag',tag,commit]);subprocess.run(['git','push','origin','refs/tags/'+tag],cwd=R,check=True)
url=f'https://github.com/{repo}/releases/download/{tag}/Avatar-Foundation-Cleanup.zip';notes=R.parent/'foundation-release-notes.md';notes.write_text('Окремий review-архів, main та гра не змінені. Рух ножа виправлено для чоловічого й жіночого аватарів: кисть разом із ножем, стабільний лікоть,4000мс. Є автономні Report.html, Avatar-Lab.html, повні RGBAкадри, крупні плани та нові відео із фактичними PTS.\n\nПотрібне художнє погодження. Відома невдача тесту захищеного base_male.png не прихована; активний runtime має окрему очищену копію. Не production-ready.\n\n[Завантажити ZIP]('+url+') — розпакувати ВЕСЬ архів, відкрити Report.html у браузері. Не відкривати HTML як текст на GitHub.\n')
tests=json.loads((O/'Evidence/final-tests/summary.json').read_text())
notes.write_text(notes.read_text()+f"\nТести:119/119JavaScript; {tests['passed']}/{tests['total']}Python. Невдалі перевірки збережені. Відкрито: контакт приклада нового clean rifle для обох статей та відомий alpha-шум захищеного оригіналу.\n\nКнопки Source code містять лише прев’ю. Повний результат — файл Avatar-Foundation-Cleanup.zip. Report.html та Avatar-Lab.html можна завантажити окремо.\n")
subprocess.run(['gh','release','create',tag,pkg['zip'],str(D/'Avatar-Lab.html'),str(D/'Report.html'),'--repo',repo,'--verify-tag','--prerelease','--latest=false','--title','Avatar Core — relaxed knife та очищення кистей','--notes-file',str(notes)],cwd=R,check=True)
download=R.parent/'Avatar-Foundation-Cleanup-github-verified.zip';subprocess.run(['curl','--fail','--location','--retry','2','--silent','--show-error','--output',str(download),url],check=True)
assert hashlib.sha256(download.read_bytes()).hexdigest()==pkg['sha256']
expected={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in D.rglob('*') if p.is_file()}
with zipfile.ZipFile(download) as z:
 assert z.testzip() is None;actual={n.split('/',1)[1]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')};assert expected==actual
assert run(['gh','api',f'repos/{repo}/commits/main','--jq','.sha'])==main
result={'download_url':url,'release_url':f'https://github.com/{repo}/releases/tag/{tag}','artifact_commit':commit,'source_commit':source,'main_unchanged':main,'downloaded_files_verified':len(actual),'zip_bytes':download.stat().st_size,'zip_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'production_ready':False,'full_frames_in_release_asset_not_git':True,'lab_url':f'https://github.com/{repo}/releases/download/{tag}/Avatar-Lab.html','report_url':f'https://github.com/{repo}/releases/download/{tag}/Report.html','motion_urls':{g:f'https://raw.githubusercontent.com/{repo}/{tag}/Gallery/{g}-knife-motion-before-after.webp' for g in ['male','female']}};(O/'https-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
