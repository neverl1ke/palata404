"""Run every discovered test once, keeping asset-mutating cases isolated.
Preparation/reproduction tests run serially first. Read-only tests then share
bounded browser shards, each with its own HTTP server and browser profile.
"""
import argparse,concurrent.futures,json,os,re,subprocess,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# These tests deliberately rewrite runtime PNGs/rigs while checking exact
# reproducibility. Never run a renderer alongside that intermediate state.
MUTATING_TESTS={
 'tests.test_avatar_polish.PolishSourceTests.test_registration_is_reproducible_without_moving_sources',
 'tests.test_female_donor_arms.FemaleDonorSourceTests.test_export_is_reproducible_including_rig_without_regeneration',
 'tests.test_independent_anatomy.IndependentSurfaceSourceTests.test_local_repaint_process_is_deterministic',
}
def flatten(suite):
 for item in suite:
  if isinstance(item,unittest.TestSuite):yield from flatten(item)
  else:yield item
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--jobs',type=int,default=3);parser.add_argument('--output',type=Path,default=ROOT/'test-results/full-suite');a=parser.parse_args()
 if not 1<=a.jobs<=4:parser.error('--jobs must be between 1 and 4')
 sys.path.insert(0,str(ROOT));os.chdir(ROOT);tests=list(flatten(unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))))
 ids=[t.id() for t in tests];assert len(ids)==len(set(ids)),'Duplicate discovered test IDs';a.output.mkdir(parents=True,exist_ok=True)
 def run(pair):
  label,selected=pair;start=time.monotonic();path=a.output/f'{label}.log'
  with path.open('w') as log:result=subprocess.run([sys.executable,'-m','unittest',*selected,'-v'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT) if selected else None
  output=path.read_text();runs=re.findall(r'^Ran (\d+) tests? in ',output,re.M);failed=re.findall(r'^(?:FAIL|ERROR): (\w+) \(([^)]+)\)',output,re.M)
  failure_ids=[name if name.endswith('.'+method) else name+'.'+method for method,name in failed];ran=int(runs[-1]) if runs else 0;skipped=len(re.findall(r'^test_.* \.{3} skipped ',output,re.M))
  return {'shard':label,'tests':len(selected),'ran':ran,'passed':max(0,ran-len(failure_ids)-skipped),'failure_ids':failure_ids,'skipped':skipped,'test_ids':selected,'exit':result.returncode if result else 0,'seconds':round(time.monotonic()-start,3)}
 preparation=[i for i in ids if i in MUTATING_TESTS];readonly=[i for i in ids if i not in MUTATING_TESTS]
 results=[run(('preparation',preparation))]
 shards=[readonly[i::a.jobs] for i in range(a.jobs)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:results+=list(pool.map(run,[(f'shard-{i}',s) for i,s in enumerate(shards)]))
 assert sorted(i for r in results for i in r['test_ids'])==sorted(ids),'Every discovered scenario must execute exactly once'
 report={'total':len(ids),'ran':sum(r['ran'] for r in results),'passed':sum(r['passed'] for r in results),'failure_ids':[i for r in results for i in r['failure_ids']],'skipped':sum(r['skipped'] for r in results),'all_passed':all(r['exit']==0 for r in results),'execution':'serialized asset-mutating preparation followed by read-only bounded shards; no retries','shards':results}
 (a.output/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));sys.exit(not report['all_passed'])
