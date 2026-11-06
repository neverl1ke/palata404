// Instance-based weapon data and one combat calculator. No avatar art is changed.
const WEAPON_RARITIES = Object.freeze({
    common: { label: 'ОБЫЧНОЕ', color: '#8C8478' },
    improved: { label: 'УЛУЧШЕННОЕ', color: '#A77B49' },
    rare: { label: 'РЕДКОЕ', color: '#9F5263' },
    experimental: { label: 'ЭКСПЕРИМЕНТАЛЬНОЕ', color: '#B84A43', mark: 'ОСОБЫЙ ОБРАЗЕЦ' }
});
const WEAPON_UPGRADE_COSTS = Object.freeze([
    { silver: 150, equipmentParts: 0 }, { silver: 300, equipmentParts: 2 },
    { silver: 500, equipmentParts: 4 }, { silver: 800, equipmentParts: 6 },
    { silver: 1200, equipmentParts: 10 }
]);
const WEAPON_ABSOLUTE_COST = Object.freeze({ silver: 2500, equipmentParts: 15, experimentalComponents: 1 });
const WEAPON_MODULES = Object.freeze({
    mechanism: [
        { id: 'standard', name: 'Стандартный', cost: {} },
        { id: 'accelerated', name: 'Ускоренный', cooldown: -.2, cost: { silver: 200, equipmentParts: 2 } },
        { id: 'quick-reload', name: 'Быстрая перезарядка', reload: -.5, cost: { silver: 200, equipmentParts: 2 } }
    ],
    aiming: [
        { id: 'standard', name: 'Стандартное', cost: {} },
        { id: 'accuracy', name: 'Улучшенная точность', miss: -.05, cost: { silver: 300, equipmentParts: 3 } },
        { id: 'critical', name: 'Критическое наведение', critical: .07, cost: { silver: 300, equipmentParts: 3 } }
    ],
    magazine: [
        { id: 'standard', name: 'Стандартный', cost: {} },
        { id: 'extended', name: 'Увеличенный', capacity: 3, cost: { silver: 300, equipmentParts: 3 } }
    ]
});
const WEAPON_SLOT_LEVELS = Object.freeze({ mechanism: 0, aiming: 2, magazine: 4 });
const WEAPON_MODELS = Object.freeze({
    'gear-aks': { name: 'Штурмовий АКС-74У', damage: [35,37,39,41,43,45], cooldown: 4, miss: .05, critical: .05, criticalMultiplier: 1.5, capacity: 10, reload: 2.5, minCooldown: .25, minReload: .25, modules: WEAPON_MODULES, rarity: {} },
    'gear-pm': { name: 'ПМ (Пістолет Макарова)', damage: [18,19,20,21,22,23], cooldown: 4, miss: .05, critical: .05, criticalMultiplier: 1.5, capacity: 8, reload: 2.5, minCooldown: .25, minReload: .25, modules: WEAPON_MODULES, rarity: {} },
    'gear-knife': { name: 'Іржавий ніж', damage: [8,9,10,11,12,13], cooldown: 4, miss: 0, critical: .05, criticalMultiplier: 1.5, capacity: 0, reload: 0, minCooldown: .25, minReload: 0, modules: { mechanism: [WEAPON_MODULES.mechanism[0]], aiming: [WEAPON_MODULES.aiming[0]], magazine: [WEAPON_MODULES.magazine[0]] }, rarity: {} }
});
const WEAPON_RAID_MATERIALS = Object.freeze({ nurse: { equipmentParts: 1, experimentalComponents: 0 }, doctor: { equipmentParts: 3, experimentalComponents: 1 } });
const WEAPON_RESOURCE_NAMES = Object.freeze({ silver: 'Серебро', equipmentParts: 'Детали', experimentalComponents: 'Эксп. компонент' });
const WEAPON_TRANSACTION_KEY = 'palata404_weapon_transaction';
function weaponModelId(item) { return item?.modelId && WEAPON_MODELS[item.modelId] ? item.modelId : Object.keys(WEAPON_MODELS).find(id => WEAPON_MODELS[id].name === item?.name) || null; }
function normalizeWeaponInstance(item, index = 0) {
    const modelId = weaponModelId(item);
    if (!modelId) return item;
    const model = WEAPON_MODELS[modelId];
    const upgradeLevel = Number.isInteger(item.upgradeLevel) ? Math.min(5, Math.max(0, item.upgradeLevel)) : 0;
    const modules = {};
    for (const [slot, options] of Object.entries(model.modules)) {
        modules[slot] = upgradeLevel >= WEAPON_SLOT_LEVELS[slot] && options.some(m => m.id === item.modules?.[slot]) ? item.modules[slot] : 'standard';
    }
    const instanceId = typeof item.instanceId === 'string' && /^[\w-]{1,100}$/.test(item.instanceId) ? item.instanceId : `legacy-${modelId}-${index}`;
    return { ...item, modelId, instanceId, rarity: Object.hasOwn(WEAPON_RARITIES, item.rarity) ? item.rarity : 'common', upgradeLevel, absolute: upgradeLevel === 5 && item.absolute === true, modules, count: 1 };
}
function initializeWeaponCatalog() {
    // Seed the requested four examples once, only for owners of the original AKS.
    const aks = inventory.find(i => i.category === 'weapon' && weaponModelId(i) === 'gear-aks');
    if (!stats.weaponCatalogVersion) {
        if (aks) for (const [rarity, level, absolute] of [['improved',2,false],['rare',5,false],['experimental',5,true]]) {
            if (!inventory.some(i => i.instanceId === `demo-aks-${rarity}`)) inventory.push(normalizeWeaponInstance({ ...aks, instanceId: `demo-aks-${rarity}`, rarity, upgradeLevel: level, absolute, modules: {}, paperDollId: `weapon-demo-aks-${rarity}` }));
        }
        stats.weaponCatalogVersion = 1;
    }
    const templates = Object.fromEntries(Object.keys(WEAPON_MODELS).map(id => [id, PAPER_DOLL_ITEMS.find(i => i.id === id)]));
    const usedIds = new Set();
    for (const item of inventory.filter(i => i.category === 'weapon' && weaponModelId(i))) {
        const template = templates[item.modelId];
        if (!template) continue;
        let id = item.paperDollId || (!usedIds.has(item.modelId) ? item.modelId : `weapon-${item.instanceId}`);
        if (!/^[\w-]+$/.test(id) || usedIds.has(id)) id = `weapon-${item.instanceId}`;
        usedIds.add(id); item.paperDollId = id;
        const entry = { ...template, id, modelId: item.modelId, inventoryInstanceId: item.instanceId };
        const existing = PAPER_DOLL_ITEMS.findIndex(i => i.id === id);
        if (existing >= 0) PAPER_DOLL_ITEMS[existing] = entry; else PAPER_DOLL_ITEMS.push(entry);
    }
}
function weaponInventoryItem(value) {
    const id = typeof value === 'string' ? value : value?.inventoryInstanceId || value?.instanceId;
    if (typeof id !== 'string' || !id) return undefined;
    return inventory.find(i => i.category === 'weapon' && i.count > 0 && (i.instanceId === id || i.paperDollId === id));
}
function weaponItemLabel(item) { return `${item.name} +${item.upgradeLevel || 0}${item.absolute ? ' ★' : ''}`; }
function calculateWeaponStats(item, bonuses = {}) {
    const model = WEAPON_MODELS[weaponModelId(item)];
    if (!model) return { weaponDamage: Math.max(0, item?.damageBonus || 0), damage: Math.max(0, item?.damageBonus || 0) + Math.max(0, bonuses.damage || 0), cooldown: 4, miss: 0, critical: 0, criticalMultiplier: 1.5, capacity: 0, reload: 0 };
    const normalized = normalizeWeaponInstance(item);
    const rarity = model.rarity[normalized.rarity] || {};
    const values = { cooldown: model.cooldown, miss: model.miss, critical: model.critical, criticalMultiplier: model.criticalMultiplier, capacity: model.capacity, reload: model.reload };
    const weaponDamage = Math.round((rarity.damage?.[normalized.upgradeLevel] ?? model.damage[normalized.upgradeLevel]) * (normalized.absolute ? 1.2 : 1));
    for (const [slot, options] of Object.entries(model.modules)) {
        const module = options.find(m => m.id === normalized.modules[slot]);
        for (const key of Object.keys(values)) values[key] += Number(module?.[key] || 0);
    }
    for (const key of Object.keys(values)) values[key] += Number(rarity[key] || 0) + Number(bonuses[key] || 0);
    const clamp = (n, min, max) => Math.round(Math.min(max, Math.max(min, Number.isFinite(n) ? n : min)) * 1000000) / 1000000;
    return { weaponDamage, damage: Math.max(0, weaponDamage + (bonuses.damage || 0)), cooldown: clamp(values.cooldown, model.minCooldown, 60), miss: clamp(values.miss, 0, 1), critical: clamp(values.critical, 0, 1), criticalMultiplier: clamp(values.criticalMultiplier, 1, 10), capacity: model.capacity ? Math.floor(clamp(values.capacity, 1, 100)) : 0, reload: model.capacity ? clamp(values.reload, model.minReload, 60) : 0 };
}
function getCombatWeaponStats() { return calculateWeaponStats(getEquippedItem('weapon'), { damage: stats.baseDamage }); }
function weaponUpgradeOffer(item) {
    if (!item || !WEAPON_MODELS[weaponModelId(item)] || item.absolute) return null;
    return item.upgradeLevel < 5 ? { kind: 'upgrade', label: `Улучшить до +${item.upgradeLevel + 1}`, cost: WEAPON_MODELS[item.modelId]?.upgradeCosts?.[item.upgradeLevel] || WEAPON_UPGRADE_COSTS[item.upgradeLevel] } : { kind: 'absolute', label: 'АБСОЛЮТ ★', cost: WEAPON_MODELS[item.modelId]?.absoluteCost || WEAPON_ABSOLUTE_COST };
}
function canAffordWeaponCost(cost) { return Object.entries(cost).every(([key,n]) => Number.isSafeInteger(stats[key]) && stats[key] >= n); }
function weaponCostText(cost) { return Object.entries(cost).filter(([,n]) => n > 0).map(([key,n]) => `${WEAPON_RESOURCE_NAMES[key]}: ${n}`).join(' · ') || 'Бесплатно'; }
function readWeaponTransaction() { try { const t = JSON.parse(safeStorageGet(WEAPON_TRANSACTION_KEY)); return t?.stats && Array.isArray(t.inventory) ? t : null; } catch { return null; } }
function weaponSaveSnapshot() { return { stats, inventory, equippedGear, paperDoll: wardrobeSession?.savedState || paperDollState }; }
function prepareWeaponSave() { return !readWeaponTransaction() || safeStorageSet(WEAPON_TRANSACTION_KEY, JSON.stringify(weaponSaveSnapshot())); }
function finishWeaponSave(saved) { if (saved && readWeaponTransaction()) safeStorageRemove(WEAPON_TRANSACTION_KEY); return saved; }
function weaponTransaction(change) {
    if (isBattleActive) return { ok: false, error: 'Изменения доступны после боя.' };
    const before = { stats: { ...stats }, inventory: JSON.parse(JSON.stringify(inventory)) };
    const result = change();
    if (!result.ok) return result;
    recalculateEquipmentStats();
    if (!safeStorageSet(WEAPON_TRANSACTION_KEY, JSON.stringify(weaponSaveSnapshot()))) {
        stats = before.stats; inventory = before.inventory; recalculateEquipmentStats();
        return { ok: false, error: 'Не удалось сохранить. Ресурсы не списаны.' };
    }
    const persisted = saveGameProgress();
    updateUI(); renderWardrobe();
    return { ...result, pendingSave: !persisted };
}
function upgradeWeaponInstance(id) {
    return weaponTransaction(() => {
        const item = weaponInventoryItem(id), offer = weaponUpgradeOffer(item);
        if (!offer) return { ok: false, error: 'Достигнут предел улучшений.' };
        if (!canAffordWeaponCost(offer.cost)) return { ok: false, error: 'Недостаточно ресурсов.' };
        for (const [key, n] of Object.entries(offer.cost)) stats[key] -= n;
        if (offer.kind === 'absolute') item.absolute = true; else item.upgradeLevel++;
        return { ok: true };
    });
}
function weaponModuleOwned(slot, id) { return id === 'standard' || inventory.some(i => i.category === 'weapon-module' && i.moduleKey === `${slot}:${id}` && i.count > 0); }
function setWeaponModule(id, slot, moduleId) {
    return weaponTransaction(() => {
        const item = weaponInventoryItem(id), model = WEAPON_MODELS[weaponModelId(item)];
        const module = model?.modules[slot]?.find(m => m.id === moduleId);
        if (!item || !module || item.upgradeLevel < WEAPON_SLOT_LEVELS[slot]) return { ok: false, error: 'Слот заблокирован или модуль несовместим.' };
        if (!weaponModuleOwned(slot, moduleId)) {
            if (!canAffordWeaponCost(module.cost)) return { ok: false, error: 'Недостаточно ресурсов.' };
            for (const [key, n] of Object.entries(module.cost)) stats[key] -= n;
            inventory.push({ name: module.name, category: 'weapon-module', moduleKey: `${slot}:${moduleId}`, icon: 'gear', count: 1, desc: 'Разблокирован для совместимого оружия.' });
        }
        item.modules[slot] = moduleId;
        return { ok: true };
    });
}
