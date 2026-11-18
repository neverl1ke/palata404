"""Drive work surfaces from their public evidence using actual UI controls."""
import json
from pathlib import Path

SOLVER = (Path(__file__).parent / 'quest-workbench-solver.cjs').read_text()
STAFF_DIALOGUE = '#quest-staff-dialogue[open]'


def room(game, destination):
    if game.locator('#quest-location-screen').is_visible():
        game.locator('.quest-room-tools button').first.click()
    elif game.locator('#map-modal').is_hidden():
        game.locator('#location-card-box').click()
    game.locator(f'.quest-map-pin[data-room="{destination}"]').dblclick(delay=40)
    game.wait_for_function(
        'id=>PalataQuestPrototype.snapshot().room===id&&'
        '!document.getElementById("quest-location-screen").classList.contains("hidden")',
        arg=destination,
    )


def action(game, id, *, confirm_dialogue=True):
    mirror = game.locator(f'.scene-document-actions [data-scene-action="{id}"]')
    visible = next((item for item in mirror.all() if item.is_visible()), None)
    target = visible if visible is not None else game.locator(f'[data-action="{id}"]').first
    target.click()
    if confirm_dialogue and id.startswith(('accept:', 'claim:')):
        dialogue = game.locator(STAFF_DIALOGUE)
        dialogue.locator('[data-dialogue-confirm]').click()
        # The acceptance/rejection remains testable through the real state and
        # toast. Dialogue-specific tests can keep the confirmation open.
        dialogue.locator('[data-dialogue-close]').click()


def board(game, id):
    return game.evaluate('id=>PalataQuestEngine.workbench(PalataQuestPrototype.snapshot(),id)', id)


def operate(game, op, value=None):
    if op == 'spreadSheet':
        game.locator('input[data-sheet-spread]').press('End')
        return
    if isinstance(value, (dict, list)):
        encoded = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    else:
        encoded = str(value) if value is not None else None
    for button in game.locator('[data-work-op]').all():
        if button.get_attribute('data-work-op') != op:
            continue
        if button.get_attribute('data-work-value') == encoded:
            button.click()
            return
    raise AssertionError('No real UI control for ' + repr((op, value)))


def complete(game, id, open_board=True):
    if open_board:
        action(game, id)
    for _ in range(40):
        current = board(game, id)
        if current is None:
            return
        instruction = '(board)=>{const module={exports:{}};' + SOLVER + ';return module.exports.nextOperation(board)}'
        operation = game.evaluate(instruction, current)
        if operation.get('navigate'):
            # Resolve shortages and observe a chosen subject by entering the
            # actual room, without modifying the stored progress in the driver.
            close = game.locator('[data-work-focus="close"]')
            if close.count():
                close.click()
            room(game, operation['navigate'])
            complete(game, operation['action'])
            if operation.get('completeOnly'):
                return
            room(game, operation['resumeRoom'])
            action(game, operation['resume'])
            continue
        operate(game, operation['op'], operation.get('value'))
    raise AssertionError('Workbench did not finish: ' + id)


def return_home(game):
    dialogue = game.locator(STAFF_DIALOGUE)
    if dialogue.is_visible():
        dialogue.locator('[data-dialogue-close]').click()
    if game.locator('[data-work-focus="close"]').count():
        game.locator('[data-work-focus="close"]').click()
    if game.locator('#quest-location-screen').is_visible():
        game.locator('.quest-room-tools button').first.click()
    if game.locator('#map-modal').is_visible():
        game.locator('#map-modal .btn-close-map').click()


def complete_call_cycle(game):
    """Finish outstanding diagnosis, service and retest through public routing."""
    for _ in range(8):
        state = game.evaluate('PalataQuestPrototype.snapshot()')
        if state['jobs']['d1'].get('revision') not in (4, 5):
            return
        if game.evaluate('PalataQuestEngine.ready(PalataQuestPrototype.snapshot(),"d1")'):
            return
        route = game.evaluate('PalataQuestEngine.jobStage(PalataQuestPrototype.snapshot(),"d1")')
        if not route or not route.get('action'):
            raise AssertionError('An unfinished call cycle has no actionable player route: ' + repr(route))
        room(game, route['room'])
        complete(game, route['action'])
    raise AssertionError('Authorized call cycle did not reach final verified submission')
