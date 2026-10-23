"""Paired actual-browser benchmark; git snapshot vs working tree, identical page/PNG/settings."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests import test_game as t
ROOT=t.ROOT
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--before',default='backup/project-general-audit-20261017');parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();t.GameTests.setUpClass();results={}
 try:
  for phase in ['before','after']:
   c=t.GameTests();c.setUp()
   try:
    if phase=='before':
     for name in ['paper-doll.js','hair-color.js']:
      data=subprocess.check_output(['git','show',a.before+':'+name],cwd=ROOT)
      c.context.route('**/'+name+'?*',lambda route,request,data=data:route.fulfill(content_type='application/javascript',body=data))
    c.load();c.page.evaluate('openCustomization();setGender("male");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-shoulder-length")');c.page.wait_for_timeout(200)
    results[phase]=c.page.evaluate('''()=>{const observer=new MutationObserver(()=>{});observer.observe(document.getElementById('wardrobe-paperdoll'),{subtree:true,attributes:true,attributeFilter:['src']});let calls=0;const original=smoothPaperDollCrown;smoothPaperDollCrown=(...a)=>{calls++;return original(...a)};const samples=[];for(let n=0;n<7;n++){const t=performance.now();for(let i=0;i<100;i++)renderPaperDoll();samples.push(performance.now()-t)}smoothPaperDollCrown=original;const mutations=observer.takeRecords().filter(r=>r.target.id==='wardrobe-layer-hair').length;observer.disconnect();return{iterations:700,batch:100,samples_ms:samples,median_ms:[...samples].sort((a,b)=>a-b)[3],front_src_mutations:mutations,crown_calculations:calls}}''')
   finally:c.tearDown()
  results['conditions']={'source':a.before,'same_browser':True,'same_pngs':True,'network':'local','scope':'Synthetic synchronous render benchmark; not end-to-end FPS or physical phone measurements'}
  results['median_reduction_percent']=100*(1-results['after']['median_ms']/results['before']['median_ms'])
  a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
 finally:t.GameTests.tearDownClass()
