const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const root = path.join(__dirname, '..');
const expected = {
    upperBody: 'patient-pajama-top',
    pants: 'patient-pajama-pants',
    footwear: 'patient-pajama-slippers'
};

function wardrobe() {
    const storage = new Map();
    const context = vm.createContext({
        inventory: [], equippedGear: {}, wardrobeSession: {},
        normalizeHairColor: value => value || 'original',
        renderWardrobe() {}, window: {},
        document: { getElementById: () => null },
        readWeaponTransaction: () => null,
        safeStorageGet: key => storage.get(key) ?? null,
        safeStorageSet: (key, value) => { storage.set(key, value); return true; }
    });
    const run = code => vm.runInContext(code, context);
    const load = file => vm.runInContext(fs.readFileSync(path.join(root, file), 'utf8'), context, { filename: file });
    load('paper-doll-data.js');
    const original = run('JSON.stringify(PAPER_DOLL_ITEMS)');
    const originalOrder = run('PAPER_DOLL_LAYER_ORDER.join()');
    load('pajama-data.js');
    load('paper-doll.js');
    run('var paperDollState = normalizePaperDollState(null);');
    return { run, storage, original, originalOrder };
}

test('approved pajamas append three cosmetic items without replacing existing items or slots', () => {
    const g = wardrobe();
    const all = JSON.parse(g.run('JSON.stringify(PAPER_DOLL_ITEMS)'));
    const original = JSON.parse(g.original);
    assert.deepEqual(all.slice(0, original.length), original);
    assert.equal(g.run('PAPER_DOLL_LAYER_ORDER.join()'), g.originalOrder);
    const added = all.slice(original.length);
    assert.deepEqual(added.map(item => item.id), Object.values(expected));
    assert.deepEqual(added.map(item => item.slot), Object.keys(expected));
    for (const item of added) {
        assert.equal(item.availableByDefault, true);
        assert.equal(item.poseAwareClothing, true);
        assert.equal(item.artApproval, 'pajamas-20261111');
        assert.deepEqual(item.genders, ['male', 'female']);
        assert.deepEqual(item.placement, { x: 0, y: 0, width: 941, height: 1672 });
        assert.equal(Object.hasOwn(item, 'poseClothingMaskByGender'), item.slot === 'footwear');
        assert.equal(Object.hasOwn(item, 'poseClothingForegroundMaskByGender'), item.slot === 'upperBody');
        for (const key of ['inventoryName', 'inventoryCategory', 'starterForPatient', 'damage', 'armorBonus', 'criticalBonus']) {
            assert.equal(Object.hasOwn(item, key), false, item.id + ' unexpectedly changes ' + key);
        }
        for (const gender of ['male', 'female']) {
            const poses = item.poseClothingByGender[gender];
            assert.deepEqual(Object.keys(poses), ['idle', 'melee', 'rifle']);
            assert.equal(item.genderVariants[gender], poses.idle);
            assert.ok(item.thumbnailByGender[gender].includes('/' + gender + '/thumb-'));
            assert.ok(Object.values(poses).every(source => source.startsWith('assets/wardrobe/clothing/patient/pajamas/' + gender + '/')));
            if (item.slot !== 'upperBody') assert.equal(new Set(Object.values(poses)).size, 1);
            else assert.equal(new Set(Object.values(poses)).size, 3);
            if (item.slot === 'footwear') {
                const masks = item.poseClothingMaskByGender[gender];
                assert.deepEqual(Object.keys(masks), ['idle', 'melee', 'rifle']);
                assert.equal(new Set(Object.values(masks)).size, 1);
                assert.ok(Object.values(masks).every(source => source.split('?')[0] ===
                    'assets/wardrobe/clothing/patient/pajamas/' + gender + '/mask-footwear.webp'));
            }
            if (item.slot === 'upperBody') {
                const foreground = item.poseClothingForegroundMaskByGender[gender];
                assert.deepEqual(Object.keys(foreground), ['rifle']);
                assert.equal(foreground.rifle.split('?')[0],
                    'assets/wardrobe/clothing/patient/pajamas/' + gender + '/foreground-hands-rifle.webp');
            }
        }
    }
});

test('new availability preserves the existing patient starter and saved empty clothing slots', () => {
    const g = wardrobe();
    const starter = JSON.parse(g.run('JSON.stringify(loadPaperDollState({}))'));
    assert.equal(starter.patientLoadout.upperBody, 'patient-tunic');
    assert.equal(starter.patientLoadout.pants, null);
    assert.equal(starter.patientLoadout.footwear, null);
    g.run('paperDollState = normalizePaperDollState(null); savePaperDollState();');
    const restored = JSON.parse(g.run('JSON.stringify(loadPaperDollState({}))'));
    for (const loadout of ['patientLoadout', 'combatLoadout']) {
        for (const slot of Object.keys(expected)) assert.equal(restored[loadout][slot], null);
    }
});

test('each piece equips and removes independently in both genders and survives both saved loadouts', () => {
    for (const gender of ['male', 'female']) {
        const g = wardrobe();
        g.run('paperDollState.selectedGender = ' + JSON.stringify(gender));
        for (const [slot, id] of Object.entries(expected)) {
            assert.equal(g.run(`equipPaperDollItem(${JSON.stringify(slot)}, ${JSON.stringify(id)})`), true);
            assert.equal(g.run(`selectedPaperDollItem(${JSON.stringify(slot)}).id`), id);
        }
        assert.equal(g.run('equipPaperDollItem("pants", null)'), true);
        assert.equal(g.run('activePaperDollLoadout().pants'), null);
        assert.equal(g.run('selectedPaperDollItem("upperBody").id'), expected.upperBody);
        assert.equal(g.run('selectedPaperDollItem("footwear").id'), expected.footwear);
        assert.equal(g.run('setPaperDollView("combat")'), true);
        for (const [slot, id] of Object.entries(expected)) {
            assert.equal(g.run(`equipPaperDollItem(${JSON.stringify(slot)}, ${JSON.stringify(id)})`), true);
        }
        assert.equal(g.run('paperDollState.patientLoadout.pants'), null);
        const before = g.run('JSON.stringify(paperDollState)');
        assert.equal(g.run('savePaperDollState()'), true);
        assert.equal(g.run('JSON.stringify(loadPaperDollState({}))'), before);
        assert.equal(g.run('PAPER_DOLL_STORAGE_KEY'), 'palata404_paper_doll');
        assert.equal(g.storage.size, 1);
    }
});
