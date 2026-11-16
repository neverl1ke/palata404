// One manual attack clock, two independently preserved weapon states per raid.
let battleWeaponProfile = null;
let battleWeaponAmmo = 0;
let weaponReloadEndsAt = 0;
let weaponReloadTimer = null;
let battleWeaponSlots = null;
let battleWeaponSlot = null;
function raidWeaponKind(item) { return weaponModelId(item)==='gear-knife'?'melee':WEAPON_MODELS[weaponModelId(item)]?.capacity?'ranged':null; }
function rememberRaidWeapon(itemId, state=paperDollState) {
    const item=weaponInventoryItem(itemId),kind=raidWeaponKind(item);
    if(kind){state.raidWeapons ||= {};state.raidWeapons[kind]=item.paperDollId;}
}
function getBattleAttackProfile() { return battleWeaponProfile || getCombatWeaponStats(); }
function stashBattleWeapon() {
    const slot=battleWeaponSlots?.[battleWeaponSlot];
    if(slot){slot.ammo=battleWeaponAmmo;slot.reloadAt=weaponReloadEndsAt;}
}
function loadBattleWeaponSlot() {
    const slot=battleWeaponSlots?.[battleWeaponSlot];
    if(slot){battleWeaponProfile=slot.profile;battleWeaponAmmo=slot.ammo;weaponReloadEndsAt=slot.reloadAt;}
}
function finishReadyWeaponReloads() {
    stashBattleWeapon();
    for(const slot of Object.values(battleWeaponSlots||{}))if(slot?.reloadAt&&slot.reloadAt<=Date.now()){
        slot.ammo=slot.profile.capacity;slot.reloadAt=0;
    }
    loadBattleWeaponSlot();
}
function scheduleWeaponReloads() {
    clearTimeout(weaponReloadTimer);weaponReloadTimer=null;
    const at=Object.values(battleWeaponSlots||{}).map(s=>s?.reloadAt||0).filter(Boolean).sort((a,b)=>a-b)[0];
    if(!at)return;
    const generation=battleGeneration;
    weaponReloadTimer=setTimeout(()=>{
        if(generation!==battleGeneration||!isBattleActive)return;
        finishReadyWeaponReloads();scheduleWeaponReloads();renderWeaponBattleState();
        window.dispatchEvent?.(new Event('raid-weapon-state'));
    },Math.max(0,at-Date.now()));
}
function initializeWeaponBattle() {
    stopWeaponBattleTimers();
    const equipped=getEquippedItem('weapon'),active=raidWeaponKind(equipped),saved=paperDollState.raidWeapons||{};
    const bonus=globalThis.PalataRehabRules?.bonuses(stats.rehabTraining)||{damage:0,critical:0};
    const entry=item=>{
        if(!item)return null;
        const p=calculateWeaponStats(item,{damage:stats.baseDamage+bonus.damage});p.critical=Math.min(1,p.critical+bonus.critical);
        return {itemId:item.instanceId,descriptorId:item.paperDollId,profile:p,ammo:p.capacity,reloadAt:0};
    };
    battleWeaponSlots=Object.fromEntries(['ranged','melee'].map(kind=>{
        const remembered=weaponInventoryItem(saved[kind]);
        const item=active===kind?equipped:raidWeaponKind(remembered)===kind?remembered:inventory.find(i=>i.count>0&&raidWeaponKind(i)===kind);
        return [kind,entry(item)];
    }));
    battleWeaponSlot=active;
    battleWeaponProfile={...getCombatWeaponStats()};battleWeaponAmmo=battleWeaponProfile.capacity;
    loadBattleWeaponSlot();renderWeaponBattleState();
}
function stopWeaponBattleTimers() {
    clearTimeout(weaponReloadTimer);weaponReloadTimer=null;weaponReloadEndsAt=0;battleWeaponProfile=null;battleWeaponSlots=null;battleWeaponSlot=null;
}
function selectBattleWeapon(kind) {
    if(!isBattleActive||!battleWeaponSlots?.[kind])return false;
    finishReadyWeaponReloads();battleWeaponSlot=kind;loadBattleWeaponSlot();renderWeaponBattleState();
    window.dispatchEvent?.(new Event('raid-weapon-state'));return true;
}
function startWeaponReload() {
    finishReadyWeaponReloads();
    const profile=getBattleAttackProfile();
    if(!isBattleActive||!profile.capacity||weaponReloadEndsAt||battleWeaponAmmo>=profile.capacity)return false;
    weaponReloadEndsAt=Date.now()+profile.reload*1000;stashBattleWeapon();scheduleWeaponReloads();renderWeaponBattleState();return true;
}
function battleWeaponSnapshot() { stashBattleWeapon();return battleWeaponSlots?{active:battleWeaponSlot,slots:JSON.parse(JSON.stringify(battleWeaponSlots))}:null; }
function restoreBattleWeapons(saved, legacy) {
    const validProfile=p=>p&&['damage','weaponDamage','cooldown','miss','critical','criticalMultiplier','capacity','reload'].every(k=>Number.isFinite(p[k])&&p[k]>=0)&&Number.isSafeInteger(p.capacity)&&p.capacity<=100;
    if(saved&&['ranged','melee'].every(kind=>{
        const s=saved.slots?.[kind];if(s===null)return true;
        return s&&raidWeaponKind(weaponInventoryItem(s.itemId))===kind&&validProfile(s.profile)&&Number.isSafeInteger(s.ammo)&&s.ammo>=0&&s.ammo<=s.profile.capacity&&Number.isFinite(s.reloadAt)&&s.reloadAt>=0;
    })&&(saved.active===null||['ranged','melee'].includes(saved.active)&&saved.slots[saved.active])){
        battleWeaponSlots=JSON.parse(JSON.stringify(saved.slots));battleWeaponSlot=saved.active;loadBattleWeaponSlot();
    }else{
        // Old checkpoints contain only one frozen weapon profile. Keep its ammo,
        // damage and pending reload exactly; never refill a legacy magazine.
        const item=getEquippedItem('weapon'),kind=raidWeaponKind(item)||((legacy.profile.capacity||0)>0?'ranged':'melee');
        battleWeaponSlots={ranged:null,melee:null};battleWeaponSlots[kind]={itemId:item?.instanceId||null,descriptorId:item?.paperDollId||null,profile:legacy.profile,ammo:legacy.ammo,reloadAt:legacy.reloadAt};battleWeaponSlot=kind;loadBattleWeaponSlot();
    }
    finishReadyWeaponReloads();scheduleWeaponReloads();
}
function renderWeaponBattleState() {
    const panel=document.getElementById('weapon-battle-state');if(!panel)return;
    const profile=getBattleAttackProfile(),reloading=Date.now()<weaponReloadEndsAt;
    panel.innerHTML=`<span>${profile.capacity?reloading?'Перезарядка…':`Магазин: ${battleWeaponAmmo}/${profile.capacity}`:'Ближний бой'} · КД ${profile.cooldown.toFixed(1)} с</span><button type="button" onclick="event.stopPropagation();startWeaponReload()"${!profile.capacity||reloading||battleWeaponAmmo>=profile.capacity?' disabled':''}>Перезарядить</button>`;
    window.PalataRaidHUD?.renderWeapons();
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
    if(category==='weapon'&&descriptor)rememberRaidWeapon(descriptor.id);
    if(category==='weapon'&&descriptor&&wardrobeSession)rememberRaidWeapon(descriptor.id,wardrobeSession.savedState);
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
