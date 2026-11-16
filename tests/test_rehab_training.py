"""Actual timed UI exercises; rank-boundary saves are diagnostic fixtures."""
import json
from pathlib import Path
import unittest
from tests import test_game

class RehabTrainingTests(unittest.TestCase):
    setUpClass=classmethod(test_game.GameTests.setUpClass.__func__)
    tearDownClass=classmethod(test_game.GameTests.tearDownClass.__func__)
    setUp=test_game.GameTests.setUp
    tearDown=test_game.GameTests.tearDown
    load=test_game.GameTests.load

    def gym(self):
        self.page.locator('#location-card-box').click()
        self.page.locator('.quest-map-pin[data-room="gym"]').dblclick(delay=40)
        self.page.locator('[data-rehab-equipment="rope"]').click()
        self.page.locator('[data-train="rope"]').wait_for(state='visible')

    def test_timed_rank_energy_reload_and_shared_mode(self):
        self.load({'palata404_stats':json.dumps({'rehabTraining':{'rope':{'completed':9},'pullup':{'completed':10},'bench':{'completed':20},'bag':{'completed':30}}})})
        self.assertEqual(self.page.evaluate('getCombatWeaponStats().damage'),13)
        self.assertAlmostEqual(self.page.evaluate('getCombatWeaponStats().critical'),.03)
        self.gym();self.page.locator('[data-train="rope"]').click()
        self.assertEqual(self.page.evaluate('stats.energy'),100)
        self.page.wait_for_function('stats.rehabTraining.rope.completed===10',timeout=16000)
        self.assertEqual(self.page.evaluate('stats.maxEnergy'),101)
        self.assertEqual(self.page.evaluate('stats.energy'),92)
        self.assertEqual(self.page.evaluate('stats.silver'),150)
        self.page.locator('[data-train="rope"]').click()
        self.assertIn('60 секунд',self.page.locator('.rehab-training>[role="status"]').inner_text())
        out=Path(__file__).resolve().parents[1]/'test-results/level-rehab';out.mkdir(parents=True,exist_ok=True)
        self.page.locator('.rehab-training h4').scroll_into_view_if_needed()
        self.page.screenshot(path=str(out/'training-real-preview.png'))
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.evaluate('stats.rehabTraining.rope.completed'),10)
        self.assertEqual(self.page.evaluate('stats.maxEnergy'),101)
        self.page.locator('.quest-room-tools button').first.click()
        self.page.locator('#map-modal .btn-close-map').click()
        self.page.locator('.room-trip-switch').click()
        self.assertEqual(self.page.evaluate('stats.rehabTraining.rope.completed'),10)
        self.gym();self.assertTrue(self.page.locator('[data-train="rope"]').is_visible())

    def test_cancellation_and_failed_transaction_do_not_charge_or_grant(self):
        self.load();self.gym();self.page.locator('[data-train="rope"]').click()
        self.page.get_by_role('button',name='Скасувати без витрат',exact=True).click()
        self.assertEqual(self.page.evaluate('stats.energy'),100)
        self.assertEqual(self.page.evaluate('PalataRehabRules.normalize(stats.rehabTraining).rope.completed'),0)
        # Deny the atomic profile journal; normal UI timing still runs fully.
        self.page.evaluate('window.rehabOriginalSet=safeStorageSet;safeStorageSet=(k,v)=>k===WEAPON_TRANSACTION_KEY?false:rehabOriginalSet(k,v)')
        self.page.locator('[data-train="rope"]').click()
        self.page.wait_for_function('document.querySelector(".rehab-training>[role=status]").textContent.includes("Ресурсы не списаны")',timeout=16000)
        self.assertEqual(self.page.evaluate('stats.energy'),100)
        self.assertEqual(self.page.evaluate('PalataRehabRules.normalize(stats.rehabTraining).rope.completed'),0)

    def test_interrupted_profile_write_recovers_one_rank_only(self):
        self.load({'palata404_stats':json.dumps({'rehabTraining':{'rope':{'completed':9}}})})
        self.gym()
        self.page.evaluate('window.rehabOriginalSet=safeStorageSet;safeStorageSet=(k,v)=>k==="palata404_stats"?false:rehabOriginalSet(k,v)')
        self.page.locator('[data-train="rope"]').click()
        self.page.wait_for_function('stats.rehabTraining.rope.completed===10',timeout=16000)
        self.assertTrue(self.page.evaluate('Boolean(readWeaponTransaction())'))
        for _ in range(2):
            self.page.reload(wait_until='networkidle')
            self.assertEqual(self.page.evaluate('stats.rehabTraining.rope.completed'),10)
            self.assertEqual(self.page.evaluate('stats.maxEnergy'),101)
            self.assertEqual(self.page.evaluate('stats.energy'),92)
