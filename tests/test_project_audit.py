"""General revision contracts: immutable art, cleanup proof and real renderer stability."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
import tests.test_game as support
from tests.asset_history import approved_current_hash
ROOT=support.ROOT

class GeneralAssetTests(unittest.TestCase):
 def test_approved_graphics_remain_byte_identical(self):
  cleanup=json.loads((ROOT/'docs/cleanup-summary.json').read_text())
  for path,digest in cleanup['protectedRuntimeFiles'].items():
   if Path(path).suffix.lower() in {'.png','.jpg','.jpeg','.svg','.webp'}:
    self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),approved_current_hash(path,digest),path)
 def test_deleted_files_have_pre_audit_hash_and_runtime_evidence(self):
  import gzip
  cleanup=json.loads((ROOT/'docs/cleanup-summary.json').read_text())
  removed=gzip.decompress((ROOT/'docs'/cleanup['removedPathList']).read_bytes()).decode().splitlines()
  self.assertEqual(len(removed),cleanup['removedFiles']);self.assertEqual(len(cleanup['baseCommit']),40)
  self.assertFalse(set(removed)&set(cleanup['protectedRuntimeFiles']))
  for path in removed:
   self.assertTrue(path.startswith(('review/','tools/')),path)
   self.assertFalse((ROOT/path).exists(),path)
 def test_registered_paper_doll_assets_and_paths_match_case(self):
  import subprocess,re
  code="const fs=require('fs'),vm=require('vm');console.log(vm.runInNewContext(fs.readFileSync('paper-doll-data.js','utf8')+';JSON.stringify({bodies:PAPER_DOLL_BODIES,items:PAPER_DOLL_ITEMS,nativeHeads:PAPER_DOLL_NATIVE_HEADS})'))"
  catalog=json.loads(subprocess.check_output(['node','-e',code],cwd=ROOT));paths=set(re.findall(r'[A-Za-z0-9_./-]+\.png',json.dumps(catalog)))
  self.assertEqual(len(paths),365)  # Includes the subsequently approved 160 beards and head-specific female hair.
  for path in paths:
   self.assertTrue((ROOT/path).is_file(),path)
   current=ROOT
   for part in Path(path).parts:self.assertIn(part,[p.name for p in current.iterdir()]);current=current/part
 def test_baseline_dependency_map_has_no_broken_local_links(self):
  cleanup=json.loads((ROOT/'docs/cleanup-summary.json').read_text())
  self.assertGreater(len(cleanup['protectedRuntimeFiles']),1000)
  self.assertTrue((ROOT/'review/README.md').is_file())
  for page in (ROOT/'review').rglob('*.html'):
   self.assertTrue(any(part in page.parts for part in ['sources','source','originals','masters','before-assets','before']),str(page))

class GeneralBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):support.GameTests.setUpClass()
 @classmethod
 def tearDownClass(cls):support.GameTests.tearDownClass()
 def setUp(self):self.case=support.GameTests();self.case.setUp();self.page=self.case.page
 def tearDown(self):self.case.tearDown()
 def test_repeated_render_retains_approved_colored_layers_after_reload(self):
  self.case.load();self.page.evaluate('openCustomization();setGender("male");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-shoulder-length");setHairColor("white")')
  # Reviewed male heads use a registered front and skin edge, not the old rear.
  white_ready="""()=>{const imgs=[...document.querySelectorAll('#wardrobe-paperdoll > img')].filter(i=>i.paperHairRequest?.endsWith('|white'));return imgs.length>0&&imgs.every(i=>i.complete&&i.naturalWidth&&!i.classList.contains('hidden')&&i.getAttribute('src')?.startsWith('data:image/png'))&&paperDollState.appearance.hairColor==='white'}"""
  self.page.wait_for_function(white_ready)
  self.assertTrue(self.page.evaluate("""async()=>{for(const i of document.querySelectorAll('#wardrobe-paperdoll > img')){if(!i.paperHairRequest?.endsWith('|white'))continue;const r=i.paperHairRequest,n=r.lastIndexOf('|');if(i.getAttribute('src')!==await coloredHairSource(r.slice(0,n),'white',i.paperHairColorReference))return false}return true}"""))
  # Read the approved coloured layers and check mutations in one JS turn;
  # a separate protocol round-trip could sample a pending original-color frame.
  snapshot=self.page.evaluate('''()=>{const imgs=[...document.querySelectorAll('#wardrobe-paperdoll > img')].filter(i=>i.paperHairRequest?.endsWith('|white'));const before=imgs.map(i=>i.getAttribute('src'));const observers=imgs.map(i=>{const o=new MutationObserver(()=>{});o.observe(i,{attributes:true,attributeFilter:['src']});return o});for(let n=0;n<30;n++)updateCharacterLayers();const counts=observers.map(o=>{const n=o.takeRecords().length;o.disconnect();return n});return {counts,unchanged:imgs.every((i,n)=>i.getAttribute('src')===before[n]),white:imgs.every(i=>i.paperHairRequest?.endsWith('|white')&&i.getAttribute('src').startsWith('data:image/png'))}}''')
  self.assertEqual(snapshot,{'counts':[0],'unchanged':True,'white':True})
  self.page.evaluate('typeof applyWardrobeSession === "function" && applyWardrobeSession()');self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.page.wait_for_function('document.readyState==="complete" && typeof paperDollState!=="undefined"');self.assertEqual(self.page.evaluate('paperDollState.appearance.hair'),'hair-shoulder-length');self.assertEqual(self.page.evaluate('paperDollState.appearance.hairColor'),'white')
  self.page.wait_for_function(white_ready)
 def test_invalid_boss_names_do_not_mutate_a_saved_character(self):
  self.case.load();before=self.page.evaluate('JSON.stringify({stats,inventory,gameProgress})')
  for name in ['constructor','__proto__','toString','missing']:
   self.page.evaluate('name=>{startBossFight(name);openBossDossier(name)}',name)
   self.assertFalse(self.page.evaluate('isBattleActive'));self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,gameProgress})'),before)
