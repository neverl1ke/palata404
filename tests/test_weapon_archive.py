"""Production integration: independent weapons, real draft, battle and approved UI."""
import json,unittest
from pathlib import Path
from tests import test_game as support
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-results/weapon-archive'
class WeaponArchiveBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        support.GameTests.setUpClass.__func__(cls);OUT.mkdir(parents=True,exist_ok=True)
    @classmethod
    def tearDownClass(cls):support.GameTests.tearDownClass.__func__(cls)
    setUp=support.GameTests.setUp
    tearDown=support.GameTests.tearDown
    load=support.GameTests.load
    def ready_pose(self,pose):
        self.page.wait_for_function('''p=>{const h=document.getElementById('wardrobe-paperdoll'),s=avatarCoreGamePreview.instances.get(h);return h.dataset.avatarCoreReady==='true'&&s?.engine.pose===p&&!s.running}''',arg=pose,timeout=60000)
    def open(self):
        self.page.evaluate('openCustomization();setPaperDollView("combat");equipPaperDollItem("upperBody",null)')
    def test_four_rarities_one_sprite_readable_single_tablet_and_saved_avatar(self):
        self.load();self.page.set_viewport_size({'width':1680,'height':1000});self.open()
        self.page.evaluate('setGender("female");equipPaperDollItem("hair","hair-bob");selectWardrobeItem("gear-aks");applyWardrobeItemAction()');self.ready_pose('rifle')
        cards=self.page.locator('#wardrobe-container [data-wardrobe-card]')
        self.assertEqual(cards.count(),6)
        self.assertEqual(cards.evaluate_all('(es)=>es.slice(0,4).map(e=>e.dataset.rarity)'),['common','improved','rare','experimental'])
        self.assertEqual(len(set(cards.locator('img').evaluate_all('(es)=>es.slice(0,4).map(e=>e.getAttribute("src"))'))),1)
        self.assertEqual(self.page.locator('.archive-tablet').count(),1)
        self.assertEqual(self.page.evaluate('getEquippedItem("weapon")'),None)
        self.assertGreaterEqual(self.page.locator('.weapon-stat-grid').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)'),14)
        self.assertIn('Palata Typewriter',self.page.locator('body').evaluate('e=>getComputedStyle(e).fontFamily'))
        self.assertEqual(self.page.evaluate("[...document.querySelectorAll('body *')].filter(e=>!getComputedStyle(e).fontFamily.includes('Palata Typewriter')).map(e=>e.tagName+'.'+e.className).slice(0,10)"),[])
        self.page.screenshot(path=str(OUT/'four-rarities-female.png'))
        self.assertTrue(self.page.evaluate('applyWardrobeSession()'))
        self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()');self.ready_pose('rifle')
        self.assertEqual(self.page.evaluate('paperDollState.selectedGender'),'female')
        self.assertEqual(self.page.evaluate('getCombatWeaponStats().weaponDamage'),35)
    def test_upgrade_plus_three_modules_and_absolute_use_real_resources(self):
        self.load({'palata404_stats':json.dumps({'silver':10000,'equipmentParts':100,'experimentalComponents':2})});self.page.set_default_timeout(60000);self.page.set_viewport_size({'width':1680,'height':1000});self.open()
        self.page.evaluate('selectWardrobeItem("gear-aks");applyWardrobeItemAction()');self.ready_pose('rifle')
        for level in [1,2,3]:
            self.page.locator('[data-weapon-upgrade]').click(no_wait_after=True);self.page.locator('#weapon-dialog').get_by_role('button',name='Подтвердить',exact=True).click(no_wait_after=True)
            self.assertEqual(self.page.evaluate('weaponInventoryItem("gear-aks").upgradeLevel'),level)
        self.assertEqual(self.page.evaluate('stats.silver'),9050)
        self.assertIn('41',self.page.locator('.weapon-stat-grid').inner_text())
        self.page.screenshot(path=str(OUT/'tablet-plus-three.png'))
        self.page.locator('[data-weapon-modules]').click(no_wait_after=True)
        self.page.locator('[data-install-module="mechanism:accelerated"]').click(no_wait_after=True)
        self.page.locator('#weapon-dialog').get_by_role('button',name='Приобрести и установить',exact=True).click(no_wait_after=True)
        self.page.locator('#weapon-dialog').get_by_role('button',name='Закрыть',exact=True).click(no_wait_after=True)
        self.assertIn('3.8',self.page.locator('.weapon-stat-grid').inner_text())
        for _ in range(3):
            self.page.locator('[data-weapon-upgrade]').click(no_wait_after=True);self.page.locator('#weapon-dialog').get_by_role('button',name='Подтвердить',exact=True).click(no_wait_after=True)
        self.assertTrue(self.page.evaluate('weaponInventoryItem("gear-aks").absolute'))
        self.assertIn('54',self.page.locator('.weapon-stat-grid').inner_text())
        self.assertIn('ПРЕДЕЛЬНАЯ',self.page.locator('.tablet-approval').inner_text())
        self.page.screenshot(path=str(OUT/'tablet-absolute.png'))
        self.assertTrue(self.page.locator('[data-weapon-upgrade]').is_disabled())
        self.page.evaluate('applyWardrobeSession()');self.page.reload(wait_until='networkidle');self.page.evaluate('openCustomization()')
        self.assertEqual(self.page.evaluate('getCombatWeaponStats().weaponDamage'),54)
        self.assertAlmostEqual(self.page.evaluate('getCombatWeaponStats().cooldown'),3.8)
    def test_draft_close_keyboard_cancel_apply_and_old_save_migration(self):
        self.load({'palata404_equipped':json.dumps({'weapon':'Штурмовий АКС-74У','helmet':None,'armor':None}),'palata404_gender':'male'})
        before=self.page.evaluate('JSON.stringify(paperDollState)');self.open()
        self.page.evaluate('setGender("female");equipPaperDollItem("weapon","weapon-demo-aks-rare")')
        self.page.keyboard.press('Escape');self.page.locator('#weapon-dialog').get_by_role('button',name='Отменить изменения',exact=True).click(no_wait_after=True)
        self.assertEqual(self.page.evaluate('JSON.stringify(paperDollState)'),before)
        self.assertEqual(self.page.evaluate('getEquippedItem("weapon").rarity'),'common')
        self.open();self.page.evaluate('equipPaperDollItem("weapon","weapon-demo-aks-experimental")')
        self.page.locator('.archive-footer').get_by_role('button',name='Применить',exact=True).click(no_wait_after=True)
        self.assertEqual(self.page.evaluate('stats.damage'),64)
        self.page.evaluate('closeCustomization()');self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('getEquippedItem("weapon").rarity'),'experimental')
    def test_all_instances_keep_approved_poses_both_genders_and_temporary_hide(self):
        self.load();self.open()
        for gender in ['male','female']:
            self.page.evaluate('g=>setGender(g)',gender)
            for id in ['gear-aks','weapon-demo-aks-improved','weapon-demo-aks-rare','weapon-demo-aks-experimental']:
                self.page.evaluate('id=>equipPaperDollItem("weapon",id)',id);self.ready_pose('rifle')
            self.page.locator('[data-hide-slot="weapon"]').click(no_wait_after=True);self.ready_pose('idle')
            self.page.locator('[data-hide-slot="weapon"]').click(no_wait_after=True);self.ready_pose('rifle')
            self.page.evaluate('equipPaperDollItem("weapon","gear-knife")');self.ready_pose('melee')
            self.page.evaluate('equipPaperDollItem("weapon",null)');self.ready_pose('idle')
            self.page.screenshot(path=str(OUT/f'{gender}-idle.png'))
        # The eye must also invalidate the static clothing composition cache.
        self.page.evaluate('setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")')
        self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"&&!document.getElementById("wardrobe-paperdoll").hasAttribute("data-paper-loading")')
        self.page.locator('[data-hide-slot="upperBody"]').click(no_wait_after=True);self.ready_pose('idle')
        self.assertEqual(self.page.locator('#wardrobe-layer-upper-body-front').count(),0)
        self.page.locator('[data-hide-slot="upperBody"]').click(no_wait_after=True)
        self.page.wait_for_function('document.getElementById("wardrobe-paperdoll").dataset.avatarCoreBlocked==="clothing"&&!document.getElementById("wardrobe-paperdoll").hasAttribute("data-paper-loading")')
        self.assertEqual(self.page.locator('#wardrobe-layer-upper-body-front').count(),1)
    def test_responsive_rails_catalog_detail_and_upgrade_dialog_stay_accessible(self):
        self.load();self.open();self.page.set_default_timeout(60000)
        for width,height in [(1680,1000),(1280,800),(1024,768),(768,1024),(390,844),(320,568)]:
            print('Responsive viewport',width,height,flush=True)
            self.page.set_viewport_size({'width':width,'height':height})
            self.page.evaluate('document.querySelector(".archive-wardrobe").removeAttribute("data-inspecting")')
            self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            self.assertTrue(self.page.locator('.archive-footer').get_by_role('button',name='Применить',exact=True).is_visible())
            self.assertTrue(self.page.evaluate('''()=>{const b=document.querySelector('.archive-footer').getBoundingClientRect();return b.bottom<=innerHeight+1}'''))
            self.page.locator('[data-wardrobe-card="gear-aks"]').click(no_wait_after=True)
            self.assertTrue(self.page.locator('.archive-tablet').is_visible())
            self.page.locator('[data-weapon-upgrade]').scroll_into_view_if_needed();self.page.locator('[data-weapon-upgrade]').click(no_wait_after=True)
            self.assertTrue(self.page.locator('#weapon-dialog').is_visible())
            self.page.locator('#weapon-dialog').get_by_role('button',name='Назад',exact=True).click(no_wait_after=True)
            if width==390:self.page.screenshot(path=str(OUT/'mobile-tablet.png'))
            if width<=1100:self.page.locator('.archive-detail-close').click(no_wait_after=True)
            self.page.screenshot(path=str(OUT/f'wardrobe-{width}x{height}.png'))
    def test_browser_manual_cooldown_miss_reload_and_material_reward(self):
        self.load();self.page.clock.install();self.page.evaluate('setPaperDollView("combat");equipPaperDollItem("weapon","gear-aks");stats.baseArmor=10000;recalculateEquipmentStats();startBossFight("doctor")')
        self.page.locator('#battle-arena-screen').click(position={'x':600,'y':400})
        self.assertEqual(self.page.evaluate('battleWeaponAmmo'),9)
        hp=self.page.evaluate('bossCurrentHp');self.page.locator('#battle-arena-screen').click(position={'x':600,'y':400});self.assertEqual(self.page.evaluate('bossCurrentHp'),hp)
        self.page.clock.fast_forward(4100);self.assertEqual(self.page.evaluate('bossCurrentHp'),hp)
        self.page.locator('#weapon-battle-state button').click(no_wait_after=True);self.page.clock.fast_forward(2600)
        self.assertEqual(self.page.evaluate('battleWeaponAmmo'),10);self.assertEqual(self.page.evaluate('bossCurrentHp'),hp)
        self.page.evaluate('bossCurrentHp=1;performPlayerAttack()')
        self.assertEqual(self.page.evaluate('stats.equipmentParts'),3);self.assertEqual(self.page.evaluate('stats.experimentalComponents'),1)
        self.assertIn('Детали: +3',self.page.locator('#victory-weapon-materials').inner_text())
        self.page.reload(wait_until='networkidle');self.assertEqual(self.page.evaluate('stats.equipmentParts'),3)
