const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'script.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
let fixtureRaidSequence = 0;

// Exercise the actual game script with controlled storage/time. Layout and input
// handling belong to test_game.py; these stubs intentionally don't model them.
function game(saves = {}, deniedStorage = false, failWrites = [], telegramId = null, sharedStorage = null) {
    let now = 1700000000000;
    let sequence = 0;
    const timers = new Map();
    const storage = sharedStorage || new Map(Object.entries(saves));
    const failedKeys = new Set(failWrites);
    const elements = new Map();
    const listeners = new Map();
    function element(id = '') {
        const classes = new Set();
        return {
            id, style: { setProperty(name, value) { this[name] = value; } }, children: [], textContent: '', innerHTML: '',
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
            addEventListener() {}, querySelectorAll(selector) {
                return selector === '[data-paper-extra]' ? this.children.filter(child => child['data-paper-extra'] && elements.get(child.id) === child) : [];
            },
            setAttribute(name, value) { this[name] = value; },
            getAttribute(name) { return this[name] ?? null; },
            removeAttribute(name) { delete this[name]; },
            focus() {}, scrollTo() {}, getClientRects() { return []; },
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
        crypto: { randomUUID: () => `fixture-${++fixtureRaidSequence}` },
    };
    if (telegramId !== null) window.Telegram = { WebApp: {
        initDataUnsafe: { user: { id: telegramId, first_name: `Пацієнт ${telegramId}` } }, ready() {}, expand() {}
    } };
    Object.defineProperty(window, 'localStorage', {
        get() {
            if (deniedStorage) throw new Error('storage denied');
            return {
                get length() { return storage.size; },
                key(index) { return [...storage.keys()][index] ?? null; },
                getItem(key) { return storage.get(key) ?? null; },
                setItem(key, value) {
                    if (failedKeys.has(key)) throw new Error('Simulated interrupted write');
                    storage.set(key, String(value));
                },
                removeItem(key) { storage.delete(key); },
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
    vm.runInContext('Math.random=()=>0.5;', context);
    vm.runInContext(fs.readFileSync(path.join(root, 'icons.js'), 'utf8'), context, { filename: 'icons.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'staff-archive-data.js'), 'utf8'), context, { filename: 'staff-archive-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'battle-results.js'), 'utf8'), context, { filename: 'battle-results.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'raid-archive.js'), 'utf8'), context, { filename: 'raid-archive.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'staff-archive.js'), 'utf8'), context, { filename: 'staff-archive.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'paper-doll-data.js'), 'utf8'), context, { filename: 'paper-doll-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'hair-color.js'), 'utf8'), context, { filename: 'hair-color.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'female-hair-fit-data.js'), 'utf8'), context, { filename: 'female-hair-fit-data.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'female-hair-fit.js'), 'utf8'), context, { filename: 'female-hair-fit.js' });
    // This VM tests state/DOM commands; real pixel fitting is checked in test_appearance_catalog.py.
    vm.runInContext('fittedFemaleHairSource = source => ({ then(resolve) { resolve(source); return { catch() {} }; } });', context);
    vm.runInContext(fs.readFileSync(path.join(root, 'paper-doll.js'), 'utf8'), context, { filename: 'paper-doll.js' });
    vm.runInContext(fs.readFileSync(path.join(root, 'wardrobe.js'), 'utf8'), context, { filename: 'wardrobe.js' });
    vm.runInContext(source, context, { filename: 'script.js' });
    const run = code => vm.runInContext(code, context);
    for (const callback of listeners.get('DOMContentLoaded') || []) callback();
    return {
        run, storage, elements, failedKeys,
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

test('icon images accept only registered assets and preserve legacy emoji saves', () => {
    const g = game();
    assert.equal(g.run('resolveIconKey("🗝️")'), 'key');
    assert.equal(g.run('resolveIconKey("__proto__")'), 'box');
    assert.equal(g.run('resolveIconKey("https://example.org/track.svg")'), 'box');
    assert.equal(g.run('resolveIconKey("<img src=x onerror=bad>")'), 'box');
    assert.match(g.run('iconHTML("🔫")'), /src="assets\/icons\/pistol\.svg"/);
    assert.doesNotMatch(g.run(`iconHTML(${JSON.stringify('<img onerror=bad>')}, ${JSON.stringify('" onerror=bad')})`), /onerror/);
    for (const value of g.run('Object.values(GAME_ICONS)')) {
        assert.ok(fs.existsSync(path.join(root, value)), value);
        assert.doesNotMatch(fs.readFileSync(path.join(root, value), 'utf8'), /<script|<text|https?:\/\/(?!www.w3.org\/2000\/svg)/);
    }
});

test('item names and notifications stay escaped next to decorative images', () => {
    const g = game({
        palata404_inventory: JSON.stringify([{ name: '<img onerror=bad>', icon: '<script>bad</script>', category: 'mod', count: 3 }]),
    });
    g.run('openItemInfo(inventory[0]); showCustomToast("<img onerror=bad>");');
    assert.match(g.elements.get('item-info-title').innerHTML, /&lt;img onerror=bad&gt;/);
    assert.match(g.elements.get('item-info-title').innerHTML, /assets\/icons\/box.svg/);
    assert.match(g.elements.get('toast-message').innerHTML, /&lt;img onerror=bad&gt;/);
    assert.equal(g.run('inventory[0].count'), 3);
});

test('both bosses produce their own registry identity and one MVP-adjusted reward', () => {
    for (const [key, code, exp, silver] of [['nurse','404-KL',52,31],['doctor','404-IZ',126,84]]) {
        const g = game();
        g.run(`stats.baseDamage=300; recalculateEquipmentStats(); startBossFight('${key}'); performPlayerAttack();`);
        assert.equal(g.run('lastBattleResult.boss.id'), key);
        assert.equal(g.run('lastBattleResult.boss.caseCode'), code);
        assert.equal(g.run('lastBattleResult.boss.name'), g.run(`bossesDatabase.${key}.name`));
        assert.equal(g.run('lastBattleResult.boss.conclusion'), g.run(`bossesDatabase.${key}.victoryReport.conclusion`));
        assert.equal(g.run('lastBattleResult.payout.exp'), exp);
        assert.equal(g.run('lastBattleResult.payout.silver'), silver);
        assert.equal(g.run('stats.silver'), 150+silver);
        g.run('handleVictory(); openLastBattleResult(); closeLastBattleResult(); openLastBattleResult();');
        assert.equal(g.run('stats.silver'), 150+silver);
        assert.equal(g.run('stats.bossesKilled'), 1);
        assert.equal(g.run('inventory.filter(i=>i.category==="quest").length'), 1);
        const reload = game(Object.fromEntries(g.storage));
        reload.run('openLastBattleResult(); handleVictory();');
        assert.equal(reload.run('stats.silver'), 150+silver);
        assert.equal(reload.run('stats.bossesKilled'), 1);
        assert.equal(reload.run('lastBattleResult.battleId'), g.run('lastBattleResult.battleId'));
    }
});

test('a future configured boss needs no result-screen logic and MVP adds exactly five percent', () => {
    const g = game();
    g.run(`bossesDatabase.archive = {...bossesDatabase.nurse, key:'archive', name:'Архівний об’єкт',
        expReward:100, silverReward:200, dossier:{code:'003'},
        victoryReport:{caseCode:'404-AR',status:'Стабілізовано',conclusion:'Новий медичний висновок.'}};
        stats.baseDamage=300; recalculateEquipmentStats(); startBossFight('archive'); performPlayerAttack();`);
    assert.equal(g.run('lastBattleResult.payout.bonusExp'), 5);
    assert.equal(g.run('lastBattleResult.payout.bonusSilver'), 10);
    assert.equal(g.run('lastBattleResult.payout.exp'), 105);
    assert.equal(g.run('lastBattleResult.payout.silver'), 210);
    g.run('openDetailedBattleReport();');
    assert.equal(g.elements.get('victory-case-code').textContent, '404-AR');
    assert.equal(g.elements.get('victory-boss-number').textContent, '№003');
    assert.equal(g.run('stats.level'), 2);
    assert.equal(g.run('stats.exp'), 5);
});

test('effective healing, armor damage, medicine actions and madness track real events', () => {
    const g = game({palata404_stats:'{"silver":1000}'});
    g.run(`buyMedicalItem('hp_full',150,'silver'); buyMedicalItem('hp_full',150,'silver');
        buyMedicalItem('madness_pills',50,'silver');
        stats.baseArmor=40; stats.baseDamage=45; recalculateEquipmentStats(); startBossFight('nurse'); performPlayerAttack();`);
    g.advance(501);
    assert.equal(g.run('raidMembers[0].metrics.damageTaken'), 9);
    g.run('useBattleMedkit("big"); useBattleMedkit("big");');
    assert.equal(g.run('raidMembers[0].metrics.healing'), 9);
    assert.equal(g.run('raidMembers[0].metrics.turns'), 2);
    assert.equal(g.run('inventory.find(i=>i.name==="Велика армійська аптечка").count'), 1);
    g.run('openItemInfo(inventory.find(i=>i.effectType==="madness")); document.getElementById("item-action-btn").onclick();');
    g.advance(4000); g.run('performPlayerAttack()'); g.advance(501);
    g.advance(4000); g.run('performPlayerAttack()');
    assert.equal(g.run('lastBattleResult.participants[0].damage'), 120);
    assert.equal(g.run('lastBattleResult.participants[0].damageTaken'), 18);
    assert.equal(g.run('lastBattleResult.participants[0].healing'), 9);
    assert.equal(g.run('lastBattleResult.participants[0].turns'), 5);
    assert.equal(g.run('lastBattleResult.participants[0].madnessStart'), 20);
    assert.equal(g.run('lastBattleResult.participants[0].madnessEnd'), 5);
    assert.equal(g.run('lastBattleResult.participants[0].madnessDelta'), -15);
    assert.equal(g.run('lastBattleResult.participants[0].damageShare'), 100);
});

test('local helper MVP retains base player payout and unavailable fields are not fabricated', () => {
    const g = game();
    g.run(`startBossFight('nurse'); raidMembers[1].status='Халтурив'; callAllFriends(); Math.random=()=>0;
        for(let i=0;i<10;i++) friendsAutoAttackTick();`);
    assert.equal(g.run('lastBattleResult.mvpId'), 'friend_1');
    assert.equal(g.run('lastBattleResult.payout.exp'), 50);
    assert.equal(g.run('lastBattleResult.payout.silver'), 30);
    assert.equal(g.run('lastBattleResult.participants[0].specialStatus'), 'Халтурив');
    for (const member of g.run('lastBattleResult.participants.filter(m=>!m.isPlayer)')) {
        assert.equal(member.damage, 40);
        assert.equal(member.turns, 10);
        assert.equal(member.damageTaken, null);
        assert.equal(member.healing, null);
        assert.equal(member.madnessStart, null);
        assert.equal(member.rewards, null);
    }
    assert.equal(g.run('lastBattleResult.participants.find(m=>m.isPlayer).turns'), 0);
});

test('new raid resets metrics and duplicate event identifiers do not increment them', () => {
    const g = game();
    g.run(`startBossFight('nurse'); const id=nextBattleEventId('test');
        recordBattleEvent(id,raidMembers[0],{damage:4,turns:1});
        recordBattleEvent(id,raidMembers[0],{damage:4,turns:1});`);
    assert.equal(g.run('raidMembers[0].damage'), 4);
    assert.equal(g.run('raidMembers[0].metrics.turns'), 1);
    const oldId = g.run('currentBattleSession.id');
    g.run('openFleeConfirmModal(); startBossFight("doctor");');
    assert.notEqual(g.run('currentBattleSession.id'), oldId);
    assert.equal(g.run('raidMembers[0].damage'), 0);
    assert.equal(g.run('raidMembers[0].metrics.turns'), 0);
    assert.equal(g.run('raidMembers[0].metrics.healing'), 0);
    g.run('recordBattleEvent(id,raidMembers[0],{damage:99,turns:1});');
    assert.equal(g.run('raidMembers[0].damage'), 0);
    assert.equal(g.run('raidMembers[0].metrics.turns'), 0);
});

test('interrupted reward writes recover snapshots exactly once without replaying gains', () => {
    const g = game({palata404_stats:'{"silver":150}'},false,['palata404_stats']);
    g.run('stats.baseDamage=150; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();');
    assert.equal(JSON.parse(g.storage.get('palata404_stats')).silver,150);
    assert.ok(g.storage.has('palata404_pending_battle_reward'));
    assert.equal(g.run('battleResultPersisted'),false);
    const restored = game(Object.fromEntries(g.storage));
    assert.equal(restored.run('stats.silver'),181);
    assert.equal(restored.run('stats.exp'),52);
    assert.equal(restored.run('stats.bossesKilled'),1);
    assert.equal(restored.run('bossKillsCount.nurse'),1);
    assert.equal(restored.run('inventory.filter(i=>i.category==="quest").length'),1);
    assert.equal(restored.storage.has('palata404_pending_battle_reward'),false);
    restored.run('openLastBattleResult(); retryBattleResultSave(); handleVictory();');
    assert.equal(restored.run('stats.silver'),181);
});

test('failed journal persistence leaves a visible retry and cannot award twice on retry', () => {
    const g = game({},false,['palata404_pending_battle_reward']);
    g.run('stats.baseDamage=150; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();');
    assert.equal(g.run('battleResultPersisted'),false);
    assert.equal(g.elements.get('victory-save-retry').classList.contains('hidden'),false);
    g.failedKeys.clear();
    g.run('retryBattleResultSave(); retryBattleResultSave(); handleVictory();');
    assert.equal(g.run('battleResultPersisted'),true);
    assert.equal(g.run('stats.silver'),181);
    assert.equal(g.run('stats.bossesKilled'),1);
});

test('participant text is escaped in the protocol and malformed saved reports are rejected', () => {
    const g = game({palata404_nickname:'<img src=x onerror=bad>'});
    g.run('stats.baseDamage=150; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();');
    g.run('openDetailedBattleReport();');
    assert.match(g.elements.get('victory-statistics-body').innerHTML,/&lt;img src=x onerror=bad&gt;/);
    assert.doesNotMatch(g.elements.get('victory-statistics-body').innerHTML,/<img src=x/);
    assert.equal(g.run('normalizeBattleResult({schemaVersion:1})'),null);
    assert.equal(game({palata404_last_battle_result:'{bad'}).run('lastBattleResult'),null);
});

test('summary and repeated detailed views preserve every result and never mutate resources or storage', () => {
    const g = game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack();');
    const before = g.run('JSON.stringify({stats,inventory,bossKillsCount,lastBattleResult})');
    const saves = [...g.storage];
    assert.equal(g.elements.get('victory-summary-exp').textContent, '+126');
    assert.equal(g.elements.get('victory-summary-silver').textContent, '+84');
    assert.equal(g.elements.get('victory-summary-mvp').classList.contains('hidden'), false);
    assert.match(g.elements.get('victory-summary-items').innerHTML, /Отримано:/);
    for (let i=0;i<3;i++) g.run('openDetailedBattleReport(); closeDetailedBattleReport();');
    assert.equal(g.run('JSON.stringify({stats,inventory,bossKillsCount,lastBattleResult})'), before);
    assert.deepEqual([...g.storage], saves);
    assert.equal(g.elements.get('victory-report-id').textContent, g.run('lastBattleResult.battleId'));
    g.run('victoryRestartFight(); performPlayerAttack();');
    assert.match(g.elements.get('victory-summary-items').innerHTML, /Вже в інвентарі:/);
    assert.doesNotMatch(g.elements.get('victory-summary-items').innerHTML, /Отримано:/);
    assert.equal(g.run('inventory.filter(i=>i.category==="quest").length'), 1);
});

test('summary does not advertise a personal MVP bonus when a helper wins it', () => {
    const g = game();
    g.run(`startBossFight('nurse'); callAllFriends(); Math.random=()=>0;
        for(let i=0;i<10;i++) friendsAutoAttackTick();`);
    assert.equal(g.elements.get('victory-summary-exp').textContent, '+50');
    assert.equal(g.elements.get('victory-summary-silver').textContent, '+30');
    assert.equal(g.elements.get('victory-summary-mvp').classList.contains('hidden'), false);
    assert.equal(g.elements.get('victory-summary-mvp-name').textContent, 'MVP: Сліпий Микола');
    assert.equal(g.elements.get('victory-summary-mvp-bonus').classList.contains('hidden'), true);
    g.run('openDetailedBattleReport();');
    assert.match(g.elements.get('victory-statistics-body').innerHTML, /Локальний помічник/);
    assert.match(g.elements.get('victory-statistics-body').innerHTML, /Не застосовується/);
});

test('archive keeps exactly the newest 50 real raid snapshots across reloads', () => {
    const g = game();
    const ids = [];
    g.run('stats.baseDamage=300; recalculateEquipmentStats();');
    for (let i=0;i<51;i++) {
        g.run('startBossFight("nurse"); performPlayerAttack();');
        ids.push(g.run('lastBattleResult.battleId'));
        g.advance(1);
    }
    assert.equal(g.run('readRaidArchive().length'), 50);
    assert.equal([...g.storage.keys()].filter(key=>key.includes(':raid:')).length,50);
    assert.equal(g.run('readRaidArchive()[0].battleId'), ids[50]);
    assert.equal(g.run('readRaidArchive()[49].battleId'), ids[1]);
    assert.equal(g.run('readRaidArchive().some(r=>r.battleId===lastBattleResult.battleId)'),true);
    const before = g.run('JSON.stringify(readRaidArchive())');
    g.run('handleVictory(); openLastBattleResult(); openDetailedBattleReport(); closeDetailedBattleReport();');
    assert.equal(g.run('JSON.stringify(readRaidArchive())'),before);
    const reloaded = game(Object.fromEntries(g.storage));
    assert.equal(reloaded.run('JSON.stringify(readRaidArchive())'),before);
});

test('historical protocols retain original boss, names, MVP and rewards without changing saves', () => {
    const g=game({palata404_nickname:'Первісний нік'});
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack(); const first=readRaidArchive()[0];');
    const original = g.run('JSON.stringify(first)');
    g.advance(1);
    g.run('playerName="Новий нік"; bossesDatabase.nurse.name="Змінений бос"; bossesDatabase.nurse.expReward=500; startBossFight("doctor"); performPlayerAttack();');
    const saves=[...g.storage];
    g.run('openDetailedBattleReport(first,"archive");');
    assert.equal(g.elements.get('victory-mvp-name').textContent,'Первісний нік');
    assert.equal(g.elements.get('victory-total-exp').textContent,52);
    assert.equal(g.elements.get('victory-boss-name').textContent,JSON.parse(original).boss.name);
    assert.equal(g.run('JSON.stringify(readRaidArchive().find(r=>r.battleId===first.battleId))'), original);
    g.run('closeDetailedBattleReport();');
    assert.deepEqual([...g.storage],saves);
    assert.equal(g.elements.get('raid-archive-modal').classList.contains('hidden'),false);
});

test('clearing requires UI confirmation, retains resources and does not replay old records', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();');
    const state=g.run('JSON.stringify({stats,inventory,bossKillsCount,gameProgress})');
    const protectedSaves=[...g.storage].filter(([key])=>!key.startsWith('palata404_raid_archive:'));
    g.run('openRaidArchive(); requestRaidArchiveClear(); cancelRaidArchiveClear();');
    assert.equal(g.run('readRaidArchive().length'),1);
    g.run('requestRaidArchiveClear(); confirmRaidArchiveClear();');
    assert.equal(g.run('readRaidArchive().length'),0);
    assert.equal(g.run('JSON.stringify({stats,inventory,bossKillsCount,gameProgress})'),state);
    assert.deepEqual([...g.storage].filter(([key])=>!key.startsWith('palata404_raid_archive:')), protectedSaves);
    g.run('handleVictory(); retryBattleResultSave(); openLastBattleResult(); appendRaidArchive(lastBattleResult);');
    assert.equal(g.run('readRaidArchive().length'),0);
    assert.equal(game(Object.fromEntries(g.storage)).run('readRaidArchive().length'),0);
    // A genuinely new raid is retained even when the clock has not advanced.
    g.run('victoryRestartFight(); performPlayerAttack();');
    assert.equal(g.run('readRaidArchive().length'),1);
    assert.equal(g.run('inventory.filter(i=>i.category==="quest").length'),1);
});

test('archive write failures retain the reward journal, retry once and honor clearing', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack(); startBossFight("doctor");');
    g.failedKeys.add(g.run('raidArchiveRecordKey(currentBattleSession.id)'));
    g.run('performPlayerAttack();');
    assert.equal(g.run('stats.silver'),265);
    assert.equal(g.run('raidArchiveSaveFailed'),true);
    assert.equal(g.run('readRaidArchive().length'),1);
    assert.ok(g.storage.has('palata404_pending_battle_reward'));
    g.run('clearRaidArchive();');
    g.failedKeys.clear();
    g.run('retryBattleResultSave(); handleVictory();');
    assert.equal(g.run('stats.silver'),265);
    assert.equal(g.run('readRaidArchive().length'),0);
    assert.equal(g.storage.has('palata404_pending_battle_reward'),false);
    const restored=game(Object.fromEntries(g.storage));
    assert.equal(restored.run('readRaidArchive().length'),0);
    assert.equal(restored.run('stats.silver'),265);
});

test('archives and pending-result access are isolated by stable identity, not nickname', () => {
    const shared=new Map();
    const a=game({},false,[],101,shared);
    a.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack();');
    const aHistory=a.run('JSON.stringify(readRaidArchive())');
    const b=game({},false,[],202,shared);
    assert.equal(b.run('readRaidArchive().length'),0);
    assert.equal(b.run('lastBattleResult'),null);
    b.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("doctor"); performPlayerAttack(); clearRaidArchive();');
    assert.equal(a.run('JSON.stringify(readRaidArchive())'),aHistory);
    assert.equal(b.run('readRaidArchive().length'),0);
    a.run('playerName="Перейменований";');
    assert.equal(a.run('JSON.stringify(readRaidArchive())'),aHistory);
    // A copied record for another identity is neither imported nor displayed.
    b.run(`openDetailedBattleReport(${aHistory}[0],"archive");`);
    assert.equal(b.elements.get('victory-report-id').textContent,'');
});

test('separate tabs keep distinct raid IDs and retries cannot overwrite a historical snapshot', () => {
    const shared=new Map([['palata404_web_id','WEB-shared']]);
    const a=game({},false,[],null,shared);
    const b=game({},false,[],null,shared);
    for (const [g,boss] of [[a,'nurse'],[b,'doctor']]) g.run(`stats.baseDamage=300; recalculateEquipmentStats(); startBossFight('${boss}'); performPlayerAttack();`);
    assert.equal(a.run('readRaidArchive().length'),2);
    assert.equal(b.run('readRaidArchive().length'),2);
    const before=a.run('JSON.stringify(readRaidArchive())');
    a.run('const changed=JSON.parse(JSON.stringify(lastBattleResult)); changed.boss.name="Не перезаписувати"; appendRaidArchive(changed);');
    assert.equal(a.run('JSON.stringify(readRaidArchive())'),before);
});

test('medical stamps use verified inactivity, spare support actions, NPCs and unknown legacy data', () => {
    const idle=game();
    idle.run('startBossFight("nurse"); callAllFriends(); Math.random=()=>0; for(let i=0;i<10;i++) friendsAutoAttackTick(); openDetailedBattleReport();');
    assert.equal((idle.elements.get('victory-statistics-body').innerHTML.match(/УХИЛЯВСЯ ВІД ПРОЦЕДУРИ/g)||[]).length,1);
    assert.match(idle.elements.get('victory-statistics-body').innerHTML,/report-participant-stamp">MVP/);
    for (const contribution of ['healing','turns','damageTaken']) {
        const g=game();
        g.run(`startBossFight("nurse"); raidMembers[0].metrics.${contribution}=1; callAllFriends(); Math.random=()=>0; for(let i=0;i<10;i++) friendsAutoAttackTick(); openDetailedBattleReport();`);
        assert.doesNotMatch(g.elements.get('victory-statistics-body').innerHTML,/УХИЛЯВСЯ/);
    }
    idle.run('const legacy=JSON.parse(JSON.stringify(lastBattleResult)); legacy.participants.forEach(m=>delete m.activityStatus); renderBattleResult(legacy);');
    assert.doesNotMatch(idle.elements.get('victory-statistics-body').innerHTML,/УХИЛЯВСЯ/);
});

test('timeout, defeat and flee create zero-reward records, while damaged archives stay usable', () => {
    const g=game();
    g.run('startBossFight("nurse"); handleRaidTimeOut(); handleRaidTimeOut();');
    assert.equal(g.run('readRaidArchive().length'),1);
    assert.equal(g.run('readRaidArchive()[0].outcome'),'timeout');
    g.advance(1);
    g.run('startBossFight("nurse"); openFleeConfirmModal();');
    assert.equal(g.run('readRaidArchive()[0].outcome'),'fled');
    g.advance(1);
    g.run('startBossFight("nurse"); stats.hp=1; performPlayerAttack();');
    g.advance(501);
    assert.equal(g.run('readRaidArchive()[0].outcome'),'defeat');
    assert.equal(g.run('readRaidArchive().length'),3);
    assert.equal(g.run('readRaidArchive().every(r=>r.payout.exp===0 && r.payout.silver===0 && r.extraRewards.length===0)'),true);
    assert.equal(g.run('stats.silver'),130);
    assert.equal(g.run('stats.bossesKilled'),0);
    g.storage.set(g.run('raidArchiveRecordKey("corrupt")'),'{bad');
    assert.equal(g.run('readRaidArchive().length'),3);
});

test('archive dossiers reuse configured full cards and preserve their historical binding', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack(); const first=readRaidArchive()[0];');
    assert.equal(g.run('first.boss.dossierImage'),'nurse_dossier_card.png');
    g.run('bossesDatabase.nurse.dossier.cardImg="replacement.png"; renderRaidArchive();');
    assert.match(g.elements.get('raid-archive-list').innerHTML,/src="nurse_dossier_card.png"/);
    assert.match(g.elements.get('raid-archive-list').innerHTML,/Справа 404-KL/);
    g.run('startBossFight("doctor"); performPlayerAttack(); renderRaidArchive();');
    assert.match(g.elements.get('raid-archive-list').innerHTML,/src="doctor_dossier_card.png"/);
    assert.equal(g.run('readRaidArchive().find(r=>r.boss.id==="doctor").boss.dossierImage'),'doctor_dossier_card.png');
    g.run('const legacy=JSON.parse(JSON.stringify(first)); delete legacy.boss.dossierImage;');
    assert.equal(g.run('getRaidDossierImage(legacy)'),'replacement.png');
    g.run('legacy.boss.id="unconfigured";');
    assert.equal(g.run('getRaidDossierImage(legacy)'),null);
    g.run('legacy.boss.dossierImage=null;');
    assert.equal(g.run('getRaidDossierImage(legacy)'),null);
    for (const value of ['https://example.com/card.png','../card.png','javascript:bad','card.png" onerror="bad']) {
        g.run(`legacy.boss.dossierImage=${JSON.stringify(value)};`);
        assert.equal(g.run('getRaidDossierImage(legacy)'),null);
    }
});

test('archive personal stamps describe only the owner, not an MVP helper or useful teammate', () => {
    const winner=game();
    winner.run('stats.baseDamage=300; recalculateEquipmentStats(); startBossFight("nurse"); performPlayerAttack(); renderRaidArchive();');
    assert.match(winner.elements.get('raid-archive-list').innerHTML,/raid-card-personal-stamp">MVP/);
    const idle=game();
    idle.run('startBossFight("nurse"); callAllFriends(); Math.random=()=>0; for(let i=0;i<10;i++) friendsAutoAttackTick(); renderRaidArchive();');
    assert.match(idle.elements.get('raid-archive-list').innerHTML,/raid-card-personal-stamp">УХИЛЯВСЯ ВІД ПРОЦЕДУРИ/);
    assert.doesNotMatch(idle.elements.get('raid-archive-list').innerHTML,/raid-card-personal-stamp">MVP/);
    const support=game();
    support.run('startBossFight("nurse"); raidMembers[0].metrics.healing=1; callAllFriends(); Math.random=()=>0; for(let i=0;i<10;i++) friendsAutoAttackTick(); renderRaidArchive();');
    assert.doesNotMatch(support.elements.get('raid-archive-list').innerHTML,/raid-card-personal-stamp/);
    assert.match(support.elements.get('raid-archive-list').innerHTML,/MVP: Сліпий Микола/);
    assert.equal(support.run('lastBattleResult.payout.exp'),50);
});

test('staff identities stay sealed until actual combat and survive defeat, repeats and reload', () => {
    const g=game();
    g.run('openStaffArchive(); openBossDossier("doctor"); openStaffArchive("doctor");');
    assert.equal(g.run('Object.keys(staffArchiveState.cases).length'),0);
    assert.match(g.elements.get('staff-case-list').innerHTML,/ОСОБУ НЕ ВСТАНОВЛЕНО/);
    assert.doesNotMatch(g.elements.get('staff-case-list').innerHTML,/doctor_dossier|nurse_dossier|Черговий|Клара/);
    assert.doesNotMatch(g.elements.get('staff-case-sheet').innerHTML,/Незаповнена графа|наказ|Черговий/);
    g.run('startBossFight("doctor"); stats.hp=1; performPlayerAttack();'); g.advance(501);
    assert.ok(g.run('staffArchiveState.cases.doctor'));
    assert.equal(g.run('Object.keys(staffArchiveState.cases.doctor.documents).length'),2);
    g.run('startBossFight("doctor"); openFleeConfirmModal();');
    assert.equal(g.run('Object.keys(staffArchiveState.cases.doctor.documents).length'),2);
    const restored=game(Object.fromEntries(g.storage));
    assert.equal(restored.run('staffCaseProgress("doctor").opened'),2);
    assert.equal(restored.run('staffArchiveState.cases.nurse'),undefined);
});

test('staff drop threshold is five percent; only new raid documents roll and reset misses', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0.05; startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),1);
    assert.equal(g.run('lastBattleResult.extraRewards.filter(r=>r.type==="document").length'),0);
    g.run('Math.random=()=>0.049; startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),0);
    assert.equal(g.run('lastBattleResult.extraRewards.filter(r=>r.type==="document").length'),1);
    assert.equal(g.run('staffArchiveState.cases.doctor.documents["002-02"]!==undefined'),true);
    g.run('startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.doctor.documents["002-03"]!==undefined'),true);
    g.run('Math.random=()=>0.5; startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),0);
    assert.equal(g.run('lastBattleResult.extraRewards.filter(r=>r.type==="document").length'),0);
    assert.equal(g.run('staffArchiveState.cases.doctor.documents["002-04"]'),undefined);
});

test('document finalization rejects premature and mismatched combat results', () => {
    const g=game();
    g.run('startBossFight("doctor"); Math.random=()=>0; const premature=buildBattleResult(bossesDatabase.doctor); processStaffRaid(premature);');
    assert.equal(g.run('Object.keys(staffArchiveState.processedRaids).length'),0);
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),0);
    g.run('bossCurrentHp=0; const wrong=buildBattleResult(bossesDatabase.doctor); wrong.boss.id="nurse"; processStaffRaid(wrong);');
    assert.equal(g.run('Object.keys(staffArchiveState.processedRaids).length'),0);
    g.run('handleVictory();');
    assert.equal(g.run('Object.keys(staffArchiveState.processedRaids).length'),1);
});

test('pity gives a new eligible document on exactly the thirtieth unsuccessful winning raid', () => {
    let g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0.5;');
    for(let i=0;i<29;i++) g.run('startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),29);
    assert.equal(g.run('staffCaseProgress("doctor").opened'),3); // initial two + five-victory achievement
    g=game(Object.fromEntries(g.storage));
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0.5; startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),0);
    assert.equal(g.run('lastBattleResult.extraRewards.filter(r=>r.type==="document").length'),1);
    const opened=g.run('staffCaseProgress("doctor").opened');
    g.run('handleVictory(); openLastBattleResult(); openDetailedBattleReport(); processStaffRaid(lastBattleResult);');
    assert.equal(g.run('staffCaseProgress("doctor").opened'),opened);
    for(let i=0;i<30;i++) g.run('startBossFight("doctor"); performPlayerAttack();');
    assert.equal(g.run('staffCaseProgress("doctor").complete'),true);
    assert.equal(g.run('staffArchiveState.cases.doctor.misses'),0);
});

test('quest document follows the existing rubble milestone and never joins the random pool', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0; startBossFight("nurse"); performPlayerAttack(); startBossFight("nurse"); performPlayerAttack();');
    assert.equal(g.run('staffArchiveState.cases.nurse.documents["001-05"]'),undefined);
    assert.equal(g.run('staffArchiveState.cases.nurse.misses'),0);
    g.run('const floor=gameFloorsData.find(f=>f.id===10); handleNodeClick(floor.nodes.find(n=>n.type==="grind"),floor);');
    assert.equal(g.run('staffArchiveState.cases.nurse.documents["001-05"]!==undefined'),true);
    assert.equal(g.run('lastBattleResult.extraRewards.some(r=>r.id==="001-05")'),false);
});

test('staff collection rewards journal exactly once; raid-history clear cannot remove documents or claims', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0; for(let i=0;i<5;i++){startBossFight("doctor"); performPlayerAttack();}');
    assert.equal(g.run('staffCaseProgress("doctor").complete'),true);
    const before=g.run('stats.silver');
    assert.equal(g.run('claimStaffReward("case-002-v1")'),true);
    assert.equal(g.run('claimStaffReward("case-002-v1")'),false);
    assert.equal(g.run('claimStaffReward("isolation-v1")'),true);
    assert.equal(g.run('stats.silver'),before+2);
    const state=g.run('JSON.stringify(staffArchiveState)');
    g.run('clearRaidArchive(); openStaffArchive("doctor");');
    assert.equal(g.run('JSON.stringify(staffArchiveState)'),state);
    const restored=game(Object.fromEntries(g.storage));
    assert.equal(restored.run('stats.silver'),before+2);
    assert.equal(restored.run('claimStaffReward("isolation-v1")'),false);
    restored.run('bossesDatabase.future={...bossesDatabase.nurse,key:"future"};');
    assert.equal(restored.run('staffCollectionProgress(STAFF_ARCHIVE_COLLECTIONS[1]).complete'),true);
});

test('interrupted document and collection saves recover ready snapshots without rerolling or recrediting', () => {
    const g=game();
    g.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0; startBossFight("doctor");');
    g.failedKeys.add('palata404_stats'); g.run('performPlayerAttack();');
    const profile=g.run('JSON.stringify(staffArchiveState)');
    const restored=game(Object.fromEntries(g.storage));
    assert.equal(restored.run('JSON.stringify(staffArchiveState)'),profile);
    assert.equal(restored.run('stats.silver'),234);
    restored.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0; for(let i=0;i<4;i++){startBossFight("doctor"); performPlayerAttack();}');
    const before=restored.run('stats.silver');
    restored.failedKeys.add('palata404_stats');
    restored.run('claimStaffReward("case-002-v1");');
    assert.ok(restored.storage.has(restored.run('staffRewardJournalKey()')));
    assert.equal(restored.elements.get('staff-save-note').classList.contains('hidden'),false);
    const recovered=game(Object.fromEntries(restored.storage));
    assert.equal(recovered.run('stats.silver'),before+1);
    assert.equal(recovered.run('claimStaffReward("case-002-v1")'),false);
    assert.equal(recovered.storage.has(recovered.run('staffRewardJournalKey()')),false);
});

test('staff progress is isolated per ID and only trustworthy owned history restores encounters', () => {
    const shared=new Map();
    const a=game({},false,[],101,shared);
    a.run('stats.baseDamage=300; recalculateEquipmentStats(); Math.random=()=>0; startBossFight("nurse"); performPlayerAttack();');
    const b=game({},false,[],202,shared);
    assert.equal(b.run('Object.keys(staffArchiveState.cases).length'),0);
    assert.equal(b.run('Object.keys(staffArchiveState.processedRaids).length'),0);
    const key=a.run('staffArchiveKey()');
    shared.delete(key);
    const migrated=game({},false,[],101,shared);
    assert.ok(migrated.run('staffArchiveState.cases.nurse'));
    assert.equal(migrated.run('staffArchiveState.cases.nurse.documents["001-02"]'),undefined); // no retrospective random rolls
    assert.equal(migrated.run('staffArchiveState.cases.doctor'),undefined);
});

test('data-defined future bosses need no component change and locked secret titles/content never enter DOM', () => {
    const g=game();
    g.run('bossesDatabase.future={...bossesDatabase.nurse,key:"future",name:"Майбутній об’єкт",staffArchive:{department:"Новий блок",rewardId:"case-003-v1",reward:null,introduction:"Вступ",documents:[{id:"003-01",title:"Картка",acquisition:"initial",content:"Перевірений контакт",secret:false}]}}; startBossFight("future"); openFleeConfirmModal(); openStaffArchive("future");');
    assert.equal(g.run('staffCaseProgress("future").total'),1);
    assert.equal(g.run('staffCaseProgress("future").percent'),100);
    g.run('startBossFight("doctor"); openFleeConfirmModal(); openStaffArchive("doctor"); changeStaffArchiveTab("documents");');
    assert.match(g.elements.get('staff-case-sheet').innerHTML,/ДОКУМЕНТ №002-03 — ЗАСЕКРЕЧЕНО/);
    assert.doesNotMatch(g.elements.get('staff-case-sheet').innerHTML,/Незаповнена графа наказу|Копія наказу головного лікаря/);
});

test('staff floor filters use map and boss assignments while department collections and progress stay intact', () => {
    const g=game();
    g.run('startBossFight("doctor"); openFleeConfirmModal(); openStaffArchive("doctor");');
    assert.match(g.elements.get('staff-floor-filter').innerHTML,/Усі поверхи/);
    assert.match(g.elements.get('staff-floor-filter').innerHTML,/9 поверх/);
    assert.match(g.elements.get('staff-floor-filter').innerHTML,/10 поверх/);
    assert.doesNotMatch(g.elements.get('staff-floor-filter').innerHTML,/Процедурне|Блок ізоляторів/);
    assert.match(g.elements.get('staff-case-sheet').innerHTML,/<dt>Локація:<\/dt><dd>Кабінет спостереження/);
    assert.match(g.elements.get('staff-case-sheet').innerHTML,/<dt>Відділення:<\/dt><dd>Блок ізоляторів/);
    const state=g.run('JSON.stringify(staffArchiveState)');
    g.elements.get('staff-floor-filter').value='9';
    g.run('renderStaffArchive();');
    assert.equal(g.elements.get('staff-case-list').innerHTML,'');
    assert.match(g.elements.get('staff-case-sheet').innerHTML,/На цьому поверсі справ не зареєстровано/);
    g.run('bossesDatabase.future={...bossesDatabase.nurse,key:"future",floorId:3}; openStaffArchive();');
    assert.match(g.elements.get('staff-floor-filter').innerHTML,/3 поверх/);
    g.elements.get('staff-floor-filter').value='3'; g.run('renderStaffArchive();');
    assert.equal((g.elements.get('staff-case-list').innerHTML.match(/data-case-index=/g)||[]).length,1);
    assert.equal(g.run('selectedStaffBossId'),'future');
    assert.equal(g.run('JSON.stringify(staffArchiveState)'),state);
});

test('paper doll retires trial faces and persists independent previews without changing combat gear', () => {
    const g = game({ palata404_gender: 'female', palata404_face: 'face_3.png' });
    assert.equal(g.run('paperDollState.selectedGender'), 'female');
    assert.equal(g.run('paperDollState.appearance.face'), null);
    assert.equal(g.run('paperDollState.patientLoadout.face'), null);
    const combat = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    g.run('equipPaperDollItem("armor","gear-br1"); setPaperDollView("combat"); setFace("face_2.png"); equipPaperDollItem("weapon","gear-pm"); setGender("male");');
    assert.equal(g.run('paperDollState.patientLoadout.armor'), 'gear-br1');
    assert.equal(g.run('paperDollState.patientLoadout.weapon'), null);
    assert.equal(g.run('paperDollState.combatLoadout.armor'), null);
    assert.equal(g.run('paperDollState.appearance.face'), null);
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), combat);
    const restored = game(Object.fromEntries(g.storage));
    assert.equal(restored.run('JSON.stringify(paperDollState)'), g.run('JSON.stringify(paperDollState)'));
    restored.run('setPaperDollView("patient"); equipPaperDollItem("face",null);');
    assert.equal(restored.run('paperDollState.appearance.face'), null);
    assert.equal(restored.run('paperDollState.appearance.face'), null);
    assert.equal(restored.run('paperDollState.combatLoadout.weapon'), 'gear-pm');
});

test('paper doll rejects malformed saves, wrong slots and unsupported images while owned gear without PNG remains usable', () => {
    const g = game({ palata404_paper_doll: JSON.stringify({ schemaVersion: 1, selectedGender: '../missing', activeViewMode: 'evil',
        patientLoadout: { weapon: 'face_1.png', face: '../../missing.png', armor: 'sample-armor' }, combatLoadout: null }) });
    assert.equal(g.run('paperDollState.selectedGender'), 'male');
    assert.equal(g.run('paperDollState.activeViewMode'), 'patient');
    assert.equal(g.run('paperDollState.patientLoadout.weapon'), null);
    assert.equal(g.run('paperDollState.appearance.face'), null);
    assert.equal(g.run('paperDollState.patientLoadout.armor'), 'gear-br1');
    assert.equal(g.elements.get('layer-armor').getAttribute('src'), null);
    assert.equal(g.elements.get('layer-armor').classList.contains('hidden'), true);
    const before = g.run('JSON.stringify(paperDollState)');
    assert.equal(g.run('equipPaperDollItem("baseBody","face_1.png")'), false);
    assert.equal(g.run('equipPaperDollItem("weapon","face_1.png")'), false);
    assert.equal(g.run('equipPaperDollItem("unknown",null)'), false);
    assert.equal(g.run('setPaperDollView("unknown")'), false);
    assert.equal(g.run('JSON.stringify(paperDollState)'), before);
    assert.equal(g.run('paperDollImageCandidates({genderVariants:{female:"https://example.test/a.png",male:"face_1.png"},image:"../missing.png"},"female").join()'), 'face_1.png');
    const broken = game({ palata404_paper_doll: '{', palata404_face: 'face_4.png' });
    assert.equal(broken.run('paperDollState.appearance.face'), null);
});

test('paper doll gender fallback, missing PNG errors and stable layer order do not alter selected equipment', () => {
    const g = game();
    g.run('PAPER_DOLL_ITEMS.push({id:"future-coat",slot:"outerwear",name:"Плащ",availableByDefault:true,genderVariants:{female:"missing-coat.png",male:"face_1.png"}}); setGender("female"); equipPaperDollItem("outerwear","future-coat");');
    const layer = g.elements.get('layer-outerwear');
    assert.equal(layer.getAttribute('src'), 'missing-coat.png');
    layer.onerror();
    assert.equal(layer.getAttribute('src'), 'face_1.png');
    layer.onerror();
    assert.equal(layer.getAttribute('src'), null);
    assert.equal(layer.classList.contains('hidden'), true);
    assert.equal(g.run('paperDollState.patientLoadout.outerwear'), 'future-coat');
    assert.equal(g.run('PAPER_DOLL_LAYER_ORDER.join()'), 'baseBody,pants,footwear,upperBody,outerwear,armor,loadout,gloves,back,hair,headwear,face,weapon,accessory');
    assert.equal(g.elements.get('layer-weapon').style.zIndex, '12');
    assert.equal(g.elements.get('layer-armor').style.width, '100%');
});

test('paper doll storage failures preserve in-memory choices and retry without combat changes', () => {
    const g = game({}, false, ['palata404_paper_doll']);
    const combat = g.run('JSON.stringify({stats,inventory,equippedGear})');
    g.run('setGender("female"); setPaperDollView("combat"); equipPaperDollItem("headwear","gear-helmet");');
    assert.equal(g.run('paperDollSaveFailed'), true);
    assert.equal(g.elements.get('paper-doll-save-note').classList.contains('hidden'), false);
    assert.equal(g.storage.has('palata404_paper_doll'), false);
    g.failedKeys.clear(); g.run('retryPaperDollSave();');
    assert.equal(g.run('paperDollSaveFailed'), false);
    assert.equal(JSON.parse(g.storage.get('palata404_paper_doll')).combatLoadout.headwear, 'gear-helmet');
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear})'), combat);
});

test('wardrobe v1 migration retires trial faces while preserving owned gear and inert legacy metadata', () => {
    const g = game({ palata404_paper_doll: JSON.stringify({ schemaVersion: 1, selectedGender: 'female', activeViewMode: 'combat',
        patientLoadout: { face: 'face_3.png', armor: 'sample-armor' }, combatLoadout: { face: 'face_2.png', weapon: 'sample-weapon' } }) });
    assert.equal(g.run('paperDollState.schemaVersion'),2);
    assert.equal(g.run('paperDollState.appearance.face'),null);
    assert.equal(g.run('paperDollState.legacyFaces.patient'),'face_3.png');
    assert.equal(g.run('paperDollState.legacyFaces.combat'),'face_2.png');
    assert.equal(g.run('paperDollState.patientLoadout.armor'),'gear-br1');
    assert.equal(g.run('paperDollState.combatLoadout.weapon'),'gear-pm');
    g.run('setPaperDollView("patient");');
    assert.equal(g.run('currentFace'),'');
    g.run('setFace("face_4.png"); setPaperDollView("combat");');
    assert.equal(g.run('currentFace'),'');
    const restored=game(Object.fromEntries(g.storage));
    assert.equal(restored.run('JSON.stringify(paperDollState)'),g.run('JSON.stringify(paperDollState)'));
});

test('wardrobe cannot equip unowned inventory gear or create quantities through repeated choices', () => {
    const g=game({palata404_inventory:'[]',palata404_paper_doll:JSON.stringify({schemaVersion:2,appearance:{face:'face_1.png'},patientLoadout:{weapon:'gear-pm'},combatLoadout:{armor:'gear-br1'}})});
    assert.equal(g.run('paperDollState.patientLoadout.weapon'),null);
    assert.equal(g.run('equipPaperDollItem("weapon","gear-pm")'),false);
    assert.equal(g.run('inventory.length'),0);
    g.run('inventory.push({...DEFAULT_INVENTORY.find(item=>item.category==="armor"),count:1});');
    const before=g.run('JSON.stringify({inventory,stats,equippedGear})');
    g.run('for(let i=0;i<5;i++){equipPaperDollItem("armor","gear-br1");equipPaperDollItem("armor",null)};setPaperDollView("combat");equipPaperDollItem("armor","gear-br1");');
    assert.equal(g.run('JSON.stringify({inventory,stats,equippedGear})'),before);
});

test('one paper doll renderer synchronizes both views and removes front and rear parts when unequipped', () => {
    const g=game();
    g.run('PAPER_DOLL_ITEMS.push({id:"layered-fixture",slot:"back",name:"Fixture",availableByDefault:true,layers:[{id:"rear",image:"base_male.png",renderOrder:-1},{id:"front",image:"base_female.png",renderOrder:9}]}); equipPaperDollItem("back","layered-fixture");');
    for(const prefix of ['', 'wardrobe-']) {
        assert.equal(g.elements.get(prefix+'layer-back-rear').style.zIndex,'-1');
        assert.equal(g.elements.get(prefix+'layer-back-front').style.zIndex,'9');
        assert.equal(g.elements.get(prefix+'layer-back-rear').getAttribute('src'),'base_male.png');
    }
    g.run('equipPaperDollItem("back",null);');
    assert.equal(g.elements.has('layer-back-rear'),false);
    assert.equal(g.elements.has('wardrobe-layer-back-front'),false);
});


test('retired faces are disabled in legacy, v1 and v2 saves without losing character data', () => {
    for (let i=1;i<=6;i++) {
        const id=`face_${i}.png`;
        const sources=[{palata404_face:id}, ...[1,2].map(schemaVersion=>({palata404_paper_doll:JSON.stringify({schemaVersion,selectedGender:'female',activeViewMode:'combat',appearance:{face:id,hair:'saved-hair'},patientLoadout:{face:id,armor:'gear-br1'},combatLoadout:{face:id,weapon:'gear-pm'}})}))];
        for (const saves of sources) {
            const g=game(saves);
            assert.equal(g.run('paperDollState.appearance.face'),null);
            assert.equal(g.run('setFace('+JSON.stringify(id)+')'),undefined);
            assert.equal(g.run('equipPaperDollItem("face",'+JSON.stringify(id)+')'),false);
            for (const prefix of ['', 'wardrobe-']) assert.equal(g.elements.get(prefix+'layer-face').getAttribute('src'),g.run('paperDollState.selectedGender==="female"?PAPER_DOLL_NATIVE_HEADS.female.genderVariants.female:null'));
            if(saves.palata404_paper_doll) {
                assert.equal(g.run('paperDollState.selectedGender'),'female');
                assert.equal(g.run('paperDollState.activeViewMode'),'combat');
                assert.equal(g.run('paperDollState.patientLoadout.armor'),'gear-br1');
                assert.equal(g.run('paperDollState.combatLoadout.weapon'),'gear-pm');
            }
            const before=g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
            g.run('saveGameProgress();');
            const restored=game(Object.fromEntries(g.storage));
            assert.equal(restored.run('paperDollState.appearance.face'),null);
            assert.equal(restored.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before);
        }
    }
});

test('future approved face layers remain selectable, shared and persistent', () => {
    const g=game();
    g.run('PAPER_DOLL_ITEMS.push({id:"approved-face",slot:"face",name:"Approved",image:"base_male.png",availableByDefault:true,placement:{x:360,y:32,width:220,height:218}});');
    assert.equal(g.run('equipPaperDollItem("face","approved-face")'),true);
    g.run('setPaperDollView("combat"); setGender("female");');
    assert.equal(g.run('paperDollState.appearance.face'),'approved-face');
    assert.equal(g.run('normalizePaperDollState(JSON.parse(safeStorageGet(PAPER_DOLL_STORAGE_KEY))).appearance.face'),'approved-face');
    for(const prefix of ['', 'wardrobe-']) assert.equal(g.elements.get(prefix+'layer-face').getAttribute('src'),'base_male.png');
    g.run('equipPaperDollItem("face",null);');
    assert.equal(g.run('paperDollState.appearance.face'),null);
});

test('wardrobe V3 inspection is transient and only the action changes the visual loadout', () => {
    const g=game();
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})');
    const saved=JSON.stringify([...g.storage]);
    g.run('selectWardrobeCategory("weapons");selectWardrobeItem("gear-pm");');
    assert.equal(g.run('wardrobeSelectedItemId'),'gear-pm');
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})'),before);
    assert.equal(JSON.stringify([...g.storage]),saved);
    assert.equal(g.run('selectWardrobeItem("gear-br1")'),false);
    assert.equal(g.run('applyWardrobeItemAction()'),true);
    assert.equal(g.run('paperDollState.patientLoadout.weapon'),'gear-pm');
    assert.equal(g.run('applyWardrobeItemAction()'),true);
    assert.equal(g.run('paperDollState.patientLoadout.weapon'),null);
});

test('wardrobe V3 shows unowned item details without granting equipment', () => {
    const g=game({palata404_inventory:'[]'});
    g.run('selectWardrobeCategory("weapons");selectWardrobeItem("gear-pm");');
    assert.match(g.elements.get('wardrobe-item-detail').innerHTML,/disabled/);
    assert.match(g.elements.get('wardrobe-item-detail').innerHTML,/Недоступно/);
    const before=g.run('JSON.stringify({inventory,stats,equippedGear,paperDollState})');
    assert.equal(g.run('applyWardrobeItemAction()'),false);
    assert.equal(g.run('JSON.stringify({inventory,stats,equippedGear,paperDollState})'),before);
});

test('production patient tunic preserves the exact approved corrected ZIP bytes', () => {
    const g = game();
    const expectedBlobs = {
        male: '28343fe90d876c7d785d0093d4f34fc3a5148a36',
        female: 'fa3fac64dac856654ec4cf9eb9da72af05f1cc21',
    };
    for (const [gender, expected] of Object.entries(expectedBlobs)) {
        const source = g.run(`PAPER_DOLL_ITEMS.find(item=>item.id==='patient-tunic').genderVariants.${gender}`);
        const png = fs.readFileSync(path.join(root, source.split('?')[0]));
        const blob = require('node:crypto').createHash('sha1')
            .update(`blob ${png.length}\0`).update(png).digest('hex');
        assert.equal(blob, expected, `${gender} clothing must preserve the corrected PNG bytes`);
    }
});

test('a fresh patient starts dressed while the combat outfit stays independent without inventory grants', () => {
    const g = game({ palata404_inventory: '[]' });
    assert.equal(g.run('paperDollState.patientLoadout.upperBody'), 'patient-tunic');
    assert.equal(g.run('paperDollState.combatLoadout.upperBody'), null);
    assert.equal(g.run('inventory.length'), 0);
    assert.equal(g.run('isPaperDollItemOwned(selectedPaperDollItem("upperBody"))'), true);
    for (const prefix of ['', 'wardrobe-']) {
        assert.equal(g.elements.get(prefix + 'layer-upper-body-front').getAttribute('src'),
            'assets/wardrobe/clothing/patient/patient_tunic_male.png?v=b0da3128');
    }
    const combat = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    g.run('setPaperDollView("combat");');
    for (const prefix of ['', 'wardrobe-']) {
        assert.equal(g.elements.get(prefix + 'layer-upper-body-front')?.getAttribute('src') ?? null, null);
    }
    assert.equal(g.run('equipPaperDollItem("upperBody","patient-tunic")'), true);
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), combat);
    assert.equal(g.run('inventory.length'), 0);
});

test('existing empty, corrupt and unsupported wardrobe records never receive a new starter outfit', () => {
    const records = [
        ...[1, 2].map(schemaVersion => JSON.stringify({ schemaVersion, selectedGender: 'female',
            activeViewMode: 'combat', patientLoadout: { upperBody: null }, combatLoadout: { upperBody: null } })),
        JSON.stringify({ schemaVersion: 2, patientLoadout: {}, combatLoadout: {} }),
        JSON.stringify({ schemaVersion: 99, patientLoadout: {}, combatLoadout: {} }),
        '{', 'null', '',
    ];
    for (const record of records) {
        const g = game({ palata404_paper_doll: record });
        assert.equal(g.run('paperDollState.patientLoadout.upperBody'), null, record);
        assert.equal(g.run('paperDollState.combatLoadout.upperBody'), null, record);
        const restored = game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.patientLoadout.upperBody'), null, record);
        assert.equal(restored.run('paperDollState.combatLoadout.upperBody'), null, record);
    }
});

test('tunic removal and independent patient and combat choices survive reloads', () => {
    let g = game();
    const combat = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    assert.equal(g.run('equipPaperDollItem("upperBody",null)'), true);
    g.run('setPaperDollView("combat"); equipPaperDollItem("upperBody","patient-tunic");');
    g = game(Object.fromEntries(g.storage));
    assert.equal(g.run('paperDollState.patientLoadout.upperBody'), null);
    assert.equal(g.run('paperDollState.combatLoadout.upperBody'), 'patient-tunic');
    g.run('equipPaperDollItem("upperBody",null); setPaperDollView("patient");');
    g = game(Object.fromEntries(g.storage));
    assert.equal(g.run('paperDollState.patientLoadout.upperBody'), null);
    assert.equal(g.run('paperDollState.combatLoadout.upperBody'), null);
    for (const prefix of ['', 'wardrobe-']) {
        assert.equal(g.elements.get(prefix + 'layer-upper-body-front')?.getAttribute('src') ?? null, null);
    }
    g.run('equipPaperDollItem("upperBody","patient-tunic");');
    const restored = game(Object.fromEntries(g.storage));
    assert.equal(restored.run('paperDollState.patientLoadout.upperBody'), 'patient-tunic');
    assert.equal(restored.run('paperDollState.combatLoadout.upperBody'), null);
    assert.equal(restored.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), combat);
});

test('gender changes retain the tunic selection and use matching clothing in both character views', () => {
    const g = game();
    const combat = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    g.run('setPaperDollView("combat"); equipPaperDollItem("upperBody","patient-tunic");');
    for (const [gender, source] of [
        ['female', 'assets/wardrobe/clothing/patient/patient_tunic_female.png?v=809fd1e8'],
        ['male', 'assets/wardrobe/clothing/patient/patient_tunic_male.png?v=b0da3128'],
    ]) {
        g.run(`setGender('${gender}');`);
        assert.equal(g.run('paperDollState.patientLoadout.upperBody'), 'patient-tunic');
        assert.equal(g.run('paperDollState.combatLoadout.upperBody'), 'patient-tunic');
        for (const prefix of ['', 'wardrobe-']) {
            assert.equal(g.elements.get(prefix + 'layer-upper-body-front').getAttribute('src'), source);
        }
        const restored = game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.selectedGender'), gender);
        assert.equal(restored.elements.get('layer-upper-body-front').getAttribute('src'), source);
    }
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), combat);
});

test('failed fitted clothing hides instead of substituting shared or opposite-gender art', () => {
    const g = game();
    const before = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})');
    g.elements.get('layer-upper-body-front').onerror();
    for (const prefix of ['', 'wardrobe-']) {
        const layer = g.elements.get(prefix + 'layer-upper-body-front');
        assert.equal(layer.getAttribute('src'), null);
        assert.equal(layer.classList.contains('hidden'), true);
    }
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,paperDollState})'), before);
    // A missing current variant is also a missing image, even if the fitted
    // garment has another gender's variant or a generic image configured.
    assert.equal(g.run(`paperDollImageCandidates({
        ...PAPER_DOLL_ITEMS.find(item=>item.id==='patient-tunic'),
        genderVariants:{female:'base_female.png'}, image:'base_male.png'
    },'male').length`), 0);
    g.run('setGender("female");');
    assert.equal(g.elements.get('layer-upper-body-front').getAttribute('src'),
        'assets/wardrobe/clothing/patient/patient_tunic_female.png?v=809fd1e8');
    g.elements.get('layer-upper-body-front').onerror();
    assert.equal(g.elements.get('layer-upper-body-front').getAttribute('src'), null);
    assert.equal(g.run('paperDollState.patientLoadout.upperBody'), 'patient-tunic');
});

test('fitted clothing keeps local PNG path restrictions', () => {
    const g = game();
    for (const source of [
        'https://example.test/shirt.png', '//example.test/shirt.png', '../shirt.png',
        'assets/../shirt.png', 'assets/%2e%2e/shirt.png', 'shirt.svg',
        'shirt.png?tracking=1', 'shirt.png?v=ok&tracking=1',
    ]) {
        assert.equal(g.run(`paperDollImageCandidates({
            ...PAPER_DOLL_ITEMS.find(item=>item.id==='patient-tunic'),
            genderVariants:{male:${JSON.stringify(source)}}
        },'male').length`), 0, source);
    }
});

test('retrying a failed wardrobe save preserves an intentionally removed starter', () => {
    const g = game({}, false, ['palata404_paper_doll']);
    assert.equal(g.run('paperDollState.patientLoadout.upperBody'), 'patient-tunic');
    const combat = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    g.run('equipPaperDollItem("upperBody",null);');
    assert.equal(g.run('paperDollSaveFailed'), true);
    assert.equal(g.run('paperDollState.patientLoadout.upperBody'), null);
    g.failedKeys.clear();
    g.run('retryPaperDollSave();');
    assert.equal(g.run('paperDollSaveFailed'), false);
    const restored = game(Object.fromEntries(g.storage));
    assert.equal(restored.run('paperDollState.patientLoadout.upperBody'), null);
    assert.equal(restored.run('paperDollState.combatLoadout.upperBody'), null);
    assert.equal(restored.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), combat);
});

test('the approved neckline part follows only the female tunic across modes, saves and replacements', () => {
    const g = game();
    const before = g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    const neck = 'assets/wardrobe/clothing/patient/female_neckline_skin_underlay.png?v=8a9076fa';
    for (const mode of ['patient', 'combat']) {
        g.run(`setPaperDollView('${mode}');setGender('female');equipPaperDollItem('upperBody','patient-tunic');`);
        assert.equal(g.run('wardrobeImageStatus(PAPER_DOLL_ITEMS.find(item=>item.id==="patient-tunic")).state'), 'ready');
        for (const prefix of ['', 'wardrobe-']) {
            const layer = g.elements.get(prefix+'layer-upper-body-neckline');
            assert.equal(layer.getAttribute('src'), neck);
            assert.equal(layer.style.zIndex, '2');
            for (const id of ['layer-body','layer-upper-body-front','layer-upper-body-neckline']) {
                const style = g.elements.get(prefix+id).style;
                assert.equal(style.left, '0%'); assert.equal(style.top, '0%');
                assert.equal(style.width, '100%'); assert.equal(style.height, '100%');
            }
        }
        const restored = game(Object.fromEntries(g.storage));
        assert.equal(restored.elements.get('layer-upper-body-neckline').getAttribute('src'), neck);
        g.run('setGender("male");');
        assert.equal(g.run('wardrobeImageStatus(PAPER_DOLL_ITEMS.find(item=>item.id==="patient-tunic")).state'), 'ready');
        for (const prefix of ['', 'wardrobe-']) assert.equal(g.elements.has(prefix+'layer-upper-body-neckline'), false);
        g.run('setGender("female");equipPaperDollItem("upperBody",null);');
        for (const prefix of ['', 'wardrobe-']) {
            assert.equal(g.elements.has(prefix+'layer-upper-body-neckline'), false);
            assert.equal(g.elements.has(prefix+'layer-upper-body-front'), false);
        }
    }
    g.run('PAPER_DOLL_ITEMS.push({id:"other-clothing",slot:"upperBody",availableByDefault:true,image:"base_female.png"});equipPaperDollItem("upperBody","patient-tunic");equipPaperDollItem("upperBody","other-clothing");');
    for (const prefix of ['', 'wardrobe-']) assert.equal(g.elements.has(prefix+'layer-upper-body-neckline'), false);
    g.run('equipPaperDollItem("upperBody","patient-tunic");');
    g.elements.get('layer-upper-body-neckline').onerror();
    assert.equal(g.run('wardrobeImageStatus(PAPER_DOLL_ITEMS.find(item=>item.id==="patient-tunic")).state'), 'partial');
    g.run('setGender("male");');
    assert.equal(g.run('wardrobeImageStatus(PAPER_DOLL_ITEMS.find(item=>item.id==="patient-tunic")).state'), 'ready');
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'), before);
});

test('approved hair remains shared appearance with eight choices, gender-fitted art and persistent bald reset', () => {
    const g=game();
    assert.equal(g.run('paperDollState.appearance.hair'),'hair-none');
    assert.equal(g.run('PAPER_DOLL_SLOTS.hair.label'),'Зачіски');
    assert.equal(g.run('PAPER_DOLL_ITEMS.filter(item=>item.slot==="hair"&&!item.id.startsWith("hair-m6-")&&item.id!=="hair-trial-braided-curls"&&![\"hair-f5-pixie\", \"hair-f5-jaw-bob\", \"hair-f5-long-waves\", \"hair-f5-high-ponytail\", \"hair-f5-braided-updo\"].includes(item.id)).length'),8);
    assert.equal(g.run('wardrobeImageStatus(selectedPaperDollItem("hair")).state'),'ready');
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    for(const id of ['hair-messy','hair-bob','hair-double-buns','hair-classic-short','hair-textured-short','hair-shoulder-length']) {
        assert.equal(g.run(`equipPaperDollItem('hair','${id}')`),true);
        for(const gender of ['male','female']) {
            g.run(`setGender('${gender}');setPaperDollView('combat');`);
            assert.equal(g.run('paperDollState.appearance.hair'),id);
            const source=g.run('selectedPaperDollItem("hair").genderVariants[paperDollState.selectedGender]');
            if (['hair-classic-short','hair-textured-short'].includes(id)) {
                assert.match(source,/\/hair\/classic_short_unisex_style_[AB]\.png/);
                assert.equal(g.run('selectedPaperDollItem("hair").genderVariants.male===selectedPaperDollItem("hair").genderVariants.female'),true);
                assert.notEqual(g.run('JSON.stringify(selectedPaperDollItem("hair").placementByGender.male)'),g.run('JSON.stringify(selectedPaperDollItem("hair").placementByGender.female)'));
            } else assert.match(source,new RegExp(`/hair/${gender}_`));
            for(const prefix of ['', 'wardrobe-']) {
                assert.equal(g.elements.get(prefix+'layer-hair').getAttribute('src'),source);
                assert.equal(g.elements.get(prefix+'layer-hair').style.objectFit,id==='hair-messy'&&gender==='male'?'fill':'');
            }
            g.run('setPaperDollView("patient")');
            assert.equal(g.run('paperDollState.appearance.hair'),id);
            const restored=game(Object.fromEntries(g.storage));
            assert.equal(restored.run('paperDollState.appearance.hair'),id);
            assert.equal(restored.elements.get('layer-hair').getAttribute('src'),source);
        }
    }
    g.run('equipPaperDollItem("hair",null)');
    for(const prefix of ['', 'wardrobe-']) assert.equal(g.elements.get(prefix+'layer-hair').getAttribute('src'),null);
    assert.equal(g.run('paperDollState.appearance.hair'),'hair-none');
    assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.hair'),'hair-none');
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before);
    assert.equal(g.run('equipPaperDollItem("hair","patient-tunic")'),false);
    assert.equal(g.run('equipPaperDollItem("upperBody","hair-bob")'),false);
    assert.equal(g.run('Object.hasOwn(paperDollState.patientLoadout,"hair")'),false);
});

test('hair migration retains inert legacy metadata, failed art never swaps gender and inspection never saves', () => {
    for(const saves of [{},{palata404_hair:'retired-hair'}, {palata404_paper_doll:JSON.stringify({schemaVersion:1,selectedGender:'female',patientLoadout:{upperBody:'patient-tunic'}})},
        {palata404_paper_doll:JSON.stringify({schemaVersion:2,appearance:{hair:'old-hair'},patientLoadout:{upperBody:'patient-tunic'}})}]) {
        const g=game(saves);
        assert.equal(g.run('selectedPaperDollItem("hair").id'),'hair-none');
        assert.equal(g.elements.get('layer-hair').getAttribute('src'),null);
        if(saves.palata404_hair) assert.equal(g.run('paperDollState.appearance.hair'),'retired-hair');
        g.run('selectWardrobeCategory("hair")');
        const before=JSON.stringify([...g.storage]),state=g.run('JSON.stringify(paperDollState)');
        g.run('selectWardrobeItem("hair-bob")');
        assert.equal(JSON.stringify([...g.storage]),before);assert.equal(g.run('JSON.stringify(paperDollState)'),state);
        g.run('applyWardrobeItemAction()');
        assert.equal(g.run('paperDollState.appearance.hair'),'hair-bob');
        const source=g.elements.get('layer-hair').getAttribute('src');
        g.elements.get('layer-hair').onerror();
        assert.equal(g.elements.get('layer-hair').getAttribute('src'),null);
        assert.equal(g.run('paperDollState.appearance.hair'),'hair-bob');
        g.run('setGender(paperDollState.selectedGender==="male"?"female":"male")');
        assert.notEqual(g.elements.get('layer-hair').getAttribute('src'),source);
        assert.notEqual(g.elements.get('layer-hair').getAttribute('src'),null);
    }
});

test('hair colors migrate safely and preserve pigment texture, alpha and cosmetic save scope', () => {
    const g=game();
    assert.equal(g.run('Object.keys(WARDROBE_CATEGORIES).length'),5);
    assert.equal(g.run('WARDROBE_CATEGORIES.appearance.slots.join(",")'),'baseBody,face,hair');
    assert.equal(g.run('HAIR_COLORS.length'),25);
    assert.equal(g.run('new Set(HAIR_COLORS.map(c=>c.id)).size'),25);
    assert.equal(g.run('HAIR_COLORS.filter(c=>c.group==="natural").length'),12);
    assert.equal(g.run('HAIR_COLORS.filter(c=>c.group==="alternative").length'),12);
    for(const value of [null,{}, {schemaVersion:1}, {schemaVersion:2,appearance:{hairColor:'bad'}}]) {
        assert.equal(g.run(`normalizePaperDollState(${JSON.stringify(value)}).appearance.hairColor`),'original');
    }
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    for(const color of g.run('HAIR_COLORS.map(c=>c.id)')) {
        assert.equal(g.run(`setHairColor(${JSON.stringify(color)})`),true);
        assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.hairColor'),color);
    }
    assert.equal(g.run('setHairColor("unknown")'),false);
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before);
    // Transparent and translucent edges retain exact alpha; separate strands keep contrast.
    for(const hex of ['#201A19','#E7E4DD','#E6DDC8','#F07BAF','#2876EC']) {
        const result=g.run(`Array.from(recolorHairPixels(new Uint8ClampedArray([22,12,8,255,80,55,35,255,150,110,70,255,80,55,35,1,77,88,99,0]),'${hex}'))`);
        assert.deepEqual([result[3],result[7],result[11],result[15],result[19]],[255,255,255,1,0]);
        assert.ok(result[0]<result[4] && result[4]<result[8],hex+' retains strand lighting');
        assert.deepEqual(Array.from(result.slice(16,19)),[77,88,99]);
    }
});

test('approved Asian head variants stay below hair and preserve shared cosmetics, outfits and reloads', () => {
    const g=game();
    assert.equal(g.run('paperDollState.appearance.face'),null);
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    const hairGeometry=g.run('JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>i.placementByGender))');
    for(const gender of ['male','female']) for(const hair of ['hair-none','hair-classic-short','hair-textured-short','hair-messy','hair-shoulder-length','hair-bob','hair-double-buns']) {
        g.run(`setGender('${gender}');equipPaperDollItem('hair','${hair}');equipPaperDollItem('face','face-asian')`);
        assert.equal(g.run('paperDollState.appearance.hair'),hair);
        for(const prefix of ['','wardrobe-']) {
            const face=g.elements.get(prefix+'layer-face');
            assert.match(face.getAttribute('src'),new RegExp('/faces/'+(gender==='female'?'standardized/':'')+gender+'_asian_head.png'));
            assert.ok(Number(face.style.zIndex)>Number(g.elements.get(prefix+'layer-body').style.zIndex));
            assert.ok(Number(face.style.zIndex)<Number(g.elements.get(prefix+'layer-hair').style.zIndex));
        }
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.appearance.face'),'face-asian');
        assert.equal(restored.run('paperDollState.appearance.hair'),hair);
        g.run('equipPaperDollItem("face",null)');
        assert.equal(g.run('paperDollState.appearance.hair'),hair);
        assert.equal(g.elements.get('layer-face').getAttribute('src'),gender==='female'?g.run('PAPER_DOLL_NATIVE_HEADS.female.genderVariants.female'):null);
    }
    g.run('equipPaperDollItem("hair","hair-none");setHairColor("blue");equipPaperDollItem("face","face-asian");setPaperDollView("combat")');
    assert.equal(g.run('paperDollState.appearance.hairColor'),'blue');
    assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.hairColor'),'blue');
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before);
    assert.equal(g.run('JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>i.placementByGender))'),hairGeometry);
});

test('female face packs keep legacy IDs and add female-only catalog choices', () => {
    const g=game();
    assert.equal(g.run('PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"female")).length'),15);
    assert.equal(g.run('PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"male")).length'),15);
    for(const id of ['face-asian','face-young','face-exhausted','face-elder','face-alternative']) {
        for(const gender of ['male','female']) {
            g.run(`setGender('${gender}')`);
            assert.equal(g.run(`equipPaperDollItem('face','${id}')`),true);
            assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.face'),id);
        }
    }
});

test('female-only faces reset safely on gender changes and unsupported male saves', () => {
    const g=game();
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    for(const id of ['face-ginger-soft','face-goth-septum','face-goth-black-lips']) {
        g.run('setGender("female");equipPaperDollItem("hair","hair-messy");setHairColor("white")');
        assert.equal(g.run(`equipPaperDollItem('face','${id}')`),true);
        const saved=JSON.parse(g.storage.get('palata404_paper_doll'));
        assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.face'),id);
        saved.selectedGender='male';
        const migrated=game({...Object.fromEntries(g.storage),palata404_paper_doll:JSON.stringify(saved)});
        assert.equal(migrated.run('paperDollState.appearance.face'),null);
        assert.equal(migrated.run('paperDollState.appearance.hair'),'hair-messy');
        assert.equal(migrated.run('paperDollState.appearance.hairColor'),'white');
        g.run('setGender("male")');
        assert.equal(g.run('paperDollState.appearance.face'),null);
        assert.equal(g.run(`equipPaperDollItem('face','${id}')`),false);
        for(const prefix of ['','wardrobe-']) assert.equal(g.elements.get(prefix+'layer-face').getAttribute('src'),null);
        assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before);
    }
});

test('independent face audit rejects malformed and retired face IDs without changing progress or outfits', () => {
    const valid=game();
    valid.run('setGender("female");setPaperDollView("combat");equipPaperDollItem("upperBody",null);setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic")');
    const saved=Object.fromEntries(valid.storage);
    const expected=valid.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    for(const face of ['face_1.png','missing-face','',42,[],{},null]) {
        const doll=JSON.parse(saved.palata404_paper_doll);doll.appearance.face=face;
        const g=game({...saved,palata404_paper_doll:JSON.stringify(doll)});
        assert.equal(g.run('paperDollState.appearance.face'),null);
        assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),expected);
        const reloaded=game(Object.fromEntries(g.storage));
        assert.equal(reloaded.run('paperDollState.appearance.face'),null);
    }
});

test('independent face audit migrates v1 selected mode and keeps old paired IDs across gender changes', () => {
    for(const id of ['face-asian','face-young','face-exhausted','face-elder','face-alternative']) {
        const g=game({palata404_paper_doll:JSON.stringify({schemaVersion:1,selectedGender:'female',activeViewMode:'combat',
            patientLoadout:{face:'face-young',upperBody:'patient-tunic'},combatLoadout:{face:id}})});
        assert.equal(g.run('paperDollState.appearance.face'),id);
        g.run('setGender("male")');assert.equal(g.run('paperDollState.appearance.face'),id);
        assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.face'),id);
        assert.equal(g.run('paperDollState.patientLoadout.upperBody'),'patient-tunic');
        assert.equal(g.run('paperDollState.combatLoadout.upperBody'),null);
    }
});

test('crown clipping covers affected heads and clears on unaffected hairstyles', () => {
    const g=game();
    const geometry=g.run('JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>i.placementByGender))');
    for(const [gender,face,hair,active] of [
        ['male','face-asian','hair-shoulder-length',true],
        ['female','face-asian','hair-shoulder-length',true],
        ['male','face-asian','hair-shoulder-length',true],
        ['male','face-asian','hair-classic-short',false],
        ['male','face-asian','hair-shoulder-length',true],
        ['male',null,'hair-shoulder-length',true],
        ['male','face-asian','hair-shoulder-length',true],
        ['male','face-asian','hair-none',false],
        ['male',null,'hair-bob',true],
        ['female',null,'hair-bob',true],
        ['male',null,'hair-double-buns',true],
        ['female',null,'hair-double-buns',true],
        ['male',null,'hair-messy',false],
        ['male','face-asian','hair-messy',true],
        ['female','face-asian','hair-textured-short',false]
    ]) {
        g.run(`setGender('${gender}');equipPaperDollItem('face',${JSON.stringify(face)});equipPaperDollItem('hair','${hair}')`);
        for(const prefix of ['','wardrobe-']) for(const slot of ['body','face']) {
            const clip=g.elements.get(prefix+'layer-'+slot).style.clipPath;
            assert.equal(Boolean(clip),active);
            if(active) assert.match(clip,/^polygon\(/);
        }
    }
    assert.equal(g.run('JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>i.placementByGender))'),geometry);
});

test('young face variants persist without changing approved hair, outfits or old-face rendering', () => {
    const g=game();
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    const geometry=g.run('JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>i.placementByGender))');
    for(const gender of ['male','female']) {
        g.run(`setGender('${gender}');equipPaperDollItem('face','face-young');equipPaperDollItem('hair','hair-bob');setHairColor('white')`);
        for(const prefix of ['','wardrobe-']) {
            const face=g.elements.get(prefix+'layer-face'),body=g.elements.get(prefix+'layer-body');
            assert.ok(face.getAttribute('src').includes(gender+'_young_head.png'));
            assert.equal(face.style.zIndex,'1');
            assert.ok(body.style.maskImage.includes(gender+'_young_body.png'));
            assert.match(body.style.maskImage,/^url\(/);
            assert.match(face.style.clipPath,/^polygon/);
        }
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.appearance.face'),'face-young');
        assert.equal(restored.run('paperDollState.appearance.hairColor'),'white');
        for(const face of [null]) {
            g.run(`equipPaperDollItem('face',${JSON.stringify(face)})`);
            for(const prefix of ['','wardrobe-']) assert.equal(g.elements.get(prefix+'layer-body').style.maskImage,gender==='female'?'url("'+g.run('PAPER_DOLL_NATIVE_HEADS.female.bodyMaskByGender.female')+'")':'');
        }
    }
    g.run("equipPaperDollItem('face','face-young');failedPaperDollImages.add(selectedPaperDollItem('face').genderVariants[paperDollState.selectedGender]);renderPaperDoll()");
    assert.equal(g.elements.get('layer-body').style.maskImage,'');
    assert.ok(g.elements.get('layer-face').classList.contains('hidden'));
    assert.equal(g.run('JSON.stringify(PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair").map(i=>i.placementByGender))'),geometry);
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before);
});

test('all face-pack types select the correct gender, preserve saves and reset local masks', () => {
    const g=game();
    const approved=g.run('JSON.stringify({hair:PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"),colors:HAIR_COLORS})');
    for(const gender of ['male','female']) for(const kind of ['young','exhausted','elder']) {
        g.run(`setGender('${gender}');equipPaperDollItem('face','face-${kind}');equipPaperDollItem('hair','hair-none')`);
        assert.ok(g.elements.get('layer-face').getAttribute('src').includes(`${gender}_${kind}_head.png`));
        assert.equal(g.elements.get('layer-face').style.zIndex,'1');
        assert.ok(g.elements.get('layer-body').style.maskImage.includes(`${gender}_${kind}_body.png`));
        assert.ok(!g.elements.get('layer-body').style.maskImage.includes('linear-gradient'));
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.appearance.face'),`face-${kind}`);
        g.run(`failedPaperDollImages.add(selectedPaperDollItem('face').genderVariants['${gender}']);renderPaperDoll()`);
        assert.equal(g.elements.get('layer-body').style.maskImage,'');
        g.run('equipPaperDollItem("face",null)');
        assert.equal(g.elements.get('layer-body').style.maskImage,gender==='female'?'url("'+g.run('PAPER_DOLL_NATIVE_HEADS.female.bodyMaskByGender.female')+'")':'');
    }
    assert.equal(g.run('JSON.stringify({hair:PAPER_DOLL_ITEMS.filter(i=>i.slot==="hair"),colors:HAIR_COLORS})'),approved);
});

test('the paired face and female bob use real files and persist without altering loadouts', () => {
    const g=game();
    const before=g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})');
    for(const gender of ['male','female']) {
        g.run(`setGender('${gender}');equipPaperDollItem('face','face-alternative');equipPaperDollItem('hair','${gender==='female'?'hair-bob-bangs':'hair-shoulder-length'}');`);
        for(const slot of ['face','hair']) {
            const source=g.run(`selectedPaperDollItem('${slot}').genderVariants['${gender}']`);
            assert.ok(fs.existsSync(path.join(root,source.split('?')[0])),source);
            if(slot==='face')assert.match(source,new RegExp('/'+gender+'_alternative_head\\.png'));
            for(const prefix of ['', 'wardrobe-']) {
                assert.equal(g.elements.get(prefix+'layer-'+slot).getAttribute('src'),source);
                assert.equal(g.elements.get(prefix+'layer-'+slot).style.zIndex,slot==='face'?'1':'9');
            }
        }
        const mask=g.run(`selectedPaperDollItem('face').bodyMaskByGender['${gender}']`);
        assert.ok(fs.existsSync(path.join(root,mask.split('?')[0])));
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.appearance.face'),'face-alternative');
        assert.equal(restored.run('paperDollState.appearance.hair'),gender==='female'?'hair-bob-bangs':'hair-shoulder-length');
        assert.equal(restored.run('paperDollState.selectedGender'),gender);
    }
    assert.equal(g.run('PAPER_DOLL_ITEMS.find(i=>i.id==="hair-bob-bangs").genderVariants.male'),undefined);
    assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,patient:paperDollState.patientLoadout,combat:paperDollState.combatLoadout})'),before);
});


test('female bangs are hidden and rejected for men and old male saves migrate safely', () => {
    const old={schemaVersion:2,selectedGender:'male',appearance:{hair:'hair-bob-bangs',face:'face-young',hairColor:'black'},patientLoadout:{upperBody:'patient-tunic'},combatLoadout:{}};
    const g=game({palata404_paper_doll:JSON.stringify(old)});
    assert.equal(g.run('paperDollState.appearance.hair'),'hair-none');
    assert.equal(g.run('paperDollState.appearance.face'),'face-young');
    assert.equal(g.run('paperDollState.appearance.hairColor'),'black');
    g.run('selectWardrobeCategory("appearance");selectWardrobeSlot("hair")');
    assert.equal(g.run('wardrobeVisibleItems().some(i=>i.id==="hair-bob-bangs")'),false);
    assert.equal(g.run('equipPaperDollItem("hair","hair-bob-bangs")'),false);
    g.run('setGender("female");equipPaperDollItem("hair","hair-bob-bangs")');
    assert.equal(g.run('selectedPaperDollItem("hair").id'),'hair-bob-bangs');
    g.run('setGender("male")');
    assert.equal(g.run('paperDollState.appearance.hair'),'hair-none');
    assert.equal(game(Object.fromEntries(g.storage)).run('paperDollState.appearance.hair'),'hair-none');
});


test('male shoulder rear is local, shares pigment reference and disappears on switch', () => {
    const g=game();g.run('setGender("male");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-shoulder-length")');
    for(const prefix of ['', 'wardrobe-']) {
        const rear=g.elements.get(prefix+'layer-hair-rear');assert.ok(rear);assert.equal(rear.style.zIndex,'-1');
        assert.equal(rear.style.width,'100%');assert.equal(rear.style.top,'0%');
        assert.equal(g.elements.get(prefix+'layer-hair').style.zIndex,'9');
        assert.ok(rear.paperHairColorReference.includes('male_medium_shoulder_length.png'));
    }
    g.run('setGender("female")');assert.equal(g.elements.has('layer-hair-rear'),false);assert.ok(g.elements.get('layer-hair').getAttribute('src').includes('female_medium'));
    g.run('setGender("male");equipPaperDollItem("hair","hair-shoulder-length");equipPaperDollItem("hair","hair-messy")');
    assert.equal(g.elements.has('layer-hair-rear'),false);assert.ok(g.elements.get('layer-hair').getAttribute('src').includes('male_messy'));
});

test('crown smoothing is monotone in x and remains local above y=90', () => {
    const g=game();const cases=JSON.parse(g.run('JSON.stringify(PAPER_DOLL_CROWN_CONTOURS)'));
    for(const genders of Object.values(cases)) for(const points of Object.values(genders)) {
        const curve=JSON.parse(g.run('JSON.stringify(smoothPaperDollCrown('+JSON.stringify(points)+'))'));
        assert.ok(curve.length>points.length);let x=-Infinity;
        for(const p of curve){assert.ok(p[0]>=x);assert.ok(p[1]>=0&&p[1]<=90);x=p[0];}
        assert.deepEqual(curve[0],points[0]);assert.deepEqual(curve.at(-1),points.at(-1));
    }
});

test('rear and front recoloring use the same lighting median without changing alpha', () => {
    const g=game();const result=JSON.parse(g.run('JSON.stringify((()=>{const a=[60,40,30,255,120,80,60,255],b=[60,40,30,255];const m=hairLuminanceMedian(a);recolorHairPixels(a,"#C8C3BA",m);recolorHairPixels(b,"#C8C3BA",m);return {a,b}})())'));
    assert.deepEqual(result.a.slice(0,4),result.b);assert.equal(result.a[3],255);assert.equal(result.a[7],255);
});

test('all historical and malformed save shapes retain valid progression and boot safely', () => {
    for (const malformed of ['null','[]','true','17','"text"','{broken','{"schemaVersion":999}']) {
        const savedStats = { ...JSON.parse(JSON.stringify({silver:1234,level:7,exp:42,nextLvlExp:840,baseDamage:31,baseArmor:6,gymRounds:2})) };
        const g=game({palata404_stats:JSON.stringify(savedStats),palata404_inventory:malformed,
            palata404_equipped:malformed,palata404_gym:malformed,palata404_paper_doll:malformed,
            palata404_friends:malformed,palata404_progress:malformed});
        assert.equal(g.run('stats.silver'),1234);
        assert.equal(g.run('stats.level'),7);
        assert.equal(g.run('stats.exp'),42);
        assert.equal(g.run('stats.baseDamage'),31);
        assert.equal(g.run('stats.baseArmor'),6);
        const again=game(Object.fromEntries(g.storage));
        assert.equal(again.run('stats.silver'),1234);
        assert.equal(again.run('stats.level'),7);
        assert.equal(again.run('stats.baseDamage'),31);
    }
});

test('boss actions reject inherited property names without starting or corrupting combat', () => {
    const g=game();const before=g.run('JSON.stringify({stats,inventory,gameProgress})');
    for (const name of ['constructor','toString','__proto__','missing']) {
        g.run(`startBossFight(${JSON.stringify(name)});openBossDossier(${JSON.stringify(name)})`);
        assert.equal(g.run('isBattleActive'),false);
        assert.equal(g.run('JSON.stringify({stats,inventory,gameProgress})'),before);
    }
});

test('repeated multipart hair renders preserve the current front request and source', () => {
    const g=game();g.run('setGender("male");equipPaperDollItem("hair","hair-shoulder-length")');
    const hair=g.elements.get('wardrobe-layer-hair');let removals=0;
    const remove=hair.removeAttribute.bind(hair);
    hair.removeAttribute=name=>{if(name==='src')removals++;remove(name);};
    const request=hair.paperHairRequest;
    g.run('renderPaperDoll();renderPaperDoll();updateUI()');
    assert.equal(removals,0);
    assert.equal(hair.paperHairRequest,request);
    assert.ok(hair.getAttribute('src').includes('male_medium_shoulder_length'));
});

test('an evicted reference image failure cannot delete a newer retry promise', async () => {
    const g=game();g.run('globalThis.images=[];globalThis.Image=class {constructor(){images.push(this)}}');
    const failed=g.run('hairReferenceMedian("retry.png")');
    for(let i=0;i<25;i++)g.run(`hairReferenceMedian("filler-${i}.png")`);
    const retry=g.run('hairReferenceMedian("retry.png")');
    g.run('images[0].onerror()');await assert.rejects(failed);
    await Promise.resolve();
    assert.equal(g.run('hairReferenceMedians.get("retry.png")'),retry);
});

test('unchanged crown contours are reused without recomputation or a visual change', () => {
    const g=game();g.run('setGender("male");equipPaperDollItem("face","face-alternative");equipPaperDollItem("hair","hair-messy")');
    const clip=g.elements.get('wardrobe-layer-face').style.clipPath;
    g.run('globalThis.crownCalls=0;globalThis.originalCrown=smoothPaperDollCrown;smoothPaperDollCrown=(...args)=>{crownCalls++;return originalCrown(...args)};renderPaperDoll();updateUI()');
    assert.equal(g.run('crownCalls'),0);
    assert.equal(g.elements.get('wardrobe-layer-face').style.clipPath,clip);
    assert.ok(clip.startsWith('polygon('));
});

test('new male-only portraits survive saves and reject unsupported female states', () => {
    for(const id of ['face-male-goth-pierced','face-male-freckled','face-male-blue-eyes']) {
        const g=game();
        const before=g.run('JSON.stringify({stats,inventory,equippedGear})');
        g.run('setGender("male");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("hair","hair-messy");setHairColor("white")');
        assert.equal(g.run(`equipPaperDollItem('face','${id}')`),true);
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.appearance.face'),id);
        assert.equal(restored.run('paperDollState.patientLoadout.upperBody'),'patient-tunic');
        assert.equal(restored.run('paperDollState.combatLoadout.upperBody'),null);
        assert.equal(restored.run('JSON.stringify({stats,inventory,equippedGear})'),before);
        restored.run('setGender("female")');
        assert.equal(restored.run('paperDollState.appearance.face'),null);
        assert.equal(restored.run(`equipPaperDollItem('face','${id}')`),false);
    }
});

test('legacy shared face IDs and save schema remain valid after male pack replacement', () => {
    const g=game();
    for(const id of ['face-asian','face-young','face-exhausted','face-elder','face-alternative']) {
        g.run(`setGender('male');equipPaperDollItem('face','${id}');saveGameProgress()`);
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.schemaVersion'),2);
        assert.equal(restored.run('paperDollState.appearance.face'),id);
        restored.run('setGender("female")');
        assert.equal(restored.run('paperDollState.appearance.face'),id);
    }
});

test('new female portraits retain separate loadouts, colour and appearance across reload', () => {
    const ids=game().run('PAPER_DOLL_ITEMS.filter(i=>i.id.startsWith("face-female-new-")).map(i=>i.id)');
    assert.equal(ids.length,7);
    for(const id of ids) {
        const g=game();const protectedState=g.run('JSON.stringify({stats,inventory,equippedGear})');
        g.run('setGender("female");setPaperDollView("patient");equipPaperDollItem("upperBody","patient-tunic");setPaperDollView("combat");equipPaperDollItem("upperBody",null);equipPaperDollItem("hair","hair-bob-bangs");setHairColor("white")');
        assert.equal(g.run(`equipPaperDollItem('face','${id}')`),true);
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('paperDollState.appearance.face'),id);
        assert.equal(restored.run('paperDollState.appearance.hairColor'),'white');
        assert.equal(restored.run('paperDollState.patientLoadout.upperBody'),'patient-tunic');
        assert.equal(restored.run('paperDollState.combatLoadout.upperBody'),null);
        assert.equal(restored.run('JSON.stringify({stats,inventory,equippedGear})'),protectedState);
        restored.run('setGender("male")');assert.equal(restored.run('paperDollState.appearance.face'),null);
        assert.equal(restored.run(`equipPaperDollItem('face','${id}')`),false);
    }
});

test('female catalog retains seven approved additions and excludes the removed mature face', () => {
    const g=game();
    assert.equal(g.run('PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"female")).length'),15);
    assert.equal(g.run('PAPER_DOLL_ITEMS.filter(i=>i.slot==="face"&&paperDollItemSupportsGender(i,"male")).length'),15);
    for(const id of ['face-asian','face-young','face-exhausted','face-elder','face-alternative','face-ginger-soft','face-goth-septum','face-goth-black-lips']) {
        g.run(`setGender('female');equipPaperDollItem('face','${id}')`);
        assert.equal(g.run('paperDollState.appearance.face'),id);
    }
    g.run('equipPaperDollItem("face",null)');assert.equal(g.run('paperDollState.appearance.face'),null);
});

test('female native head normalization is render-only and never becomes a saved item', () => {
    const g=game();g.run('setGender("female");equipPaperDollItem("face",null)');
    const protectedState=g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
    assert.equal(g.run('paperDollState.appearance.face'),null);
    assert.equal(g.run('selectedPaperDollItem("face")'),undefined);
    assert.equal(g.run('PAPER_DOLL_ITEMS.some(i=>i.id==="native-female-head")'),false);
    for(const prefix of ['', 'wardrobe-']) {
        assert.equal(g.elements.get(prefix+'layer-face').getAttribute('src'),g.run('PAPER_DOLL_NATIVE_HEADS.female.genderVariants.female'));
        assert.equal(g.elements.get(prefix+'layer-face').style.zIndex,'1');
    }
    const restored=game(Object.fromEntries(g.storage));assert.equal(restored.run('paperDollState.appearance.face'),null);
    restored.run('setGender("male")');assert.equal(restored.elements.get('layer-face').getAttribute('src'),null);
    assert.equal(restored.elements.get('layer-body').style.maskImage,'');
    assert.equal(restored.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),protectedState);
});


test('removed female hair and mature face stay unavailable and old saves fall back safely', () => {
    for(const id of ['hair-trial-braided-curls','hair-f5-long-waves','hair-f5-high-ponytail']) {
        const g=game();g.run('setGender("female")');
        assert.equal(g.run(`equipPaperDollItem('hair','${id}')`),false);
        g.run(`paperDollState.appearance.hair='${id}';saveGameProgress()`);
        const restored=game(Object.fromEntries(g.storage));
        assert.equal(restored.run('selectedPaperDollItem("hair").id'),'hair-none');
        assert.equal(restored.elements.get('layer-hair').getAttribute('src'),null);
    }
    const g=game();g.run('setGender("female")');
    assert.equal(g.run('equipPaperDollItem("face","face-female-new-mature")'),false);
});

for (const key of ['pixie','jaw-bob','braided-updo']) {
    test(`new female ${key}: catalog, shared appearance, reload and individual removal`, () => {
        const g=game(),id='hair-f5-'+key;
        const before=g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})');
        assert.equal(g.run(`equipPaperDollItem('hair','${id}')`),false);
        g.run('setGender("female");equipPaperDollItem("face","face-young")');
        assert.equal(g.run(`equipPaperDollItem('hair','${id}')`),true);
        assert.equal(g.run('JSON.stringify(selectedPaperDollItem("hair").placementByGender.female)'),JSON.stringify({x:0,y:0,width:941,height:1672}));
        assert.equal(g.run('paperDollState.appearance.hairColor'),'original');
        assert.equal(g.elements.get('layer-hair').style.zIndex,'9');
        g.run('setHairColor("black");setPaperDollView("patient");setPaperDollView("combat")');
        const reload=game(Object.fromEntries(g.storage));
        assert.equal(reload.run('paperDollState.appearance.hair'),id);
        assert.equal(reload.run('paperDollState.appearance.hairColor'),'black');
        assert.equal(reload.run('paperDollState.appearance.face'),'face-young');
        assert.equal(g.run('JSON.stringify({stats,inventory,equippedGear,gameProgress})'),before);
        g.run(`PAPER_DOLL_ITEMS.splice(PAPER_DOLL_ITEMS.findIndex(i=>i.id==='${id}'),1);renderPaperDoll()`);
        assert.equal(g.run('selectedPaperDollItem("hair").id'),'hair-none');
        assert.equal(g.elements.get('layer-hair').getAttribute('src'),null);
        assert.equal(g.run('PAPER_DOLL_ITEMS.filter(i=>i.id.startsWith("hair-f5-")).length'),2);
    });
}
