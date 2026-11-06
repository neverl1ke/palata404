"""Document material, live translations, geometry and production integration."""
import unittest
from tests import test_game as support
class DocumentSystemBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):support.GameTests.setUpClass.__func__(cls)
    @classmethod
    def tearDownClass(cls):support.GameTests.tearDownClass.__func__(cls)
    setUp=support.GameTests.setUp
    tearDown=support.GameTests.tearDown
    load=support.GameTests.load
    def test_both_headers_three_languages_and_sizes_keep_graphics_and_alignment(self):
        self.page.goto(self.url+'document-demo.html',wait_until='networkidle')
        self.page.evaluate('document.fonts.ready')
        for width in [960,640,320]:
            self.page.select_option('#demo-width',str(width))
            graphics=None
            for locale in ['ru','uk','en']:
                self.page.select_option('[data-document-language]',locale)
                self.page.wait_for_timeout(40)
                for variant in ['left','center']:
                    header=self.page.locator(f'[data-demo-variant="{variant}"] > document-header')
                    self.assertIn(self.page.evaluate('PalataI18n.t("documents.name1")'),header.inner_text())
                    metrics=header.evaluate('''h=>{const r=e=>{const b=e.getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,right:b.right,bottom:b.bottom}};const title=h.querySelector('.document-institution'),logo=h.querySelector('.document-emblem-cell');return {box:r(h),title:r(title),logo:r(logo),department:r(h.querySelector('.document-department')),overflow:[...h.querySelectorAll('[data-fit-text],.document-institution span')].filter(e=>e.scrollWidth>e.clientWidth+1).length,source:h.querySelector('img').getAttribute('src')}}''')
                    self.assertEqual(metrics['overflow'],0,(width,locale,variant,metrics))
                    self.assertLessEqual(metrics['title']['right'],metrics['box']['right']+1)
                    if variant=='left':self.assertGreaterEqual(metrics['title']['x'],metrics['logo']['right'])
                    else:self.assertGreaterEqual(metrics['title']['y'],metrics['logo']['bottom'])
                    self.assertGreaterEqual(metrics['department']['y'],metrics['title']['bottom']-1)
                geometry=self.page.locator('[data-demo-variant="left"] > document-header .document-emblem-cell').bounding_box()
                if graphics is None:graphics=geometry
                else:self.assertEqual(graphics,geometry)
                self.assertEqual(self.page.locator('[data-demo-variant="center"] document-stamp[type=service]').inner_text().strip(),self.page.evaluate('PalataI18n.t("documents.service")'))
                self.assertTrue(self.page.locator('[data-demo-variant="left"]').evaluate('e=>getComputedStyle(e,"::after").borderImageSource.includes("paper-source.jpg")'))
    def test_custom_department_layout_api_safe_text_and_language_survives_reload(self):
        self.page.goto(self.url+'document-demo.html',wait_until='networkidle')
        self.page.fill('#demo-custom-department','<img src=x onerror=alert(1)> Department')
        self.assertEqual(self.page.locator('[data-demo-variant="left"] .document-department').inner_text(),'<img src=x onerror=alert(1)> Department')
        self.assertEqual(self.page.locator('.document-department img').count(),0)
        self.page.select_option('#demo-width','320')
        self.page.fill('#demo-custom-department','ВІДДІЛ ДОСЛІДЖЕННЯ ТА ОБЛІКУ ЕКСПЕРИМЕНТАЛЬНОГО ОБЛАДНАННЯ ЗАКРИТОГО МЕДИЧНОГО КОМПЛЕКСУ')
        for variant in ['left','center']:
            header=self.page.locator(f'[data-demo-variant="{variant}"] document-header')
            self.assertTrue(header.evaluate('h=>h.querySelector(".document-department").getBoundingClientRect().bottom<=h.getBoundingClientRect().bottom+1'))
        self.page.evaluate('''()=>{const layout=document.createElement('document-layout');layout.id='api-document';layout.setAttribute('variant','center');layout.setAttribute('department','documents.staff');layout.innerHTML='<p>Record</p>';document.body.append(layout);}''')
        self.assertEqual(self.page.locator('#api-document > document-header').get_attribute('variant'),'center')
        self.page.evaluate('PalataI18n.setLocale("en")')
        self.assertIn('PERSONNEL ARCHIVE',self.page.locator('#api-document').inner_text())
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('PalataI18n.locale'),'en')
        self.assertFalse(self.page.evaluate('PalataI18n.setLocale("invalid")'))
    def test_live_wardrobe_and_post_battle_protocol_keep_game_state(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("weapon","gear-aks");selectWardrobeItem("gear-aks")')
        before=self.page.evaluate('JSON.stringify({inventory,stats,paperDollState})')
        for locale in ['en','ru','uk']:
            self.page.select_option('.archive-file-note [data-document-language]',locale)
            for selector in ['.archive-letterhead document-header','.tablet-main-sheet document-header']:
                self.assertIn(self.page.evaluate('PalataI18n.t("documents.name1")'),self.page.locator(selector).inner_text())
            self.assertEqual(self.page.evaluate('JSON.stringify({inventory,stats,paperDollState})'),before)
        self.page.evaluate('discardWardrobeSession();document.getElementById("custom-modal").classList.add("hidden");stats.baseDamage=300;recalculateEquipmentStats();startBossFight("doctor");performPlayerAttack();openDetailedBattleReport()')
        self.assertTrue(self.page.locator('#battle-detail-modal document-header[variant=center]').is_visible())
        rewards=self.page.evaluate('JSON.stringify(stats)')
        self.page.evaluate('PalataI18n.setLocale("en")')
        self.assertIn('POST-BATTLE',self.page.locator('#battle-detail-modal document-header').inner_text())
        self.assertEqual(self.page.evaluate('JSON.stringify(stats)'),rewards)
        self.assertTrue(self.page.locator('#battle-detail-modal .report-actions button').count()>0)

    def test_clipboard_large_center_header_and_both_sheets_fit_without_scrolling(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeItem("weapon-demo-aks-rare")')
        self.assertIn('paper-header-only.svg',self.page.locator('.archive-letterhead').evaluate('e=>getComputedStyle(e).backgroundImage'))
        self.assertEqual(self.page.locator('.tablet-main-sheet>document-header').get_attribute('variant'),'center')
        self.assertEqual(self.page.locator('.tablet-paper-face.document-paper').count(),2)
        self.page.wait_for_function('document.querySelector(".tablet-weapon-mount img").complete&&document.querySelector(".tablet-weapon-mount img").naturalWidth>0')
        self.assertEqual(self.page.locator('.tablet-original-fasteners image').get_attribute('href'),'assets/ui/wardrobe/weapon-tablet-blank.webp')
        self.assertEqual(self.page.locator('.tablet-seal img').get_attribute('src'),'assets/ui/wardrobe/weapon-red-seal.svg')
        for width,height in [(1800,1070),(1680,1000),(1280,800),(1024,768),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.evaluate('document.querySelector(".archive-wardrobe").setAttribute("data-inspecting","true")')
            self.assertTrue(self.page.locator('.tablet-weapon-mount').evaluate('e=>{const i=e.querySelector("img"),b=i.getBoundingClientRect(),s=Math.min(b.width/i.naturalWidth,b.height/i.naturalHeight);return i.naturalWidth*s>=e.clientWidth*.65;}'),(width,height))
            for locale in ['ru','uk','en']:
                self.page.evaluate('(l)=>PalataI18n.setLocale(l,{persist:false})',locale)
                detail=self.page.locator('#wardrobe-item-detail').bounding_box()
                footer=self.page.locator('.tablet-approval-sheet').bounding_box()
                self.assertLessEqual(footer['y']+footer['height'],min(height,detail['y']+detail['height'])+1,(width,height,locale))
                self.assertTrue(self.page.locator('#wardrobe-item-detail').evaluate('e=>e.scrollHeight<=e.clientHeight+1'),(width,height,locale))
                self.assertTrue(self.page.locator('.tablet-inspection-copy').evaluate('e=>e.scrollHeight<=e.clientHeight+1'),(width,height,locale))
                signature=self.page.locator('.tablet-signature').bounding_box()
                self.assertLessEqual(signature['y']+signature['height'],footer['y']+footer['height']-12,(width,height,locale))
                for selector in ['.tablet-actions','.tablet-responsible','.tablet-seal']:
                    box=self.page.locator(selector).bounding_box()
                    self.assertGreaterEqual(box['y'],detail['y'])
                    self.assertLessEqual(box['y']+box['height'],min(height,detail['y']+detail['height'])+1,(width,height,locale,selector))

class DocumentMaterialTests(unittest.TestCase):
    def test_material_sources_and_approved_graphics_are_exact(self):
        import base64,hashlib,json,re
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        manifest=json.loads((root/'assets/ui/documents/provenance.json').read_text())
        for entry in manifest['files']:
            self.assertEqual(hashlib.sha256((root/entry['file']).read_bytes()).hexdigest(),entry['sha256'],entry['file'])
        for path,digest in manifest['approved_unchanged'].items():
            self.assertEqual(hashlib.sha256((root/path).read_bytes()).hexdigest(),digest,path)
        center=(root/'assets/ui/documents/paper-center.svg').read_text()
        data=re.search(r'data:image/jpeg;base64,([^\"]+)',center).group(1)
        self.assertEqual(base64.b64decode(data),(root/'assets/ui/documents/paper-source.jpg').read_bytes())
