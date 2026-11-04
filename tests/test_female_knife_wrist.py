"""Restore the authored female knife wrist, independent of idle and rifle art."""
import base64,hashlib,io,json,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from tests import test_beards_weapons as support
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review/female-knife-wrist-20261105'
class FemaleKnifeWristAssets(unittest.TestCase):
    def test_restored_authored_layers_keep_historical_bytes(self):
        for source in json.loads((REVIEW/'sources.json').read_text())['files']:
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        self.assertEqual(hashlib.sha256((ROOT/'base_female.png').read_bytes()).hexdigest(),'a27b499c03fc15c4788ae3a651483a36463f28b1f034178feccdaa852e7e50f9')
class FemaleKnifeWristBrowser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):support.BeardWeaponBrowserTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):support.BeardWeaponBrowserTests.tearDownClass.__func__(cls)
    setUp=support.BeardWeaponBrowserTests.setUp
    tearDown=support.BeardWeaponBrowserTests.tearDown
    load=support.BeardWeaponBrowserTests.load
    ready=support.BeardWeaponBrowserTests.ready
    start=support.BeardWeaponBrowserTests.start
    def test_wrist_and_closed_grip_survive_weapon_changes_and_reload(self):
        self.start();self.page.evaluate('setGender("female");equipPaperDollItem("face",null)');self.ready()
        neutral=self.page.evaluate('''()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();return e.canvas.toDataURL().split(',')[1]}''')
        base=Image.open(io.BytesIO(base64.b64decode(neutral))).convert('RGBA')
        expected=np.array(Image.open(REVIEW/'restored-wrist-reference.png').convert('RGBA'))
        for weapon,pose in [('gear-knife','melee'),('gear-aks','rifle'),(None,'idle'),('gear-knife','melee')]:
            self.page.evaluate('w=>equipPaperDollItem("weapon",w)',weapon);self.ready(pose)
            if pose!='melee':continue
            raw=self.page.evaluate('''()=>{const e=avatarCoreGamePreview.instances.get(document.getElementById('wardrobe-paperdoll')).engine;e.pause();e.time=0;e.render();return e.canvas.toDataURL().split(',')[1]}''')
            image=Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGBA')
            self.assertTrue(np.array_equal(np.array(image.crop((155,780,410,980))),expected),'Closed-hand knife wrist was replaced or shifted')
            self.assertTrue(np.array_equal(np.array(image.crop((450,1000,900,1600))),np.array(base.crop((450,1000,900,1600)))),'Other arm/legs changed')
        self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready('melee')
        self.page.evaluate('equipPaperDollItem("weapon",null)');self.ready()
