"""Capture exact original-color render geometry for all 90 registered combinations.
Usage: python tools/capture-project-geometry.py OUTPUT.json
"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tests import test_game as t
t.GameTests.setUpClass();c=t.GameTests();c.setUp()
try:
 c.load();c.page.evaluate('openCustomization()');rows=[]
 for g in ['male','female']:
  c.page.evaluate('g=>setGender(g)',g)
  for f in [None,'face-asian','face-young','face-exhausted','face-elder','face-alternative']:
   c.page.evaluate('f=>equipPaperDollItem("face",f)',f)
   for h in c.page.evaluate('PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"&&paperDollItemSupportsGender(i)).map(i=>i.id)'):
    c.page.evaluate('h=>equipPaperDollItem("hair",h)',h)
    rows.append(c.page.evaluate('''({g,f,h})=>({g,f,h,layers:[...document.querySelectorAll('#wardrobe-paperdoll .char-layer')].map(i=>({id:i.id,style:i.getAttribute('style'),request:i.paperHairRequest})).sort((a,b)=>a.id.localeCompare(b.id))})''',{'g':g,'f':f,'h':h}))
 Path(sys.argv[1]).write_text(json.dumps(rows,indent=2)+'\n');print(len(rows))
finally:c.tearDown();t.GameTests.tearDownClass()
