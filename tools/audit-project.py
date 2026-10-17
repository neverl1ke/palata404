"""Tracked-file dependency inventory. Unreferenced is a review hint, never a deletion instruction."""
import argparse,collections,hashlib,json,posixpath,re,subprocess
from pathlib import Path
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
def audit():
 paths=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().rstrip('\0').split('\0');known=set(paths);case={p.lower():p for p in paths};files=[];edges=[];missing=[];dynamic=[];texts={};hashes=collections.defaultdict(list)
 text_ext={'.js','.cjs','.py','.html','.css','.md','.json','.yml','.yaml','.txt'}
 for path in paths:
  p=ROOT/path
  if not p.is_file():continue
  data=p.read_bytes();sha=hashlib.sha256(data).hexdigest();hashes[sha].append(path)
  category='runtime' if '/' not in path and p.suffix in {'.js','.css','.html','.png','.jpg'} else path.split('/')[0] if '/' in path else 'config/docs'
  files.append({'path':path,'bytes':len(data),'sha256':sha,'git_blob':subprocess.check_output(['git','hash-object',path],cwd=ROOT,text=True).strip(),'category':category})
  if p.suffix in text_ext:
   try:texts[path]=data.decode()
   except UnicodeDecodeError:pass
 def link(src,raw,kind,strict=False):
  if raw.startswith(('#','data:','mailto:','javascript:','http:','https:','//')):return
  raw=unquote(urlsplit(raw).path)
  if not raw:return
  if any(c in raw for c in '${}*<>') or '\\' in raw:dynamic.append({'source':src,'expression':raw,'kind':kind});return
  target=posixpath.normpath(posixpath.join(posixpath.dirname(src),raw))
  if target == '.' or any(p.startswith(target.rstrip('/')+'/') for p in known) and raw.endswith('/') :return
  if target in known:edges.append({'source':src,'target':target,'kind':kind});return
  if raw in known:edges.append({'source':src,'target':raw,'kind':kind+'-root'});return
  if kind=='css' and not re.search(r'\.(?:png|jpe?g|svg|webp|woff2?)(?:$|\?)',raw):dynamic.append({'source':src,'expression':raw,'kind':'css-expression'});return
  if strict:
   missing.append({'source':src,'target':target,'reference':raw,'kind':kind,'case_match':case.get(target.lower())})
 for path,text in texts.items():
  suffix=Path(path).suffix
  if suffix=='.html':
   for x in re.findall(r'(?:src|href)\s*=\s*["\']([^"\']+)',text):link(path,x,'html',True)
  if suffix in {'.css','.html'}:
   for x in re.findall(r'url\(\s*["\']?([^\)"\']+)',text):link(path,x,'css',True)
  if suffix=='.md':
   for x in re.findall(r'\]\(<?([^\s)>]+)',text):link(path,x,'documentation',True)
  for x in re.findall(r'["\'`]([^"\'`\n]+\.(?:png|jpe?g|svg|webp|js|css|html|json|woff2?)(?:\?[^"\'`\n]*)?)["\'`]',text):
   if len(x)<240:link(path,x,'literal',suffix in {'.js','.cjs'} and path.count('/')==0)
  for x in re.findall(r'["\'`]([^"\'`\n]*\$\{[^"\'`\n]*)["\'`]',text):
   if re.search(r'assets/|\.png|\.json|\.js',x):dynamic.append({'source':path,'expression':x,'kind':'template'})
 # Global classic scripts depend on execution order, not import syntax.
 runtime_scripts=re.findall(r'<script[^>]+src="([^"?]+)',texts.get('index.html',''))
 for i,path in enumerate(runtime_scripts):
  if path in known:
   for previous in runtime_scripts[:i]:
    if previous in known:edges.append({'source':path,'target':previous,'kind':'classic-script-order'})
 referenced={e['target'] for e in edges};candidates=[f['path'] for f in files if f['path'] not in referenced and f['category'] not in {'review','.github','tests','tools','docs','config/docs'} and f['path']!='index.html']
 declarations=[]
 for path,text in texts.items():
  if path.endswith('.js') and '/' not in path:
   for m in re.finditer(r'^(?:async\s+)?function\s+(\w+)\s*\(',text,re.M):
    name=m[1];uses=[p for p,t in texts.items() if re.search(r'\b'+re.escape(name)+r'\b',t)]
    declarations.append({'name':name,'source':path,'line':text.count('\n',0,m.start())+1,'references_in':uses,'runtime_occurrences':sum(len(re.findall(r'\b'+re.escape(name)+r'\b',texts[p])) for p in runtime_scripts+['index.html'] if p in texts)})
 owners={}
 for path,text in texts.items():
  if path.endswith('.js') and '/' not in path:
   for name in re.findall(r'^(?:function|const|let)\s+(\w+)',text,re.M):owners.setdefault(name,[]).append(path)
 for path in runtime_scripts+['index.html']:
  if path not in texts:continue
  for name in set(re.findall(r'\b[A-Za-z_$][\w$]*\b',texts[path])):
   for owner in owners.get(name,[]):
    if owner!=path:edges.append({'source':path,'target':owner,'kind':'global-symbol:'+name})
 code="const fs=require('fs'),vm=require('vm');console.log(vm.runInNewContext(fs.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify({frame:PAPER_DOLL_FRAME,bodies:PAPER_DOLL_BODIES,items:PAPER_DOLL_ITEMS})'))"
 catalog=json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT))
 active_pngs=sorted(set(re.findall(r'[A-Za-z0-9_./-]+\.png',json.dumps(catalog))))
 for png in active_pngs:link('paper-doll-data.js',png,'evaluated-catalog',True)
 return {'paper_doll':{'frame':catalog['frame'],'registered_pngs':active_pngs,'faces':len([i for i in catalog['items'] if i['slot']=='face']),'hairstyles':len([i for i in catalog['items'] if i['slot']=='hair'])},'schema':1,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'tracked_files':len(files),'bytes':sum(f['bytes'] for f in files),'categories':dict(collections.Counter(f['category'] for f in files)),'files':files,'edges':list({(e['source'],e['target'],e['kind']):e for e in edges}.values()),'missing_static_references':missing,'dynamic_paths_requiring_runtime_check':dynamic,'unreferenced_candidates_not_safe_to_delete':candidates,'identical_file_groups':[{'sha256':k,'paths':v} for k,v in hashes.items() if len(v)>1],'classic_scripts':runtime_scripts,'functions':declarations,'limitations':['Static candidates include dynamic and legacy resources; runtime traces and historical documentation must be checked before deletion.','Tool input/output paths and template expressions are evidence, not a complete call graph.']}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'test-results/project-inventory.json');args=parser.parse_args();r=audit();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['commit','tracked_files','bytes','categories','unreferenced_candidates_not_safe_to_delete']},ensure_ascii=False))
