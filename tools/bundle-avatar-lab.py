"""Bundle the real lab, engine, original images and catalog into one offline HTML.
No screenshots substitute for the interactive rig; file:// needs no server or CDN.
"""
from pathlib import Path
import json,base64,mimetypes,re,subprocess,argparse
ROOT=Path(__file__).resolve().parents[1];CORE=ROOT/'avatar-core';LAB=ROOT/'avatar-lab'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',default='review/avatar-core-1/avatar-lab-offline.html');args=parser.parse_args();OUT=ROOT/args.output;OUT.parent.mkdir(parents=True,exist_ok=True)
def data(p):return 'data:'+mimetypes.guess_type(p.name)[0]+';base64,'+base64.b64encode(p.read_bytes()).decode()
resources={'json':{},'images':{},'catalogImages':{}}
for p in CORE.rglob('*.json'):resources['json'][str(p.relative_to(CORE))]=json.loads(p.read_text())
for p in CORE.rglob('*.png'):resources['images'][str(p.relative_to(CORE))]=data(p)
for g in ['male','female']:resources['images']['../base_'+g+'.png']=data(ROOT/('base_'+g+'.png'))
script="const f=require('fs'),v=require('vm');console.log(v.runInNewContext(f.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify({items:PAPER_DOLL_ITEMS.filter(i=>[\"hair\",\"face\"].includes(i.slot)),native:PAPER_DOLL_NATIVE_HEADS})'))"
catalog=json.loads(subprocess.check_output(['node','-e',script],cwd=ROOT,text=True))
def walk(v):
 if isinstance(v,str) and re.search(r'\.png(?:\?v=[\w-]+)?$',v):
  p=ROOT/v.split('?')[0]
  if not p.is_file():raise FileNotFoundError(v)
  resources['catalogImages'][v]=data(p)
 elif isinstance(v,dict):
  for x in v.values():walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
walk(catalog)
text=re.sub(r'<link[^>]+href="lab\.css"[^>]*>',lambda m:'<style>'+(LAB/'lab.css').read_text()+'</style>',(LAB/'index.html').read_text())
def safe(s):return s.replace('</script','<\\/script')
text=re.sub(r'<script src="([^"]+)"></script>',lambda m:'<script>'+safe((LAB/m[1]).resolve().read_text())+'</script>',text)
# Resolve catalog assets to embedded originals, preserving real recoloring and masks.
text=re.sub(r"const absolute\s*=\s*\(?path\)?\s*=>\s*new URL\('\.\./'\s*\+\s*path,\s*location.href\).href;","const absolute = path => window.AVATAR_CORE_EMBED.catalogImages[path];",text)
modules={name:(CORE/name).read_text() for name in ['math.mjs','weapon-controller.mjs','skin.mjs','engine.mjs']};bootstrap='window.AVATAR_CORE_EMBED='+json.dumps(resources,separators=(',',':'))+';\nconst moduleURL=source=>URL.createObjectURL(new Blob([source],{type:"text/javascript"}));\n'
bootstrap+='const mathURL=moduleURL('+json.dumps(modules['math.mjs'])+');\n'
for var,name in [('weaponURL','weapon-controller.mjs'),('skinURL','skin.mjs')]:bootstrap+='const '+var+'=moduleURL('+json.dumps(modules[name])+'.replace("\'./math.mjs\'",JSON.stringify(mathURL)));\n'
bootstrap+='const engineURL=moduleURL('+json.dumps(modules['engine.mjs'])+'.replace("\'./math.mjs\'",JSON.stringify(mathURL)).replace("\'./weapon-controller.mjs\'",JSON.stringify(weaponURL)).replace("\'./skin.mjs\'",JSON.stringify(skinURL)));\n'
bootstrap+='const labSource='+json.dumps((LAB/'lab.mjs').read_text())+'.replace("\'../avatar-core/engine.mjs\'",JSON.stringify(engineURL));\nimport(moduleURL(labSource));\n'
text=text.replace('<script type="module" src="lab.mjs"></script>','<script type="module">'+safe(bootstrap)+'</script>');text=text.replace('<title>Палата 404 · Avatar Lab 1.0</title>','<title>Палата 404 · автономний Avatar Lab 1.0</title>');OUT.write_text(text)
print(OUT.name,OUT.stat().st_size,'bytes;',len(resources['images']),'rig PNGs;',len(resources['catalogImages']),'catalog PNGs')
