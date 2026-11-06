// Production archive UI. All avatar layers still use the existing renderer.
wardrobeCategory = 'weapons'; wardrobeSlot = 'weapon'; wardrobeSelectedItemId = 'gear-aks';
let wardrobeVirtualSlot = null;
const archiveVisibleItems = wardrobeVisibleItems;
wardrobeVisibleItems = function(){ const items=archiveVisibleItems();return wardrobeVirtualSlot==='cap'&&wardrobeSlot==='headwear'?items.filter(i=>i.id!=='gear-helmet'):items; };
const ARCHIVE_SLOT_LABELS = { headwear:'Головной убор',helmet:'Шлем',upperBody:'Верхняя одежда',outerwear:'Куртка',gloves:'Перчатки',pants:'Брюки',footwear:'Обувь',armor:'Бронежилет',loadout:'Разгрузка',weapon:'Оружие',accessory:'Аксессуар',appearance:'Внешность',baseBody:'Персонаж',face:'Головы',hair:'Причёски',beard:'Борода и усы' };
const ARCHIVE_TILES = {helmet:0,upperBody:1,outerwear:2,gloves:3,pants:4,footwear:5,armor:6,loadout:7,weapon:8,accessory:10,appearance:11};
function archiveSelectSlot(slot) {
    wardrobeVirtualSlot=slot==='headwear'?'cap':slot==='helmet'?'helmet':null;
    if(slot==='helmet') slot='headwear';
    if (slot === 'appearance') { wardrobeCategory='appearance'; wardrobeSlot='face'; }
    else {
        const category = Object.entries(WARDROBE_CATEGORIES).find(([,c]) => c.slots.includes(slot));
        if (!category) return;
        wardrobeCategory=category[0]; wardrobeSlot=slot;
    }
    wardrobeSelectedItemId=null; wardrobePaletteExpanded=false; document.querySelector('.archive-wardrobe')?.removeAttribute('data-inspecting'); renderWardrobe();
}
function archiveRenderRails() {
    for (const [id,list] of [['archive-left-slots',['headwear','upperBody','outerwear','gloves','pants','footwear']],['archive-right-slots',['helmet','armor','loadout','weapon','accessory','appearance']]]) {
        const host=document.getElementById(id); if (!host) continue;
        host.innerHTML=list.map(slot=>{const tile=ARCHIVE_TILES[slot]??0;const cat={upperBody:'clothes',helmet:'gear',weapon:'weapons',accessory:'accessories',appearance:'appearance'}[slot];const compatSlot=slot==='helmet'?'headwear':slot==='headwear'?'cap':slot;return `<div class="archive-slot-wrap"><button type="button" class="archive-slot${slot==='appearance'?' appearance':''}" data-archive-slot="${slot}" ${cat?`data-wardrobe-category="${cat}"`:""} ${!["appearance","headwear"].includes(slot)?`data-wardrobe-slot="${compatSlot}"`:""} aria-pressed="${slot==='appearance'?wardrobeCategory==='appearance':(slot==='helmet'?wardrobeSlot==='headwear'&&wardrobeVirtualSlot!=='cap':slot==='headwear'?wardrobeSlot==='headwear'&&wardrobeVirtualSlot==='cap':wardrobeSlot===slot)}"><span>${ARCHIVE_SLOT_LABELS[slot]}</span><i class="slot-art" style="background-position:${tile%4*100/3}% ${Math.floor(tile/4)*100/3}%" aria-hidden="true"></i></button>${['helmet','headwear','appearance','accessory'].includes(slot)?'':`<button type="button" class="archive-eye" data-hide-slot="${slot}" aria-pressed="${wardrobeHiddenSlots.has(slot)}" aria-label="${wardrobeHiddenSlots.has(slot)?'Показать':'Скрыть'}: ${ARCHIVE_SLOT_LABELS[slot]}">◉</button>`}</div>`;}).join('');
        host.querySelectorAll('[data-archive-slot]').forEach(b=>b.onclick=()=>archiveSelectSlot(b.dataset.archiveSlot));
        host.querySelectorAll('[data-hide-slot]').forEach(b=>b.onclick=()=>{const slot=b.dataset.hideSlot;wardrobeHiddenSlots.has(slot)?wardrobeHiddenSlots.delete(slot):wardrobeHiddenSlots.add(slot);renderWardrobe();});
    }
}
function wardrobeItemCard(item) {
    const instance=weaponInventoryItem(item), label=instance?weaponItemLabel(instance):item.name;
    const equipped=selectedPaperDollItem(item.slot)?.id===item.id, selected=wardrobeSelectedItemId===item.id;
    const source=wardrobeItemImage(item);
    return `<button type="button" class="wardrobe-item-card${equipped?' equipped':''}${selected?' selected':''}" data-wardrobe-item="${escapeHTML(item.id)}" data-wardrobe-card="${escapeHTML(item.id)}" data-available="${isPaperDollItemOwned(item)}" data-equipped="${equipped}" data-rarity="${instance?.rarity || 'common'}" aria-pressed="${selected}" data-wardrobe-focus="item-${escapeHTML(item.id)}"><span class="wardrobe-item-image${item.slot==='weapon'?' weapon-icon-frame':item.slot==='face'?' wardrobe-face-portrait':''}">${source?`<img src="${escapeHTML(source)}" alt="" draggable="false">`:iconHTML(item.icon||PAPER_DOLL_SLOTS[item.slot].icon,'large')}</span><strong class="wardrobe-item-name">${escapeHTML(label)}</strong>${instance?`<span class="rarity-tag" data-rarity="${instance.rarity}">${WEAPON_RARITIES[instance.rarity].label}</span>`:''}<span class="wardrobe-item-state">${equipped?'✓ ПРИМЕРЕНО':isPaperDollItemOwned(item)?'ДОСТУПНО':'НЕТ В ИНВЕНТАРЕ'}</span><span class="wardrobe-image-note hidden" data-paper-image-item="${escapeHTML(item.id)}"></span></button>`;
}
function archiveInstitution() { return `<header class="tablet-institution"><img src="assets/ui/wardrobe/requested-header-emblem.webp" alt="Эмблема учреждения"><div><small>МИНИСТЕРСТВО ЗДРАВООХРАНЕНИЯ</small><strong>ЦЕНТР ИНТЕНСИВНОГО ЛЕЧЕНИЯ<br>ПСИХИЧЕСКИХ РАССТРОЙСТВ №404</strong></div></header>`; }
function renderWardrobeItemDetail(item) {
    const panel=document.getElementById('wardrobe-item-detail'); if (!panel) return;
    panel.classList.remove('hidden'); panel.dataset.slot=item?.slot||wardrobeSlot;
    if (!item) { panel.innerHTML=`<div class="archive-tablet empty-tablet">${archiveInstitution()}<div class="tablet-empty"><h4>${ARCHIVE_SLOT_LABELS[wardrobeSlot]||'Карточка'}</h4><p>В этом разделе пока нет доступных предметов.</p></div></div>`;return; }
    if (['hair','beard','face'].includes(item.slot)) {
        const equipped=selectedPaperDollItem(item.slot)?.id===item.id;
        panel.innerHTML=`<div class="archive-cosmetic-action"><strong>${escapeHTML(item.name)}</strong><button type="button" data-wardrobe-action="${escapeHTML(item.id)}"${item.slot==='hair'&&equipped?' disabled':''}>${equipped?item.slot==='hair'?'Выбрано':'Снять':'Выбрать'}</button></div>`;
        panel.querySelector('[data-wardrobe-action]').addEventListener('click',applyWardrobeItemAction);return;
    }
    const instance=weaponInventoryItem(item), profile=instance?calculateWeaponStats(instance):null;
    const equipped=selectedPaperDollItem(item.slot)?.id===item.id, owned=isPaperDollItemOwned(item), source=wardrobeItemImage(item);
    const label=instance?weaponItemLabel(instance):item.name;
    const reference=inventory.find(i=>instance?i.instanceId===instance.instanceId:i.name===item.inventoryName&&i.category===item.inventoryCategory);
    const offer=instance?weaponUpgradeOffer(instance):null;
    const percentages=n=>`${Math.round(n*100)}%`;
    panel.innerHTML=`<button type="button" class="archive-detail-close" onclick="document.querySelector('.archive-wardrobe').removeAttribute('data-inspecting')">← Назад</button><article class="archive-tablet" data-instance-id="${escapeHTML(instance?.instanceId||'')}" data-rarity="${instance?.rarity||'common'}">
        ${archiveInstitution()}<header class="tablet-title"><h4 id="wardrobe-detail-title">${escapeHTML(label)}</h4>${instance?`<span class="rarity-tag" data-rarity="${instance.rarity}">${WEAPON_RARITIES[instance.rarity].label}</span>`:`<span>${ARCHIVE_SLOT_LABELS[item.slot]}</span>`}</header>
        <span class="tablet-use-stamp">${equipped?'ИСПОЛЬЗУЕТСЯ':'КАРТОТЕКА'}</span>
        <div class="tablet-weapon-mount rarity-frame" data-rarity="${instance?.rarity||'common'}">${instance?.rarity==='experimental'?'<small class="weapon-sample-mark">ОСОБЫЙ ОБРАЗЕЦ</small>':instance?.rarity==='rare'?'<small class="weapon-sample-mark">АРХИВ · III</small>':''}${source?`<img src="${escapeHTML(source)}" alt="${escapeHTML(item.name)}">`:iconHTML(item.icon,'large')}</div>
        ${instance?`<div class="weapon-progress" aria-label="Улучшение +${instance.upgradeLevel}">${['I','II','III','IV','V'].map((n,i)=>`<span class="${instance.upgradeLevel>i?'completed':''}">${n}</span>`).join('')}<span class="absolute-star${instance.absolute?' complete':''}" aria-label="${instance.absolute?'Абсолют':'Абсолют доступен после +5'}">${instance.absolute?'★':'☆'}</span></div>
        <dl class="weapon-stat-grid"><div><dt>Урон</dt><dd>${profile.weaponDamage}</dd></div><div><dt>КД атаки</dt><dd>${profile.cooldown.toFixed(1)} с</dd></div><div><dt>Промах</dt><dd>${percentages(profile.miss)}</dd></div><div><dt>Крит</dt><dd>${percentages(profile.critical)}</dd></div><div><dt>Магазин</dt><dd>${profile.capacity||'—'}</dd></div><div><dt>Перезарядка</dt><dd>${profile.capacity?profile.reload.toFixed(1)+' с':'—'}</dd></div></dl>
        <button type="button" class="tablet-modules" data-weapon-modules="${instance.instanceId}">МОДИФИКАЦИИ · ${Object.values(instance.modules).filter(v=>v!=='standard').length}/3</button>`:`<div class="tablet-description"><p>${escapeHTML(reference?.desc||item.description||ARCHIVE_SLOT_LABELS[item.slot])}</p>${reference?.armorBonus?`<p>Броня: +${reference.armorBonus}</p>`:''}<p class="wardrobe-image-note hidden" data-paper-image-item="${escapeHTML(item.id)}" data-paper-image-detail role="status"></p></div>`}
        <div class="tablet-actions"><button type="button" data-wardrobe-action="${escapeHTML(item.id)}"${!owned||item.slot==='hair'&&equipped?' disabled':''}>${equipped?item.slot==='hair'?'Выбрано':'Снять':item.slot==='face'||item.slot==='hair'||item.slot==='beard'?'Выбрать':'Надеть'}</button><button type="button" data-tablet-inspect>Осмотреть</button>${instance?`<button type="button" class="weapon-upgrade" data-weapon-upgrade="${instance.instanceId}"${!offer||!owned||isBattleActive?' disabled':''}>${offer?offer.label:'АБСОЛЮТ ★'}</button><span class="tablet-upgrade-note">${instance.absolute?'АБСОЛЮТ ★':offer?.kind==='absolute'?'Финальный этап':'Гарантированное улучшение'}</span>`:''}</div>
        <div class="tablet-approval"><strong>${instance?.absolute?'ПРЕДЕЛЬНАЯ МОДИФИКАЦИЯ':instance?.upgradeLevel||Object.values(instance?.modules||{}).some(v=>v!=='standard')?'МОДИФИЦИРОВАНО':'УЧТЕНО'}</strong><small>Ответственный врач · подпись</small><img class="tablet-signature" src="assets/ui/wardrobe/weapon-doctor-signature.svg" alt="Подпись"></div><img class="tablet-seal" src="assets/ui/wardrobe/weapon-red-seal.svg" alt="Красная печать учреждения">
    </article>`;
    panel.querySelector('[data-wardrobe-action]')?.addEventListener('click',applyWardrobeItemAction);
    panel.querySelector('[data-weapon-upgrade]')?.addEventListener('click',()=>openWeaponUpgrade(instance.instanceId));
    panel.querySelector('[data-weapon-modules]')?.addEventListener('click',()=>openWeaponModules(instance.instanceId));
    panel.querySelector('[data-tablet-inspect]')?.addEventListener('click',()=>showWeaponDialog(label,`<p>${escapeHTML(reference?.desc||item.description||'Архивная карточка предмета.')}</p>${profile?`<p>Урон оружия: ${profile.weaponDamage}. Вместе с постоянными бонусами персонажа: ${calculateWeaponStats(instance,{damage:stats.baseDamage}).damage}.</p><p>Критический множитель: ×${profile.criticalMultiplier}. Модификации сохраняются для этого экземпляра.</p>`:''}`,[['Назад',hideWeaponDialog]]));
}
function renderWardrobeUI() {
    if (wardrobeSlot==='beard' && paperDollState.selectedGender!=='male') wardrobeSlot='hair';
    const container=document.getElementById('wardrobe-container'); if(!container)return;
    document.querySelector('.archive-wardrobe').dataset.category=wardrobeCategory;
    const scroll=container.scrollTop;
    archiveRenderRails();
    document.getElementById('wardrobe-items').dataset.slot=wardrobeSlot;
    document.getElementById('wardrobe-items-title').textContent=wardrobeSlot==='headwear'&&wardrobeVirtualSlot!=='cap'?'Шлем':ARCHIVE_SLOT_LABELS[wardrobeSlot]||PAPER_DOLL_SLOTS[wardrobeSlot].label;
    const categories=document.getElementById('wardrobe-categories');
    categories.innerHTML=wardrobeCategory==='appearance'?['baseBody','face','hair','beard'].filter(s=>s!=='beard'||paperDollState.selectedGender==='male').map(s=>`<button type="button" data-wardrobe-slot="${s}" aria-pressed="${s===wardrobeSlot}">${ARCHIVE_SLOT_LABELS[s]}</button>`).join(''):'';
    categories.querySelectorAll('[data-wardrobe-slot]').forEach(b=>b.onclick=()=>selectWardrobeSlot(b.dataset.wardrobeSlot));
    document.getElementById('wardrobe-slots').innerHTML='';
    document.getElementById('wardrobe-gender-switch').classList.toggle('hidden',wardrobeCategory!=='appearance');
    document.querySelectorAll('[data-paper-gender]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.paperGender===paperDollState.selectedGender)));
    const items=wardrobeVisibleItems().sort((a,b)=>(b.modelId==='gear-aks')-(a.modelId==='gear-aks'));
    if(!items.some(i=>i.id===wardrobeSelectedItemId))wardrobeSelectedItemId=items.find(i=>i.id===selectedPaperDollItem(wardrobeSlot)?.id)?.id||items[0]?.id||null;
    renderHairPalette();
    container.classList.toggle('wardrobe-hair-grid',['hair','beard','face'].includes(wardrobeSlot));
    if(wardrobeSlot==='baseBody') container.innerHTML='<p class="archive-empty">Выберите пол персонажа или раздел внешности. Примерка сохраняется после «Применить».</p>';
    else container.innerHTML=(wardrobeSlot==='face'?`<button type="button" class="archive-native" data-wardrobe-native-face onclick="equipPaperDollItem('face',null)">Оригинальная голова</button>`:'')+(items.length?items.map(wardrobeItemCard).join(''):'<p class="archive-empty">Нет доступных предметов.</p>');
    container.querySelectorAll('[data-wardrobe-item]').forEach(b=>b.onclick=()=>{selectWardrobeItem(b.dataset.wardrobeItem);if(!['face','hair','beard','baseBody'].includes(wardrobeSlot))document.querySelector('.archive-wardrobe')?.setAttribute('data-inspecting','true');});
    renderWardrobeItemDetail(items.find(i=>i.id===wardrobeSelectedItemId));
    container.scrollTop=scroll;
    document.getElementById('archive-resources').textContent=`Серебро: ${stats.silver} · Детали: ${stats.equipmentParts} · Эксп. компоненты: ${stats.experimentalComponents}`;
    document.getElementById('archive-draft-note').textContent=wardrobeHasChanges()?'Есть неприменённые изменения':'Комплект готов к осмотру';
    renderPaperDoll(); renderPaperDollControls(false);
}

function toggleArchiveCatalog(){document.getElementById('wardrobe-items')?.classList.toggle('expanded')}
