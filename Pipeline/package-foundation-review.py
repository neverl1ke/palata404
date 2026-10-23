"""Build the reviewed offline delivery; historical/incomplete attempts stay in source evidence."""
from pathlib import Path
import json,shutil,hashlib,subprocess,zipfile,html,base64,re,mimetypes
R=Path(__file__).resolve().parents[1];O=R/'review/avatar-foundation-cleanup';D=R.parent/'Avatar-Foundation-Cleanup';D.mkdir(exist_ok=True)
subprocess.run(['python','tools/bundle-avatar-lab.py','--output',str(D/'Avatar-Lab.html')],cwd=R,check=True)
for folder in ['Gallery','Before','Edits','Inputs']:
 shutil.copytree(O/folder,D/folder,dirs_exist_ok=True)
shutil.copy2(O/'ViewFrames.html',D/'ViewFrames.html');shutil.copy2(O/'README.md',D/'README.md')
# Exact implementation, registered art and reproducible exporters, not an installer.
shutil.copytree(R/'avatar-core',D/'Runtime',dirs_exist_ok=True)
for gender in ['male','female']:shutil.copy2(R/f'base_{gender}.png',D/f'base_{gender}.png')
for n in ['avatar-lab','tests']:
 shutil.copytree(R/n,D/'Source'/n,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for p in (R/'tools').glob('*foundation*.py'):
 (D/'Pipeline').mkdir(exist_ok=True);shutil.copy2(p,D/'Pipeline'/p.name)
for p in [R/'docs/avatar-weapon-attachments.md',O/'active-arms-before.json',O/'male-preview-before.json',O/'female-preview-before.json']:shutil.copy2(p,D/p.name)
E=D/'Evidence';E.mkdir(exist_ok=True)
for n in ['final-tests','baseline-tests']:
 if (O/'Evidence'/n).exists():shutil.copytree(O/'Evidence'/n,E/n,dirs_exist_ok=True)
for p in (O/'Evidence').rglob('*'):
 if p.is_file() and p.suffix in ['.json','.log','.png'] and p.stat().st_size<22*1024*1024:
  target=E/p.relative_to(O/'Evidence');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
blocks=[]
for g,title in [('male','Чоловічий'),('female','Жіночий')]:
 blocks.append('<h2>'+title+' аватар</h2><h3>Ніж: рух ДО / ПІСЛЯ</h3><img loading="lazy" src="Gallery/'+g+'-knife-motion-before-after.webp"><p>80 кадрів × 50 мс; зменшене прев’ю. Нативні 241 кадр — у Gallery/Dense.</p>')
 blocks.append('<h3>Кисть і ніж — збільшений рух</h3><img loading="lazy" src="Gallery/'+g+'-knife-wrist-motion-before-after.webp"><h3>Нативні контрольні фази</h3><img loading="lazy" src="Gallery/'+g+'-knife-native-phases.webp">')
 for pose in ['idle','melee','pistol','rifle']:
  blocks.append(f'<h3>{html.escape(pose)}</h3><img loading="lazy" src="Gallery/{g}-{pose}-comparison.webp"><p>Ліворуч — c2822a7; центр — поточний предмет; праворуч — та сама рука без предмета.</p>')
  if (D/'Gallery'/f'after-{g}-{pose}-raf.webm').exists():blocks.append(f'<video preload="none" controls loop src="Gallery/after-{g}-{pose}-raf.webm"></video>')
blocks.append('<h2>Крупні плани 100% / 300%</h2>')
for p in sorted((D/'Gallery').glob('*-3x.webp')):blocks.append(f'<figure><img loading="lazy" src="Gallery/{p.name}"><figcaption>{html.escape(p.stem)}</figcaption></figure>')
blocks.append('<h2>Шия, талія, діагностичні скіни</h2>')
for p in sorted((D/'Gallery').glob('*fractional*.png')):blocks.append(f'<img loading="lazy" src="Gallery/{p.name}">')
for p in sorted((D/'Gallery').glob('*diagnostic*.webp')):blocks.append(f'<img loading="lazy" src="Gallery/{p.name}">')
blocks.append('<h2>Повна галерея та покадрові матеріали</h2><ul>')
for p in sorted((D/'Gallery').iterdir()):
 if p.is_file():blocks.append(f'<li><a href="Gallery/{p.name}">{html.escape(p.name)}</a></li>')
blocks.append('</ul>')
style='body{font:16px system-ui;background:#172026;color:#eee;max-width:1400px;margin:auto;padding:16px;line-height:1.5}img,video{display:block;max-width:100%;height:auto;margin:12px 0}a{color:#94d6ff}li{overflow-wrap:anywhere}figure{margin:0}nav{position:sticky;top:0;background:#172026;padding:8px}.notice{border-left:4px solid #dfab55;padding:12px}h2{margin-top:40px}'
(D/'Report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Avatar Core — рух кисті та cleanup</title><style>'+style+'</style><h1>Палата 404 — кисті, ніж і поверхні Avatar Core</h1><nav><a href="Avatar-Lab.html">Інтерактивний Lab</a> · <a href="Technical-report.html">Технічний звіт</a> · <a href="ViewFrames.html">Нативні кадри</a></nav><p class="notice">Версія для візуального погодження. Main, гра, вихідні бази й система збережень не змінені. Художні обмеження та відома невдача тесту захищеного оригіналу описані у звіті.</p>'+''.join(blocks)+'</html>')
# Keep the report readable even if the user opens only its HTML. Videos and
# full native packs remain explicit links in the extracted review folder.
report=D/'Report.html'
def embed(m):
 path=D/m[1]
 return 'src="data:'+mimetypes.guess_type(path.name)[0]+';base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
report.write_text(re.sub(r'src="(Gallery/[^" ]+\.(?:webp|png|webm))"',embed,report.read_text()))
def inline(text):
 text=html.escape(text)
 text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
 return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text)
parts=[];lines=(O/'README.md').read_text().splitlines();i=0
while i<len(lines):
 line=lines[i]
 if not line.strip():i+=1;continue
 if line.startswith('#'):
  level=min(6,len(line)-len(line.lstrip('#')));parts.append(f'<h{level}>'+inline(line[level:].strip())+f'</h{level}>');i+=1
 elif line.startswith('|'):
  rows=[]
  while i<len(lines) and lines[i].startswith('|'):
   cells=[c.strip() for c in lines[i].strip('|').split('|')]
   if not all(re.fullmatch(r'[-: ]+',c) for c in cells):rows.append(cells)
   i+=1
  parts.append('<div class="table"><table>'+''.join('<tr>'+''.join(('<th>' if n==0 else '<td>')+inline(c)+('</th>' if n==0 else '</td>') for c in row)+'</tr>' for n,row in enumerate(rows))+'</table></div>')
 else:
  paragraph=[]
  while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|')):paragraph.append(lines[i]);i+=1
  parts.append('<p>'+inline(' '.join(paragraph))+'</p>')
(D/'Technical-report.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Технічний звіт</title><style>body{font:16px system-ui;max-width:1200px;margin:20px auto;padding:16px;line-height:1.6;overflow-wrap:anywhere}.table{overflow:auto}table{border-collapse:collapse;min-width:900px}td,th{border:1px solid #bbb;padding:8px;vertical-align:top}code{font-size:.9em;background:#eee}</style><a href="Report.html">Галерея</a>'+''.join(parts)+'</html>')
results=json.loads((O/'Evidence/final-tests/summary.json').read_text())
report.write_text(report.read_text().replace('<h1>Палата 404 — кисті, ніж і поверхні Avatar Core</h1>', '<h1>Палата 404 — кисті, ніж і поверхні Avatar Core</h1>'+f"<p>JavaScript119/119. Python{results['passed']}/{results['total']}; невдалі перевірки не приховано, подробиці в технічному звіті.</p>"))
(D/'ВІДКРИЙ_СПОЧАТКУ.txt').write_text('Розпакуйте ВЕСЬ ZIP. Відкрийте Report.html браузером. Інтерактивний Lab — Avatar-Lab.html, без інтернету/сервера. У Lab виберіть чоловік/жінка → melee та ввімкніть дихання. Порівняння ножа ДО/ПІСЛЯ — на початку галереї. ViewFrames.html відкриває точні .avframes із Gallery/Dense. Не відкривайте HTML як текст на GitHub.\n')
files={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.rglob('*')) if p.is_file() and p.name!='SHA256.json'};(D/'SHA256.json').write_text(json.dumps(files,indent=2));z=R.parent/'Avatar-Foundation-Cleanup.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as out:
 for p in sorted(D.rglob('*')):
  if p.is_file():out.write(p,'Avatar-Foundation-Cleanup/'+str(p.relative_to(D)))
with zipfile.ZipFile(z) as q:assert q.testzip() is None
result={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'files':len(files)+1,'zip':str(z),'bytes':z.stat().st_size,'sha256':hashlib.sha256(z.read_bytes()).hexdigest()};(O/'package.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
