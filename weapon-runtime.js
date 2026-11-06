// Manual attack state belongs to one raid and never schedules a player attack.
let battleWeaponProfile = null;
let battleWeaponAmmo = 0;
let weaponReloadEndsAt = 0;
let weaponReloadTimer = null;
function getBattleAttackProfile() { return battleWeaponProfile || getCombatWeaponStats(); }
function initializeWeaponBattle() {
    stopWeaponBattleTimers();
    battleWeaponProfile = { ...getCombatWeaponStats() };
    battleWeaponAmmo = battleWeaponProfile.capacity;
    renderWeaponBattleState();
}
function stopWeaponBattleTimers() {
    clearTimeout(weaponReloadTimer); weaponReloadTimer = null; weaponReloadEndsAt = 0; battleWeaponProfile = null;
}
function startWeaponReload() {
    const profile = getBattleAttackProfile();
    if (!isBattleActive || !profile.capacity || weaponReloadEndsAt || battleWeaponAmmo >= profile.capacity) return false;
    weaponReloadEndsAt = Date.now() + profile.reload * 1000;
    const generation = battleGeneration;
    weaponReloadTimer = setTimeout(() => {
        if (generation !== battleGeneration || !isBattleActive) return;
        battleWeaponAmmo = profile.capacity; weaponReloadEndsAt = 0; weaponReloadTimer = null;
        renderWeaponBattleState();
    }, profile.reload * 1000);
    renderWeaponBattleState();
    return true;
}
function renderWeaponBattleState() {
    const panel = document.getElementById('weapon-battle-state');
    if (!panel) return;
    const profile = getBattleAttackProfile();
    const reloading = Date.now() < weaponReloadEndsAt;
    panel.innerHTML = `<span>${profile.capacity ? reloading ? 'Перезарядка…' : `Магазин: ${battleWeaponAmmo}/${profile.capacity}` : 'Ближний бой'} · КД ${profile.cooldown.toFixed(1)} с</span><button type="button" onclick="event.stopPropagation();startWeaponReload()"${!profile.capacity || reloading || battleWeaponAmmo >= profile.capacity ? ' disabled' : ''}>Перезарядить</button>`;
}
let wardrobeSession = null;
const wardrobeHiddenSlots = new Set();
function beginWardrobeSession() {
    if (wardrobeSession) return;
    wardrobeSession = { savedState: JSON.parse(JSON.stringify(paperDollState)) };
    wardrobeHiddenSlots.clear();
}
function wardrobeHasChanges() { return !!wardrobeSession && JSON.stringify(wardrobeSession.savedState) !== JSON.stringify(paperDollState); }
function discardWardrobeSession() {
    if (!wardrobeSession) return;
    paperDollState = wardrobeSession.savedState; wardrobeSession = null; wardrobeHiddenSlots.clear();
    syncLegacyPaperDollSelection(); updateCharacterLayers(); renderWardrobe();
}
function applyWardrobeSession() {
    if (!wardrobeSession) return true;
    if (isBattleActive) { showCustomToast('Примените комплект после боя.'); return false; }
    const original = wardrobeSession, beforeGear = { ...equippedGear }, beforeStats = { ...stats };
    wardrobeSession = null; wardrobeHiddenSlots.clear();
    syncLegacyPaperDollSelection(); syncCombatEquipmentFromPaperDoll(); recalculateEquipmentStats();
    if (!safeStorageSet(WEAPON_TRANSACTION_KEY, JSON.stringify(weaponSaveSnapshot()))) {
        equippedGear = beforeGear; stats = beforeStats; wardrobeSession = original; paperDollSaveFailed = true;
        renderWardrobe(); return false;
    }
    paperDollSaveFailed = !saveGameProgress();
    updateUI(); renderWardrobe(); return true;
}
function syncCombatEquipmentFromPaperDoll() {
    if (typeof paperDollState === 'undefined' || wardrobeSession) return;
    for (const category of ['weapon','helmet','armor']) {
        const slot = category === 'helmet' ? 'headwear' : category;
        const visual = PAPER_DOLL_ITEMS.find(i => i.id === paperDollState.combatLoadout[slot]);
        if (category === 'weapon') {
            const instance = weaponInventoryItem(visual);
            equippedGear.weapon = instance?.instanceId || null;
        } else equippedGear[category] = visual?.inventoryName || null;
    }
}
function syncInventoryEquipmentToPaperDoll(category) {
    if (typeof paperDollState === 'undefined') return;
    const item = getEquippedItem(category);
    const descriptor = PAPER_DOLL_ITEMS.find(i => category === 'weapon' ? i.inventoryInstanceId === item?.instanceId : i.inventoryCategory === category && i.inventoryName === item?.name);
    const slot = category === 'helmet' ? 'headwear' : category;
    paperDollState.combatLoadout[slot] = descriptor?.id || null;
    if (wardrobeSession) wardrobeSession.savedState.combatLoadout[slot] = descriptor?.id || null;
    updateCharacterLayers();
}
function openWardrobeCloseDialog() {
    showWeaponDialog('Сохранить изменения?', '<p>Вы примерили другой комплект. Применить его или вернуться к сохранённому?</p>', [
        ['Применить', () => { if (applyWardrobeSession()) { hideWeaponDialog(); closeCustomization(); } }],
        ['Отменить изменения', () => { hideWeaponDialog(); discardWardrobeSession(); closeCustomization(); }],
        ['Продолжить примерку', hideWeaponDialog]
    ]);
}
function showWeaponDialog(title, body, actions = []) {
    const dialog = document.getElementById('weapon-dialog');
    if (!dialog) return;
    dialog.innerHTML = `<section role="dialog" aria-modal="true" aria-labelledby="weapon-dialog-title"><h3 id="weapon-dialog-title">${escapeHTML(title)}</h3>${body}<div class="weapon-dialog-actions"></div></section>`;
    const footer = dialog.querySelector('.weapon-dialog-actions');
    actions.forEach(([label, action, disabled = false]) => { const b = document.createElement('button'); b.type='button'; b.disabled=disabled; b.textContent=label; b.addEventListener('click',action); footer.appendChild(b); });
    dialog.classList.remove('hidden');
    dialog.querySelector('button')?.focus();
}
function hideWeaponDialog() { document.getElementById('weapon-dialog')?.classList.add('hidden'); }
function showWeaponActionResult(result) {
    if (!result.ok) { showCustomToast(result.error); return false; }
    hideWeaponDialog();
    showCustomToast(result.pendingSave ? 'Изменение записано в журнал. Повторяем сохранение.' : 'Изменение сохранено.');
    return true;
}
function openWeaponUpgrade(id) {
    const item = weaponInventoryItem(id), offer = weaponUpgradeOffer(item);
    if (!offer) return;
    showWeaponDialog(offer.label, `<p>${escapeHTML(weaponItemLabel(item))}</p><p>${escapeHTML(weaponCostText(offer.cost))}</p><p>${canAffordWeaponCost(offer.cost) ? 'Ресурсов достаточно.' : 'Недостаточно ресурсов.'}</p><p>Улучшение гарантировано. Изменение сохраняется сразу и не отменяется вместе с примеркой.</p>`, [
        ['Подтвердить', () => showWeaponActionResult(upgradeWeaponInstance(id)), !canAffordWeaponCost(offer.cost)], ['Назад', hideWeaponDialog]
    ]);
}
function openWeaponModules(id) {
    const item = weaponInventoryItem(id), model = WEAPON_MODELS[weaponModelId(item)];
    if (!item || !model) return;
    const names = { mechanism:'Механизм', aiming:'Наведение', magazine:'Магазин' };
    const body = `<p>Приобретённые модули можно переставлять бесплатно. Изменения сохраняются сразу.</p>` + Object.entries(model.modules).map(([slot, options]) =>
        `<fieldset><legend>${names[slot]} ${item.upgradeLevel < WEAPON_SLOT_LEVELS[slot] ? `· доступно с +${WEAPON_SLOT_LEVELS[slot]}` : ''}</legend>${options.map(m => `<button type="button" data-install-module="${slot}:${m.id}"${item.upgradeLevel < WEAPON_SLOT_LEVELS[slot] ? ' disabled' : ''}>${escapeHTML(m.name)}${item.modules[slot] === m.id ? ' ✓' : ''}<small>${weaponModuleEffect(m)} · ${weaponModuleOwned(slot,m.id) ? 'Разблокировано' : escapeHTML(weaponCostText(m.cost))}</small></button>`).join('')}</fieldset>`).join('');
    showWeaponDialog('УСТАНОВЛЕННЫЕ МОДИФИКАЦИИ', body, [['Закрыть', hideWeaponDialog]]);
    document.getElementById('weapon-dialog').querySelectorAll('[data-install-module]').forEach(button => button.addEventListener('click', () => {
        const [slot,moduleId] = button.dataset.installModule.split(':');
        if (!weaponModuleOwned(slot,moduleId)) {
            const module = model.modules[slot].find(m => m.id === moduleId);
            showWeaponDialog('Приобрести модуль?', `<p>${escapeHTML(module.name)}</p><p>${escapeHTML(weaponCostText(module.cost))}</p>`, [['Приобрести и установить', () => { if(showWeaponActionResult(setWeaponModule(id,slot,moduleId))) openWeaponModules(id); }, !canAffordWeaponCost(module.cost)], ['Назад', () => openWeaponModules(id)]]);
        } else if (showWeaponActionResult(setWeaponModule(id,slot,moduleId))) openWeaponModules(id);
    }));
}

function weaponModuleEffect(m){return [m.cooldown ? `КД ${m.cooldown.toFixed(1)} с` : '', m.reload ? `Перезарядка ${m.reload.toFixed(1)} с` : '', m.miss ? `Промах ${Math.round(m.miss*100)} п.п.` : '',m.critical ? `Крит +${Math.round(m.critical*100)} п.п.` : '',m.capacity ? `Магазин +${m.capacity}` : ''].filter(Boolean).join(' · ') || 'Без изменений';}
