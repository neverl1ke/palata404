"""General revision contracts: immutable art, cleanup proof and real renderer stability."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
import tests.test_game as support
from tests.asset_history import approved_current_hash
ROOT=support.ROOT

class GeneralAssetTests(unittest.TestCase):
 def test_approved_graphics_remain_byte_identical(self):
  before=json.loads((ROOT/'review/project-general-audit/inventory-before.json').read_text())
  manifest=ROOT/'review/project-general-audit/cleanup-manifest.json'
  cleanup=json.loads(manifest.read_text()) if manifest.exists() else {'removed':[]}
  removed={e['path'] for e in cleanup['removed']}
  for entry in before['files']:
   if Path(entry['path']).suffix.lower() not in {'.png','.jpg','.jpeg','.svg','.webp'} or entry['path'] in removed:continue
   self.assertEqual(hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest(),approved_current_hash(entry['path'],entry['sha256']),entry['path'])
 def test_deleted_files_have_pre_audit_hash_and_runtime_evidence(self):
  before=json.loads((ROOT/'review/project-general-audit/inventory-before.json').read_text());entries={e['path']:e for e in before['files']}
  manifest=ROOT/'review/project-general-audit/cleanup-manifest.json'
  removed=json.loads(manifest.read_text())['removed'] if manifest.exists() else []
  self.assertEqual({e['path'] for e in removed},{p for p in entries if not (ROOT/p).exists()})
  requests=json.loads((ROOT/'review/project-general-audit/before/browser.json').read_text())['requested_paths']
  for entry in removed:
   self.assertEqual(entry['sha256'],entries[entry['path']]['sha256']);self.assertEqual(entry['git_blob'],entries[entry['path']]['git_blob'])
   self.assertNotIn(entry['path'],[p.split('?')[0] for p in requests]);self.assertTrue(entry['reason']);self.assertFalse(any(e['target']==entry['path'] for e in before['edges']))
 def test_registered_paper_doll_assets_and_paths_match_case(self):
  import subprocess,re
  code="const fs=require('fs'),vm=require('vm');console.log(vm.runInNewContext(fs.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify({bodies:PAPER_DOLL_BODIES,items:PAPER_DOLL_ITEMS,nativeHeads:PAPER_DOLL_NATIVE_HEADS})'))"
  catalog=json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT));paths=set(re.findall(r'[A-Za-z0-9_./-]+\.png',json.dumps(catalog)))
  self.assertEqual(len(paths),99)  # Approved appearance assets plus two weapon thumbnails.
  for path in paths:
   self.assertTrue((ROOT/path).is_file(),path)
   current=ROOT
   for part in Path(path).parts:self.assertIn(part,[p.name for p in current.iterdir()]);current=current/part
 def test_baseline_dependency_map_has_no_broken_local_links(self):
  before=json.loads((ROOT/'review/project-general-audit/inventory-before.json').read_text())
  self.assertEqual(before['missing_static_references'],[])
  self.assertEqual(before['tracked_files'],917)

class GeneralBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):support.GameTests.setUpClass()
 @classmethod
 def tearDownClass(cls):support.GameTests.tearDownClass()
 def setUp(self):self.case=support.GameTests();self.case.setUp();self.page=self.case.page
 def tearDown(self):self.case.tearDown()
 def test_repeated_render_retains_colored_front_and_rear_after_reload(self):
  self.case.load();self.page.evaluate('openCustomization();setGender("male");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-shoulder-length");setHairColor("white")')
  white_ready='''async()=>{for(const id of ['wardrobe-layer-hair','wardrobe-layer-hair-rear']){const i=document.getElementById(id);if(!i?.paperHairRequest||!i.paperHairRequest.endsWith('|white'))return false;const r=i.paperHairRequest,n=r.lastIndexOf('|');const expected=await coloredHairSource(r.slice(0,n),'white',i.paperHairColorReference);if(i.paperHairRequest!==r||i.getAttribute('src')!==expected||!i.complete||!i.naturalWidth||i.classList.contains('hidden'))return false}return paperDollState.appearance.hairColor==='white'}'''
  self.page.wait_for_function(white_ready)
  # Read both layers and perform the synchronous mutation check in one JS turn;
  # a separate protocol round-trip could sample a pending original-color frame.
  snapshot=self.page.evaluate('''()=>{const imgs=['wardrobe-layer-hair','wardrobe-layer-hair-rear'].map(id=>document.getElementById(id));const before=imgs.map(i=>i.getAttribute('src'));const observers=imgs.map(i=>{const o=new MutationObserver(()=>{});o.observe(i,{attributes:true,attributeFilter:['src']});return o});for(let n=0;n<30;n++)updateCharacterLayers();const counts=observers.map(o=>{const n=o.takeRecords().length;o.disconnect();return n});return {counts,unchanged:imgs.every((i,n)=>i.getAttribute('src')===before[n]),white:imgs.every(i=>i.paperHairRequest?.endsWith('|white')&&i.getAttribute('src').startsWith('data:image/png'))}}''')
  self.assertEqual(snapshot,{'counts':[0,0],'unchanged':True,'white':True})
  self.page.reload(wait_until='networkidle');self.page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"');self.assertEqual(self.page.evaluate('paperDollState.appearance.hair'),'hair-shoulder-length');self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'white')
  self.page.wait_for_function(white_ready)
 def test_invalid_boss_names_do_not_mutate_a_saved_character(self):
  self.case.load();before=self.page.evaluate('JSON.stringify({stats,inventory,gameProgress})')
  for name in ['constructor','__proto__','toString','missing']:
   self.page.evaluate('name=>{startBossFight(name);openBossDossier(name)}',name)
   self.assertFalse(self.page.evaluate('isBattleActive'));self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,gameProgress})'),before)
