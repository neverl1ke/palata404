"""Portable male Core2 review package. Does not publish, push or modify main."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/avatar-core-grip-pass'
DEST=ROOT.parent/'Avatar-Core-Chest-Review';DEST.mkdir(exist_ok=True)
for name in ['Avatar-Lab.html','README.md']:
    shutil.copyfile(OUT/name,DEST/name)
# A small HTML with local media is easier to open than an85MB data-URI page.
# All files still work via file:// after unpacking the complete ZIP.
gallery=DEST/'Gallery';gallery.mkdir(exist_ok=True)
report=(OUT/'index.html').read_text().replace('href="../../avatar-lab/"','href="Avatar-Lab.html"')
exports=[]
for relative in re.findall(r'src="([^"]+)"',report):
    source=OUT/relative
    if source.is_file():
        target=gallery/source.name
        if source.name.endswith('-chest-breathing.webp'):
            original=Image.open(source);frames=[]
            for index in range(original.n_frames):
                original.seek(index);frames.append(original.convert('RGB').resize((760,340),Image.Resampling.LANCZOS))
            frames[0].save(target,save_all=True,append_images=frames[1:],duration=125,loop=0,lossless=True)
            exports.append({'path':'Gallery/'+target.name,'source_size':[1140,510],'portable_size':[760,340],'frames':len(frames),'frame_duration_ms':125,'duration_ms':4000,'method':'uniform Lanczos resize of real captured frames; no generated frames'})
        else:shutil.copyfile(source,target)
        report=report.replace('src="'+relative+'"','src="Gallery/'+source.name+'"')
shutil.copytree(OUT/'frames',gallery/'frames',dirs_exist_ok=True)
(DEST/'Media-export.json').write_text(json.dumps(exports,indent=2)+'\n')
report=report.replace('"frames/','"Gallery/frames/')
(DEST/'Report.html').write_text(report)

body=subprocess.check_output(['npx','--offline','--yes','marked@15.0.12','--input',str(OUT/'README.md')],cwd=ROOT,text=True)
def portable_link(m):
    path=m[1]
    if path=='index.html':return 'href="Report.html"'
    if path=='../../avatar-lab/':return 'href="Avatar-Lab.html"'
    if path.endswith('avatar-core-transition-proposal.md'):return 'href="Transitions-proposal.html"'
    if path.endswith('.json'):return 'href="Parameters/'+Path(path).name+'"'
    return m[0]
body=re.sub('href="([^"]+)"',portable_link,body)
style='body{max-width:1100px;margin:auto;padding:20px;background:#172022;color:#ece4d4;font:17px/1.6 system-ui;overflow-wrap:anywhere}a{color:#a6d7df}pre,table{display:block;overflow:auto}code{font-size:14px}'
# The full report retains repository links as text; all portable navigation is
# explicit below so file:// never opens raw Markdown as the primary page.
doc='<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Чоловічий Core2 · технічний звіт</title><style>'+style+'</style><p><a href="Avatar-Lab.html">Lab</a> · <a href="Report.html">Галерея</a></p>'+body+'</html>'
(DEST/'Technical-report.html').write_text(doc)
proposal=subprocess.check_output(['npx','--offline','--yes','marked@15.0.12','--input',str(ROOT/'docs/avatar-core-transition-proposal.md')],cwd=ROOT,text=True)
(DEST/'Transitions-proposal.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+style+'</style><p><a href="Technical-report.html">Назад до звіту</a></p>'+proposal+'</html>')
for folder in ['test-logs']:
    if (OUT/folder).exists():shutil.copytree(OUT/folder,DEST/folder,dirs_exist_ok=True)
shutil.copytree(ROOT/'avatar-core/assets/male/weapon-pass',DEST/'avatar-core/assets/male/weapon-pass',dirs_exist_ok=True)
shutil.copytree(ROOT/'avatar-core/assets/weapons/male-lobby',DEST/'avatar-core/assets/weapons/male-lobby',dirs_exist_ok=True)
shutil.copytree(ROOT/'avatar-core/assets/male/lobby',DEST/'avatar-core/assets/male/lobby',dirs_exist_ok=True)
previews=DEST/'Previews';previews.mkdir(exist_ok=True)
for path in [OUT/'four-poses-overview.jpg',*OUT.glob('after-*.webp'),*OUT.glob('*-close.webp'),OUT/'rifle-stock-contact.webp']:
    if path.exists():shutil.copyfile(path,previews/path.name)
params=DEST/'Parameters';params.mkdir(exist_ok=True)
for p in list(OUT.glob('*.json'))+list((ROOT/'avatar-core/rigs').glob('*.json'))+[ROOT/'avatar-core/male-preview.json']:
    if p.name!='offline-package-check.json':shutil.copyfile(p,params/p.name)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(DEST/'Revision.txt').write_text('feature/avatar-core-2-weapon-transitions\nRevision: '+revision+'\nBaseline: f49ae7b\nNot production-approved. No push/main changes.\n')
(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('ПАЛАТА404 — ЧОЛОВІЧИЙ AVATAR CORE2\n\nРозпакуй весь ZIP. Відкрий Avatar-Lab.html у Chrome/Chromium.\nReport.html — реальні кадри ДО/ПІСЛЯ, крупні плани та анімація.\nTechnical-report.html — результати й відкриті обмеження.\n\nІнтернет, сервер і встановлення програм не потрібні. Не відділяй Report.html від папки Gallery.\nЧастковий результат: грудне дихання змінено, хвати НЕ виправлено — інструмент відхилив перемальовування. Не production-ready.\nЖіночий риг, вихідні PNG та main не змінені.\n')
manifest=[]
for p in sorted(DEST.rglob('*')):
    if p.is_file() and p.name!='Package-SHA256.json':manifest.append({'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT.parent/'Avatar-Core-Chest-Review.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(DEST.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(DEST.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
