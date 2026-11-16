"""Real raid UI: paired weapon state, saved raids and reference-layout controls."""
from pathlib import Path
import unittest
from tests import test_game as support
OUT=Path(__file__).resolve().parents[1]/'test-results/raid-hud';OUT.mkdir(parents=True,exist_ok=True)
class RaidHUDTests(unittest.TestCase):
 setUpClass=classmethod(support.GameTests.setUpClass.__func__)
 tearDownClass=classmethod(support.GameTests.tearDownClass.__func__)
 setUp=support.GameTests.setUp
 tearDown=support.GameTests.tearDown
 load=support.GameTests.load
 def enter(self,weapon='gear-aks',boss='nurse'):
  self.load();self.page.locator('#quest-unlock-all').click();self.page.locator('.room-trip-switch').click()
  self.page.locator('#location-card-box').click();self.page.locator(f'.quest-map-pin[data-room="{boss}"]').dblclick(delay=40)
  self.page.wait_for_selector(f'[data-scene-room="{boss}"]')
  self.page.evaluate('''([weapon,boss])=>{stats.baseArmor=10000;recalculateEquipmentStats();equipPaperDollItem('weapon',weapon);startBossFight(boss);}''',[weapon,boss])
  self.page.locator('#nurse-battle-modal').wait_for(state='visible')
  self.page.wait_for_function('document.getElementById("raid-player-portrait").querySelector("img")?.complete')
 def hit(self):self.page.locator('#battle-arena-screen').click(position={'x':500,'y':260})
 def test_switching_keeps_ammo_reload_and_shared_attack_cooldown(self):
  self.enter(boss='doctor');self.page.clock.install();self.hit();self.page.clock.run_for(20)
  ring=self.page.locator('[data-raid-slot="ranged"] .raid-cd-fill');initial=ring.evaluate('e=>parseFloat(e.style.strokeDashoffset)');self.page.clock.run_for(1000);self.assertLess(ring.evaluate('e=>parseFloat(e.style.strokeDashoffset)'),initial)
  self.assertEqual(self.page.evaluate('battleWeaponAmmo'),9)
  hp=self.page.evaluate('bossCurrentHp');end=self.page.evaluate('attackCooldownEndsAt')
  self.page.locator('[data-raid-weapon="melee"]').click();self.hit()
  self.assertEqual(self.page.evaluate('bossCurrentHp'),hp);self.assertEqual(self.page.evaluate('attackCooldownEndsAt'),end)
  self.page.locator('[data-raid-weapon="ranged"]').click();self.assertEqual(self.page.evaluate('battleWeaponAmmo'),9)
  self.page.locator('#weapon-battle-state button').click();self.page.locator('[data-raid-weapon="melee"]').click()
  self.page.clock.fast_forward(2700);self.page.locator('[data-raid-weapon="ranged"]').click()
  self.assertEqual(self.page.evaluate('battleWeaponAmmo'),10);self.assertEqual(self.page.evaluate('bossCurrentHp'),hp)
  self.page.clock.fast_forward(1500);self.page.clock.run_for(20);self.assertFalse(self.page.locator('[data-raid-slot="ranged"] .raid-cooldown').is_visible());self.hit();self.assertEqual(self.page.evaluate('battleWeaponAmmo'),9)
  self.assertLess(self.page.evaluate('bossCurrentHp'),hp)
 def test_journal_sections_medkits_portrait_and_cursor(self):
  self.enter();self.assertEqual(self.page.locator('.raid-accordion.open').count(),0)
  self.page.locator('#raid-members-toggle').click();self.assertTrue(self.page.locator('#battle-raid-panel').is_visible())
  self.page.locator('#raid-actions-toggle').click();self.assertFalse(self.page.locator('#battle-raid-panel').is_visible());self.assertTrue(self.page.locator('#raid-actions-panel').is_visible())
  self.page.locator('.raid-invite').click();self.page.locator('#friend-invite-modal').get_by_role('button',name='Пригласить всех',exact=False).click()
  self.hit();self.page.wait_for_timeout(650)
  self.assertIn('атака',self.page.locator('#raid-actions-list').inner_text());self.assertIn('присоединился',self.page.locator('#raid-actions-list').inner_text())
  self.assertTrue(self.page.locator('#raid-cursor-cooldown').is_visible());self.assertTrue(self.page.locator('[data-raid-slot="ranged"] .raid-cooldown').is_visible())
  self.page.evaluate("stats.hp=50;inventory.push({...MEDICAL_ITEMS.hp_10,count:2});updateUI()")
  self.page.locator('#medkit-btn-small').click();self.assertEqual(self.page.evaluate('stats.hp'),60)
  self.assertEqual(self.page.locator('#medkit-count-small').inner_text(),'1');self.assertIn('восстановлено 10 HP',self.page.locator('#raid-actions-list').inner_text())
  self.assertEqual(self.page.locator('#b-player-name').inner_text(),self.page.evaluate('playerName'))
  self.assertRegex(self.page.locator('#battle-timer-display').inner_text(),r'^\d\d:\d\d\.\d{3}$')
  self.assertEqual(self.page.locator('#raid-player-portrait .char-layer').count(),self.page.locator('#hud-portrait .char-layer').count())
  self.page.screenshot(path=str(OUT/'raid-actions.png'))
  self.page.locator('#raid-members-toggle').click();self.assertEqual(self.page.locator('.raid-member').count(),4);self.page.screenshot(path=str(OUT/'raid-members.png'))
 def test_reload_restores_both_weapons_and_log_without_refill(self):
  self.enter(boss='doctor');self.hit();self.page.locator('[data-raid-weapon="melee"]').click()
  before=self.page.evaluate('({id:currentBattleSession.id,end:raidEndsAt,cd:attackCooldownEndsAt,hp:bossCurrentHp,ammo:battleWeaponSnapshot().slots.ranged.ammo,log:currentBattleSession.log.length})')
  self.page.reload(wait_until='networkidle');self.assertTrue(self.page.locator('#nurse-battle-modal').is_hidden());self.page.locator('#nav-raid-btn').click();self.page.locator('#nurse-battle-modal').wait_for(state='visible')
  self.assertEqual(self.page.evaluate('currentBattleSession.id'),before['id']);self.assertEqual(self.page.evaluate('raidEndsAt'),before['end']);self.assertEqual(self.page.evaluate('attackCooldownEndsAt'),before['cd'])
  self.assertEqual(self.page.evaluate('battleWeaponSlot'),'melee');self.assertEqual(self.page.evaluate('battleWeaponSnapshot().slots.ranged.ammo'),before['ammo']);self.assertEqual(self.page.evaluate('bossCurrentHp'),before['hp'])
  self.assertGreaterEqual(self.page.evaluate('currentBattleSession.log.length'),before['log'])
  self.page.locator('#raid-members-toggle').click();self.assertTrue(self.page.locator('#battle-raid-panel').is_visible())
  self.page.locator('.raid-minimize').click();self.assertFalse(self.page.locator('#nurse-battle-modal').is_visible());self.assertTrue(self.page.evaluate('isBattleActive'))
  self.page.locator('#nav-raid-btn').click();self.assertTrue(self.page.locator('#nurse-battle-modal').is_visible());self.assertEqual(self.page.evaluate('raidEndsAt'),before['end']);self.assertTrue(self.page.locator('#battle-raid-panel').is_visible());self.assertEqual(self.page.locator('#raid-members-toggle').get_attribute('aria-expanded'),'true')
 def test_responsive_controls_and_legacy_checkpoint(self):
  self.enter(weapon='gear-pm')
  for w,h in [(1672,941),(1280,800),(844,390),(390,844),(320,568)]:
   self.page.set_viewport_size({'width':w,'height':h});self.page.wait_for_timeout(80)
   self.page.screenshot(path=str(OUT/f'check-{w}x{h}.png'))
   self.assertTrue(self.page.evaluate('''()=>['.raid-exit','.raid-minimize','.raid-invite','[data-raid-weapon="ranged"]','[data-raid-weapon="melee"]','#raid-members-toggle','#raid-actions-toggle','#medkit-btn-small'].every(s=>{const r=document.querySelector(s).getBoundingClientRect();return r.left>=-1&&r.top>=-1&&r.right<=innerWidth+1&&r.bottom<=innerHeight+1;})'''), self.page.evaluate('''()=>({w:innerWidth,h:innerHeight,arena:document.getElementById('battle-arena-screen').getBoundingClientRect().toJSON(),buttons:[...document.querySelectorAll('.raid-top-controls button,.raid-invite,#medkit-btn-small')].map(b=>({name:b.textContent,rect:b.getBoundingClientRect().toJSON()}))})'''))
   self.assertTrue(self.page.locator('.raid-weapon-select .weapon-icon-frame>:is(img,svg)').evaluate_all('''imgs=>imgs.every(img=>{const a=img.getBoundingClientRect(),b=img.parentElement.getBoundingClientRect();return a.left>=b.left-1&&a.top>=b.top-1&&a.right<=b.right+1&&a.bottom<=b.bottom+1;})'''))
   self.page.locator('#raid-actions-toggle').click();self.page.locator('#raid-members-toggle').click()
   self.page.screenshot(path=str(OUT/f'raid-{w}x{h}.png'))
  self.page.evaluate('''()=>{const key='palata404_floor10_progress:'+encodeURIComponent(raidArchiveOwnerId),s=JSON.parse(localStorage.getItem(key));delete s.raid.weapons;s.raid.ammo=3;localStorage.setItem(key,JSON.stringify(s));}''')
  # The pagehide checkpoint must not overwrite the deliberately seeded old schema.
  legacy=self.page.evaluate('localStorage.getItem("palata404_floor10_progress:"+encodeURIComponent(raidArchiveOwnerId))')
  self.context.add_init_script('if(!sessionStorage.getItem("legacy-seeded")){localStorage.setItem('+repr(self.page.evaluate('"palata404_floor10_progress:"+encodeURIComponent(raidArchiveOwnerId)'))+','+repr(legacy)+');sessionStorage.setItem("legacy-seeded","yes")}')
  self.page.reload(wait_until='networkidle');self.assertTrue(self.page.locator('#nurse-battle-modal').is_hidden());self.page.locator('#nav-raid-btn').click();self.page.locator('#nurse-battle-modal').wait_for(state='visible');self.assertEqual(self.page.evaluate('battleWeaponAmmo'),3)
