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
    def test_both_headers_russian_text_and_sizes_keep_graphics_and_alignment(self):
        self.page.goto(self.url+'document-demo.html',wait_until='networkidle')
        self.page.evaluate('document.fonts.ready')
        for width in [960,640,320]:
            self.page.select_option('#demo-width',str(width))
            graphics=None
            for locale in ['ru']:
                self.page.evaluate('(l)=>PalataI18n.setLocale(l)',locale)
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
    def test_custom_department_layout_api_safe_text_and_russian_ignores_saved_locale(self):
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
        self.assertFalse(self.page.evaluate('PalataI18n.setLocale("en")'))
        self.assertIn('АРХИВ ПЕРСОНАЛА',self.page.locator('#api-document').inner_text())
        self.page.evaluate('localStorage.setItem("palata404_locale","uk")')
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('PalataI18n.locale'),'ru')
        self.assertEqual(self.page.locator('[data-document-language]').count(),0)
        self.assertFalse(self.page.evaluate('PalataI18n.setLocale("invalid")'))
    def test_live_wardrobe_and_post_battle_protocol_keep_game_state(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("weapon","gear-aks");selectWardrobeItem("gear-aks")')
        before=self.page.evaluate('JSON.stringify({inventory,stats,paperDollState})')
        for locale in ['ru']:
            self.assertEqual(self.page.locator('[data-document-language]').count(),0)
            for selector in ['.archive-letterhead document-header','.p404-institution']:
                self.assertIn(self.page.evaluate('PalataI18n.t("documents.name1")'),self.page.locator(selector).inner_text())
            self.assertEqual(self.page.evaluate('JSON.stringify({inventory,stats,paperDollState})'),before)
        self.page.evaluate('discardWardrobeSession();document.getElementById("custom-modal").classList.add("hidden");stats.baseDamage=300;recalculateEquipmentStats();startBossFight("doctor");performPlayerAttack();openDetailedBattleReport()')
        self.assertTrue(self.page.locator('#battle-detail-modal document-header[variant=center]').is_visible())
        rewards=self.page.evaluate('JSON.stringify(stats)')
        self.page.evaluate('PalataI18n.setLocale("en")')
        self.assertIn('ПОСЛЕБОЕВОГО',self.page.locator('#battle-detail-modal document-header').inner_text())
        self.assertEqual(self.page.evaluate('JSON.stringify(stats)'),rewards)
        self.assertTrue(self.page.locator('#battle-detail-modal .report-actions button').count()>0)

    def test_clipboard_large_center_header_and_both_sheets_fit_without_scrolling(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeItem("weapon-demo-aks-rare")')
        self.assertIn('paper-header-only.svg',self.page.locator('.archive-letterhead').evaluate('e=>getComputedStyle(e).backgroundImage'))
        self.assertEqual(self.page.locator('.p404-institution').evaluate('e=>getComputedStyle(e).textAlign'),'center')
        self.assertEqual(self.page.locator('.p404-slip-document-header').evaluate('e=>getComputedStyle(e).textAlign'),'left')
        self.assertEqual(self.page.locator('.p404-board-art,.p404-slip-art').count(),2)
        self.page.wait_for_function('document.querySelector(".p404-mount-gun").complete&&document.querySelector(".p404-mount-gun").naturalWidth>0')
        self.assertEqual(self.page.locator('.p404-board-art').get_attribute('src'),'assets/ui/wardrobe/clipboard-v2/board-original.png')
        self.assertEqual(self.page.locator('.p404-slip-seal').get_attribute('src'),'assets/ui/wardrobe/weapon-red-seal.svg')
        for width,height in [(1800,1070),(1680,1000),(1280,800),(1024,768),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.evaluate('document.querySelector(".archive-wardrobe").setAttribute("data-inspecting","true")')
            self.assertTrue(self.page.locator('.p404-mount').evaluate('e=>{const i=e.querySelector(".p404-mount-gun"),b=i.getBoundingClientRect(),s=Math.min(b.width/i.naturalWidth,b.height/i.naturalHeight);return i.naturalWidth*s>=e.clientWidth*.65;}'),(width,height))
            for locale in ['ru']:
                self.page.evaluate('(l)=>PalataI18n.setLocale(l,{persist:false})',locale)
                detail=self.page.locator('#wardrobe-item-detail').bounding_box()
                footer=self.page.locator('.p404-slip').bounding_box()
                self.assertLessEqual(footer['y']+footer['height'],min(height,detail['y']+detail['height'])+1,(width,height,locale))
                self.assertTrue(self.page.locator('#wardrobe-item-detail').evaluate('e=>e.scrollHeight<=e.clientHeight+1'),(width,height,locale))
                self.assertTrue(self.page.locator('.p404-copy').evaluate('e=>e.scrollHeight<=e.clientHeight+1'),(width,height,locale))
                signature=self.page.locator('.p404-signature').bounding_box()
                self.assertLessEqual(signature['y']+signature['height'],footer['y']+footer['height']-1,(width,height,locale))
                for selector in ['.p404-actions','.p404-signoff','.p404-slip-seal']:
                    box=self.page.locator(selector).bounding_box()
                    self.assertGreaterEqual(box['y'],detail['y'])
                    self.assertLessEqual(box['y']+box['height'],min(height,detail['y']+detail['height'])+1,(width,height,locale,selector))

    def test_rarity_marks_keep_rectangle_geometry_and_insert_titles_follow_progress(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.page.evaluate('openCustomization();selectWardrobeItem("weapon-demo-aks-rare")')
        for locale in ['ru']:
            self.page.evaluate('(locale)=>PalataI18n.setLocale(locale,{persist:false})',locale)
            titles=self.page.evaluate("""()=>Object.keys(WEAPON_RARITIES).flatMap(rarity=>Array.from({length:7},(_,i)=>archiveInsertHeading({rarity,upgradeLevel:Math.min(i,5),absolute:i===6})))""")
            self.assertEqual(len(set(titles)),28,(locale,titles))
            self.assertIn('АРХИВНАЯ МОДИФИКАЦИЯ',self.page.locator('.p404-slip-title').inner_text())
            self.assertIn('V',self.page.locator('.p404-slip-series').inner_text())
            self.assertEqual(self.page.locator('[data-weapon-modules]').count(),0)
            self.assertIn(self.page.evaluate('PalataI18n.t("insert.rifles")'),self.page.locator('.p404-info').inner_text())
            self.assertTrue(self.page.locator('.archive-rarity-mark b').evaluate_all("""marks=>marks.every(e=>{const m=new DOMMatrix(getComputedStyle(e).transform);return Math.abs(m.a*m.c+m.b*m.d)<.00001&&Math.abs(Math.hypot(m.a,m.b)-Math.hypot(m.c,m.d))<.00001;})"""))
            for width,height in [(1800,1070),(1280,800),(390,844),(320,568)]:
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('document.querySelector(".archive-wardrobe").setAttribute("data-inspecting","true")')
                self.page.wait_for_timeout(40)
                mount=self.page.locator('.p404-mount').bounding_box()
                progress=self.page.locator('.p404-progress').bounding_box()
                self.assertLessEqual(abs(progress['y']-mount['y']-mount['height']),8,(width,locale))
                self.assertTrue(self.page.locator('.p404-copy').evaluate('e=>e.scrollHeight<=e.clientHeight+1'),(width,locale))
                self.assertTrue(self.page.locator('.p404-case').evaluate("""e=>[...e.children].every(row=>{const b=row.getBoundingClientRect(),label=row.querySelector('dt').getBoundingClientRect(),value=row.querySelector('dd').getBoundingClientRect();return label.bottom<=value.top+1&&value.bottom<=b.bottom+1&&b.right<=e.getBoundingClientRect().right+1;})"""),(width,locale))
                self.assertTrue(self.page.locator('.archive-rarity-mark').evaluate_all("""marks=>marks.every(e=>e.querySelector('small').getBoundingClientRect().top>=e.querySelector('b').getBoundingClientRect().bottom+1)"""))
        self.assertEqual(self.page.locator('.p404-signature image').get_attribute('href'),'assets/ui/wardrobe/weapon-doctor-signature.svg')

    def test_full_height_clipboard_and_single_line_palette_share_aligned_edges(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.page.evaluate('openCustomization();selectWardrobeItem("weapon-demo-aks-experimental")')
        for width,height in [(1800,1070),(1680,1000),(1280,800)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.wait_for_function("""()=>{const frame=document.querySelector('.p404-backing').getBoundingClientRect(),catalog=document.querySelector('.wardrobe-items').getBoundingClientRect();return Math.abs(frame.top-catalog.top)<1&&Math.abs(frame.bottom-catalog.bottom)<1;}""")
            ratio=self.page.locator('.p404-board').evaluate('e=>e.clientWidth/e.clientHeight')
            self.assertAlmostEqual(ratio,1054/1492,delta=.003)
            cards=self.page.locator('.wardrobe-item-card:has(.weapon-icon-frame)')
            self.assertTrue(cards.evaluate_all("""cards=>cards.every(e=>{const n=e.querySelector('.wardrobe-item-name'),r=n.getBoundingClientRect();return Math.abs(r.height-parseFloat(getComputedStyle(n).lineHeight))<1;})"""))
            rights=cards.evaluate_all("""cards=>cards.slice(0,4).map(e=>e.getBoundingClientRect().right-e.querySelector('.archive-rarity-mark b').getBoundingClientRect().right)""")
            self.assertLess(max(rights)-min(rights),1)
        self.assertEqual(self.page.locator('.archive-wardrobe').get_attribute('data-palette-shadow'),'strong')
        self.assertEqual(self.page.locator('.p404-title-underline').count(),1)
        self.assertGreater(self.page.locator('.p404-redacted path').count(),1)

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
