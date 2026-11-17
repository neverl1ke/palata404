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
    def assert_proportional_paper(self, locator):
        """Inspect painted planes, not a CSS token which may be hidden/unused.

        A cropped, single-scale sheet is fine. Tiled paper, a stretched border
        image, an unloaded asset or a transparent pseudo-element is not.
        """
        planes=locator.evaluate('''async element=>{
            const planes=[];
            for(const pseudo of [null,'::before','::after']){
                const style=getComputedStyle(element,pseudo);
                if(style.display==='none'||Number(style.opacity)===0||pseudo&&['none','normal'].includes(style.content))continue;
                const urls=[...style.backgroundImage.matchAll(/url\\(["']?([^"')]+)["']?\\)/g)].map(match=>match[1]);
                const paper=urls.filter(url=>url.includes('weapon-paper-fine-'));
                if(!paper.length)continue;
                const images=await Promise.all(paper.map(url=>new Promise(resolve=>{
                    const image=new Image();image.onload=()=>resolve({url,width:image.naturalWidth,height:image.naturalHeight});
                    image.onerror=()=>resolve({url,width:0,height:0});image.src=url;
                })));
                planes.push({pseudo,images,size:style.backgroundSize.split(',').at(-1).trim(),
                    repeat:style.backgroundRepeat.split(',').at(-1).trim(),
                    border:style.borderImageSource,pointerEvents:style.pointerEvents});
            }
            return planes;
        }''')
        self.assertTrue(planes, 'No visible fine paper on '+str(locator))
        for plane in planes:
            self.assertEqual(plane['repeat'],'no-repeat',plane)
            self.assertEqual(plane['border'],'none',plane)
            # cover/contain always use one scale for both image dimensions.
            # Auto on either axis also preserves the source proportions.
            self.assertTrue(plane['size'] in ['cover','contain','auto'] or 'auto' in plane['size'].split(),plane)
            if plane['pseudo']:
                self.assertEqual(plane['pointerEvents'],'none',plane)
            for image in plane['images']:
                self.assertGreaterEqual(min(image['width'],image['height']),700,image)
        return planes

    def enter_trip(self):
        # Equipment documents belong to Trip. Changing a preview alone does not
        # change the quest adapter's authoritative Patient/Trip mode.
        self.page.locator('.room-trip-switch').click()
        self.page.wait_for_function('PalataQuestPrototype.snapshot().mode==="trip"')
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
                for variant in ['left','center','layout']:
                    self.assert_proportional_paper(self.page.locator(f'[data-demo-variant="{variant}"]'))
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
        self.enter_trip()
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("weapon","gear-aks");selectWardrobeItem("gear-aks")')
        before=self.page.evaluate('JSON.stringify({inventory,stats,paperDollState})')
        for locale in ['ru']:
            self.assertEqual(self.page.locator('[data-document-language]').count(),0)
            for selector in ['.archive-letterhead document-header','.p404-institution']:
                self.assertIn(self.page.evaluate('PalataI18n.t("documents.name1")'),self.page.locator(selector).inner_text())
            self.assertEqual(self.page.evaluate('JSON.stringify({inventory,stats,paperDollState})'),before)
        # Only combat damage is a fixture shortcut; access, travel, starting the
        # raid and opening its resulting protocol use the real game controls.
        self.page.evaluate('discardWardrobeSession();closeCustomization();stats.baseDamage=300;recalculateEquipmentStats()')
        self.page.locator('#quest-unlock-all').click()
        self.page.locator('#location-card-box').click()
        self.page.locator('.quest-map-pin[data-room="doctor"]').dblclick(delay=40)
        self.page.wait_for_function('PalataQuestPrototype.snapshot().room==="doctor"')
        before_fight=self.page.evaluate('({level:stats.level,silver:stats.silver,pills:stats.pills,bucks:stats.bucks})')
        self.page.locator('[data-action="boss:doctor"]').click()
        self.page.wait_for_function('isBattleActive')
        self.page.locator('#battle-arena-screen').click(position={'x':600,'y':300})
        self.page.locator('#nurse-victory-modal').wait_for(state='visible')
        after_fight=self.page.evaluate('({level:stats.level,silver:stats.silver,pills:stats.pills,bucks:stats.bucks,payout:lastBattleResult.payout.silver})')
        levels=after_fight['level']-before_fight['level']
        self.assertGreater(levels,0)
        self.assertEqual(after_fight['silver']-before_fight['silver'],after_fight['payout']+100*levels)
        self.assertEqual(after_fight['pills']-before_fight['pills'],50*levels)
        self.assertEqual(after_fight['bucks']-before_fight['bucks'],5*levels)
        from pathlib import Path
        capture=Path('/dev/shm/paper-unification-20261117/level-notice-after.png')
        capture.parent.mkdir(parents=True,exist_ok=True)
        for _ in range(levels):
            notice=self.page.locator('#level-notice[open]')
            self.assert_proportional_paper(notice.locator('article'))
            self.assertEqual(notice.locator('li').count(),3)
            self.page.screenshot(path=str(capture))
            notice.locator('button').click()
        self.assertEqual(self.page.locator('#level-notice[open]').count(),0)
        self.page.locator('#nurse-victory-modal [onclick="openDetailedBattleReport()"]').click()
        self.assertTrue(self.page.locator('#battle-detail-modal document-header[variant=center]').is_visible())
        rewards=self.page.evaluate('JSON.stringify(stats)')
        self.page.evaluate('PalataI18n.setLocale("en")')
        self.assertIn('ПОСЛЕБОЕВОГО',self.page.locator('#battle-detail-modal document-header').inner_text())
        self.assertEqual(self.page.evaluate('JSON.stringify(stats)'),rewards)
        self.assertTrue(self.page.locator('#battle-detail-modal .report-actions button').count()>0)

    def test_clipboard_preserves_both_sheets_and_scrolls_to_reachable_actions(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.enter_trip()
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null);selectWardrobeItem("weapon-demo-aks-rare")')
        header_material=self.page.locator('.archive-letterhead').evaluate('e=>{const s=getComputedStyle(e);return {image:s.backgroundImage,size:s.backgroundSize,repeat:s.backgroundRepeat}}')
        self.assertIn('composed/wardrobe-header.svg',header_material['image'])
        self.assertEqual(header_material['size'],'contain')
        self.assertEqual(header_material['repeat'],'no-repeat')
        self.assertEqual(self.page.locator('.archive-letterhead .document-emblem').get_attribute('src'),'assets/ui/wardrobe/requested-header-emblem.webp')
        self.assertEqual(self.page.locator('.p404-institution').evaluate('e=>getComputedStyle(e).textAlign'),'center')
        self.assertEqual(self.page.locator('.p404-slip-document-header').evaluate('e=>getComputedStyle(e).textAlign'),'left')
        self.assertEqual(self.page.locator('.p404-board-art,.p404-slip-art').count(),2)
        self.page.wait_for_function('document.querySelector(".p404-mount-gun").complete&&document.querySelector(".p404-mount-gun").naturalWidth>0')
        self.assertEqual(self.page.locator('.p404-board-art').get_attribute('src'),'assets/ui/wardrobe/clipboard-v2/board-original.png')
        for selector,name in [('.p404-board-art','weapon-board'),('.p404-slip-art','weapon-slip')]:
            self.assertIn('composed/'+name+'.svg',self.page.locator(selector).evaluate('e=>getComputedStyle(e).content'))
        self.assertEqual(self.page.locator('.p404-slip-seal').get_attribute('src'),'assets/ui/wardrobe/weapon-red-seal.svg')
        for width,height in [(1800,1070),(1680,1000),(1280,800),(1024,768),(390,844),(320,568)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.evaluate('document.querySelector(".archive-wardrobe").setAttribute("data-inspecting","true")')
            self.assertTrue(self.page.locator('.p404-mount').evaluate('e=>{const i=e.querySelector(".p404-mount-gun"),b=i.getBoundingClientRect(),s=Math.min(b.width/i.naturalWidth,b.height/i.naturalHeight);return i.naturalWidth*s>=e.clientWidth*.65;}'),(width,height))
            for locale in ['ru']:
                self.page.evaluate('(l)=>PalataI18n.setLocale(l,{persist:false})',locale)
                detail=self.page.locator('#wardrobe-item-detail').bounding_box()
                footer=self.page.locator('.p404-slip').bounding_box()
                # The document may scroll vertically instead of shrinking text and controls.
                self.assertTrue(self.page.locator('#wardrobe-item-detail').evaluate('e=>e.scrollWidth<=e.clientWidth+1'),(width,height,locale))
                self.assertTrue(self.page.locator('.p404-copy').evaluate('e=>e.scrollHeight<=e.clientHeight+1'),(width,height,locale))
                signature=self.page.locator('.p404-signature').bounding_box()
                self.assertLessEqual(signature['y']+signature['height'],footer['y']+footer['height']-1,(width,height,locale))
                for selector in ['.p404-actions','.p404-signoff','.p404-slip-seal']:
                    self.page.locator(selector).scroll_into_view_if_needed()
                    box=self.page.locator(selector).bounding_box()
                    self.assertGreaterEqual(box['y'],detail['y'])
                    self.assertLessEqual(box['y']+box['height'],min(height,detail['y']+detail['height'])+1,(width,height,locale,selector))

    def test_settings_and_quest_paper_keep_text_controls_and_progress(self):
        self.load()
        before=self.page.evaluate('JSON.stringify({inventory,paperDollState,level:stats.level,exp:stats.exp,silver:stats.silver,pills:stats.pills,bucks:stats.bucks,quests:PalataQuestPrototype.snapshot()})')
        for width,height in [(1280,800),(844,390),(390,844)]:
            with self.subTest(width=width,height=height):
                self.page.set_viewport_size({'width':width,'height':height})
                self.page.evaluate('openSettings()')
                settings=self.page.locator('#settings-modal .settings-paper')
                self.assert_proportional_paper(settings)
                self.assertEqual(settings.locator('.settings-action-label').count(),4)
                self.assertTrue(settings.evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
                close=settings.locator('.btn-close-mini')
                close.scroll_into_view_if_needed();close.focus()
                self.assertTrue(close.evaluate('e=>document.activeElement===e'))
                close.press('Enter')
                self.assertTrue(self.page.locator('#settings-modal').is_hidden())
                task_button=self.page.locator('.hud-task')
                task_button.scroll_into_view_if_needed();task_button.click()
                journal=self.page.locator('#tasks-modal .quest-sheet')
                self.assert_proportional_paper(journal)
                self.assertEqual(journal.locator('#tasks-title').inner_text(),'Задания · 10-й этаж')
                for category,title in [('nurse','Клара'),('doctor','Врач'),('story','Сюжет')]:
                    tab=journal.locator(f'[data-quest-tab="{category}"]')
                    tab.scroll_into_view_if_needed();tab.click()
                    self.assertEqual(tab.get_attribute('aria-pressed'),'true')
                    self.assertEqual(tab.inner_text(),title)
                    self.assertTrue(journal.evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
                close=journal.get_by_role('button',name='Закрыть задания',exact=True)
                close.scroll_into_view_if_needed();close.click()
                self.assertTrue(self.page.locator('#tasks-modal').is_hidden())
        after=self.page.evaluate('JSON.stringify({inventory,paperDollState,level:stats.level,exp:stats.exp,silver:stats.silver,pills:stats.pills,bucks:stats.bucks,quests:PalataQuestPrototype.snapshot()})')
        self.assertEqual(after,before,'Changing paper or browsing documents changed player progress')

    def test_compact_settings_and_dossier_titles_stay_centred_clear_and_whole(self):
        self.load()
        for width,height in [(320,568),(390,844)]:
            self.page.set_viewport_size({'width':width,'height':height})
            for open_action,selector in [('openSettings()','#settings-modal'),('openDossier()','#dossier-modal')]:
                with self.subTest(width=width,modal=selector):
                    self.page.evaluate(open_action)
                    modal=self.page.locator(selector)
                    heading=modal.locator('.modal-header>h3')
                    geometry=heading.evaluate('''heading=>{
                        const box=heading.getBoundingClientRect(),paper=heading.closest('.modal-content').getBoundingClientRect();
                        const walker=document.createTreeWalker(heading,NodeFilter.SHOW_TEXT),words=[],glyphs=[];
                        while(walker.nextNode()){
                            const node=walker.currentNode;
                            if(!node.textContent.trim())continue;
                            const pattern=/\\S+/g;let match;
                            while((match=pattern.exec(node.textContent))){
                                const word=document.createRange();word.setStart(node,match.index);word.setEnd(node,match.index+match[0].length);
                                words.push({word:match[0],lines:word.getClientRects().length});
                                glyphs.push(...word.getClientRects());
                            }
                        }
                        const close=heading.parentElement.querySelector('button').getBoundingClientRect();
                        const icon=heading.querySelector('.game-icon')?.getBoundingClientRect();
                        const stamp=heading.closest('.modal-content').querySelector('.dossier-header-stamp')?.getBoundingClientRect();
                        const ink={left:Math.min(...glyphs.map(r=>r.left)),right:Math.max(...glyphs.map(r=>r.right)),top:Math.min(...glyphs.map(r=>r.top)),bottom:Math.max(...glyphs.map(r=>r.bottom))};
                        return {box:box.toJSON(),paper:paper.toJSON(),ink,close:close.toJSON(),icon:icon?.toJSON(),stamp:stamp?.toJSON(),words};
                    }''')
                    self.assertLessEqual(abs(geometry['box']['x']+geometry['box']['width']/2-geometry['paper']['x']-geometry['paper']['width']/2),1,geometry)
                    self.assertGreaterEqual(geometry['ink']['left'],geometry['box']['left']-1,geometry)
                    self.assertLessEqual(geometry['ink']['right'],geometry['box']['right']+1,geometry)
                    self.assertTrue(all(word['lines']==1 for word in geometry['words']),geometry)
                    def overlaps(a,b):
                        return min(a['right'],b['right'])>max(a['left'],b['left'])+1 and min(a['bottom'],b['bottom'])>max(a['top'],b['top'])+1
                    self.assertFalse(overlaps(geometry['ink'],geometry['close']),geometry)
                    if selector=='#settings-modal' and width<=360:
                        self.assertLessEqual(abs(geometry['icon']['top']+geometry['icon']['height']/2-geometry['close']['top']-geometry['close']['height']/2),2,geometry)
                    if geometry['stamp']:
                        self.assertFalse(overlaps(geometry['stamp'],geometry['ink']),geometry)
                        self.assertFalse(overlaps(geometry['stamp'],geometry['close']),geometry)
                    modal.locator('.btn-close-mini').click()

    def test_landscape_wardrobe_slot_titles_fit_and_centre_inside_their_frames(self):
        self.load();self.page.set_viewport_size({'width':844,'height':390})
        self.enter_trip();self.page.locator('.room-cabinet-action').click()
        self.page.locator('#custom-modal').wait_for(state='visible')
        self.page.wait_for_function('''()=>{
            const labels=[...document.querySelectorAll('#custom-modal .archive-slot>span')];
            return labels.length===12&&labels.every(label=>{
                const box=label.parentElement.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(label);
                const ink=range.getBoundingClientRect();return box.width>0&&box.height>0&&ink.width>0&&ink.height>0;
            });
        }''')
        labels=self.page.locator('#custom-modal .archive-slot>span').evaluate_all('''labels=>labels.map(label=>{
            const range=document.createRange();range.selectNodeContents(label);
            return {text:label.innerText,ink:range.getBoundingClientRect().toJSON(),frame:label.parentElement.getBoundingClientRect().toJSON()};
        })''')
        self.assertEqual(len(labels),12)
        self.assertTrue(any(label['text']=='Бронежилет' for label in labels))
        for label in labels:
            self.assertGreaterEqual(label['ink']['left'],label['frame']['left']+1,label)
            self.assertLessEqual(label['ink']['right'],label['frame']['right']-1,label)
            self.assertLessEqual(abs(label['ink']['left']+label['ink']['width']/2-label['frame']['left']-label['frame']['width']/2),1.5,label)
        title=self.page.locator('.wardrobe-items-heading h4').evaluate('''heading=>{
            const range=document.createRange();range.selectNodeContents(heading);
            return {ink:range.getBoundingClientRect().toJSON(),frame:heading.parentElement.getBoundingClientRect().toJSON()};
        }''')
        self.assertLessEqual(abs(title['ink']['left']+title['ink']['width']/2-title['frame']['left']-title['frame']['width']/2),1.5,title)

    def test_rarity_marks_keep_rectangle_geometry_and_insert_titles_follow_progress(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.enter_trip()
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

    def test_clipboard_preserves_aspect_ratio_and_single_line_palette(self):
        self.load();self.page.set_viewport_size({'width':1800,'height':1070})
        self.enter_trip()
        self.page.evaluate('openCustomization();selectWardrobeItem("weapon-demo-aks-experimental")')
        for width,height in [(1800,1070),(1680,1000),(1280,800)]:
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.wait_for_function("""()=>{const board=document.querySelector('.p404-board');return board.clientWidth>0&&board.clientHeight>0;}""")
            self.assertTrue(self.page.locator('#wardrobe-item-detail').evaluate('e=>e.scrollWidth<=e.clientWidth+1'))
            ratio=self.page.locator('.p404-board').evaluate('e=>e.clientWidth/e.clientHeight')
            self.assertAlmostEqual(ratio,1054/1492,delta=.003)
            # Raid loadout buttons reuse this class even while their battle
            # screen is hidden. This assertion is about the wardrobe palette.
            cards=self.page.locator('.archive-wardrobe .wardrobe-item-card:has(.weapon-icon-frame)')
            self.assertTrue(cards.evaluate_all("""cards=>cards.every(e=>{const n=e.querySelector('.wardrobe-item-name'),r=n.getBoundingClientRect();return Math.abs(r.height-parseFloat(getComputedStyle(n).lineHeight))<1;})"""))
            rights=cards.evaluate_all("""cards=>cards.slice(0,4).map(e=>e.getBoundingClientRect().right-e.querySelector('.archive-rarity-mark b').getBoundingClientRect().right)""")
            self.assertLess(max(rights)-min(rights),1)
        self.assertEqual(self.page.locator('.archive-wardrobe').get_attribute('data-palette-shadow'),'strong')
        self.assertEqual(self.page.locator('.p404-title-underline').count(),1)
        self.assertGreater(self.page.locator('.p404-redacted path').count(),1)

class DocumentMaterialTests(unittest.TestCase):
    def test_composed_paper_keeps_source_hardware_and_uses_unstretched_native_material(self):
        import base64,hashlib,json
        from pathlib import Path
        import xml.etree.ElementTree as ET
        root=Path(__file__).resolve().parents[1]
        directory=root/'assets/ui/documents/composed'
        manifest=json.loads((directory/'manifest.json').read_text())
        namespace={'s':'http://www.w3.org/2000/svg'}
        materials={path.read_bytes() for path in (root/'assets/ui/documents').glob('weapon-paper-fine-*.webp')}
        self.assertEqual(len(materials),3)
        for name,entry in manifest['files'].items():
            with self.subTest(surface=name):
                source=(root/entry['source']).read_bytes()
                self.assertEqual(hashlib.sha256(source).hexdigest(),entry['source_sha256'])
                tree=ET.fromstring((directory/name).read_text())
                self.assertEqual(tree.get('viewBox'),'0 0 '+' '.join(map(str,entry['size'])))
                hardware_only=name=='map-hardware.svg' or name.startswith('rarity-')
                if not hardware_only:
                    self.assertNotEqual(tree.get('preserveAspectRatio'),'none')
                original=tree.find('.//s:image[@id="original"]',namespace)
                self.assertIsNotNone(original)
                embedded_source=base64.b64decode(original.get('href').split(',',1)[1])
                if entry['source'].endswith('.svg'):
                    self.assertEqual(embedded_source,source)
                else:
                    # Lossless WebP may store the same original pixels more
                    # compactly inside the SVG. Encoding bytes need not match.
                    from io import BytesIO
                    from PIL import Image
                    with Image.open(BytesIO(source)) as expected,Image.open(BytesIO(embedded_source)) as actual:
                        self.assertEqual(actual.size,expected.size)
                        self.assertEqual(actual.convert('RGBA').tobytes(),expected.convert('RGBA').tobytes(),'Source hardware pixels changed: '+name)
                original_layer=tree.find('./s:use[@href="#original"]',namespace)
                self.assertIsNotNone(original_layer,'Source hardware has no active layer')
                if hardware_only:
                    # Paper is a separate CSS cover plane because these layouts
                    # change proportions. These SVGs contain hardware only.
                    self.assertEqual(original_layer.get('mask'),'url(#hardware)')
                    continue
                face_group=next((group for group in tree.findall('./s:g',namespace) if group.find('s:image',namespace) is not None),None)
                self.assertIsNotNone(face_group,'Paper exists only in unused definitions')
                self.assertTrue(face_group.get('mask') or face_group.get('clip-path'),'Paper paints over original hardware without a region mask')
                face=face_group.find('s:image',namespace)
                self.assertIsNotNone(face,'Paper exists only in unused definitions')
                self.assertIn(base64.b64decode(face.get('href').split(',',1)[1]),materials)
                self.assertEqual(face.get('preserveAspectRatio'),'xMidYMid slice')

    def test_generated_fine_paper_formats_are_real_distinct_native_images(self):
        import hashlib,json
        from pathlib import Path
        from PIL import Image
        root=Path(__file__).resolve().parents[1]
        manifest=json.loads((root/'assets/ui/documents/weapon-paper-fine-provenance.json').read_text())
        self.assertEqual(set(manifest['variants']),{'landscape','portrait','strip'})
        dimensions={}
        hashes=[]
        for name,entry in manifest['variants'].items():
            path=root/entry['asset']
            with Image.open(path) as image:
                image.load()
                self.assertEqual(list(image.size),entry['dimensions'],name)
                self.assertGreaterEqual(min(image.size),700,name)
                self.assertGreater(len(image.getcolors(maxcolors=256) or range(257)),256,name+' has a flat replacement instead of paper texture')
                dimensions[name]=image.width/image.height
            hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(set(hashes)),3,'Format alternatives reuse the same image')
        self.assertLess(dimensions['portrait'],1)
        self.assertGreater(dimensions['landscape'],1)
        self.assertGreater(dimensions['strip'],2.5)

    def test_preserved_original_material_and_graphic_sources_are_unchanged(self):
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
