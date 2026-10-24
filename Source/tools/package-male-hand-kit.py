"""Portable hand-art authoring kit, not a runtime hand integration."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'review/male-hand-art-kit';DEST=ROOT.parent/'Male-Hand-Art-Kit-2.1';DEST.mkdir(exist_ok=True)
for folder in ['Hands','Gallery','test-logs']:
 if (OUT/folder).exists():shutil.copytree(OUT/folder,DEST/folder,dirs_exist_ok=True)
for name in ['Report.html','README.md','hand-contract.json','browser-capture.json','protected-runtime.json']:
 shutil.copyfile(OUT/name,DEST/name)
for p in OUT.glob('*.json'):
 if p.name!='offline-package-check.json':shutil.copyfile(p,DEST/p.name)
shutil.copyfile(ROOT/'review/avatar-core-grip-pass/Avatar-Lab.html',DEST/'Avatar-Lab.html')
# Existing current engine only; exporting this note does not alter its source.
p=DEST/'Avatar-Lab.html';s=p.read_text().replace('<main>','<p style="padding:16px;border:2px solid #dbb16f">Комплект художника: нових кистей немає; усі шаблони порожні й не підключені.</p><main>',1);p.write_text(s)
body=subprocess.check_output(['npx','--offline','--yes','marked@15.0.12','--input',str(OUT/'README.md')],cwd=ROOT,text=True)
style='body{max-width:1150px;margin:auto;padding:20px;background:#182024;color:#eee4d3;font:17px/1.55 system-ui;overflow-wrap:anywhere}a{color:#9cd7ef}pre,table{display:block;overflow:auto}td,th{padding:8px;border:1px solid #667}img{max-width:100%}'
(DEST/'Technical-report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hand Art Kit · технічний звіт</title><style>'+style+'</style><p><a href="Report.html">Галерея</a> · <a href="Avatar-Lab.html">Чинний Lab</a></p>'+body+'</html>')
(DEST/'Tools').mkdir(exist_ok=True);shutil.copyfile(ROOT/'tools/validate-male-hand-delivery.py',DEST/'Tools/validate-male-hand-delivery.py')
(DEST/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('КОМПЛЕКТ ДЛЯ ХУДОЖНИКА — НЕ НОВІ КИСТІ\n\nРозпакуй весь ZIP.\nReport.html — галерея, шари та маски.\nTechnical-report.html — контракт і координати.\nAvatar-Lab.html — чинний незмінений Core7854994.\n\nНових художніх кистей0;9 candidate-шарів порожні. Вони не інтегровані.\nЗберігай Hands і Gallery поряд з HTML. Сервер та Інтернет для перегляду не потрібні.\n\nНеобов’язкова технічна перевірка повернених PNG (Python,Pillow,NumPy):\npython Tools/validate-male-hand-delivery.py --kit . --delivery .\nПорожні шаблони навмисно повертають код2 — це не готовий малюнок.\n')
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();(DEST/'Revision.txt').write_text('Source checkout: '+revision+'\nProtected runtime baseline:7854994\nNew hand artwork:0\nNo main/runtime modifications. Artist authoring fallback from task section7.\n')
manifest=[{'path':str(p.relative_to(DEST)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='Package-SHA256.json'];(DEST/'Package-SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
archive=ROOT.parent/'Male-Hand-Art-Kit-2.1.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(DEST.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(DEST.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
