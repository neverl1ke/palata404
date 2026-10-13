const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'script.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

// Exercise the actual game script with controlled storage/time. Layout and input
// handling belong to test_game.py; these stubs intentionally don't model them.
function game(saves = {}, deniedStorage = false) {
    let now = 1700000000000;
    let sequence = 0;
    const timers = new Map();
    const storage = new Map(Object.entries(saves));
    const elements = new Map();
    const listeners = new Map();
    function element(id = '') {
        const classes = new Set();
        return {
            id, style: {}, children: [], textContent: '', innerHTML: '',
            classList: {
                add(...names) { names.forEach(name => classes.add(name)); },
                remove(...names) { names.forEach(name => classes.delete(name)); },
                contains(name) { return classes.has(name); },
                toggle(name, force) {
                    const enabled = force ?? !classes.has(name);
                    enabled ? classes.add(name) : classes.delete(name);
                    return enabled;
                }
            },
            appendChild(child) { this.children.push(child); if (child.id) elements.set(child.id, child); },
            remove() { elements.delete(this.id); },
            addEventListener() {}, querySelectorAll() { return []; },
            setAttribute(name, value) { this[name] = value; },
            focus() {}, getClientRects() { return []; },
            contains() { return false; },
        };
    }
    for (const match of html.matchAll(/\bid="([^"]+)"/g)) elements.set(match[1], element(match[1]));
    const document = {
        getElementById(id) { return elements.get(id) || null; },
        createElement() { return element(); },
        querySelectorAll() { return []; },
        addEventListener(name, callback) {
            if (!listeners.has(name)) listeners.set(name, []);
            listeners.get(name).push(callback);
        },
        body: element('body'), hidden: false,
    };
    const window = {
        document, innerWidth: 390, innerHeight: 844,
        location: { search: '' }, addEventListener() {},
    };
    Object.defineProperty(window, 'localStorage', {
        get() {
            if (deniedStorage) throw new Error('storage denied');
            return {
                getItem(key) { return storage.get(key) ?? null; },
                setItem(key, value) { storage.set(key, String(value)); },
            };
        }
    });
    const context = vm.createContext({
        window, document, URLSearchParams, console,
        Date: class extends Date { static now() { return now; } },
        alert() {}, confirm() { return true; }, prompt() { return null; },
        MutationObserver: class { observe() {} },
        setInterval() { return ++sequence; }, clearInterval() {},
        setTimeout(callback, delay) { const id = ++sequence; timers.set(id, { at: now + delay, callback }); return id; },
        clearTimeout(id) { timers.delete(id); },
    });
    vm.runInContext(source, context, { filename: 'script.js' });
    const run = code => vm.runInContext(code, context);
    for (const callback of listeners.get('DOMContentLoaded') || []) callback();
    return {
        run, storage, elements,
        advance(ms) {
            const target = now + ms;
            while (true) {
                const next = [...timers.entries()].filter(([,t]) => t.at <= target).sort((a,b) => a[1].at-b[1].at)[0];
                if (!next) break;
                now = next[1].at; timers.delete(next[0]); next[1].callback();
            }
            now = target;
        }
    };
}

test('malformed saves and unavailable storage allow startup, exercise, energy recovery', () => {
    const g = game({ palata404_stats: '{bad', palata404_inventory: 'null', palata404_gym: '[]' }, true);
    assert.equal(g.run('stats.damage'), 10);
    g.run('doGymExercise("squats")');
    assert.equal(g.run('stats.energy'), 98);
    g.advance(120001);
    g.run('updateEnergyTimer()');
    assert.equal(g.run('stats.energy'), 99);
    g.run('updateEnergyTimer()');
    assert.equal(g.run('stats.energy'), 99);
});

test('legacy equipment and permanent training gains survive swapping and reloading', () => {
    const g = game({
        palata404_stats: JSON.stringify({ damage: 51, armor: 40, gymRounds: 2 }),
        palata404_equipped: JSON.stringify({ weapon: 'Штурмовий АКС-74У', helmet: 'Побитий шолом санітара', armor: 'Бронежилет БР-1' }),
    });
    assert.equal(g.run('stats.damage'), 51);
    g.run('openItemInfo(inventory.find(i=>i.name==="Іржавий ніж")); document.getElementById("item-action-btn").onclick();');
    assert.equal(g.run('stats.damage'), 24);
    g.run('openItemInfo(inventory.find(i=>i.name==="Іржавий ніж")); document.getElementById("item-action-btn").onclick();');
    assert.equal(g.run('stats.damage'), 16);
    const reload = game(Object.fromEntries(g.storage));
    assert.equal(reload.run('stats.damage'), 16);
    assert.equal(reload.run('stats.armor'), 40);
});

test('all five shop products can be purchased, invalid price does not spend funds', () => {
    const g = game({ palata404_stats: JSON.stringify({ silver: 1000, bucks: 100 }) });
    g.run('buyMedicalItem("stamina_full", 10, "bucks"); buyMedicalItem("hp_10", -5, "silver");');
    assert.equal(g.run('stats.bucks'), 90);
    assert.equal(g.run('stats.silver'), 1000);
    g.run('stats.energy=10; consumeMedicalItem(inventory.find(i=>i.name==="Стимулятор")); updateUI();');
    assert.equal(g.run('stats.energy'), 100);
    g.run('Object.entries(MEDICAL_ITEMS).forEach(([key,item])=>buyMedicalItem(key,item.cost,item.currency));');
    assert.equal(g.run('inventory.filter(i=>i.category==="meds").length'), 5);
});

test('legacy gym rounds populate dossier and preserve permanent damage', () => {
    const g = game({
        palata404_gym: JSON.stringify({ completedRounds: 4 }),
        palata404_stats: JSON.stringify({ gymRounds: 0, damage: 22 }),
    });
    g.run('openDossier()');
    assert.equal(g.run('stats.gymRounds'), 4);
    assert.equal(g.elements.get('dossier-gym-rounds').textContent, 4);
    assert.equal(g.run('stats.damage'), 22);
    const reload = game(Object.fromEntries(g.storage));
    assert.equal(reload.run('stats.gymRounds'), 4);
    assert.equal(reload.run('stats.damage'), 22);
});

test('medkits have consistent effects in battle and no charge at full health', () => {
    const g = game({ palata404_stats: '{"silver":1000}' });
    g.run('buyMedicalItem("hp_10",30,"silver"); buyMedicalItem("hp_full",150,"silver"); startBossFight("nurse");');
    g.run('useBattleMedkit("small")');
    assert.equal(g.run('inventory.find(i=>i.name==="Мала аптечка").count'), 1);
    g.run('stats.hp=20; useBattleMedkit("small");');
    assert.equal(g.run('stats.hp'), 30);
    g.run('useBattleMedkit("big")');
    assert.equal(g.run('stats.hp'), 100);
    assert.equal(g.run('inventory.some(i=>i.name==="Велика армійська аптечка")'), false);
});

test('armor reduces counterattacks; cooldown prevents duplicate taps', () => {
    const g = game();
    g.run('stats.baseArmor=40; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); performPlayerAttack();');
    assert.equal(g.run('bossMaxHp-bossCurrentHp'), 10);
    g.advance(501);
    assert.equal(g.run('stats.hp'), 100-g.run('Math.ceil(bossesDatabase.doctor.damage*100/140)'));
    assert.equal(g.elements.get('b-player-hp').textContent, `${g.run('stats.hp')}/100`);
    assert.equal(JSON.parse(g.storage.get('palata404_stats')).hp, g.run('stats.hp'));
});

test('delayed attacks cannot leak into a new fight', () => {
    const g = game();
    g.run('startBossFight("doctor"); performPlayerAttack(); openFleeConfirmModal(); startBossFight("nurse");');
    g.advance(600);
    assert.equal(g.run('stats.hp'), 100);
    assert.equal(g.run('bossCurrentHp'), 120);
});

test('battle expiry uses elapsed time and does not reward after expiry', () => {
    const g = game();
    g.run('startBossFight("nurse"); minimizeNurseBattle();');
    g.advance(301000);
    g.run('reopenNurseBattle(); performPlayerAttack();');
    assert.equal(g.run('isBattleActive'), false);
    assert.equal(g.run('stats.bossesKilled'), 0);
    assert.equal(g.run('stats.silver'), 150);
});

test('victory is credited once and persists', () => {
    const g = game();
    g.run('stats.baseDamage=150; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();');
    const silver = g.run('stats.silver');
    g.run('handleVictory(); performPlayerAttack();');
    assert.equal(g.run('stats.silver'), silver);
    assert.equal(g.run('stats.bossesKilled'), 1);
    assert.equal(g.run('raidMembers[0].damage'), 120);
    assert.equal(game(Object.fromEntries(g.storage)).run('stats.bossesKilled'), 1);
});

test('rubble unlock, room, gym and live dossier remain consistent after reload', () => {
    const g = game();
    g.run('selectRoom("gym"); doGymExercise("squats"); handleNodeClick(gameFloorsData[0].nodes.find(n=>n.type==="grind"),gameFloorsData[0]); stats.madness=100; updateUI(); doGymExercise("squats"); openDossier();');
    assert.equal(g.run('gymComplex.exercises[0].current'), 1);
    assert.equal(g.elements.get('dossier-madness-attacks').textContent, 4);
    const reload = game(Object.fromEntries(g.storage));
    assert.equal(reload.run('currentRoom.id'), 'gym');
    assert.equal(reload.run('gameFloorsData[0].nodes.find(n=>n.type==="boss").locked'), false);
    assert.equal(reload.run('stats.energy'), 88);
});

test('text escape and repeated toast remain safe and visible', () => {
    const g = game({ palata404_nickname: '<img onerror=bad>' });
    assert.equal(g.elements.get('player-name').textContent, '<img onerror=bad>');
    assert.equal(g.run('escapeHTML("<img onerror=bad>")'), '&lt;img onerror=bad&gt;');
    g.run('showCustomToast("first")');
    g.advance(2600);
    g.run('showCustomToast("second")');
    assert.equal(g.elements.get('custom-toast-notification').style.opacity, '1');
});
