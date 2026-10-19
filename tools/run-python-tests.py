"""Run the complete discovered unittest suite in isolated, bounded browser shards.
Each worker has its own HTTP server/profile. No tests are skipped or retried.
"""
import argparse,concurrent.futures,json,os,subprocess,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def flatten(suite):
 for item in suite:
  if isinstance(item,unittest.TestSuite):yield from flatten(item)
  else:yield item
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--jobs',type=int,default=3);parser.add_argument('--output',type=Path,default=ROOT/'test-results/full-suite');a=parser.parse_args()
 if not 1<=a.jobs<=4:parser.error('--jobs must be between 1 and 4')
 sys.path.insert(0,str(ROOT));os.chdir(ROOT)
 tests=list(flatten(unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))))
 ids=[t.id() for t in tests];assert len(ids)==len(set(ids)),'Duplicate discovered test IDs'
 browser=[i for i in ids if any('.'+name+'.' in i for name in ['GameTests','AuditBrowserTests','GeneralBrowserTests','FemaleFacesBrowserTests'])];assets=[i for i in ids if i not in browser]
 shards=[browser[i::a.jobs] for i in range(a.jobs)]+[assets];a.output.mkdir(parents=True,exist_ok=True)
 def run(pair):
  i,ids=pair;start=time.monotonic()
  with (a.output/f'shard-{i}.log').open('w') as log:
   result=subprocess.run([sys.executable,'-m','unittest',*ids,'-v'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT) if ids else None
  return {'shard':i,'tests':len(ids),'test_ids':ids,'exit':result.returncode if result else 0,'seconds':round(time.monotonic()-start,3)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs+1) as pool:results=list(pool.map(run,enumerate(shards)))
 report={'total':len(ids),'passed':sum(r['tests'] for r in results if r['exit']==0),'all_passed':all(r['exit']==0 for r in results),'shards':results}
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));sys.exit(not report['all_passed'])
