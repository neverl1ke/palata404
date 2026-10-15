"""Browser regressions: python3 -m unittest discover -s tests -v.

Uses an isolated local server and browser profile; external services are blocked.
Set PALATA_BROWSER_PATH to use a system Chromium instead of Playwright's browser.
"""
import functools
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import unittest
import xml.etree.ElementTree as ET
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PATIENT_TUNIC_IMAGES = {
    'male': 'assets/wardrobe/clothing/patient/patient_tunic_male.png?v=28343fe9',
    'female': 'assets/wardrobe/clothing/patient/patient_tunic_female.png?v=fa3fac64',
}


class IconAssetTests(unittest.TestCase):
    def test_patient_tunic_revised_release_integrity_and_transparency(self):
        expected_blobs = {
            'male': '28343fe90d876c7d785d0093d4f34fc3a5148a36',
            'female': 'fa3fac64dac856654ec4cf9eb9da72af05f1cc21',
        }
        for gender, source in PATIENT_TUNIC_IMAGES.items():
            with self.subTest(gender=gender):
                path = ROOT / source.split('?')[0]
                data = path.read_bytes()
                blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
                self.assertEqual(blob, expected_blobs[gender])
                with Image.open(path) as image:
                    self.assertEqual(image.format, 'PNG')
                    self.assertEqual(image.size, (941, 1672))
                    self.assertEqual(image.mode, 'RGBA')
                    alpha = image.getchannel('A')
                    self.assertEqual(alpha.getextrema(), (0, 255))
                    self.assertIsNotNone(alpha.getbbox())
                    self.assertGreater(alpha.histogram()[0], image.width * image.height / 2)

    def test_approved_neckline_underlay_and_bases_keep_exact_bytes(self):
        expected = {
            'assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png': 'cc9a05ce4b177122eeac62bdb3138b070904656f',
            'base_male.png': '0dec17c1c1713c00bca182bd71ca0ecb2ca1f0e0',
            'base_female.png': '5489c78c31011a0e87bf133e4c78d8053eff4b27',
        }
        for source, sha in expected.items():
            with self.subTest(source=source):
                data = (ROOT/source).read_bytes()
                self.assertEqual(hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest(), sha)
                with Image.open(ROOT/source) as image:
                    self.assertEqual(image.size, (941, 1672))
                    self.assertEqual(image.mode, 'RGBA')
                    self.assertEqual(image.getchannel('A').getextrema()[0], 0)

    def test_first_patient_shirt_drafts_are_real_transparent_pngs(self):
        for gender in ['male','female']:
            with self.subTest(gender=gender),Image.open(ROOT/f'assets/wardrobe/drafts/hospital_shirt_{gender}.png') as image:
                self.assertEqual(image.format,'PNG')
                self.assertEqual(image.size,(982,1602) if gender=='male' else (941,1670))
                self.assertEqual(image.mode,'RGBA')
                alpha=image.getchannel('A')
                self.assertEqual(alpha.getextrema(),(0,255))
                self.assertGreater(alpha.histogram()[0],image.width*image.height/2)
                bounds=alpha.point(lambda value:255 if value>=64 else 0).getbbox()
                self.assertGreater(bounds[1],300)
                self.assertLess(bounds[3],1250)

    def test_approved_body_pngs_have_real_alpha_and_match_the_new_frame(self):
        for name in ['base_male.png','base_female.png']:
            with self.subTest(image=name), Image.open(ROOT/name) as image:
                self.assertEqual(image.size,(941,1672))
                self.assertEqual(image.mode,'RGBA')
                alpha=image.getchannel('A')
                self.assertEqual(alpha.getextrema(),(0,255))
                histogram=alpha.histogram()
                self.assertGreater(histogram[0],image.width*image.height/2)
                self.assertGreater(sum(histogram[240:]),image.width*image.height/4)
                bounds=alpha.point(lambda value:255 if value>=64 else 0).getbbox()
                self.assertLess(abs((bounds[0]+bounds[2])/2-image.width/2),image.width*0.02)

    def test_approved_wardrobe_backgrounds_are_valid_matching_scenes(self):
        for name in ['wardrobe_background.png','wardrobe_background_v2.png']:
            with self.subTest(image=name), Image.open(ROOT/name) as image:
                self.assertEqual(image.format,'PNG')
                self.assertEqual(image.size,(1448,1086))
                self.assertIn(image.mode,['RGB','RGBA'])
                image.verify()

    def test_svg_assets_are_self_contained_and_valid(self):
        paths = sorted((ROOT / 'assets' / 'icons').glob('*.svg'))
        self.assertGreater(len(paths), 50)
        for path in paths:
            with self.subTest(icon=path.name):
                svg = ET.parse(path).getroot()
                self.assertEqual(svg.tag, '{http://www.w3.org/2000/svg}svg')
                self.assertEqual(svg.attrib['viewBox'], '0 0 64 64')
                for node in svg.iter():
                    self.assertNotIn(node.tag.split('}')[-1], ['script', 'text', 'foreignObject', 'image'])
                    self.assertFalse(any('href' in key for key in node.attrib))


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}/'
        cls.playwright = sync_playwright().start()
        options = {'headless': True}
        if os.getenv('PALATA_BROWSER_PATH'):
            options['executable_path'] = os.environ['PALATA_BROWSER_PATH']
        cls.browser = cls.playwright.chromium.launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 800})
        self.context.add_init_script('Math.random=()=>0.5;')
        self.context.route('https://**/*', lambda route: route.abort())
        self.errors = []
        self.page = self.context.new_page()
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.on('dialog', lambda dialog: dialog.accept())

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [], 'Unexpected browser runtime errors')

    def load(self, saves=None, query=''):
        if saves:
            self.context.add_init_script(
                'if (!sessionStorage.getItem("seeded")) {'
                f'for (const [key, value] of Object.entries({json.dumps(saves)})) '
                'localStorage.setItem(key, value);'
                'sessionStorage.setItem("seeded", "1"); }')
        self.page.goto(self.url + query, wait_until='networkidle')
        self.assertNotEqual(self.page.locator('#player-name').inner_text(), 'Завантаження...')

    def register_face_fixtures(self):
        data=(ROOT/'paper-doll-data.js').read_text()+"\nPAPER_DOLL_ITEMS.push(...Array.from({length:6},(_,i)=>({id:`fixture-face-${i+1}`,slot:'face',name:`Approved fixture ${i+1}`,image:`face_${i+1}.png`,availableByDefault:true,placement:{x:364,y:32,width:220,height:218}})));"
        self.context.route('**/paper-doll-data.js?*',lambda route:route.fulfill(content_type='application/javascript',body=data))

    def wardrobe_action(self, item_id, action):
        self.page.locator(f'[data-wardrobe-card="{item_id}"]').click()
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name=action,exact=True).click()

    def state(self):
        return self.page.evaluate('({...stats})')

    def equip(self, name):
        self.page.evaluate('(name) => { openInventory(); openItemInfo(inventory.find(i => i.name === name)); }', name)
        self.page.locator('#item-action-btn').click()

    def use(self, name):
        self.equip(name)

    def test_local_resources_markup_and_event_handlers(self):
        self.load()
        duplicates = self.page.evaluate('''() => {
            const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
            return ids.filter((id, index) => ids.indexOf(id) !== index);
        }''')
        self.assertEqual(duplicates, [])
        handlers = self.page.evaluate(r'''() => [...document.querySelectorAll('[onclick]')]
            .flatMap(e => [...e.getAttribute('onclick').matchAll(/\b([A-Za-z_$][\w$]*)\s*\(/g)])
            .map(m => m[1]).filter(name => !['stopPropagation'].includes(name))
            .filter(name => typeof window[name] !== 'function')''')
        self.assertEqual(handlers, [])
        for name in re.findall(r"[\w-]+\.(?:png|jpg)", '\n'.join(
                (ROOT / file).read_text() for file in ['index.html', 'style.css', 'script.js'])):
            if name == '_dossier_card.png':  # Filename is composed from the canonical boss key.
                continue
            self.assertTrue((ROOT / name).is_file(), name)
        self.assertEqual(self.page.evaluate('''() => [...document.images]
            .filter(img => img.getAttribute('src') && (!img.complete || !img.naturalWidth))
            .map(img => img.getAttribute('src'))'''), [])

    def test_corrupt_saves_and_denied_storage_do_not_break_boot(self):
        self.load({
            'palata404_stats': '{invalid', 'palata404_inventory': 'null',
            'palata404_equipped': '[]', 'palata404_friends': '{}',
            'palata404_gym': '{"exercises":null,"completedRounds":-5}',
            'palata404_progress': 'false', 'palata404_boss_kills': 'null',
            'palata404_gender': '../../missing', 'palata404_face': 'missing.png',
        })
        self.assertEqual(self.state()['hp'], 100)
        self.assertEqual(self.page.locator('#layer-body').get_attribute('src'), 'base_male.png?v=0dec17c1')
        self.page.evaluate('openInventory(); openGym(); openDossier();')
        self.context.add_init_script('''Object.defineProperty(window, 'localStorage', {
            get() { throw new DOMException('Storage unavailable', 'SecurityError'); }
        });''')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['damage'], 10)
        self.page.evaluate('openGym(); doGymExercise("squats"); updateEnergyTimer();')
        self.assertEqual(self.state()['energy'], 98)

    def test_untrusted_text_stays_text(self):
        attack = '<img src=x onerror="window.injected=true">'
        self.load({
            'palata404_nickname': attack,
            'palata404_friends': json.dumps([{'identifier': attack, 'status': attack}]),
            'palata404_inventory': json.dumps([{
                'name': attack, 'icon': attack, 'desc': attack, 'category': 'mod', 'count': 1}]),
        })
        self.assertEqual(self.page.locator('#player-name').inner_text(), attack)
        self.page.evaluate('openFriends()')
        self.assertEqual(self.page.locator('#friends-list img').count(), 0)
        self.page.evaluate('openInventory(); openItemInfo(inventory[0]);')
        self.assertEqual(self.page.locator('#item-info-body img').count(), 0)
        self.assertFalse(self.page.evaluate('Boolean(window.injected)'))

    def test_future_approved_face_survives_reload(self):
        self.register_face_fixtures()
        self.load()
        self.page.evaluate('openCustomization(); setGender("female"); equipPaperDollItem("face","fixture-face-3");')
        self.assertEqual(self.page.locator('#layer-face').get_attribute('src'), 'face_3.png')
        self.page.locator('#layer-face').wait_for(state='visible')
        self.assertTrue(self.page.locator('#layer-face').is_visible())
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.locator('#layer-body').get_attribute('src'), 'base_female.png?v=5489c78c')
        self.assertEqual(self.page.locator('#layer-face').get_attribute('src'), 'face_3.png')

    def test_paper_doll_ui_keeps_two_loadouts_and_shared_appearance_across_reload(self):
        self.load()
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        self.page.evaluate('openCustomization()')
        wardrobe=self.page.locator('#custom-modal')
        self.assertEqual(wardrobe.locator('select').count(),0)
        self.assertEqual(wardrobe.locator('[data-wardrobe-category]').count(),5)
        wardrobe.get_by_role('button',name='Жінка',exact=True).click()
        wardrobe.locator('[data-wardrobe-slot="face"]').click()
        self.assertEqual(wardrobe.locator('[data-wardrobe-card]').count(),0)
        self.assertIn('Базове обличчя',wardrobe.locator('#wardrobe-container').inner_text())
        for prefix in ['', 'wardrobe-']:
            self.assertIsNone(self.page.locator(f'#{prefix}layer-face').get_attribute('src'))
        wardrobe.locator('[data-wardrobe-category="gear"]').click()
        wardrobe.locator('[data-wardrobe-slot="armor"]').click()
        card=wardrobe.locator('[data-wardrobe-card="gear-br1"]')
        self.assertIn('Зображення не підготовлено',card.inner_text())
        self.assertTrue(card.locator('.game-icon').is_visible())
        card.click()
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name='Надягнути',exact=True).click()
        self.assertIn('ЕКІПІРОВАНО',card.inner_text())
        self.assertIn('на моделі не видно',card.inner_text())
        self.assertIn('на персонажі він не відображається',self.page.locator('#wardrobe-item-detail').inner_text())
        self.assertIsNone(self.page.locator('#layer-armor').get_attribute('src'))
        wardrobe.get_by_role('button',name='Трип',exact=True).click()
        self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'))
        self.assertEqual(self.page.evaluate('paperDollState.combatLoadout.armor'),None)
        wardrobe.locator('[data-wardrobe-category="weapons"]').click()
        self.assertEqual(wardrobe.locator('[data-wardrobe-card]').count(),3)
        self.wardrobe_action('gear-pm','Надягнути')
        wardrobe.get_by_role('button',name='Пацієнт',exact=True).click()
        self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.weapon'),None)
        wardrobe.locator('[data-wardrobe-category="gear"]').click()
        wardrobe.locator('[data-wardrobe-slot="armor"]').click()
        self.wardrobe_action('gear-br1','Зняти')
        wardrobe.get_by_role('button',name='Трип',exact=True).click()
        self.assertEqual(self.page.evaluate('paperDollState.combatLoadout.weapon'),'gear-pm')
        state=self.page.evaluate('JSON.stringify(paperDollState)')
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('JSON.stringify(paperDollState)'),state)
        self.assertEqual(self.page.locator('#layer-body').get_attribute('src'),'base_female.png?v=5489c78c')
        self.assertIsNone(self.page.locator('#layer-face').get_attribute('src'))
        self.assertEqual(self.page.locator('#paper-doll-view-label').inner_text(),'Комплект: Трип')
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        self.page.evaluate("PAPER_DOLL_ITEMS.push({id:'future-face',slot:'face',name:'Архівне обличчя',image:'face_1.png',availableByDefault:true}); openCustomization(); setWardrobeTab('face');")
        card=wardrobe.locator('[data-wardrobe-card="future-face"]')
        self.assertEqual(card.locator('img:not(.game-icon)').get_attribute('src'),'face_1.png')
        card.click()
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name='Обрати',exact=True).click()
        self.assertEqual(self.page.evaluate('paperDollState.appearance.face'),'future-face')
        self.assertEqual(self.page.locator('#layer-face').get_attribute('src'),'face_1.png')

    def assert_patient_tunic_layers(self, gender):
        source = PATIENT_TUNIC_IMAGES[gender]
        self.page.wait_for_function('''source => ['layer-upper-body-front', 'wardrobe-layer-upper-body-front'].every(id => {
            const image = document.getElementById(id);
            return image.getAttribute('src') === source && image.naturalWidth === 941
                && image.naturalHeight === 1672 && !image.classList.contains('hidden');
        })''', arg=source)
        for prefix in ['', 'wardrobe-']:
            layer = self.page.locator(f'#{prefix}layer-upper-body-front')
            self.assertTrue(layer.is_visible())
            self.assertEqual(layer.evaluate('e=>getComputedStyle(e).objectFit'), 'contain')
            self.assertEqual(layer.evaluate('e=>getComputedStyle(e).zIndex'), '3')
            body = self.page.locator(f'#{prefix}layer-body')
            self.assertEqual(body.get_attribute('src'),
                'base_female.png?v=5489c78c' if gender == 'female' else 'base_male.png?v=0dec17c1')
            self.assertEqual(body.evaluate('e=>[e.naturalWidth,e.naturalHeight]'), [941, 1672])
            for node in [body, layer]:
                self.assertEqual(node.evaluate('e=>[e.style.left,e.style.top,e.style.width,e.style.height]'), ['0%', '0%', '100%', '100%'])
            neckline = self.page.locator(f'#{prefix}layer-upper-body-neckline')
            if gender == 'female':
                self.page.wait_for_function('''id=>{const image=document.getElementById(id);return image&&image.complete
                    &&image.naturalWidth===941&&!image.classList.contains('hidden')}''',arg=prefix+'layer-upper-body-neckline')
                self.assertEqual(neckline.get_attribute('src'), 'assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png?v=cc9a05ce')
                self.assertEqual(neckline.evaluate('e=>getComputedStyle(e).zIndex'), '2')
            else:
                self.assertEqual(neckline.count(), 0)

    def test_patient_tunic_starter_and_independent_loadouts_survive_equip_unequip_reload(self):
        self.load()
        before = self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.upperBody'), 'patient-tunic')
        self.assertIsNone(self.page.evaluate('paperDollState.combatLoadout.upperBody'))
        self.page.get_by_role('button', name='Гардероб', exact=True).click()
        wardrobe = self.page.locator('#custom-modal')
        wardrobe.locator('[data-wardrobe-category="clothes"]').click()
        card = wardrobe.locator('[data-wardrobe-card="patient-tunic"]')
        self.assertEqual(card.get_attribute('data-available'), 'true')
        self.assertEqual(card.get_attribute('data-equipped'), 'true')
        self.assertFalse(wardrobe.locator('[data-wardrobe-empty]').count())
        self.assert_patient_tunic_layers('male')
        # Inspection cannot equip, unequip, or persist any new state.
        saved = self.page.evaluate('JSON.stringify({...localStorage})')
        outfit = self.page.evaluate('JSON.stringify(paperDollState)')
        card.click()
        self.assertEqual(self.page.evaluate('JSON.stringify({...localStorage})'), saved)
        self.assertEqual(self.page.evaluate('JSON.stringify(paperDollState)'), outfit)
        self.wardrobe_action('patient-tunic', 'Зняти')
        for prefix in ['', 'wardrobe-']:
            self.assertEqual(self.page.locator(f'#{prefix}layer-upper-body-front').count(), 0)
        self.page.reload(wait_until='networkidle')
        self.assertIsNone(self.page.evaluate('paperDollState.patientLoadout.upperBody'))
        self.assertIsNone(self.page.evaluate('paperDollState.combatLoadout.upperBody'))
        self.page.get_by_role('button', name='Гардероб', exact=True).click()
        wardrobe.locator('[data-wardrobe-category="clothes"]').click()
        self.wardrobe_action('patient-tunic', 'Надягнути')
        wardrobe.get_by_role('button', name='Трип', exact=True).click()
        self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.upperBody'), 'patient-tunic')
        self.assertIsNone(self.page.evaluate('paperDollState.combatLoadout.upperBody'))
        self.assertEqual(self.page.locator('#wardrobe-layer-upper-body-front').count(), 0)
        self.wardrobe_action('patient-tunic', 'Надягнути')
        wardrobe.locator('[data-wardrobe-category="appearance"]').click()
        wardrobe.get_by_role('button', name='Жінка', exact=True).click()
        wardrobe.locator('[data-wardrobe-category="clothes"]').click()
        self.assert_patient_tunic_layers('female')
        wardrobe.get_by_role('button', name='Пацієнт', exact=True).click()
        self.wardrobe_action('patient-tunic', 'Зняти')
        self.assertIsNone(self.page.evaluate('paperDollState.patientLoadout.upperBody'))
        self.assertEqual(self.page.evaluate('paperDollState.combatLoadout.upperBody'), 'patient-tunic')
        wardrobe.get_by_role('button', name='Трип', exact=True).click()
        self.assert_patient_tunic_layers('female')
        outfit = self.page.evaluate('JSON.stringify(paperDollState)')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('JSON.stringify(paperDollState)'), outfit)
        self.page.get_by_role('button', name='Гардероб', exact=True).click()
        self.assert_patient_tunic_layers('female')
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), before)

    def test_patient_tunic_preserves_existing_explicitly_empty_outfits(self):
        self.load({'palata404_paper_doll': json.dumps({
            'schemaVersion': 2, 'selectedGender': 'female', 'activeViewMode': 'patient',
            'appearance': {'face': None, 'hair': ''}, 'patientLoadout': {}, 'combatLoadout': {},
        })})
        self.page.get_by_role('button', name='Гардероб', exact=True).click()
        wardrobe = self.page.locator('#custom-modal')
        wardrobe.locator('[data-wardrobe-category="clothes"]').click()
        for name in ['Пацієнт', 'Трип']:
            wardrobe.get_by_role('button', name=name, exact=True).click()
            self.assertEqual(wardrobe.locator('[data-wardrobe-card="patient-tunic"]').get_attribute('data-equipped'), 'false')
            self.assertTrue(wardrobe.locator('#wardrobe-item-detail').get_by_role('button', name='Надягнути', exact=True).is_enabled())
            for prefix in ['', 'wardrobe-']:
                self.assertEqual(self.page.locator(f'#{prefix}layer-upper-body-front').count(), 0)
        self.page.reload(wait_until='networkidle')
        self.assertIsNone(self.page.evaluate('paperDollState.patientLoadout.upperBody'))
        self.assertIsNone(self.page.evaluate('paperDollState.combatLoadout.upperBody'))

    def test_patient_tunic_real_catalog_fit_in_both_scenes_genders_modes_and_viewports(self):
        self.load()
        before = self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        bounds = {}
        for gender, source in PATIENT_TUNIC_IMAGES.items():
            with Image.open(ROOT / source.split('?')[0]) as image:
                bounds[gender] = image.getchannel('A').point(lambda value: 255 if value >= 64 else 0).getbbox()
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        self.page.get_by_role('button', name='Гардероб', exact=True).click()
        wardrobe = self.page.locator('#custom-modal')
        for width, height in [(1280, 800), (1920, 1080), (390, 844), (320, 568), (844, 390)]:
            self.page.set_viewport_size({'width': width, 'height': height})
            for gender, gender_label in [('male', 'Чоловік'), ('female', 'Жінка')]:
                wardrobe.locator('[data-wardrobe-category="appearance"]').click()
                wardrobe.get_by_role('button', name=gender_label, exact=True).click()
                wardrobe.locator('[data-wardrobe-category="clothes"]').click()
                for mode, mode_label in [('patient', 'Пацієнт'), ('combat', 'Трип')]:
                    with self.subTest(viewport=(width, height), gender=gender, mode=mode):
                        wardrobe.get_by_role('button', name=mode_label, exact=True).click()
                        self.assertEqual(wardrobe.get_attribute('data-wardrobe-theme'), 'trip' if mode == 'combat' else 'patient')
                        self.assertEqual(wardrobe.locator('[data-wardrobe-card]').count(), 1)
                        card = wardrobe.locator('[data-wardrobe-card="patient-tunic"]')
                        self.assertEqual(card.get_attribute('data-available'), 'true')
                        self.assertEqual(card.locator('img:not(.game-icon)').get_attribute('src'), PATIENT_TUNIC_IMAGES[gender])
                        saved = self.page.evaluate('JSON.stringify({...localStorage})')
                        card.click()
                        self.assertEqual(self.page.evaluate('JSON.stringify({...localStorage})'), saved)
                        action = wardrobe.locator('[data-wardrobe-action="patient-tunic"]')
                        self.assertTrue(action.is_enabled())
                        action.scroll_into_view_if_needed()
                        box = action.bounding_box()
                        self.assertGreaterEqual(box['height'], 44)
                        self.assertGreaterEqual(box['y'], 0)
                        self.assertLessEqual(box['y'] + box['height'], height)
                        if action.inner_text() == 'Надягнути':
                            action.click()
                        self.assertEqual(wardrobe.locator('[data-wardrobe-action="patient-tunic"]').inner_text(), 'Зняти')
                        self.assert_patient_tunic_layers(gender)
                        self.assertEqual(card.locator('[data-paper-image-item]:visible').count(), 0)
                        self.assertEqual(wardrobe.locator('#wardrobe-item-detail [data-paper-image-item]:visible').count(), 0)
                        # Transparent source margins may extend outside a host.
                        # Project only real clothing pixels through object-fit.
                        projected = self.page.evaluate('''bounds => {
                            const box = e => { const r=e.getBoundingClientRect(); return {x:r.x,y:r.y,width:r.width,height:r.height}; };
                            return ['', 'wardrobe-'].map(prefix => {
                                const image = document.getElementById(prefix+'layer-upper-body-front');
                                const host = box(document.getElementById(prefix ? 'wardrobe-paperdoll' : 'character-paperdoll'));
                                const rect = box(image), scale = Math.min(rect.width/image.naturalWidth, rect.height/image.naturalHeight);
                                const left=rect.x+(rect.width-image.naturalWidth*scale)/2, top=rect.y+(rect.height-image.naturalHeight*scale)/2;
                                return {host, visible:{x:left+bounds[0]*scale,y:top+bounds[1]*scale,width:(bounds[2]-bounds[0])*scale,height:(bounds[3]-bounds[1])*scale}};
                            });
                        }''', bounds[gender])
                        normalized = []
                        for entry in projected:
                            host, garment = entry['host'], entry['visible']
                            self.assertGreater(host['width'], 10)
                            self.assertAlmostEqual(host['width'] / host['height'], 941 / 1672, delta=.002)
                            self.assertGreaterEqual(garment['x'], host['x'] - 1)
                            self.assertGreaterEqual(garment['y'], host['y'] - 1)
                            self.assertLessEqual(garment['x'] + garment['width'], host['x'] + host['width'] + 1)
                            self.assertLessEqual(garment['y'] + garment['height'], host['y'] + host['height'] + 1)
                            self.assertGreater(garment['width'], host['width'] * .2)
                            self.assertGreater(garment['height'], host['height'] * .15)
                            normalized.append([(garment['x']-host['x'])/host['width'], (garment['y']-host['y'])/host['height'], garment['width']/host['width'], garment['height']/host['height']])
                        for actual, expected in zip(*normalized):
                            self.assertAlmostEqual(actual, expected, delta=.005)
                        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                        if width in [1280, 390]:
                            name = f'patient-tunic-{mode}-{gender}-{width}x{height}'
                            self.page.screenshot(path=str(results / f'{name}-wardrobe.png'))
                            if width == 1280 and os.getenv('GITHUB_ACTIONS') == 'true':
                                preview = wardrobe.locator('.wardrobe-stage').screenshot(type='jpeg', quality=65)
                                print('PATIENT_TUNIC_PREVIEW:' + json.dumps({'name':name+'-wardrobe','jpeg':base64.b64encode(preview).decode()},separators=(',',':')),flush=True)
                            wardrobe.get_by_role('button', name='Закрити гардероб', exact=True).click()
                            self.page.locator('#character-paperdoll').scroll_into_view_if_needed()
                            self.page.screenshot(path=str(results / f'{name}-main.png'))
                            if width == 1280 and os.getenv('GITHUB_ACTIONS') == 'true':
                                preview = self.page.locator('#character-paperdoll').screenshot(type='jpeg', quality=65)
                                print('PATIENT_TUNIC_PREVIEW:' + json.dumps({'name':name+'-main','jpeg':base64.b64encode(preview).decode()},separators=(',',':')),flush=True)
                            self.page.get_by_role('button', name='Гардероб', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), before)

    def test_paper_doll_layers_share_canvas_and_keep_faces_aligned_on_mobile(self):
        self.register_face_fixtures()
        self.load()
        self.assertEqual(self.page.locator('#character-paperdoll > img:not([data-paper-extra])').count(),13)
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for gender in ['male','female']:
                    self.page.evaluate('g=>{setGender(g); equipPaperDollItem("face","fixture-face-1")}',gender)
                    self.page.wait_for_function('()=>["layer-body","layer-face"].every(id=>document.getElementById(id).naturalWidth>0&&!document.getElementById(id).classList.contains("hidden"))')
                    # Read the three boxes in one frame: responsive HUD buttons
                    # transition during orientation changes and move the scene.
                    boxes=self.page.evaluate('''() => Object.fromEntries(['character-paperdoll','layer-body','layer-face'].map(id=>{
                        const r=document.getElementById(id).getBoundingClientRect();
                        return [id,{x:r.x,y:r.y,width:r.width,height:r.height}];
                    }))''')
                    host,body,face=[boxes[id] for id in ['character-paperdoll','layer-body','layer-face']]
                    self.assertGreater(host['width'],30)
                    self.assertAlmostEqual(host['width']/host['height'],941/1672,delta=0.005)
                    for coordinate in ['x','y','width','height']:
                        self.assertAlmostEqual(body[coordinate],host[coordinate],delta=1)
                    self.assertGreaterEqual(face['x'],host['x'])
                    self.assertLessEqual(face['x']+face['width'],host['x']+host['width'])
                    self.assertLessEqual(face['y']+face['height'],host['y']+host['height']*0.2)
                    self.assertGreaterEqual(host['x'],0)
                    self.assertLessEqual(host['x']+host['width'],width)
                    expected_visible = 4 if gender == 'female' else 3
                    self.page.wait_for_function('''count=>document.querySelectorAll('#character-paperdoll img:not(.hidden)').length===count''',arg=expected_visible)
                    self.assertEqual(self.page.locator('#character-paperdoll img:not(.hidden)').count(),expected_visible)
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                    self.page.screenshot(path=str(results/f'paper-doll-{gender}-{width}x{height}.png'))
        self.page.evaluate('''() => {
            PAPER_DOLL_ITEMS.push({id:'fixture-pants',slot:'pants',name:'Fixture',availableByDefault:true,image:'base_male.png'},
                {id:'fixture-upper',slot:'upperBody',name:'Fixture',availableByDefault:true,image:'base_male.png'});
            equipPaperDollItem('pants','fixture-pants'); equipPaperDollItem('upperBody','fixture-upper');
        }''')
        self.page.wait_for_function('()=>["layer-pants","layer-upper-body"].every(id=>document.getElementById(id).naturalWidth>0)')
        body=self.page.locator('#layer-body').bounding_box()
        for layer,z in [('layer-pants',1),('layer-upper-body',3)]:
            image=self.page.locator(f'#{layer}')
            box=image.bounding_box()
            for coordinate in ['x','y','width','height']:
                self.assertAlmostEqual(box[coordinate],body[coordinate],delta=1)
            self.assertEqual(image.evaluate('e=>getComputedStyle(e).zIndex'),str(z))
        self.page.evaluate('equipPaperDollItem("pants",null); equipPaperDollItem("upperBody",null);')
        self.assertEqual(self.page.locator('#character-paperdoll img:not(.hidden)').count(),2)

    def test_paper_doll_missing_png_falls_back_or_hides_without_broken_images(self):
        self.load()
        requests=[]
        self.context.route('**/paper-missing*.png',lambda route:(requests.append(route.request.url),route.fulfill(status=404,body='')))
        self.page.evaluate('''() => {
            PAPER_DOLL_ITEMS.push({id:'fixture-fallback',slot:'headwear',name:'Fixture',availableByDefault:true,
                genderVariants:{female:'paper-missing-female.png',male:'face_1.png'}},
                {id:'fixture-missing',slot:'weapon',name:'Fixture',availableByDefault:true,image:'paper-missing-weapon.png'});
            setGender('female'); equipPaperDollItem('headwear','fixture-fallback'); equipPaperDollItem('weapon','fixture-missing');
        }''')
        self.page.wait_for_function('()=>document.getElementById("layer-headwear").getAttribute("src")==="face_1.png"&&document.getElementById("layer-headwear").naturalWidth>0')
        self.page.wait_for_function('()=>!document.getElementById("layer-weapon").hasAttribute("src")')
        self.assertFalse(self.page.locator('#layer-weapon').is_visible())
        self.assertTrue(self.page.locator('#layer-body').is_visible())
        count=len(requests)
        self.page.evaluate('updateCharacterLayers(); updateCharacterLayers(); openCustomization(); selectWardrobeCategory("weapons");')
        self.assertEqual(len(set(requests)),2)
        self.assertEqual(len(requests),count)
        self.assertTrue(self.page.locator('[data-wardrobe-card="fixture-missing"] [data-paper-image-item]').is_visible())
        self.assertIn('на персонажі він не відображається',self.page.locator('#wardrobe-item-detail').inner_text())
        self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.weapon'),'fixture-missing')
        # A failed part must update the already open detail, even if another
        # part loaded successfully. No outfit or inventory changes on failure.
        self.page.evaluate('''()=>{
            PAPER_DOLL_ITEMS.push({id:'fixture-partial',slot:'outerwear',name:'Fixture',availableByDefault:true,
                layers:[{id:'rear',image:'base_female.png',renderOrder:-1},{id:'front',image:'paper-missing-front.png'}]});
            selectWardrobeCategory('clothes');selectWardrobeSlot('outerwear');equipPaperDollItem('outerwear','fixture-partial');
        }''')
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})')
        self.page.wait_for_function('()=>document.querySelector("#wardrobe-item-detail [data-paper-graphics=partial]")')
        self.assertIn('видно лише доступні частини',self.page.locator('#wardrobe-item-detail').inner_text())
        self.page.locator('#wardrobe-layer-outerwear-rear').wait_for(state='visible')
        self.assertFalse(self.page.locator('#wardrobe-layer-outerwear-front').is_visible())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})'),before)

    def test_wide_wardrobe_keeps_preview_inside_and_scrolls_item_panel_on_mobile(self):
        self.register_face_fixtures()
        self.load()
        self.page.evaluate('openCustomization(); equipPaperDollItem("face","fixture-face-4"); setWardrobeTab("face");')
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.wait_for_function('()=>document.getElementById("wardrobe-layer-body").naturalWidth>0&&document.getElementById("wardrobe-layer-face").naturalWidth>0')
                boxes=self.page.evaluate('''() => Object.fromEntries(['wardrobe-paperdoll','wardrobe-layer-body','wardrobe-layer-face'].map(id=>{
                    const r=document.getElementById(id).getBoundingClientRect(); return [id,{x:r.x,y:r.y,width:r.width,height:r.height}];
                }))''')
                host,body,face=[boxes[id] for id in ['wardrobe-paperdoll','wardrobe-layer-body','wardrobe-layer-face']]
                self.assertGreater(host['height'],100)
                self.assertAlmostEqual(host['width']/host['height'],941/1672,delta=0.01)
                for coordinate in ['x','y','width','height']:
                    self.assertAlmostEqual(body[coordinate],host[coordinate],delta=1)
                self.assertGreaterEqual(host['y'],0)
                self.assertLessEqual(host['y']+host['height'],height+1)
                self.assertGreaterEqual(host['x'],0)
                self.assertLessEqual(host['x']+host['width'],width)
                self.assertLessEqual(face['y']+face['height'],host['y']+host['height']*0.2)
                document=self.page.locator('.wardrobe-document')
                self.assertLessEqual(document.bounding_box()['height'],height*.9+1)
                self.assertLessEqual(document.evaluate('e=>e.scrollHeight-e.clientHeight'),1)
                self.assertEqual(self.page.locator('[data-wardrobe-slot]').count(),2)
                self.assertEqual(self.page.locator('#wardrobe-layer-face').get_attribute('src'),self.page.locator('#layer-face').get_attribute('src'))
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                self.page.screenshot(path=str(results/f'wide-wardrobe-{width}x{height}.png'))
        self.wardrobe_action('fixture-face-2','Обрати')
        self.assertEqual(self.page.evaluate('document.activeElement.dataset.wardrobeFocus'),'action-fixture-face-2')
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('#custom-modal').is_visible())
        self.assertEqual(self.page.locator('#layer-face').get_attribute('src'),'face_2.png')

    def test_wardrobe_inventory_ownership_and_old_appearance_migration(self):
        self.load({'palata404_inventory':'[]','palata404_paper_doll':json.dumps({'schemaVersion':1,'selectedGender':'female','activeViewMode':'combat',
            'patientLoadout':{'face':'face_1.png','armor':'sample-armor'},'combatLoadout':{'face':'face_5.png','weapon':'sample-weapon'}})})
        self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'))
        self.assertEqual(self.page.evaluate('paperDollState.legacyFaces.patient'),'face_1.png')
        self.page.evaluate('openCustomization(); selectWardrobeCategory("weapons");')
        self.assertEqual(self.page.locator('[data-wardrobe-card][data-available="false"]').count(),3)
        self.assertTrue(self.page.locator('[data-wardrobe-action]').is_disabled())
        self.assertFalse(self.page.evaluate('equipPaperDollItem("weapon","gear-pm")'))
        self.assertEqual(self.page.evaluate('inventory.length'),0)
        self.page.evaluate('setPaperDollView("patient"); selectWardrobeCategory("appearance"); selectWardrobeSlot("face");')
        self.assertIsNone(self.page.locator('#wardrobe-layer-face').get_attribute('src'))
        self.assertEqual(self.page.locator('[data-wardrobe-card]').count(),0)

    def test_wardrobe_complex_layers_update_both_views_and_clean_up_after_removal(self):
        self.load()
        self.page.evaluate('''() => {
            PAPER_DOLL_ITEMS.push({id:'complex-fixture',slot:'back',name:'Fixture',availableByDefault:true,layers:[
                {id:'rear',image:'base_male.png',renderOrder:-1},
                {id:'front',image:'face_1.png',renderOrder:12,placement:{x:364,y:32,width:220,height:218}}]});
            openCustomization(); selectWardrobeCategory('gear'); selectWardrobeSlot('back');
        }''')
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        card=self.page.locator('[data-wardrobe-card="complex-fixture"]')
        card.click()
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name='Надягнути',exact=True).click()
        for prefix in ['', 'wardrobe-']:
            self.page.wait_for_function('p=>["rear","front"].every(part=>document.getElementById(p+"layer-back-"+part)?.naturalWidth>0)',arg=prefix)
            self.assertEqual(self.page.locator(f'#{prefix}layer-back-rear').evaluate('e=>getComputedStyle(e).zIndex'),'-1')
            self.assertEqual(self.page.locator(f'#{prefix}layer-back-front').evaluate('e=>getComputedStyle(e).zIndex'),'12')
        card.click()
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name='Зняти',exact=True).click()
        for prefix in ['', 'wardrobe-']:
            self.assertEqual(self.page.locator(f'#{prefix}layer-back-rear, #{prefix}layer-back-front').count(),0)
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)

    def test_approved_avatars_show_native_faces_in_both_views_and_switch_to_trip(self):
        self.load()
        self.page.evaluate('equipPaperDollItem("face",null); openCustomization();')
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})')
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            for gender in ['male','female']:
                with self.subTest(viewport=(width,height),gender=gender):
                    self.page.evaluate('g=>{setGender(g);openCustomization()}',gender)
                    self.page.wait_for_function('()=>["layer-body","wardrobe-layer-body"].every(id=>document.getElementById(id).naturalWidth===941&&document.getElementById(id).naturalHeight===1672)')
                    for prefix in ['', 'wardrobe-']:
                        # Both genders have identical dimensions; naturalWidth
                        # can still describe the previous PNG while src changes.
                        self.page.locator(f'#{prefix}layer-body').wait_for(state='visible')
                        self.assertTrue(self.page.locator(f'#{prefix}layer-body').is_visible())
                        self.assertFalse(self.page.locator(f'#{prefix}layer-face').is_visible())
                    self.assertEqual(self.page.locator('#layer-body').get_attribute('src'),self.page.locator('#wardrobe-layer-body').get_attribute('src'))
                    self.page.screenshot(path=str(results/f'approved-{gender}-wardrobe-{width}x{height}.png'))
                    self.page.evaluate('closeCustomization()')
                    self.page.locator('#character-paperdoll').scroll_into_view_if_needed()
                    self.assertTrue(self.page.locator('#layer-body').is_visible())
                    self.page.screenshot(path=str(results/f'approved-{gender}-room-{width}x{height}.png'))
        self.page.evaluate('openCustomization()')
        self.assertEqual(self.page.locator('.wardrobe-view-switch button').all_text_contents(),['Пацієнт','Трип'])
        self.page.locator('.wardrobe-view-switch').get_by_role('button',name='Трип',exact=True).click()
        self.assertEqual(self.page.evaluate('paperDollState.activeViewMode'),'combat')
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('paperDollState.activeViewMode'),'combat')
        self.assertIn('Трип',self.page.locator('#paper-doll-view-label').inner_text())

    def test_registration_room_identity_modes_monitor_and_mobile_geometry(self):
        nickname='<img src=x onerror="window.injected=true">'
        self.load({'palata404_nickname':nickname,'palata404_web_id':'WEB-482716'})
        self.page.evaluate('openCustomization()')
        self.assertEqual(self.page.locator('#wardrobe-patient-name').inner_text(),nickname)
        self.assertEqual(self.page.locator('#wardrobe-patient-case').inner_text(),'WEB-482716')
        self.assertEqual(self.page.locator('.wardrobe-registration-plate img').count(),0)
        self.page.evaluate('playerName="Новий пацієнт"; renderWardrobe();')
        self.assertEqual(self.page.locator('#wardrobe-patient-name').inner_text(),'Новий пацієнт')
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        colors=[]
        results=ROOT/'test-results'; results.mkdir(exist_ok=True)
        for mode in ['patient','combat']:
            self.page.evaluate('mode=>setPaperDollView(mode)',mode)
            self.assertEqual(self.page.locator('#wardrobe-registration').get_attribute('data-view'),mode)
            colors.append(self.page.locator('.wardrobe-stage').evaluate('e=>getComputedStyle(e).backgroundImage'))
            self.assertNotEqual(self.page.locator('.wardrobe-monitor-light').evaluate('e=>getComputedStyle(e).animationName'),'none')
            for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
                self.page.set_viewport_size({'width':width,'height':height})
                for gender in ['male','female']:
                    self.page.evaluate('g=>setGender(g)',gender)
                    self.page.wait_for_function('()=>document.getElementById("wardrobe-layer-body").naturalWidth===941')
                    boxes=self.page.evaluate('''()=>Object.fromEntries(['wardrobe-registration','.wardrobe-stage','wardrobe-paperdoll','.wardrobe-registration-plate','.wardrobe-monitor'].map(key=>{
                        const e=key.startsWith('.')?document.querySelector(key):document.getElementById(key);const r=e.getBoundingClientRect();return[key,{x:r.x,y:r.y,width:r.width,height:r.height}];
                    }))''')
                    panel,stage,body,plate,monitor=[boxes[key] for key in ['wardrobe-registration','.wardrobe-stage','wardrobe-paperdoll','.wardrobe-registration-plate','.wardrobe-monitor']]
                    self.assertGreater(body['height'],100)
                    self.assertAlmostEqual(body['width']/body['height'],941/1672,delta=.01)
                    self.assertGreaterEqual(body['y'],stage['y']-1)
                    self.assertLessEqual(body['y']+body['height'],stage['y']+stage['height']+1)
                    self.assertLessEqual(body['y']+body['height'],plate['y'])
                    self.assertLessEqual(monitor['y']+monitor['height'],panel['y']+panel['height'])
                    self.assertEqual(self.page.locator('#wardrobe-paperdoll').evaluate('e=>getComputedStyle(e).filter'),'none')
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                    self.page.screenshot(path=str(results/f'registration-{mode}-{gender}-{width}x{height}.png'))
        self.assertNotEqual(colors[0],colors[1])
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        self.page.emulate_media(reduced_motion='reduce')
        for mode in ['patient','combat']:
            self.page.evaluate('mode=>setPaperDollView(mode)',mode)
            self.assertEqual(self.page.locator('.wardrobe-monitor-light').evaluate('e=>getComputedStyle(e).animationName'),'none')
        self.page.set_viewport_size({'width':320,'height':360})
        self.page.locator('[data-wardrobe-category="weapons"]').click()
        self.wardrobe_action('gear-pm','Надягнути')
        self.assertEqual(self.page.evaluate('paperDollState.combatLoadout.weapon'),'gear-pm')
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),320)
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('#custom-modal').is_visible())

    def test_approved_wardrobe_background_loads_with_one_shared_floor_anchor(self):
        self.load()
        self.page.evaluate('openCustomization()')
        self.assertEqual(self.page.locator('.wardrobe-height-scale').count(),0)
        self.assertEqual(self.page.locator('.wardrobe-stage img:not(.char-layer)').count(),0)
        backgrounds=[]
        for gender,mode in [('male','patient'),('female','patient'),('female','combat'),('male','combat')]:
            self.page.evaluate('''({gender,mode})=>{setGender(gender);setPaperDollView(mode)}''',{'gender':gender,'mode':mode})
            scene=self.page.locator('.wardrobe-stage').evaluate('''e=>{const s=getComputedStyle(e);return{image:s.backgroundImage,size:s.backgroundSize,position:s.backgroundPosition,repeat:s.backgroundRepeat,height:e.clientHeight}}''')
            backgrounds.append(re.search(r'url\([^)]+\)',scene['image']).group())
            expected='wardrobe_background_v2.png?v=639ad612' if mode=='combat' else 'wardrobe_background.png?v=d490c304'
            self.assertIn(expected,scene['image'])
            decoded=self.page.evaluate('''src=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve([image.naturalWidth,image.naturalHeight]);image.onerror=()=>reject(new Error('Background PNG did not load: '+src));image.src=src;})''',expected)
            self.assertEqual(decoded,[1448,1086])
            self.assertEqual([value.strip() for value in scene['size'].split(',')],['100% 100%','auto 100%'])
            self.assertTrue(all(value.strip()=='50% 100%' for value in scene['position'].split(',')))
            self.assertTrue(all(value.strip()=='no-repeat' for value in scene['repeat'].split(',')))
            floor_gap=self.page.locator('#wardrobe-paperdoll').evaluate('e=>parseFloat(getComputedStyle(e).marginBottom)')
            self.assertAlmostEqual(floor_gap,scene['height']*.05,delta=1)
        self.assertEqual(len(set(backgrounds)),2)
        self.assertEqual(backgrounds[0],backgrounds[1])
        self.assertEqual(backgrounds[2],backgrounds[3])
        self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'))

    def test_ground_shadow_tracks_the_shared_frame_without_gender_or_loadout_jumps(self):
        self.load()
        self.page.evaluate('openCustomization()')
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        results=ROOT/'test-results'; results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            previous=None
            for gender,mode,gear in [('male','patient',None),('female','patient',None),('female','combat','gear-br1'),('male','combat','gear-br1')]:
                self.page.evaluate('''({gender,mode,gear})=>{setGender(gender);setPaperDollView(mode);equipPaperDollItem('armor',gear)}''',{'gender':gender,'mode':mode,'gear':gear})
                self.page.wait_for_function('()=>document.getElementById("wardrobe-layer-body").naturalWidth===941')
                data=self.page.evaluate('''()=>{
                    const selectors=['.wardrobe-stage','#wardrobe-paperdoll','.wardrobe-ground-shadow','.wardrobe-shadow-base','.wardrobe-shadow-contact'];
                    return Object.fromEntries(selectors.map(key=>{const e=document.querySelector(key),r=e.getBoundingClientRect(),s=getComputedStyle(e);return[key,{x:r.x,y:r.y,width:r.width,height:r.height,opacity:s.opacity,zIndex:s.zIndex,pointerEvents:s.pointerEvents,animation:s.animationName,background:s.backgroundImage}]}));
                }''')
                stage,frame,group,base,contact=[data[key] for key in ['.wardrobe-stage','#wardrobe-paperdoll','.wardrobe-ground-shadow','.wardrobe-shadow-base','.wardrobe-shadow-contact']]
                self.assertEqual(self.page.locator('#wardrobe-paperdoll > .wardrobe-ground-shadow').count(),1)
                self.assertEqual(self.page.locator('.wardrobe-ground-shadow').get_attribute('aria-hidden'),'true')
                self.assertEqual(group['zIndex'],'-101')
                self.assertGreater(base['width'],contact['width'])
                self.assertGreater(base['height'],contact['height'])
                self.assertGreater(float(contact['opacity']),float(base['opacity']))
                for shadow in [base,contact]:
                    self.assertEqual(shadow['pointerEvents'],'none')
                    self.assertEqual(shadow['animation'],'none')
                    self.assertIn('radial-gradient',shadow['background'])
                    self.assertLess(float(shadow['opacity']),.4)
                    self.assertAlmostEqual(shadow['x']+shadow['width']/2,frame['x']+frame['width']/2,delta=1)
                    self.assertGreaterEqual(shadow['x'],stage['x'])
                    self.assertGreaterEqual(shadow['y'],frame['y']+frame['height']*.94)
                    self.assertLessEqual(shadow['y']+shadow['height'],stage['y']+stage['height'])
                self.assertAlmostEqual(base['width']/frame['width'],.72,delta=.01)
                self.assertAlmostEqual(contact['width']/base['width'],.58,delta=.01)
                if previous:
                    for key in ['#wardrobe-paperdoll','.wardrobe-ground-shadow','.wardrobe-shadow-base','.wardrobe-shadow-contact']:
                        for coordinate in ['x','y','width','height']:
                            self.assertAlmostEqual(previous[key][coordinate],data[key][coordinate],delta=1)
                previous=data
                self.page.screenshot(path=str(results/f'ground-shadow-{gender}-{mode}-{width}x{height}.png'))
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'))
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),320)

    def test_wardrobe_themes_change_all_columns_keep_contrast_and_restore_after_reload(self):
        self.load()
        self.page.evaluate('openCustomization()')
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        snapshots=[]
        for mode,theme in [('patient','patient'),('combat','trip')]:
            self.page.evaluate('mode=>setPaperDollView(mode)',mode)
            self.assertEqual(self.page.locator('#custom-modal').get_attribute('data-wardrobe-theme'),theme)
            self.assertEqual(self.page.locator('#wardrobe-registration').get_attribute('data-view'),mode)
            snapshots.append(self.page.evaluate('''()=>Object.fromEntries(['.wardrobe-document','.wardrobe-category[aria-pressed="true"]','.wardrobe-slot[aria-pressed="true"]','.wardrobe-gender-switch button[aria-pressed="true"]','.wardrobe-registration-plate','.wardrobe-view-switch button[aria-pressed="true"]'].map(selector=>{const s=getComputedStyle(document.querySelector(selector));return[selector,{color:s.color,background:s.backgroundColor,image:s.backgroundImage,border:s.borderColor}]}))'''))
            # Test the actual inherited foreground against every solid gradient
            # endpoint (or nearest opaque ancestor), rather than only one swatch.
            contrast=self.page.evaluate(r'''()=>{
                const rgb=text=>{const values=text.match(/[\d.]+/g)?.map(Number);return values?.length>=3?values:null};
                const luminance=color=>color.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
                const backgrounds=e=>{if(!e)return[];const s=getComputedStyle(e);const colors=[s.backgroundColor,...s.backgroundImage.matchAll(/rgba?\([^)]+\)/g)].map(x=>rgb(typeof x==='string'?x:x[0])).filter(x=>x&&(x[3]??1)===1);return colors.length?colors:backgrounds(e.parentElement)};
                const selectors=['.wardrobe-header h3','.wardrobe-header .staff-section-code','.wardrobe-section-label','.wardrobe-category[aria-pressed="true"]','.wardrobe-slot[aria-pressed="true"]','.wardrobe-gender-switch button','.wardrobe-appearance-note h4','.wardrobe-appearance-note p','.wardrobe-appearance-note .wardrobe-item-state','.wardrobe-registration-title','.wardrobe-registration-plate','.wardrobe-monitor'];
                return selectors.flatMap(selector=>[...document.querySelectorAll(selector)].map(e=>{const f=luminance(rgb(getComputedStyle(e).color));return{selector,minimum:Math.min(...backgrounds(e).map(c=>{const b=luminance(c);return(Math.max(f,b)+.05)/(Math.min(f,b)+.05)}))}}));
            }''')
            for sample in contrast:
                self.assertGreaterEqual(sample['minimum'],4.5,(theme,sample))
        for selector in snapshots[0]:
            self.assertNotEqual(snapshots[0][selector],snapshots[1][selector],selector)
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openCustomization()')
        self.assertEqual(self.page.locator('#custom-modal').get_attribute('data-wardrobe-theme'),'trip')
        self.assertEqual(self.page.evaluate('paperDollState.activeViewMode'),'combat')
        self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'))
        self.page.locator('[data-wardrobe-category="gear"]').click()
        self.page.locator('[data-wardrobe-slot="armor"]').click()
        self.wardrobe_action('gear-br1','Надягнути')
        self.assertEqual(self.page.evaluate('paperDollState.combatLoadout.armor'),'gear-br1')
        self.wardrobe_action('gear-br1','Зняти')
        self.assertIsNone(self.page.evaluate('paperDollState.combatLoadout.armor'))
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            for mode in ['patient','combat']:
                self.page.evaluate('mode=>setPaperDollView(mode)',mode)
                boxes=self.page.evaluate('''()=>{const scene=document.querySelector('.wardrobe-stage').getBoundingClientRect(),body=document.getElementById('wardrobe-paperdoll').getBoundingClientRect();return{scene:{y:scene.y,height:scene.height},body:{y:body.y,height:body.height}}}''')
                self.assertGreaterEqual(boxes['body']['y']-boxes['scene']['y'],boxes['scene']['height']*.10-1)
                self.assertLessEqual(boxes['body']['y']+boxes['body']['height'],boxes['scene']['y']+boxes['scene']['height'])
                self.assertGreater(boxes['body']['height'],100)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)

    def test_wardrobe_v3_has_a_large_stage_compact_gender_switch_and_independent_inspection(self):
        self.load()
        self.page.set_viewport_size({'width':1440,'height':900})
        self.page.evaluate('openCustomization()')
        self.assertEqual(self.page.locator('.wardrobe-body-card').count(),0)
        self.assertEqual(self.page.locator('#wardrobe-gender-switch button').count(),2)
        document=self.page.locator('.wardrobe-document').bounding_box()
        self.assertGreaterEqual(document['width'],1120*1.15)
        self.assertLessEqual(document['width'],1120*1.2)
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})')
        saved=self.page.evaluate('JSON.stringify({...localStorage})')
        self.page.locator('[data-wardrobe-category="weapons"]').click()
        self.page.locator('[data-wardrobe-card="gear-pm"]').click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})'),before)
        self.assertEqual(self.page.evaluate('JSON.stringify({...localStorage})'),saved)
        self.assertIn('ПМ',self.page.locator('#wardrobe-detail-title').inner_text())
        self.assertGreater(len(self.page.locator('.wardrobe-detail-description').inner_text()),10)
        self.assertEqual(self.page.locator('#wardrobe-container [data-wardrobe-action]').count(),0)
        self.assertEqual(self.page.locator('#wardrobe-item-detail [data-wardrobe-action]').count(),1)
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name='Надягнути',exact=True).click()
        self.assertEqual(self.page.locator('[data-wardrobe-card="gear-pm"]').get_attribute('data-equipped'),'true')
        self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.weapon'),'gear-pm')
        self.assertIn('ЕКІПІРОВАНО',self.page.locator('#wardrobe-item-detail').inner_text())
        self.page.locator('#wardrobe-item-detail').get_by_role('button',name='Зняти',exact=True).click()
        self.assertIsNone(self.page.evaluate('paperDollState.patientLoadout.weapon'))
        results=ROOT/'test-results';results.mkdir(exist_ok=True)
        for width,height in [(2560,1440),(1920,1080),(1440,900),(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.evaluate('selectWardrobeCategory("appearance")')
            for mode in ['patient','combat']:
                for gender in ['male','female']:
                    self.page.evaluate('''({mode,gender})=>{setPaperDollView(mode);setGender(gender)}''',{'mode':mode,'gender':gender})
                    self.page.wait_for_function('()=>document.getElementById("wardrobe-layer-body").naturalWidth===941')
                    boxes=self.page.evaluate('''()=>{const selectors=['.wardrobe-document','.wardrobe-stage','#wardrobe-paperdoll','.wardrobe-gender-switch','.wardrobe-items'];return Object.fromEntries(selectors.map(key=>{const r=document.querySelector(key).getBoundingClientRect();return[key,{x:r.x,y:r.y,width:r.width,height:r.height}]}))}''')
                    doc,scene,body,switch,right=[boxes[key] for key in ['.wardrobe-document','.wardrobe-stage','#wardrobe-paperdoll','.wardrobe-gender-switch','.wardrobe-items']]
                    self.assertLessEqual(doc['height'],height*.9+1)
                    self.assertGreaterEqual(doc['x'],0)
                    self.assertLessEqual(doc['x']+doc['width'],width)
                    if width>=1500:
                        self.assertGreaterEqual(doc['width']/width,.80)
                        self.assertLessEqual(doc['width']/width,.85)
                    self.assertGreaterEqual(body['y']-scene['y'],scene['height']*.10-1)
                    self.assertGreaterEqual(body['x']-scene['x'],scene['width']*.06-1)
                    self.assertLessEqual(body['x']+body['width'],scene['x']+scene['width']*.94+1)
                    self.assertAlmostEqual(body['width']/body['height'],941/1672,delta=.01)
                    self.assertGreater(body['height'],100)
                    if width>=1280:self.assertGreater(body['height'],450)
                    self.assertLessEqual(switch['height'],54)
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                    self.page.screenshot(path=str(results/f'wardrobe-v3-{mode}-{gender}-{width}x{height}.png'))
            self.page.evaluate('selectWardrobeCategory("weapons");selectWardrobeItem("gear-pm");')
            self.page.locator('[data-wardrobe-action]').scroll_into_view_if_needed()
            action=self.page.locator('[data-wardrobe-action]').bounding_box()
            self.assertGreaterEqual(action['y'],0)
            self.assertLessEqual(action['y']+action['height'],height)
            self.page.screenshot(path=str(results/f'wardrobe-v3-items-{width}x{height}.png'))
        self.page.emulate_media(reduced_motion='reduce')
        self.assertEqual(self.page.locator('[data-wardrobe-card="gear-pm"]').evaluate('e=>getComputedStyle(e).transitionDuration'),'0s')

    def test_wardrobe_final_ux_empty_clothes_and_functional_text_in_both_themes(self):
        self.load()
        self.page.evaluate('openCustomization()')
        results=ROOT/'test-results';results.mkdir(exist_ok=True)
        before=self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})')
        for width,height in [(1920,1080),(768,1024),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            for mode in ['patient','combat']:
                self.page.evaluate('mode=>{setPaperDollView(mode);selectWardrobeCategory("clothes");selectWardrobeSlot("outerwear")}',mode)
                empty=self.page.locator('[data-wardrobe-empty]')
                self.assertTrue(empty.is_visible())
                if mode=='patient':self.assertIn('Лікарняний одяг',empty.inner_text())
                self.assertEqual(self.page.locator('[data-wardrobe-card]').count(),0)
                self.assertEqual(self.page.locator('[data-wardrobe-action]').count(),0)
                self.assertFalse(self.page.locator('#wardrobe-item-detail').is_visible())
                self.page.screenshot(path=str(results/f'wardrobe-final-empty-{mode}-{width}x{height}.png'))
                self.page.evaluate('selectWardrobeCategory("weapons");selectWardrobeItem("gear-pm")')
                sizes=self.page.evaluate('''()=>Object.fromEntries(['.wardrobe-category','.wardrobe-slot','.wardrobe-item-name','.wardrobe-detail-slot','.wardrobe-detail-description','.wardrobe-item-detail .report-button','.wardrobe-item-state','.wardrobe-image-note'].map(selector=>[selector,parseFloat(getComputedStyle(document.querySelector(selector)).fontSize)]))''')
                for selector,size in sizes.items():
                    minimum=12 if selector in ['.wardrobe-item-state','.wardrobe-image-note'] else 13 if width<=950 or selector=='.wardrobe-detail-slot' else 14
                    self.assertGreaterEqual(size,minimum,(width,mode,selector))
                contrast=self.page.evaluate(r'''()=>{
                    const rgb=t=>t.match(/[\d.]+/g).map(Number);
                    const lum=c=>c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
                    const backgrounds=e=>{const s=getComputedStyle(e),colors=[s.backgroundColor,...s.backgroundImage.matchAll(/rgba?\([^)]+\)/g)].map(x=>rgb(typeof x==='string'?x:x[0])).filter(c=>(c[3]??1)===1);return colors.length?colors:backgrounds(e.parentElement)};
                    return ['.wardrobe-item-name','.wardrobe-item-state','.wardrobe-image-note','.wardrobe-detail-description','.wardrobe-detail-slot','.wardrobe-item-detail .report-button'].flatMap(selector=>[...document.querySelectorAll(selector)].map(e=>{const f=lum(rgb(getComputedStyle(e).color));return{selector,ratio:Math.min(...backgrounds(e).map(c=>{const b=lum(c);return(Math.max(f,b)+.05)/(Math.min(f,b)+.05)}))}}));
                }''')
                for sample in contrast:self.assertGreaterEqual(sample['ratio'],4.5,(mode,sample))
                self.page.locator('[data-wardrobe-action]').scroll_into_view_if_needed()
                action=self.page.locator('[data-wardrobe-action]').bounding_box()
                self.assertGreaterEqual(action['height'],44)
                self.assertGreaterEqual(action['y'],0)
                self.assertLessEqual(action['y']+action['height'],height)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before)
        self.page.evaluate('inventory=[];renderWardrobe()')
        self.assertIn('Немає доступних предметів',self.page.locator('[data-wardrobe-empty]').inner_text())
        self.assertEqual(self.page.locator('[data-wardrobe-card]').count(),3)
        self.assertTrue(self.page.locator('[data-wardrobe-action]').is_disabled())

    def test_wardrobe_scale_matches_room_height_and_keeps_full_layer_canvas(self):
        self.load()
        self.page.evaluate('openCustomization()')
        results=ROOT/'test-results';results.mkdir(exist_ok=True)
        metrics=[]
        bounds={}
        for gender in ['male','female']:
            with Image.open(ROOT/f'base_{gender}.png') as image:
                bounds[gender]=image.getchannel('A').point(lambda value:255 if value>=64 else 0).getbbox()
        for width,height in [(1280,800),(1920,1080)]:
            self.page.set_viewport_size({'width':width,'height':height})
            for mode in ['patient','combat']:
                for gender in ['male','female']:
                    self.page.evaluate('''({mode,gender})=>{setPaperDollView(mode);setGender(gender)}''',{'mode':mode,'gender':gender})
                    self.page.wait_for_function('()=>document.getElementById("wardrobe-layer-body").naturalWidth===941')
                    boxes=self.page.evaluate('''()=>Object.fromEntries(['.wardrobe-stage','#wardrobe-paperdoll','.wardrobe-index','.wardrobe-items'].map(selector=>{const r=document.querySelector(selector).getBoundingClientRect();return[selector,{x:r.x,y:r.y,width:r.width,height:r.height}]}))''')
                    scene,frame,left,right=[boxes[key] for key in ['.wardrobe-stage','#wardrobe-paperdoll','.wardrobe-index','.wardrobe-items']]
                    visible_height=frame['height']*(bounds[gender][3]-bounds[gender][1])/1672/scene['height']
                    headroom=(frame['y']+frame['height']*bounds[gender][1]/1672-scene['y'])/scene['height']
                    feet=(frame['y']+frame['height']*bounds[gender][3]/1672-scene['y'])/scene['height']
                    self.assertGreaterEqual(visible_height,.82)
                    self.assertLessEqual(visible_height,.85)
                    self.assertGreaterEqual(headroom,.10)
                    self.assertLessEqual(headroom,.12)
                    self.assertGreaterEqual(feet,.93)
                    self.assertLessEqual(feet,.96)
                    self.assertGreaterEqual(scene['width']/scene['height'],.70)
                    self.assertLessEqual(scene['width']/scene['height'],1.05)
                    self.assertGreaterEqual(left['width'],180)
                    self.assertGreaterEqual(right['width'],300)
                    self.assertAlmostEqual(frame['width']/frame['height'],941/1672,delta=.001)
                    self.assertGreaterEqual(frame['x']-scene['x'],scene['width']*.06-1)
                    self.assertLessEqual(frame['x']+frame['width'],scene['x']+scene['width']*.94+1)
                    name=f'wardrobe-scale-{mode}-{gender}-{width}x{height}'
                    self.page.screenshot(path=str(results/f'{name}.png'))
                    metrics.append({'name':name,'scene':scene,'frame':frame,'visible_height':visible_height,'headroom':headroom,'feet':feet})
                    # Small, unedited browser crops allow remote visual review
                    # from job logs; the full-resolution PNGs stay in artifacts.
                    if os.getenv('GITHUB_ACTIONS')=='true':
                        preview=self.page.locator('.wardrobe-stage').screenshot(type='jpeg',quality=35)
                        print('WARDROBE_SCALE_PREVIEW:'+json.dumps({'name':name,'jpeg':base64.b64encode(preview).decode()},separators=(',',':')),flush=True)
        (results/'wardrobe-scale-metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))
        # Existing renderer: front and rear parts share the body's entire frame.
        self.page.evaluate('''()=>{
            PAPER_DOLL_ITEMS.push({id:'scale-fixture',slot:'back',name:'Fixture',availableByDefault:true,
                layers:[{id:'rear',image:'base_female.png',renderOrder:-1},{id:'front',image:'base_female.png',renderOrder:12}]});
            equipPaperDollItem('back','scale-fixture');
        }''')
        for prefix in ['', 'wardrobe-']:
            body=self.page.locator(f'#{prefix}layer-body').bounding_box()
            for part,order in [('rear','-1'),('front','12')]:
                layer=self.page.locator(f'#{prefix}layer-back-{part}')
                layer.wait_for(state='visible')
                box=layer.bounding_box()
                for coordinate in ['x','y','width','height']:self.assertAlmostEqual(box[coordinate],body[coordinate],delta=1)
                self.assertEqual(layer.evaluate('e=>getComputedStyle(e).zIndex'),order)

    def test_patient_shirt_art_preview_uses_unchanged_bases_and_preserves_game_saves(self):
        self.load()
        saved=self.page.evaluate('JSON.stringify({...localStorage})')
        self.page.goto(self.url+'art/hospital-shirt.html',wait_until='networkidle')
        self.assertEqual(self.page.locator('article').count(),2)
        for gender in ['male','female']:
            article=self.page.locator(f'[data-gender="{gender}"]')
            self.assertEqual(article.locator('.body').evaluate('e=>[e.naturalWidth,e.naturalHeight]'),[941,1672])
            self.assertEqual(article.locator('.shirt').evaluate('e=>[e.naturalWidth,e.naturalHeight]'),[982,1602] if gender=='male' else [941,1670])
            frame=article.locator('.frame').bounding_box()
            self.assertAlmostEqual(frame['width']/frame['height'],941/1672,delta=.001)
            self.assertEqual(article.locator('.shirt').evaluate('e=>getComputedStyle(e).objectFit'),'contain')
        # Canonical points that used to show bare shoulder or rear cuff fabric.
        # Project through the actual DOM image boxes, not a copied CSS offset.
        for gender in ['male','female']:
            with self.subTest(shirt_fit=gender):
                coverage=self.page.locator(f'[data-gender="{gender}"]').evaluate('''article=>{
                    const gender=article.dataset.gender,frame=article.querySelector('.frame').getBoundingClientRect();
                    const layers=['body','shirt'].map(name=>{const image=article.querySelector('.'+name),canvas=document.createElement('canvas');canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;const context=canvas.getContext('2d');context.drawImage(image,0,0);return{rect:image.getBoundingClientRect(),pixels:context.getImageData(0,0,canvas.width,canvas.height).data,width:image.naturalWidth,height:image.naturalHeight}});
                    const read=([x,y])=>layers.map(layer=>{const px=Math.round((frame.x+x/941*frame.width-layer.rect.x)/layer.rect.width*layer.width),py=Math.round((frame.y+y/1672*frame.height-layer.rect.y)/layer.rect.height*layer.height);return px>=0&&py>=0&&px<layer.width&&py<layer.height?layer.pixels[(py*layer.width+px)*4+3]:0});
                    const runs=(y,layer)=>{
                        const result=[];let start=null;
                        for(let x=0;x<=941;x++){
                            const opaque=x<941&&read([x,y])[layer]>=128;
                            if(opaque&&start===null)start=x;
                            if(!opaque&&start!==null){if(x-start>=3)result.push([start,x-1]);start=null;}
                        }
                        return result;
                    };
                    const edges=(y,layer)=>{const row=runs(y,layer);return row.length?[row[0][0],row.at(-1)[1]]:null;};
                    const contour=[];
                    for(let y=gender==='male'?440:400;y<=(gender==='male'?475:430);y+=5)contour.push({y,body:edges(y,0),cloth:edges(y,1)});
                    const armCoverage=[0,1].map(side=>{
                        let covered=0,total=0;
                        for(let y=gender==='male'?370:350;y<=(gender==='male'?450:410);y+=10){
                            const body=edges(y,0),start=side===0?body[0]:body[1]-59;
                            for(let x=start;x<start+60;x++){const [skin,cloth]=read([x,y]);if(skin>=200){total++;if(cloth>=200)covered++;}}
                        }
                        return{covered,total};
                    });
                    const collar=[];
                    for(let y=260;y<=(gender==='male'?280:290);y+=5)collar.push({y,body:edges(y,0),cloth:edges(y,1)});
                    const shoulder=gender==='male'?[[632,310],[654,320],[670,330]]:[[293,320],[304,330],[647,320],[660,330]];
                    const cuffs=gender==='male'?[[242,524],[258,530],[277,539],[700,531],[675,545],[660,551]]:[[279,472],[308,480],[331,490],[668,472],[643,480],[639,490]];
                    return{shoulder:shoulder.map(read),cuffs:cuffs.map(read),contour,armCoverage,collar};
                }''')
                for body,cloth in coverage['shoulder']:
                    self.assertGreaterEqual(body,200)
                    self.assertGreaterEqual(cloth,240)
                for body,cloth in coverage['cuffs']:
                    self.assertGreaterEqual(body,200)
                    self.assertLessEqual(cloth,5)
                # Constrain the entire lower sleeve edge, so wing-shaped cuffs
                # cannot pass by merely covering a few selected arm pixels.
                for row in coverage['contour']:
                    self.assertIsNotNone(row['body'],row)
                    self.assertIsNotNone(row['cloth'],row)
                    body_left,body_right=row['body'];cloth_left,cloth_right=row['cloth']
                    self.assertGreaterEqual(cloth_left,body_left-18,row)
                    self.assertLessEqual(cloth_left,body_left+3,row)
                    self.assertGreaterEqual(cloth_right,body_right-3,row)
                    self.assertLessEqual(cloth_right,body_right+18,row)
                for arm in coverage['armCoverage']:
                    self.assertGreater(arm['total'],0)
                    self.assertGreaterEqual(arm['covered']/arm['total'],.85)
                for row in coverage['collar']:
                    if row['cloth'] is None:
                        continue
                    self.assertGreaterEqual(row['cloth'][0],row['body'][0]-8,row)
                    self.assertLessEqual(row['cloth'][1],row['body'][1]+8,row)
        results=ROOT/'test-results';results.mkdir(exist_ok=True)
        self.page.set_viewport_size({'width':1280,'height':1000})
        for mode in ['patient','combat']:
            self.page.locator(f'button[data-mode="{mode}"]').click()
            self.assertEqual(self.page.locator('body').get_attribute('data-mode'),mode)
            self.page.evaluate('''mode=>new Promise((resolve,reject)=>{const image=new Image();image.onload=resolve;image.onerror=()=>reject(new Error('Preview background failed'));image.src=mode==='combat'?'../wardrobe_background_v2.png?v=639ad612':'../wardrobe_background.png?v=d490c304';})''',mode)
            self.page.screenshot(path=str(results/f'patient-shirt-art-{mode}-1280x1000.png'))
            if os.getenv('GITHUB_ACTIONS')=='true':
                for gender in ['male','female']:
                    preview=self.page.locator(f'[data-gender="{gender}"] .scene').screenshot(type='jpeg',quality=60)
                    print('PATIENT_SHIRT_ART_PREVIEW:'+json.dumps({'name':f'patient-shirt-{gender}-{mode}','jpeg':base64.b64encode(preview).decode()},separators=(',',':')),flush=True)
        self.assertEqual(self.page.evaluate('JSON.stringify({...localStorage})'),saved)
        self.page.set_viewport_size({'width':390,'height':844})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),390)
        self.page.screenshot(path=str(results/'patient-shirt-art-phone.png'),full_page=True)
        # Inspect actual source-scale shoulder/cuff geometry, not a tiny sprite.
        self.page.set_viewport_size({'width':1280,'height':1200})
        self.page.evaluate('''()=>{
            document.querySelector('.models').style.gridTemplateColumns='941px';
            document.querySelectorAll('article[data-gender]').forEach(article=>{
                article.querySelector('.scene').style.height='1968px';
                article.querySelector('.frame').style.height='1672px';
            });
        }''')
        for gender in ['male','female']:
            self.page.evaluate('''gender=>document.querySelectorAll('article[data-gender]').forEach(article=>{
                article.style.display=article.dataset.gender===gender?'':'none';
            })''',gender)
            for mode in ['patient','combat']:
                self.page.locator(f'button[data-mode="{mode}"]').click()
                self.page.evaluate('''mode=>new Promise((resolve,reject)=>{const image=new Image();image.onload=resolve;image.onerror=()=>reject(new Error('Preview background failed'));image.src=mode==='combat'?'../wardrobe_background_v2.png?v=639ad612':'../wardrobe_background.png?v=d490c304';})''',mode)
                frame=self.page.locator(f'[data-gender="{gender}"] .frame').bounding_box()
                clip={'x':frame['x']+140,'y':frame['y']+240,'width':660,'height':340}
                self.page.screenshot(path=str(results/f'{gender}-shirt-fit-detail-{mode}.png'),clip=clip)
                if os.getenv('GITHUB_ACTIONS')=='true':
                    preview=self.page.screenshot(type='jpeg',quality=85,clip=clip)
                    print('PATIENT_SHIRT_ART_DETAIL:'+json.dumps({'name':f'{gender}-shirt-fit-detail-{mode}','jpeg':base64.b64encode(preview).decode()},separators=(',',':')),flush=True)

    def test_approved_tunic_composite_matches_supplied_overlay_reference_in_both_views(self):
        reference = json.loads((ROOT/'tests/fixtures/patient-tunic-approved.json').read_text())
        self.load()
        self.page.evaluate('openCustomization()')
        for gender in ['male', 'female']:
            self.page.evaluate('g=>setGender(g)', gender)
            for mode in ['patient', 'combat']:
                self.page.evaluate('mode=>{setPaperDollView(mode);equipPaperDollItem("upperBody","patient-tunic")}', mode)
                self.assert_patient_tunic_layers(gender)
                for prefix in ['', 'wardrobe-']:
                    with self.subTest(gender=gender, mode=mode, view=prefix or 'main'):
                        failures = self.page.evaluate('''({prefix,samples})=>{
                            const host=document.getElementById(prefix?'wardrobe-paperdoll':'character-paperdoll');
                            const box=host.getBoundingClientRect();
                            const canvas=document.createElement('canvas');canvas.width=941;canvas.height=1672;
                            const context=canvas.getContext('2d');
                            const layers=[...host.querySelectorAll('img')].filter(image=>image.naturalWidth>0
                                &&!image.classList.contains('hidden')).sort((a,b)=>Number(a.style.zIndex)-Number(b.style.zIndex));
                            for(const image of layers){
                                const r=image.getBoundingClientRect();
                                if(Math.abs(r.x-box.x)>.05||Math.abs(r.y-box.y)>.05
                                    ||Math.abs(r.width-box.width)>.05||Math.abs(r.height-box.height)>.05)
                                    throw new Error('Approved layer lost full-frame registration: '+image.id);
                                context.drawImage(image,0,0,941,1672);
                            }
                            const data=context.getImageData(0,0,941,1672).data;
                            return samples.flatMap(([x,y,...expected])=>{
                                const actual=Array.from(data.subarray((y*941+x)*4,(y*941+x)*4+4));
                                return actual.some((value,i)=>Math.abs(value-expected[i])>6)?[{x,y,actual,expected}]:[];
                            }).slice(0,12);
                        }''', {'prefix':prefix,'samples':reference['samples'][gender]})
                        self.assertEqual(failures, [])
                self.page.evaluate('equipPaperDollItem("upperBody",null)')
                for prefix in ['', 'wardrobe-']:
                    self.assertEqual(self.page.locator(f'#{prefix}layer-upper-body-neckline').count(), 0)

    def test_production_tunic_fitting_page_uses_current_catalog_without_changing_saves(self):
        self.load()
        saved = self.page.evaluate('JSON.stringify({...localStorage})')
        self.context.add_init_script('''if(location.pathname.endsWith('/art/patient-tunic.html')){
            window.previewStorageWrites=[];
            for(const method of ['setItem','removeItem','clear']){
                const original=Storage.prototype[method];
                Storage.prototype[method]=function(...args){
                    if(this===window.localStorage)window.previewStorageWrites.push(method);
                    return original.apply(this,args);
                };
            }
        }''')
        self.page.set_viewport_size({'width':1680,'height':1100})
        self.page.goto(self.url+'art/patient-tunic.html', wait_until='networkidle')
        self.assertEqual(self.page.locator('#preview-status').inner_text(), '')
        self.assertEqual(self.page.locator('#models article[data-gender]').count(), 2)
        self.assertEqual(self.page.locator('#details .detail-panel').count(), 7)
        self.page.wait_for_function('''()=>document.images.length===25&&[...document.images]
            .every(image=>image.complete&&image.naturalWidth===941&&image.naturalHeight===1672)''')
        catalog = self.page.evaluate('''()=>{
            const item=PAPER_DOLL_ITEMS.find(entry=>entry.id==='patient-tunic');
            return {images:item.genderVariants,bodies:PAPER_DOLL_BODIES,placements:{male:{x:0,y:0,width:941,height:1672},female:{x:0,y:0,width:941,height:1672}}};
        }''')
        for gender in ['male', 'female']:
            article = self.page.locator(f'#models article[data-gender="{gender}"]')
            details = self.page.locator(f'#details .detail-group[data-gender="{gender}"]')
            regions = ['shoulders', 'underarms', 'slits'] + (['neck'] if gender == 'female' else [])
            self.assertEqual(details.locator('.detail-panel').count(), len(regions))
            for host in [article, details]:
                for image in host.locator('img.clothing').all():
                    self.assertEqual(image.get_attribute('src'), self.url+catalog['images'][gender])
                for image in host.locator('img.body').all():
                    self.assertEqual(image.get_attribute('src'), self.url+catalog['bodies'][gender])
            downloads = article.locator('.downloads a')
            self.assertEqual(downloads.nth(0).get_attribute('href'), self.url+catalog['images'][gender])
            self.assertEqual(downloads.nth(1).get_attribute('href'), self.url+catalog['bodies'][gender])
            for region in regions:
                viewport = details.locator(f'[data-region="{region}"] .detail-viewport')
                geometry = viewport.evaluate('''viewport=>{
                    const box=element=>{const r=element.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
                    return {clip:box(viewport),frame:box(viewport.querySelector('.frame')),
                        expected:{...viewport.dataset}};
                }''')
                clip, frame, expected = geometry['clip'], geometry['frame'], geometry['expected']
                self.assertAlmostEqual(clip['width'], float(expected['width']), delta=.02)
                self.assertAlmostEqual(clip['height'], float(expected['height']), delta=.02)
                self.assertAlmostEqual(frame['width'], 941, delta=.02)
                self.assertAlmostEqual(frame['height'], 1672, delta=.02)
                self.assertAlmostEqual(frame['x'], clip['x']-float(expected['x']), delta=.02)
                self.assertAlmostEqual(frame['y'], clip['y']-float(expected['y']), delta=.02)
                registration = viewport.evaluate('''viewport=>{
                    const frame=viewport.querySelector('.frame').getBoundingClientRect();
                    const image=viewport.querySelector('.clothing').getBoundingClientRect();
                    return {x:image.x-frame.x,y:image.y-frame.y,width:image.width,height:image.height};
                }''')
                for key, value in catalog['placements'][gender].items():
                    self.assertAlmostEqual(registration[key], value, delta=.03)
        results = ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for mode in ['patient', 'combat']:
            self.page.locator(f'button[data-mode="{mode}"]').click()
            self.assertEqual(self.page.locator('body').get_attribute('data-mode'), mode)
            self.assertEqual(self.page.locator(f'button[data-mode="{mode}"]').get_attribute('aria-pressed'), 'true')
            self.page.wait_for_load_state('networkidle')
            for gender in ['male', 'female']:
                self.page.locator(f'#models article[data-gender="{gender}"] .stage').screenshot(
                    path=str(results/f'patient-tunic-fit-{gender}-full-{mode}.png'))
                if mode == 'patient' and os.getenv('GITHUB_ACTIONS') == 'true':
                    preview = self.page.locator(f'#models article[data-gender="{gender}"] .stage').screenshot(type='jpeg', quality=80)
                    print('PATIENT_TUNIC_FIT_DETAIL:'+json.dumps({'name':f'{gender}-full','jpeg':base64.b64encode(preview).decode()},separators=(',',':')),flush=True)
                regions = ['shoulders', 'underarms', 'slits'] + (['neck'] if gender == 'female' else [])
                for region in regions:
                    viewport = self.page.locator(f'#details [data-gender="{gender}"] [data-region="{region}"] .detail-viewport')
                    viewport.screenshot(path=str(results/f'patient-tunic-fit-{gender}-{region}-{mode}.png'))
                    if mode == 'patient' and os.getenv('GITHUB_ACTIONS') == 'true':
                        preview = viewport.screenshot(type='jpeg', quality=80)
                        print('PATIENT_TUNIC_FIT_DETAIL:'+json.dumps({
                            'name':f'{gender}-{region}','jpeg':base64.b64encode(preview).decode()
                        },separators=(',',':')),flush=True)
        self.assertEqual(self.page.evaluate('JSON.stringify({...localStorage})'), saved)
        self.assertEqual(self.page.evaluate('window.previewStorageWrites'), [])
        self.page.set_viewport_size({'width':390,'height':844})
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 390)
        self.assertGreater(self.page.locator('.detail-scroll').first.evaluate('e=>e.scrollWidth-e.clientWidth'), 0)
        self.page.screenshot(path=str(results/'patient-tunic-fit-phone.png'), full_page=True)

    def test_trial_faces_are_not_loaded_or_selectable_after_old_save_migration(self):
        requests=[]
        self.page.on('request',lambda request:requests.append(request.url))
        self.load({'palata404_gender':'female','palata404_face':'face_3.png'})
        for index in range(1,7):
            self.page.evaluate('''id=>localStorage.setItem('palata404_paper_doll',JSON.stringify({schemaVersion:2,selectedGender:'female',activeViewMode:'combat',appearance:{face:id,hair:'old-hair'},patientLoadout:{armor:'gear-br1'},combatLoadout:{weapon:'gear-pm'}}))''',f'face_{index}.png')
            self.page.reload(wait_until='networkidle')
            self.page.evaluate('openCustomization(); setWardrobeTab("face");')
            self.assertIsNone(self.page.evaluate('paperDollState.appearance.face'))
            self.assertEqual(self.page.evaluate('paperDollState.appearance.hair'),'old-hair')
            self.assertEqual(self.page.evaluate('paperDollState.patientLoadout.armor'),'gear-br1')
            self.assertEqual(self.page.evaluate('paperDollState.combatLoadout.weapon'),'gear-pm')
            self.assertEqual(self.page.locator('[data-wardrobe-card]').count(),0)
            for prefix in ['', 'wardrobe-']:
                self.assertIsNone(self.page.locator(f'#{prefix}layer-face').get_attribute('src'))
                self.assertTrue(self.page.locator(f'#{prefix}layer-body').is_visible())
        self.assertFalse(any(re.search(r'/face_[1-6]\.png',url) for url in requests))

    def test_equipment_swap_reload_and_legacy_training_bonus(self):
        self.load({
            'palata404_stats': json.dumps({'damage': 51, 'armor': 40, 'gymRounds': 2}),
            'palata404_equipped': json.dumps({
                'weapon': 'Штурмовий АКС-74У', 'helmet': 'Побитий шолом санітара', 'armor': 'Бронежилет БР-1'}),
        })
        self.assertEqual(self.state()['damage'], 51)
        self.equip('Іржавий ніж')
        self.assertEqual(self.state()['damage'], 24)
        self.equip('Іржавий ніж')
        self.assertEqual(self.state()['damage'], 16)
        self.equip('Побитий шолом санітара')
        self.assertEqual(self.state()['armor'], 28)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['damage'], 16)
        self.assertEqual(self.state()['armor'], 28)

    def test_shop_and_medicine_effects_match_in_and_out_of_battle(self):
        self.load({'palata404_stats': json.dumps({'silver': 2000, 'bucks': 100})})
        self.page.evaluate('''() => {
            buyMedicalItem('stamina_full', 10, 'bucks');
            buyMedicalItem('hp_10', 30, 'silver');
            buyMedicalItem('hp_full', 150, 'silver');
            buyMedicalItem('madness_pills', 50, 'silver');
            stats.energy = 10; stats.hp = 20; stats.madness = 40; updateUI();
        }''')
        self.assertEqual(self.state()['bucks'], 90)
        self.assertEqual(self.state()['silver'], 1770)
        self.use('Стимулятор')
        self.assertEqual(self.state()['energy'], 100)
        self.use('Мала аптечка')
        self.assertEqual(self.state()['hp'], 30)
        self.use('Таблетки «Аміназин»')
        self.assertEqual(self.state()['madness'], 25)
        self.page.evaluate('startBossFight("nurse"); stats.hp = 20; updateBattleUI();')
        self.page.locator('#medkit-btn-big').click()
        self.assertEqual(self.state()['hp'], 100)
        self.assertEqual(self.page.locator('#medkit-count-big').inner_text(), '0')
        self.page.evaluate('openFleeConfirmModal()')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['hp'], 100)

    def test_invalid_purchase_and_full_health_do_not_spend_resources(self):
        self.load()
        self.page.evaluate("buyMedicalItem('hp_10', -5, 'silver'); buyMedicalItem('unknown', 1, 'silver');")
        self.assertEqual(self.state()['silver'], 150)
        self.page.evaluate("buyMedicalItem('hp_10', 30, 'silver')")
        self.use('Мала аптечка')
        self.assertEqual(self.page.evaluate("inventory.find(i=>i.name==='Мала аптечка').count"), 1)

    def test_gym_energy_psychosis_and_dossier_refresh(self):
        self.load()
        self.page.evaluate('openGym()')
        self.page.locator('#gym-exercises-list button').first.click()
        self.assertEqual(self.state()['energy'], 98)
        self.assertEqual(self.state()['exp'], 5)
        self.page.evaluate('stats.madness=100; updateUI(); doGymExercise("squats"); openDossier();')
        self.assertEqual(self.state()['energy'], 98)
        self.assertEqual(self.page.locator('#dossier-madness-attacks').inner_text(), '4')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('gymComplex.exercises[0].current'), 1)

    def test_energy_regeneration_after_offline_time(self):
        self.load({'palata404_stats': '{"energy":90}',
                   'palata404_last_time': str(0)})
        self.page.evaluate('energyLastTime = Date.now()-5*120000; updateEnergyTimer();')
        self.assertEqual(self.state()['energy'], 95)
        self.page.evaluate('updateEnergyTimer()')
        self.assertEqual(self.state()['energy'], 95)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['energy'], 95)

    def test_map_unlock_is_persistent_and_locked_floor_stays_closed(self):
        self.load({'palata404_stats': '{"madness":100,"energy":100}'})
        self.page.evaluate('toggleMapModal(true); openFloorMap(10);')
        self.assertEqual(self.page.locator('.node-locked').count(), 1)
        self.page.locator('.map-node-pin').filter(has_text='Завал').click()
        self.assertEqual(self.page.locator('.node-locked').count(), 0)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('toggleMapModal(true); openFloorMap(10);')
        self.assertEqual(self.page.locator('.node-locked').count(), 0)
        self.page.evaluate('showFloorsList(); openFloorMap(9);')
        self.assertTrue(self.page.locator('#map-floors-view').is_visible())

    def test_battle_damage_armor_victory_and_single_reward(self):
        self.load()
        self.equip('Штурмовий АКС-74У')
        self.equip('Побитий шолом санітара')
        self.equip('Бронежилет БР-1')
        self.page.clock.install()
        self.page.evaluate('startBossFight("nurse")')
        self.page.locator('#battle-arena-screen').click(position={'x': 400, 'y': 200})
        self.assertEqual(self.page.evaluate('bossCurrentHp'), 75)
        self.assertEqual(self.page.locator('#b-boss-hp').inner_text(), '75/120')
        self.page.clock.run_for(600)
        self.assertEqual(self.state()['hp'], 100 - self.page.evaluate('Math.ceil(bossesDatabase.nurse.damage*100/140)'))
        self.page.clock.run_for(4000)
        self.page.evaluate('performPlayerAttack()')
        self.page.clock.run_for(4000)
        self.page.evaluate('performPlayerAttack()')
        self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())
        earned = self.state()['silver']
        self.page.evaluate('handleVictory()')
        self.assertEqual(self.state()['silver'], earned)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['bossesKilled'], 1)

    def test_phone_layout_dialogs_rotation_and_keyboard(self):
        self.load()
        for width, height in [(320,568),(390,844),(768,1024),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                self.page.evaluate('openSettings()')
                self.assertTrue(self.page.locator('#settings-modal').is_visible())
                self.page.keyboard.press('Escape')
                self.assertFalse(self.page.locator('#settings-modal').is_visible())
                self.page.evaluate('openBossDossier("nurse")')
                button = self.page.locator('#universal-dossier-start-btn')
                button.scroll_into_view_if_needed()
                box = button.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                button.click()
                self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible())
                self.page.evaluate('openFleeConfirmModal()')
        self.page.evaluate('closeOtherModals();')
        self.page.locator('.user-profile-badge').focus()
        self.page.keyboard.press('Enter')
        self.assertTrue(self.page.locator('#dossier-modal').is_visible())

    def test_touch_navigation_and_arena_fit(self):
        # A mobile context also exercises coarse-pointer CSS and tap events.
        context = self.browser.new_context(viewport={'width': 390, 'height': 844},
                                           is_mobile=True, has_touch=True, device_scale_factor=3)
        context.route('https://**/*', lambda route: route.abort())
        page = context.new_page()
        page.on('pageerror', lambda error: self.errors.append(str(error)))
        page.on('dialog', lambda dialog: dialog.accept())
        try:
            page.goto(self.url, wait_until='networkidle')
            page.get_by_role('button', name='Інвентар', exact=True).tap()
            self.assertTrue(page.locator('#inventory-modal').is_visible())
            page.locator('#inventory-modal .btn-close-mini').tap()
            page.evaluate('startBossFight("nurse")')
            box = page.locator('#battle-arena-scale').bounding_box()
            self.assertGreaterEqual(box['x'], -1)
            self.assertGreaterEqual(box['y'], -1)
            self.assertLessEqual(box['x'] + box['width'], 391)
            self.assertLessEqual(box['y'] + box['height'], 845)
            results = ROOT / 'test-results'
            results.mkdir(exist_ok=True)
            page.screenshot(path=str(results / 'mobile-battle.png'), full_page=True)
            # Decorative sprites don't receive pointer events; the arena underneath does.
            target = page.locator('#nurse-boss-sprite').bounding_box()
            x = target['x'] + target['width'] / 2
            y = target['y'] + target['height'] / 2
            self.assertTrue(page.evaluate('''({x,y}) => Boolean(
                document.elementFromPoint(x,y)?.closest('#battle-arena-screen'))''', {'x': x, 'y': y}))
            page.touchscreen.tap(x, y)
            self.assertEqual(page.evaluate('bossCurrentHp'), 110)
            page.evaluate('openFleeConfirmModal()')
            page.screenshot(path=str(results / 'mobile-lobby.png'), full_page=True)
        finally:
            context.close()

    def test_local_icons_render_in_static_and_dynamic_views(self):
        self.load()
        self.assertGreater(self.page.locator('.game-icon').count(), 60)
        self.assertEqual(self.page.locator('#medkit-btn-small img').get_attribute('src'), 'assets/icons/medkit.svg')
        self.assertEqual(self.page.locator('#medkit-btn-big img').get_attribute('src'), 'assets/icons/surgery.svg')
        self.page.evaluate('openProcedureRoom()')
        self.assertEqual(self.page.get_by_role('button', name='Придбати малу аптечку за 30 срібла', exact=True).count(), 1)
        self.page.evaluate('openInventory()')
        self.assertEqual(self.page.locator('#stash-items .game-icon').count(), 5)
        self.assertEqual(self.page.locator('#stash-items .game-icon').nth(2).get_attribute('src'),
                         'assets/icons/rifle.svg')
        for action, selector in [
                ('openGym()', '#gym-exercises-list'),
                ('openMedicalHub()', '#rooms-list-container'),
                ('toggleMapModal(true); openFloorMap(10)', '#blueprint-nodes-container'),
                ('openCustomization()', '#wardrobe-container')]:
            self.page.evaluate(action)
            self.assertGreater(self.page.locator(selector + ' img.game-icon').count(), 0)
            # Every actual dynamic illustration uses a whitelisted local image.
            self.assertTrue(self.page.evaluate('''selector => [...document.querySelectorAll(selector+' img.game-icon')]
                .every(img => img.getAttribute('src').startsWith('assets/icons/'))''', selector))
        self.page.evaluate('showCustomToast("⚠️ Тест повідомлення")')
        self.assertEqual(self.page.locator('#toast-message .game-icon').get_attribute('src'),
                         'assets/icons/warning.svg')
        self.assertNotIn('⚠', self.page.locator('#toast-message').inner_text())
        self.page.wait_for_function('''() => [...document.querySelectorAll('img.game-icon')]
            .every(img => img.complete && img.naturalWidth > 0)''')

    def test_legacy_item_icons_and_untrusted_icon_urls(self):
        self.load({'palata404_inventory': json.dumps([
            {'name':'Старий ключ','icon':'🗝️','category':'quest','count':3},
            {'name':'Невідомий предмет','icon':'https://example.org/track.svg','category':'mod','count':2}
        ])})
        self.page.evaluate('openInventory()')
        icons = self.page.locator('#stash-items .game-icon')
        self.assertEqual(icons.nth(0).get_attribute('src'), 'assets/icons/key.svg')
        self.assertEqual(icons.nth(1).get_attribute('src'), 'assets/icons/box.svg')
        self.assertEqual(self.page.locator('#stash-items .item-count').first.inner_text(), '3')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('inventory[0].count'), 3)

    def test_victory_protocol_identity_rewards_and_archive_reopen(self):
        self.load()
        previous_id = None
        for key, code, number, exp, silver in [('nurse','404-KL','№001',52,31), ('doctor','404-IZ','№002',126,84)]:
            with self.subTest(boss=key):
                before = self.state()['silver']
                self.page.evaluate('''key => {
                    stats.baseDamage=300; recalculateEquipmentStats();
                    startBossFight(key); performPlayerAttack();
                }''', key)
                self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())
                self.assertEqual(self.page.locator('#victory-summary-exp').inner_text(), f'+{exp}')
                self.assertEqual(self.page.locator('#victory-summary-silver').inner_text(), f'+{silver}')
                self.assertEqual(self.page.locator('#victory-summary-boss').inner_text(), self.page.evaluate('lastBattleResult.boss.name'))
                self.assertTrue(self.page.locator('#victory-summary-mvp').is_visible())
                self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
                self.assertFalse(self.page.locator('#nurse-victory-modal').is_visible())
                self.assertTrue(self.page.locator('#battle-detail-modal').is_visible())
                self.assertEqual(self.page.locator('#victory-boss-id').inner_text(), key)
                self.assertEqual(self.page.locator('#victory-case-code').inner_text(), code)
                self.assertEqual(self.page.locator('#victory-boss-number').inner_text(), number)
                self.assertEqual(self.page.locator('#victory-total-exp').inner_text(), str(exp))
                self.assertEqual(self.page.locator('#victory-total-silver').inner_text(), str(silver))
                self.assertEqual(self.state()['silver'], before+silver)
                current_id = self.page.locator('#victory-report-id').inner_text()
                self.assertNotEqual(current_id, previous_id)
                previous_id = current_id
                self.page.evaluate('handleVictory(); closeDetailedBattleReport(); openDetailedBattleReport();')
                self.assertEqual(self.state()['silver'], before+silver)
                self.assertEqual(self.page.locator('#victory-statistics-body tr').count(), 1)
                self.assertEqual(self.page.locator('#victory-rewards').count(), 1)
        after = self.state()
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openSettings()')
        self.page.get_by_role('button', name='Останній протокол бою', exact=True).click()
        self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
        self.assertEqual(self.page.locator('#victory-case-code').inner_text(), '404-IZ')
        self.assertEqual(self.state()['silver'], after['silver'])
        self.assertEqual(self.state()['bossesKilled'], after['bossesKilled'])

    def test_victory_protocol_mobile_scroll_and_controls(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(320,568),(390,844),(844,390),(1280,800)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openDetailedBattleReport()')
                report = self.page.locator('#victory-detail-document')
                box = report.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                if width < 900:
                    self.assertTrue(self.page.locator('.report-table-scroll').evaluate('e=>e.scrollWidth>e.clientWidth'))
                for button in self.page.locator('#battle-detail-modal .report-actions button').all():
                    button.scroll_into_view_if_needed()
                    action = button.bounding_box()
                    self.assertGreaterEqual(action['x'], 0)
                    self.assertLessEqual(action['x']+action['width'], width+1)
                    self.assertGreaterEqual(action['height'], 44)
                report.evaluate('e=>e.scrollTop=0')
                self.page.screenshot(path=str(results/f'victory-{width}x{height}.png'))
                self.page.get_by_role('button', name='Закрити детальний звіт', exact=True).click()
                self.assertFalse(self.page.locator('#battle-detail-modal').is_visible())
                self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())

    def test_compact_victory_fits_desktop_and_keeps_mobile_actions_visible(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(1366,768),(1024,600),(320,568),(390,844),(844,390),(320,320)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openLastBattleResult()')
                report = self.page.locator('.victory-summary')
                box = report.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                if width >= 1024:
                    for selector in ['.victory-summary', '#victory-summary-content']:
                        self.assertTrue(self.page.locator(selector).evaluate('e=>e.scrollHeight<=e.clientHeight+1'))
                    self.assertTrue(self.page.locator('#victory-summary-items').is_visible())
                for button in self.page.locator('.victory-summary-actions button').all():
                    action = button.bounding_box()
                    self.assertGreaterEqual(action['x'], 0)
                    self.assertGreaterEqual(action['y'], 0)
                    self.assertLessEqual(action['x']+action['width'], width+1)
                    self.assertLessEqual(action['y']+action['height'], height+1)
                    self.assertGreaterEqual(action['height'], 44)
                    self.assertTrue(button.evaluate('e=>{const r=e.getBoundingClientRect(); return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}'))
                self.page.screenshot(path=str(results/f'victory-summary-{width}x{height}.png'))
                self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
                self.assertTrue(self.page.locator('#battle-detail-modal').is_visible())
                self.page.keyboard.press('Escape')
                self.assertTrue(self.page.locator('#nurse-victory-modal').is_visible())

    def test_compact_victory_actions_and_report_reopening_do_not_pay_again(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        before = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,lastBattleResult,storage:{...localStorage}})')
        for _ in range(3):
            self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
            self.assertTrue(self.page.locator('#victory-conclusion').inner_text())
            self.assertEqual(self.page.locator('#victory-statistics-body tr').count(), 1)
            self.page.get_by_role('button', name='Повернутися до підсумку', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,lastBattleResult,storage:{...localStorage}})'), before)
        self.page.get_by_role('button', name='Повернутися на карту', exact=True).click()
        self.assertTrue(self.page.locator('#map-modal').is_visible())
        self.assertFalse(self.page.locator('#nurse-victory-modal').is_visible())
        self.page.evaluate('openLastBattleResult(); currentBossKey="nurse";')
        self.page.get_by_role('button', name='Повторити бій', exact=True).click()
        self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible())
        self.assertEqual(self.page.evaluate('currentBattleSession.bossKey'), 'doctor')
        self.assertEqual(self.state()['silver'], 234)
        self.page.evaluate('performPlayerAttack()')
        self.assertEqual(self.state()['silver'], 318)
        self.assertIn('Вже в інвентарі:', self.page.locator('#victory-summary-items').inner_text())
        self.assertEqual(self.page.evaluate('inventory.filter(i=>i.category==="quest").length'), 1)

    def test_helper_mvp_and_long_report_remain_accessible_in_compact_view(self):
        self.load()
        self.page.evaluate('''() => {
            startBossFight('nurse'); callAllFriends(); Math.random=()=>0;
            for(let i=0;i<10;i++) friendsAutoAttackTick();
        }''')
        self.assertTrue(self.page.locator('#victory-summary-mvp').is_visible())
        self.assertEqual(self.page.locator('#victory-summary-mvp-name').inner_text(), 'MVP: Сліпий Микола')
        self.assertFalse(self.page.locator('#victory-summary-mvp-bonus').is_visible())
        self.assertEqual(self.page.locator('#victory-summary-exp').inner_text(), '+50')
        self.assertEqual(self.page.locator('#victory-summary-silver').inner_text(), '+30')
        self.page.get_by_role('button', name='Детальний звіт', exact=True).click()
        self.assertEqual(self.page.locator('#victory-statistics-body tr').count(), 4)
        self.assertIn('MVP', self.page.locator('#victory-statistics-body').inner_text())
        self.assertIn('Не застосовується', self.page.locator('#victory-statistics-body').inner_text())
        self.page.get_by_role('button', name='Повернутися до підсумку', exact=True).click()
        self.page.set_viewport_size({'width':320,'height':320})
        self.page.evaluate('''() => {
            const preview=JSON.parse(JSON.stringify(lastBattleResult));
            preview.boss.name='Довга назва об’єкта '.repeat(10);
            preview.extraRewards=Array.from({length:12},(_,i)=>({name:'Предмет '+i,icon:'key',granted:true}));
            renderBattleSummary(preview);
        }''')
        self.assertTrue(self.page.locator('#victory-summary-content').evaluate('e=>e.scrollHeight>e.clientHeight'))
        self.page.locator('#victory-summary-items li').last.scroll_into_view_if_needed()
        self.assertTrue(self.page.locator('#victory-summary-items li').last.is_visible())
        for button in self.page.locator('.victory-summary-actions button').all():
            box = button.bounding_box()
            self.assertGreaterEqual(box['y'], 0)
            self.assertLessEqual(box['y']+box['height'], 320)

    def test_raid_archive_hud_snapshots_and_clear_confirmation(self):
        self.load({'palata404_nickname':'Історичний пацієнт'})
        institution = 'ЦЕНТР ІНТЕНСИВНОГО ЛІКУВАННЯ ПСИХІЧНИХ РОЗЛАДІВ № 404'
        self.page.get_by_role('button', name='Архів рейдів', exact=True).click()
        self.assertTrue(self.page.locator('#raid-archive-empty').is_visible())
        self.page.get_by_role('button', name='Закрити архів рейдів', exact=True).click()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();')
        first = self.page.evaluate('JSON.parse(JSON.stringify(lastBattleResult))')
        self.assertEqual(self.page.locator('#victory-summary-mvp-name').inner_text(), 'MVP: Історичний пацієнт')
        self.assertTrue(self.page.locator('#victory-summary-mvp-bonus').is_visible())
        self.assertIn(institution, self.page.locator('#nurse-victory-modal .report-institution').inner_text())
        self.page.evaluate('playerName="Новий пацієнт"; startBossFight("doctor"); performPlayerAttack(); openRaidArchive();')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        self.assertIn(institution, self.page.locator('#raid-archive-modal .report-institution').inner_text())
        state = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,storage:{...localStorage}})')
        old = self.page.locator('.raid-archive-card').filter(has_text=first['boss']['name'])
        self.assertIn('+52 EXP', old.inner_text())
        self.assertIn('+31 срібла', old.inner_text())
        self.assertIn('Історичний пацієнт', old.inner_text())
        old.click()
        self.assertEqual(self.page.locator('#victory-report-id').inner_text(), first['battleId'])
        self.assertEqual(self.page.locator('#victory-mvp-name').inner_text(), 'Історичний пацієнт')
        self.assertIn(institution, self.page.locator('#battle-detail-modal .report-institution').inner_text())
        self.assertEqual(self.page.locator('#battle-detail-modal .report-participant-stamp').inner_text(), 'MVP')
        self.page.get_by_role('button', name='Повернутися до архіву', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,storage:{...localStorage}})'), state)
        self.page.reload(wait_until='networkidle')
        nav = self.page.get_by_role('button', name='Архів рейдів', exact=True)
        nav.focus()
        self.page.keyboard.press('Enter')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        self.page.get_by_role('button', name='Очистити архів', exact=True).click()
        self.assertTrue(self.page.locator('#raid-archive-confirm').is_visible())
        self.page.get_by_role('button', name='Скасувати', exact=True).click()
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        protected = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,lastBattleResult})')
        self.page.get_by_role('button', name='Очистити архів', exact=True).click()
        self.page.locator('#raid-archive-confirm').get_by_role('button', name='Очистити архів', exact=True).click()
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.assertTrue(self.page.locator('#raid-archive-empty').is_visible())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,gameProgress,lastBattleResult})'), protected)
        self.page.evaluate('handleVictory(); retryBattleResultSave(); openRaidArchive();')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.page.get_by_role('button', name='Закрити архів рейдів', exact=True).click()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); openRaidArchive();')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 1)
        self.assertNotIn('Отримано:', self.page.locator('.raid-archive-card').inner_text())

    def test_raid_archive_limit_mobile_bounds_and_stamps(self):
        self.load()
        self.page.evaluate('''() => {
            const originalNow=Date.now; let now=originalNow(); Date.now=()=>now;
            stats.baseDamage=300; recalculateEquipmentStats();
            for(let i=0;i<51;i++) { startBossFight('nurse'); performPlayerAttack(); now++; }
            Date.now=originalNow; openRaidArchive();
        }''')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 50)
        self.assertEqual(self.page.locator('#raid-archive-count').inner_text(), '50 / 50')
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 50)
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(320,568),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openRaidArchive()')
                box = self.page.locator('.raid-archive-document').bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                self.page.locator('.raid-archive-card').last.click()
                self.assertTrue(self.page.locator('#battle-detail-modal').is_visible())
                self.page.keyboard.press('Escape')
                self.assertTrue(self.page.locator('#raid-archive-modal').is_visible())
                self.page.locator('.raid-archive-document').evaluate('e=>e.scrollTop=0')
                self.page.screenshot(path=str(results/f'raid-archive-{width}x{height}.png'))
        self.page.evaluate('startBossFight("nurse"); callAllFriends(); Math.random=()=>0; for(let i=0;i<10;i++) friendsAutoAttackTick(); openDetailedBattleReport();')
        self.assertEqual(self.page.get_by_text('УХИЛЯВСЯ ВІД ПРОЦЕДУРИ', exact=True).count(), 1)
        self.assertEqual(self.page.locator('#battle-detail-modal .report-participant-stamp').count(), 2)

    def test_raid_archive_identity_and_shared_tabs(self):
        self.load({'palata404_web_id':'WEB-archive-tabs'})
        other = self.context.new_page()
        other.on('pageerror', lambda error: self.errors.append(str(error)))
        other.on('dialog', lambda dialog: dialog.accept())
        other.goto(self.url, wait_until='networkidle')
        for page, boss in [(self.page,'nurse'),(other,'doctor')]:
            page.evaluate('''boss=>{ stats.baseDamage=300; recalculateEquipmentStats(); startBossFight(boss); performPlayerAttack(); }''',boss)
        self.page.evaluate('openRaidArchive()')
        other.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 2)
        self.assertEqual(other.locator('.raid-archive-card').count(), 2)
        saved = self.page.evaluate('JSON.stringify(readRaidArchive())')
        self.page.evaluate('safeStorageSet("palata404_web_id","WEB-other-account")')
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').count(), 0)
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); clearRaidArchive();')
        self.assertEqual(other.evaluate('JSON.stringify(readRaidArchive())'), saved)
        other.close()

    def test_archive_full_dossier_images_and_personal_statuses(self):
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats();
            startBossFight('nurse'); performPlayerAttack();
            startBossFight('doctor'); performPlayerAttack(); openRaidArchive();
        }''')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(320,568),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for filename, case in [('nurse_dossier_card.png','404-KL'),('doctor_dossier_card.png','404-IZ')]:
                    card = self.page.locator('.raid-archive-card').filter(has_text=case)
                    image = card.locator('.raid-card-dossier-image')
                    image.scroll_into_view_if_needed()
                    self.page.wait_for_function('(src)=>[...document.querySelectorAll(".raid-card-dossier-image")].some(e=>e.getAttribute("src")===src && e.complete && e.naturalWidth>0)', arg=filename)
                    self.assertEqual(image.get_attribute('src'), filename)
                    self.assertFalse(card.locator('.raid-card-no-dossier').is_visible())
                    self.assertEqual(card.locator('.raid-card-personal-stamp').inner_text(), 'MVP')
                    self.assertTrue(image.evaluate('e=>Math.abs(e.clientWidth/e.clientHeight-e.naturalWidth/e.naturalHeight)<0.02'))
                    self.assertEqual(image.evaluate('e=>getComputedStyle(e).objectFit'), 'contain')
                    self.assertEqual(card.locator('.raid-card-dossier-image').count(), 1)
                    photo = card.locator('.raid-card-visual').bounding_box()
                    text = card.locator('.raid-card-details').bounding_box()
                    if width > 600:
                        self.assertLessEqual(photo['x']+photo['width'], text['x'])
                    else:
                        self.assertLessEqual(photo['y']+photo['height'], text['y'])
                    box = card.bounding_box()
                    self.assertGreaterEqual(box['x'], 0)
                    self.assertLessEqual(box['x']+box['width'], width+1)
                self.page.locator('.raid-archive-document').evaluate('e=>e.scrollTop=0')
                self.page.screenshot(path=str(results/f'raid-dossiers-{width}x{height}.png'))
        before = self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,archive:readRaidArchive(),storage:{...localStorage}})')
        old_card = self.page.locator('.raid-archive-card').filter(has_text='404-KL')
        old_card.locator('.raid-card-open').click()
        self.assertEqual(self.page.locator('#victory-case-code').inner_text(), '404-KL')
        self.page.get_by_role('button', name='Повернутися до архіву', exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,bossKillsCount,archive:readRaidArchive(),storage:{...localStorage}})'), before)
        self.page.evaluate('''() => {
            startBossFight('nurse'); callAllFriends(); Math.random=()=>0;
            for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();
        }''')
        idle = self.page.locator('.raid-archive-card').first
        self.assertEqual(idle.locator('.raid-card-personal-stamp').inner_text(), 'УХИЛЯВСЯ ВІД ПРОЦЕДУРИ')
        self.assertIn('MVP: Сліпий Микола', idle.inner_text())
        self.assertIn('+50 EXP', idle.inner_text())
        self.page.evaluate('''() => {
            startBossFight('nurse'); raidMembers[0].metrics.healing=1;
            callAllFriends(); for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();
        }''')
        support = self.page.locator('.raid-archive-card').first
        self.assertEqual(support.locator('.raid-card-personal-stamp').count(), 0)
        self.assertIn('MVP: Сліпий Микола', support.inner_text())
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openRaidArchive()')
        self.assertEqual(self.page.locator('.raid-archive-card').first.locator('.raid-card-personal-stamp').count(), 0)

    def test_staff_archive_unknown_cases_first_contact_and_details(self):
        self.load()
        self.page.get_by_role('button', name='Архів персоналу', exact=True).click()
        archive = self.page.locator('#staff-archive-modal')
        self.assertEqual(archive.locator('.staff-case-button').count(), 2)
        self.assertEqual(archive.get_by_text('ОСОБУ НЕ ВСТАНОВЛЕНО', exact=True).count(), 3)
        self.assertEqual(archive.locator('img[src*="dossier_card"]').count(), 0)
        self.assertNotIn('Черговий лікар', archive.inner_text())
        self.assertNotIn('Сестра Клара', archive.inner_text())
        self.assertNotIn('Копія наказу', archive.inner_text())
        self.page.evaluate('openBossDossier("doctor")')
        self.page.get_by_role('button', name='ДЕТАЛЬНІ ВІДОМОСТІ', exact=True).click()
        self.assertIn('№002', self.page.locator('#staff-case-sheet').inner_text())
        self.assertIn('ОСОБУ НЕ ВСТАНОВЛЕНО', self.page.locator('#staff-case-sheet').inner_text())
        self.assertEqual(self.page.evaluate('Object.keys(staffArchiveState.cases).length'), 0)
        self.page.evaluate('startBossFight("doctor"); stats.hp=1; performPlayerAttack();')
        self.page.wait_for_function('!isBattleActive')
        self.page.evaluate('openStaffArchive("doctor")')
        self.assertIn('Черговий лікар', self.page.locator('#staff-case-sheet').inner_text())
        image = self.page.locator('.staff-dossier-image')
        self.assertEqual(image.get_attribute('src'), 'doctor_dossier_card.png')
        self.page.get_by_role('button', name='Архівні документи', exact=True).click()
        sheet = self.page.locator('#staff-case-sheet')
        self.assertIn('ДОКУМЕНТ №002-03 — ЗАСЕКРЕЧЕНО', sheet.inner_text())
        self.assertNotIn('Незаповнена графа наказу', sheet.inner_text())
        self.assertNotIn('Копія наказу головного лікаря', sheet.inner_text())
        sheet.get_by_role('button', name='Читати документ', exact=True).first.click()
        self.assertIn('Об’єкт №002 відомий', sheet.inner_text())
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openStaffArchive("doctor")')
        self.assertIn('Черговий лікар', self.page.locator('#staff-case-sheet').inner_text())
        self.assertEqual(self.page.evaluate('staffCaseProgress("doctor").opened'), 2)

    def test_staff_pity_rewards_and_clear_preserve_collection(self):
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0.5;
            for(let i=0;i<29;i++) { startBossFight('doctor'); performPlayerAttack(); }
        }''')
        self.assertEqual(self.page.evaluate('staffArchiveState.cases.doctor.misses'), 29)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();')
        self.assertEqual(self.page.evaluate('staffArchiveState.cases.doctor.misses'), 0)
        self.assertEqual(self.page.evaluate('lastBattleResult.extraRewards.filter(r=>r.type==="document").length'), 1)
        self.page.evaluate('''() => {
            Math.random=()=>0; startBossFight('doctor'); performPlayerAttack(); openStaffArchive('doctor'); changeStaffArchiveTab('rewards');
        }''')
        self.assertEqual(self.page.evaluate('staffCaseProgress("doctor").complete'), True)
        self.assertEqual(self.page.locator('.staff-reward-status').all_text_contents(), ['ДОСТУПНО','ДОСТУПНО'])
        before = self.state()['silver']
        buttons = self.page.locator('.staff-claim-button')
        self.assertEqual(buttons.count(), 2)
        buttons.first.click()
        self.assertEqual(self.state()['silver'], before+1)
        self.assertEqual(self.page.locator('.staff-reward-status').all_text_contents(), ['ОТРИМАНО','ДОСТУПНО'])
        self.page.locator('.staff-claim-button').click()
        self.assertEqual(self.state()['silver'], before+2)
        self.assertEqual(self.page.locator('.staff-claim-button').count(), 0)
        self.assertEqual(self.page.locator('.staff-reward-status').all_text_contents(), ['ОТРИМАНО','ОТРИМАНО'])
        self.assertEqual(self.page.locator('.staff-visual-progress progress').evaluate_all('es=>es.map(e=>e.value/e.max)'), [1,1])
        profile = self.page.evaluate('JSON.stringify(staffArchiveState)')
        self.page.evaluate('openRaidArchive(); requestRaidArchiveClear();')
        self.page.locator('#raid-archive-confirm').get_by_role('button', name='Очистити архів', exact=True).click()
        self.assertEqual(self.page.evaluate('readRaidArchive().length'), 0)
        self.assertEqual(self.page.evaluate('JSON.stringify(staffArchiveState)'), profile)
        self.page.reload(wait_until='networkidle')
        self.page.evaluate('openStaffArchive("doctor"); changeStaffArchiveTab("rewards");')
        self.assertEqual(self.state()['silver'], before+2)
        self.assertEqual(self.page.locator('.staff-claim-button').count(), 0)

    def test_staff_journal_documents_and_reward_cards_are_read_only_and_responsive(self):
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0;
            for (const boss of ['nurse','doctor']) { startBossFight(boss); performPlayerAttack(); }
            openStaffArchive('nurse');
        }''')
        before=self.page.evaluate('JSON.stringify({stats,inventory,gameProgress,staffArchiveState,storage:{...localStorage}})')
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for boss in ['nurse','doctor']:
                    self.page.evaluate('boss=>openStaffArchive(boss)',boss)
                    for tab in ['identity','observations','documents','rewards']:
                        self.page.locator(f'[data-staff-tab="{tab}"]').click()
                        sheet=self.page.locator('#staff-case-sheet')
                        if tab=='identity':
                            self.assertEqual(sheet.locator('.staff-form-field').count(),8)
                        elif tab in ['observations','documents']:
                            self.assertNotRegex(sheet.inner_text(),r'5%|\d+/30|гаранті|drop rate|chance|pity')
                            self.assertGreater(sheet.locator('.staff-record-open').count(),0)
                            self.assertGreater(sheet.locator('.staff-record-locked').count(),0)
                            self.assertNotIn('Фрагмент журналу експериментів' if boss=='nurse' else 'Незаповнена графа наказу',sheet.inner_text())
                            if tab=='observations':
                                self.assertEqual(sheet.locator('.staff-observation-journal').count(),1)
                                self.assertGreater(sheet.locator('.staff-observation-text').count(),0)
                            sheet.get_by_role('button',name='Читати документ',exact=True).first.click()
                            self.assertTrue(sheet.locator('.staff-document-reading').is_visible())
                        else:
                            self.assertEqual(sheet.locator('.staff-reward-section').count(),2)
                            self.assertEqual(sheet.locator('progress').count(),2)
                            self.assertEqual(sheet.locator('.staff-reward-status').all_text_contents(),['НЕ ЗАВЕРШЕНО','НЕ ЗАВЕРШЕНО'])
                            self.assertEqual(sheet.locator('.staff-claim-button').count(),0)
                            progress=self.page.evaluate('boss=>staffCaseProgress(boss)',boss)
                            self.assertEqual(sheet.locator('progress').first.get_attribute('value'),str(progress['opened']))
                            self.assertIn('Завершено справ: 0/1',sheet.inner_text())
                            self.assertIn('+1 срібла',sheet.inner_text())
                        self.assertLessEqual(sheet.evaluate('e=>e.scrollWidth-e.clientWidth'),1)
                        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                        if width in [1280,390]:
                            self.page.screenshot(path=str(results/f'archive-{boss}-{tab}-{width}.png'))
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,gameProgress,staffArchiveState,storage:{...localStorage}})'),before)

    def test_folder_hud_navigation_active_tabs_and_mobile_bounds(self):
        self.load()
        self.page.evaluate('stats.madness=100; updateUI();')
        before=self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,storage:{...localStorage}})')
        nav=self.page.get_by_role('navigation',name='Ігрове меню')
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for button in nav.locator('.hud-folder-tab').all():
                    box=button.bounding_box()
                    self.assertIsNotNone(box)
                    self.assertGreaterEqual(box['height'],44)
                    self.assertGreaterEqual(box['x'],0)
                    self.assertLessEqual(box['x']+box['width'],width)
                    self.assertLessEqual(button.evaluate('e=>e.scrollWidth-e.clientWidth'),1)
                    self.assertTrue(button.locator('span').is_visible())
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                self.assertTrue(self.page.locator('#armor-val').is_visible())
                self.page.screenshot(path=str(results/f'folder-hud-{width}x{height}.png'))
        for name,modal in [('Інвентар','inventory-modal'),('Гардероб','custom-modal'),('Карта','map-modal'),('Сусіди по блоку','friends-modal'),('Архів рейдів','raid-archive-modal'),('Архів персоналу','staff-archive-modal')]:
            button=nav.get_by_role('button',name=name,exact=True)
            button.click()
            self.assertTrue(self.page.locator(f'#{modal}').is_visible())
            self.page.wait_for_function('name=>document.querySelector(`.center-nav [aria-label="${name}"]`).getAttribute("aria-pressed")==="true"',arg=name)
            self.assertEqual(nav.locator('[aria-pressed="true"]').count(),1)
            self.page.keyboard.press('Escape')
            self.page.wait_for_function('()=>!document.querySelector(".center-nav [aria-pressed=true]")')
        nav.get_by_role('button',name='Завдання',exact=True).click()
        nav.get_by_role('button',name='Рейд',exact=True).click()
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,storage:{...localStorage}})'),before)
        self.page.evaluate('startBossFight("nurse"); closeNurseBattle();')
        nav.get_by_role('button',name='Рейд',exact=True).click()
        self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible())
        self.assertTrue(self.page.locator('#lobby-raid-subtimer').is_visible())
        self.assertEqual(self.page.locator('#lobby-raid-subtimer').evaluate('e=>getComputedStyle(e).position'),'static')
        self.page.evaluate('openFleeConfirmModal()')

    def test_staff_archive_and_enlarged_dossiers_mobile_bounds(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); startBossFight("nurse"); performPlayerAttack(); openStaffArchive("nurse");')
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(1024,768),(768,1024),(320,568),(390,844),(844,390)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openStaffArchive("nurse")')
                paper = self.page.locator('.staff-archive-document')
                box = paper.bounding_box()
                self.assertGreaterEqual(box['x'], 0)
                self.assertGreaterEqual(box['y'], 0)
                self.assertLessEqual(box['x']+box['width'], width+1)
                self.assertLessEqual(box['y']+box['height'], height+1)
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), width)
                for name in ['Архівні документи','Службові спостереження','Винагороди та колекції','Анкетні відомості']:
                    self.page.get_by_role('button', name=name, exact=True).click()
                self.page.screenshot(path=str(results/f'staff-archive-{width}x{height}.png'))
                self.page.evaluate('openBossDossier("doctor")')
                photo = self.page.locator('#universal-dossier-img')
                self.assertEqual(photo.get_attribute('src'), 'doctor_dossier_card.png')
                if width >= 1024:
                    self.assertGreaterEqual(photo.bounding_box()['width'], 290)
                self.page.get_by_role('button', name='ДЕТАЛЬНІ ВІДОМОСТІ', exact=True).click()
                self.assertIn('Черговий лікар', self.page.locator('#staff-case-sheet').inner_text())
                self.page.evaluate('openRaidArchive()')
                image = self.page.locator('.raid-card-dossier-image').first
                image.scroll_into_view_if_needed()
                self.page.wait_for_function('()=>[...document.querySelectorAll(".raid-card-dossier-image")].some(e=>e.complete&&e.naturalWidth>0)')
                if width >= 1024:
                    self.assertGreaterEqual(image.bounding_box()['width'], 315)
                    text = self.page.locator('.raid-card-details').first.bounding_box()
                    visual = self.page.locator('.raid-card-visual').first.bounding_box()
                    self.assertAlmostEqual(visual['y'], text['y'], delta=2)
                    self.assertLessEqual(text['x']-(visual['x']+visual['width']), 13)
                self.assertTrue(image.evaluate('e=>Math.abs(e.clientWidth/e.clientHeight-e.naturalWidth/e.naturalHeight)<0.02'))
                self.page.screenshot(path=str(results/f'raid-enlarged-{width}x{height}.png'))
                self.page.keyboard.press('Escape')
                self.assertFalse(self.page.locator('#raid-archive-modal').is_visible())

    def test_staff_collection_interrupted_claim_recovers_once(self):
        self.context.add_init_script('''
            const nativeSet=Storage.prototype.setItem;
            Storage.prototype.setItem=function(key,value) {
                if(window.blockStaffClaim && key==='palata404_stats') throw new DOMException('Interrupted','QuotaExceededError');
                return nativeSet.call(this,key,value);
            };
        ''')
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0;
            for(let i=0;i<5;i++) { startBossFight('doctor'); performPlayerAttack(); }
            openStaffArchive('doctor'); changeStaffArchiveTab('rewards'); window.blockStaffClaim=true;
        }''')
        before = self.state()['silver']
        self.page.locator('.staff-claim-button').first.click()
        self.assertEqual(self.state()['silver'], before+1)
        self.assertTrue(self.page.locator('#staff-save-note').is_visible())
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['silver'], before+1)
        self.page.evaluate('openStaffArchive("doctor"); changeStaffArchiveTab("rewards");')
        self.assertEqual(self.page.locator('.staff-claim-button').count(), 1)
        self.assertFalse(self.page.locator('#staff-save-note').is_visible())

    def test_compact_photo_composition_and_floor_filter_are_read_only(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack(); startBossFight("doctor"); performPlayerAttack();')
        before = self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,archive:readRaidArchive(),storage:{...localStorage}})')
        self.page.evaluate('openStaffArchive("doctor")')
        options = self.page.locator('#staff-floor-filter option').all_text_contents()
        self.assertEqual(options, ['Усі поверхи','9 поверх','10 поверх'])
        self.assertEqual(self.page.locator('.staff-form-field').filter(has_text='Відділення:').locator('dd').inner_text(), 'Блок ізоляторів')
        self.assertEqual(self.page.locator('.staff-form-field').filter(has_text='Локація:').locator('dd').inner_text(), 'Кабінет спостереження, 10-й поверх')
        self.page.get_by_label('Поверх', exact=True).select_option('9')
        self.assertEqual(self.page.locator('.staff-case-button').count(), 0)
        self.assertIn('На цьому поверсі справ не зареєстровано', self.page.locator('#staff-case-sheet').inner_text())
        self.page.get_by_label('Поверх', exact=True).select_option('10')
        self.assertEqual(self.page.locator('.staff-case-button').count(), 2)
        self.page.get_by_label('Поверх', exact=True).select_option('')
        self.assertEqual(self.page.locator('.staff-case-button').count(), 2)
        results = ROOT / 'test-results'
        results.mkdir(exist_ok=True)
        for width, height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                for boss in ['nurse','doctor']:
                    self.page.evaluate('boss=>openStaffArchive(boss)',boss)
                    visual = self.page.locator('.staff-dossier-visual')
                    visual.scroll_into_view_if_needed()
                    image = visual.locator('img')
                    self.page.wait_for_function('()=>document.querySelector(".staff-dossier-image")?.naturalWidth>0')
                    frame = visual.bounding_box()
                    text = self.page.locator('.staff-identity-details').bounding_box()
                    if width > 600:
                        self.assertAlmostEqual(frame['y'],text['y'],delta=1)
                        self.assertGreaterEqual(text['x']-frame['x']-frame['width'],9)
                        self.assertLessEqual(text['x']-frame['x']-frame['width'],13)
                    else:
                        self.assertGreaterEqual(text['y'],frame['y']+frame['height'])
                    # Project measured source alpha bounds into the CSS viewport.
                    photo = image.bounding_box()
                    source_width = image.evaluate('e=>e.naturalWidth')
                    scale = photo['width']/source_width
                    self.assertAlmostEqual(photo['x']+312*scale,frame['x'],delta=1)
                    self.assertAlmostEqual(photo['x']+1069*scale,frame['x']+frame['width'],delta=1)
                    self.assertGreaterEqual(photo['y']+2*scale,frame['y']-1)
                    self.assertLessEqual(photo['y']+768*scale,frame['y']+frame['height']+1)
                    self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                    self.page.screenshot(path=str(results/f'compact-staff-{boss}-{width}x{height}.png'))
                self.page.evaluate('openRaidArchive()')
                for card in self.page.locator('.raid-archive-card').all():
                    visual = card.locator('.raid-card-visual')
                    frame = visual.bounding_box()
                    text = card.locator('.raid-card-details').bounding_box()
                    self.assertEqual(visual.evaluate('e=>getComputedStyle(e).borderTopWidth'),'0px')
                    self.assertEqual(visual.evaluate('e=>getComputedStyle(e).paddingLeft'),'0px')
                    if width > 600:
                        self.assertAlmostEqual(frame['y'],text['y'],delta=1)
                        self.assertLessEqual(text['x']-frame['x']-frame['width'],13)
                    self.assertTrue(card.locator('.raid-card-rewards').is_visible())
                    self.assertTrue(card.locator('.raid-card-personal-stamp').is_visible())
                self.page.screenshot(path=str(results/f'compact-raids-{width}x{height}.png'))
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,inventory,staffArchiveState,archive:readRaidArchive(),storage:{...localStorage}})'),before)

    def test_staff_forms_thumbnail_scale_and_prominent_personal_raid_stamps(self):
        self.load()
        self.page.evaluate('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); openStaffArchive("doctor");')
        profile = self.page.evaluate('JSON.stringify({stats,staffArchiveState,storage:{...localStorage}})')
        self.page.get_by_role('button', name='Архівні документи', exact=True).click()
        text = self.page.locator('#staff-case-sheet').inner_text()
        self.assertNotRegex(text, r'5%|\d+/30|гаранті|drop chance|pity')
        self.assertIn('після успішного обстеження', text)
        self.page.get_by_role('button', name='Анкетні відомості', exact=True).click()
        self.assertEqual(self.page.locator('.staff-form-field dt').all_text_contents(),
                         ['Ім’я:','Номер справи:','Код:','Посада:','Поверх:','Відділення:','Локація:','Статус / примітка:'])
        self.assertEqual(self.page.locator('.staff-identity-note').count(),1)
        self.assertIn('КОНТАКТ ЗАФІКСОВАНО', self.page.locator('.staff-identity-header').inner_text())
        self.assertEqual(self.page.evaluate('JSON.stringify({stats,staffArchiveState,storage:{...localStorage}})'),profile)
        results=ROOT/'test-results'
        results.mkdir(exist_ok=True)
        for width,height in [(1280,800),(1024,768),(768,1024),(844,390),(390,844),(320,568)]:
            with self.subTest(viewport=(width,height)):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openStaffArchive("doctor")')
                thumbnail=self.page.locator('.staff-case-photo')
                thumbnail.scroll_into_view_if_needed()
                self.assertGreaterEqual(thumbnail.bounding_box()['width'],69)
                self.assertEqual(self.page.locator('.staff-case-button.selected').evaluate('e=>getComputedStyle(e).gap'),'6px')
                self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'),width)
                self.page.screenshot(path=str(results/f'personnel-form-{width}x{height}.png'))
                self.page.evaluate('openRaidArchive()')
                card=self.page.locator('.raid-archive-card').first
                stamp=card.locator(':scope > .raid-card-personal-stamp')
                self.assertEqual(stamp.count(),1)
                self.assertEqual(stamp.inner_text(),'MVP')
                self.assertIn('MVP: Пацієнт #404',card.inner_text())
                self.assertGreaterEqual(stamp.evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'),30)
                self.assertGreaterEqual(stamp.evaluate('e=>parseInt(getComputedStyle(e).fontWeight)'),700)
                badge=stamp.bounding_box()
                if width>600:
                    detail=card.locator('.raid-card-details').bounding_box()
                    self.assertGreaterEqual(badge['x'],detail['x']+detail['width'])
                else:
                    photo=card.locator('.raid-card-visual').bounding_box()
                    self.assertGreaterEqual(badge['x'],photo['x']+photo['width'])
                self.assertGreaterEqual(badge['x'],0)
                self.assertLessEqual(badge['x']+badge['width'],width+1)
                self.page.screenshot(path=str(results/f'personal-mvp-{width}x{height}.png'))
        self.page.evaluate('''() => {
            startBossFight('nurse'); raidMembers[0].metrics.healing=1; callAllFriends(); Math.random=()=>0;
            for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();
        }''')
        card=self.page.locator('.raid-archive-card').first
        self.assertEqual(card.locator('.raid-card-personal-stamp').count(),0)
        self.assertIn('MVP: Сліпий Микола',card.inner_text())
        self.page.evaluate('startBossFight("nurse"); callAllFriends(); for(let i=0;i<10;i++) friendsAutoAttackTick(); openRaidArchive();')
        card=self.page.locator('.raid-archive-card').first
        self.assertEqual(card.locator('.raid-card-personal-stamp').count(),1)
        self.assertEqual(card.locator('.raid-card-personal-stamp').inner_text(),'УХИЛЯВСЯ ВІД ПРОЦЕДУРИ')
        self.assertEqual(card.locator('.raid-personal-mvp').count(),0)

    def test_partial_reward_save_recovers_without_duplicate_credit(self):
        self.context.add_init_script('''
            window.blockRewardSave=false;
            const originalSet=Storage.prototype.setItem;
            Storage.prototype.setItem=function(key,value) {
                if(window.blockRewardSave && key==='palata404_stats') throw new DOMException('Interrupted', 'QuotaExceededError');
                return originalSet.call(this,key,value);
            };
        ''')
        self.load()
        self.page.evaluate('''() => {
            stats.baseDamage=300; recalculateEquipmentStats(); startBossFight('nurse');
            window.blockRewardSave=true; performPlayerAttack();
        }''')
        self.assertEqual(self.state()['silver'], 181)
        self.assertTrue(self.page.locator('#victory-save-note').is_visible())
        self.assertEqual(self.page.evaluate('JSON.parse(localStorage.getItem("palata404_stats")).silver'),150)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.state()['silver'],181)
        self.assertEqual(self.state()['exp'],52)
        self.assertEqual(self.state()['bossesKilled'],1)
        self.assertIsNone(self.page.evaluate('localStorage.getItem("palata404_pending_battle_reward")'))
        self.page.evaluate('openLastBattleResult(); handleVictory(); retryBattleResultSave();')
        self.assertEqual(self.state()['silver'],181)
        self.assertFalse(self.page.locator('#victory-save-note').is_visible())


if __name__ == '__main__':
    unittest.main()
