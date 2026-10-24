"""Build the portable review archive. No runtime/server dependencies for the user."""
from pathlib import Path
import hashlib,html,json,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-cleanup'
DEST=ROOT.parent/'Avatar-Core-Cleanup';DEST.mkdir(exist_ok=True)
# Markdown is a build-only formatter already cached in the development runtime.
body=subprocess.check_output(['npx','--offline','--yes','marked@15.0.12','--input',str(OUT/'README.md')],cwd=ROOT,text=True)
params=DEST/'Parameters';params.mkdir(exist_ok=True)
for p in OUT.glob('*.json'):shutil.copyfile(p,params/p.name)
for p in (ROOT/'avatar-core/rigs').glob('*.json'):shutil.copyfile(p,params/p.name)
shutil.copyfile(ROOT/'avatar-core/weapons.json',params/'weapons.json')
for name in ['Avatar-Lab.html','Report.html']:shutil.copyfile(OUT/name,DEST/name)
shutil.copytree(OUT/'test-logs',DEST/'Test-logs',dirs_exist_ok=True)
shutil.copyfile(OUT/'README.md',DEST/'Technical-report.md')
def links(m):
    href=m[1]
    if href=='index.html':return 'href="Report.html"'
    if (params/href).is_file():return 'href="Parameters/'+href+'"'
    return m[0]
body=re.sub('href="([^"]+)"',links,body)
# The historical report is a repository reference; no broken offline navigation.
body=re.sub(r'<a href="../avatar-core-polish/README.md">(.*?)</a>',r'<span title="Історичний документ у репозиторії">\1</span>',body)
style='body{margin:auto;max-width:1100px;padding:20px;background:#172022;color:#e2dcd0;font:17px/1.6 system-ui;overflow-wrap:anywhere}a{color:#a6d7df}pre{overflow:auto;padding:12px;background:#233031}code{font-size:14px}table{display:block;overflow:auto;max-width:100%}h1,h2,h3{line-height:1.25}@media(max-width:600px){body{padding:12px}}'
doc='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core cleanup · звіт</title><style>'+style+'</style><p><a href="Avatar-Lab.html">Інтерактивний Lab</a> · <a href="Report.html">ДО/ПІСЛЯ</a></p>'+body+'</html>'
(OUT/'Technical-report.html').write_text(doc);(DEST/'Technical-report.html').write_text(doc)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(DEST/'Revision.txt').write_text('Local feature/avatar-core-1; main untouched.\nRevision: '+revision+'\nBefore cleanup:4f46b15\n')
(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('''ПАЛАТА404 — AVATAR CORE, FINAL CLEANUP

1. Завантаж ZIP і повністю розпакуй його.
2. Відкрий Avatar-Lab.html у Google Chrome/Chromium.
3. Для26 реальних контрольних зображень відкрий Report.html.
4. Докладні зміни й тести — Technical-report.html.

Не запускай HTML через панель попереднього перегляду ZIP у чаті
чи переглядач коду GitHub. Сервер та інтернет не потрібні.

Оновлено тільки зап’ястя й жіноче плече rifle. Жодних нових поз,
одягу або переробки Lab. Main і публікацію не змінювали.
''')
manifest=[]
for p in sorted(DEST.rglob('*')):
    if p.is_file() and p.name!='Package-SHA256.json':manifest.append({'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for filename,select in [('Avatar-Core-Cleanup.zip',lambda p:True),('Avatar-Core-Cleanup-Lab.zip',lambda p:p.name in ['Avatar-Lab.html','ВІДКРИЙ_СПОЧАТКУ.txt','Revision.txt']),('Avatar-Core-Cleanup-Gallery.zip',lambda p:p.name!='Avatar-Lab.html')]:
    target=ROOT.parent/filename
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(DEST.rglob('*')):
            if p.is_file() and select(p):z.write(p,str(p.relative_to(DEST.parent)))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    print(filename,target.stat().st_size,hashlib.sha256(target.read_bytes()).hexdigest())
