"""Drive work surfaces from their public evidence using actual UI controls."""
from pathlib import Path
import json
SOLVER=(Path(__file__).parent/'quest-workbench-solver.cjs').read_text()
def room(game,destination):
 if game.locator('#quest-location-screen').is_visible():game.locator('.quest-room-tools button').first.click()
 elif game.locator('#map-modal').is_hidden():game.locator('#location-card-box').click()
 game.locator(f'.quest-map-pin[data-room="{destination}"]').dblclick(delay=40)
 game.wait_for_function('id=>PalataQuestPrototype.snapshot().room===id&&!document.getElementById("quest-location-screen").classList.contains("hidden")',arg=destination)
def action(game,id):
 mirror=game.locator(f'.scene-document-actions [data-scene-action="{id}"]')
 (mirror if mirror.count() else game.locator(f'[data-action="{id}"]').first).click()
def board(game,id):return game.evaluate('id=>PalataQuestEngine.workbench(PalataQuestPrototype.snapshot(),id)',id)
def operate(game,op,value=None):
 encoded=json.dumps(value,ensure_ascii=False,separators=(',',':')) if isinstance(value,(dict,list)) else str(value) if value is not None else None
 for button in game.locator('[data-work-op]').all():
  if button.get_attribute('data-work-op')==op and button.get_attribute('data-work-value')==encoded:
   button.click();return
 raise AssertionError('No real UI control for '+repr((op,value)))
def complete(game,id,open_board=True):
 if open_board:action(game,id)
 for _ in range(40):
  current=board(game,id)
  if current is None:return
  operation=game.evaluate('(board)=>{const module={exports:{}};'+SOLVER+';return module.exports.nextOperation(board)}',current)
  operate(game,operation['op'],operation.get('value'))
 raise AssertionError('Workbench did not finish: '+id)
def return_home(game):
 if game.locator('[data-work-focus="close"]').count():game.locator('[data-work-focus="close"]').click()
 if game.locator('#quest-location-screen').is_visible():game.locator('.quest-room-tools button').first.click()
 if game.locator('#map-modal').is_visible():game.locator('#map-modal .btn-close-map').click()
