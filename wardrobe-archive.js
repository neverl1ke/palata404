// Production archive UI. All avatar layers still use the existing renderer.
wardrobeCategory = 'weapons'; wardrobeSlot = 'weapon'; wardrobeSelectedItemId = 'gear-aks';
let wardrobeVirtualSlot = null;
let archiveWeaponType = 'all';
const ARCHIVE_WEAPON_TYPES = {all:'Все',rifles:'Автоматы',pistols:'Пистолеты',melee:'Холодное оружие'};
function archiveWeaponKind(item){return ({'gear-aks':'rifles','gear-pm':'pistols','gear-knife':'melee'})[weaponInventoryItem(item)?.modelId] || 'other';}
function archiveVisibilityIcon(hidden){return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>${hidden?'<path class="eye-strike" d="M3 3 21 21"/>':''}</svg>`;}

const archiveVisibleItems = wardrobeVisibleItems;
wardrobeVisibleItems = function(){
    let items=archiveVisibleItems();
    if(wardrobeVirtualSlot==='cap'&&wardrobeSlot==='headwear') items=items.filter(i=>i.id!=='gear-helmet');
    if(wardrobeSlot!=='weapon') return items;
    // Present one representative of each rarity without deleting owned legacy copies.
    const representatives=new Map(), other=[];
    const equipped=selectedPaperDollItem('weapon')?.id;
    const rank=item=>{const weapon=weaponInventoryItem(item);return (item.id===wardrobeSelectedItemId?10000:0)+(item.id===equipped?1000:0)+(weapon?.absolute?100:0)+(weapon?.upgradeLevel||0)*10+Object.values(weapon?.modules||{}).filter(v=>v!=='standard').length;};
    for(const item of items){
        const weapon=weaponInventoryItem(item);
        if(weapon?.modelId!=='gear-aks'){other.push(item);continue;}
        const previous=representatives.get(weapon.rarity);
        if(!previous||rank(item)>rank(previous)) representatives.set(weapon.rarity,item);
    }
    return Object.keys(WEAPON_RARITIES).map(r=>representatives.get(r)).filter(Boolean).concat(other).filter(item=>archiveWeaponType==='all'||archiveWeaponKind(item)===archiveWeaponType);
};
const ARCHIVE_SLOT_LABELS = { headwear:'Головной убор',helmet:'Шлем',upperBody:'Верхняя одежда',outerwear:'Куртка',gloves:'Перчатки',pants:'Брюки',footwear:'Обувь',armor:'Бронежилет',loadout:'Разгрузка',weapon:'Оружие',accessory:'Аксессуар',appearance:'Внешность',baseBody:'Персонаж',face:'Головы',hair:'Причёски',beard:'Борода и усы',equipment:'К оснащению' };
const ARCHIVE_TILES = {helmet:0,upperBody:1,outerwear:2,gloves:3,pants:4,footwear:5,armor:6,loadout:7,weapon:8,accessory:10,appearance:11,face:12,hair:11,beard:13,equipment:0};
function archiveSelectSlot(slot) {
    wardrobeVirtualSlot=slot==='headwear'?'cap':slot==='helmet'?'helmet':null;
    if(slot==='equipment'){wardrobeCategory='weapons';wardrobeSlot='weapon';wardrobeSelectedItemId=null;wardrobePaletteExpanded=false;document.querySelector('.archive-wardrobe')?.removeAttribute('data-inspecting');renderWardrobe();return;}
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
    const appearance=wardrobeCategory==='appearance';
    const rails=appearance?[["archive-left-slots",['face','hair',...(paperDollState.selectedGender==='male'?['beard']:[])]],["archive-right-slots",['equipment']]]:[['archive-left-slots',['headwear','upperBody','outerwear','gloves','pants','footwear']],['archive-right-slots',['helmet','armor','loadout','weapon','accessory','appearance']]];
    for (const [id,list] of rails) {
        const host=document.getElementById(id); if (!host) continue;
        host.innerHTML=list.map(slot=>{const tile=ARCHIVE_TILES[slot]??0;const cat={upperBody:'clothes',helmet:'gear',weapon:'weapons',accessory:'accessories',appearance:'appearance',equipment:'weapons'}[slot];const compatSlot=slot==='helmet'?'headwear':slot==='headwear'?'cap':slot;return `<div class="archive-slot-wrap"><button type="button" class="archive-slot${slot==='appearance'?' appearance':''}" data-archive-slot="${slot}" ${cat?`data-wardrobe-category="${cat}"`:""} ${!["appearance","headwear","equipment"].includes(slot)?`data-wardrobe-slot="${compatSlot}"`:""} aria-pressed="${slot==='appearance'?wardrobeCategory==='appearance':(slot==='helmet'?wardrobeSlot==='headwear'&&wardrobeVirtualSlot!=='cap':slot==='headwear'?wardrobeSlot==='headwear'&&wardrobeVirtualSlot==='cap':wardrobeSlot===slot)}"><span>${slot==='equipment'?'↩ ':''}${ARCHIVE_SLOT_LABELS[slot]}</span><i class="slot-art" style="background-position:${tile%4*100/3}% ${Math.floor(tile/4)*100/3}%" aria-hidden="true"></i></button>${['helmet','headwear','appearance','accessory','face','hair','beard','equipment'].includes(slot)?'':`<button type="button" class="archive-eye" data-hide-slot="${slot}" aria-pressed="${wardrobeHiddenSlots.has(slot)}" aria-label="${wardrobeHiddenSlots.has(slot)?'Показать':'Скрыть'}: ${ARCHIVE_SLOT_LABELS[slot]}">${archiveVisibilityIcon(wardrobeHiddenSlots.has(slot))}</button>`}</div>`;}).join('');
        host.setAttribute('aria-label',appearance?(id==='archive-left-slots'?'Внешность':'Вернуться к оснащению'):(id==='archive-left-slots'?'Одежда':'Оснащение'));
        host.querySelectorAll('[data-archive-slot]').forEach(b=>b.onclick=()=>archiveSelectSlot(b.dataset.archiveSlot));
        host.querySelectorAll('[data-hide-slot]').forEach(b=>b.onclick=()=>{const slot=b.dataset.hideSlot;wardrobeHiddenSlots.has(slot)?wardrobeHiddenSlots.delete(slot):wardrobeHiddenSlots.add(slot);renderWardrobe();});
    }
}
// These marks are live overlays: rotation only, never stretched with the paper.
function archiveRarityMark(rarity='common') {
    const numeral=({common:'I',improved:'II',rare:'III',experimental:'IV'})[rarity]||'I';
    return `<span class="archive-rarity-mark" aria-hidden="true"><b>${numeral}</b><small data-i18n="rarity.${rarity}"></small></span>`;
}
function archiveWeaponLabel(instance){
    const name=({'gear-aks':'Штурмовой АКС-74У','gear-pm':'ПМ (пистолет Макарова)','gear-knife':'Ржавый нож'})[instance.modelId]||instance.name;
    return `${name} +${instance.upgradeLevel||0}${instance.absolute?' ★':''}`;
}
function archiveCaseId(instance,item){return `404/${(instance?.instanceId||item.id).slice(-4).toUpperCase()}`;}
function archiveInsertTitle(instance){return PalataI18n.t(instance?instance.absolute?'insert.absolute':'insert.'+instance.rarity:'documents.recorded');}
function archiveInsertStage(instance){return instance?`${PalataI18n.t('rarity.'+instance.rarity)} · ${instance.upgradeLevel?'ЭТАП '+['','I','II','III','IV','V'][instance.upgradeLevel]:'БАЗОВЫЙ'}`:'';}
function archiveInsertHeading(instance) {
    if(!instance)return PalataI18n.t('documents.recorded');
    const stage=instance.absolute?PalataI18n.t('insert.absolute'):instance.upgradeLevel?PalataI18n.t('insert.stage',{level:['','I','II','III','IV','V'][instance.upgradeLevel]}):PalataI18n.t('insert.base');
    return PalataI18n.t('insert.heading',{rarity:PalataI18n.t('insert.'+instance.rarity),stage});
}
function wardrobeItemCard(item) {
    const instance=weaponInventoryItem(item), label=instance?archiveWeaponLabel(instance):item.name;
    const equipped=selectedPaperDollItem(item.slot)?.id===item.id, selected=wardrobeSelectedItemId===item.id;
    const source=wardrobeItemImage(item);
    return `<button type="button" class="wardrobe-item-card${equipped?' equipped':''}${selected?' selected':''}" data-wardrobe-item="${escapeHTML(item.id)}" data-wardrobe-card="${escapeHTML(item.id)}" data-available="${isPaperDollItemOwned(item)}" data-equipped="${equipped}" data-rarity="${instance?.rarity || 'common'}" data-weapon-kind="${item.slot==='weapon'?archiveWeaponKind(item):''}" aria-pressed="${selected}" data-wardrobe-focus="item-${escapeHTML(item.id)}"><span class="wardrobe-item-image${item.slot==='weapon'?' weapon-icon-frame':item.slot==='face'?' wardrobe-face-portrait':''}">${source?`<img src="${escapeHTML(source)}" alt="" draggable="false">`:iconHTML(item.icon||PAPER_DOLL_SLOTS[item.slot].icon,'large')}</span><strong class="wardrobe-item-name">${escapeHTML(label)}</strong>${instance?`${archiveRarityMark(instance.rarity)}<span class="rarity-tag" data-rarity="${instance.rarity}" data-i18n="rarity.${instance.rarity}"></span>`:''}<span class="wardrobe-item-state">${equipped?'✓ ПРИМЕРЕНО':isPaperDollItemOwned(item)?'ДОСТУПНО':'НЕТ В ИНВЕНТАРЕ'}</span><span class="wardrobe-image-note hidden" data-paper-image-item="${escapeHTML(item.id)}"></span></button>`;
}
function archiveInstitution() { return PalataDocuments.header({variant:"center",department:"documents.weapons",scale:"normal"}); }
function archiveClipboardHardware(lower=false){
    const id=lower?'approved-clipboard-lower':'approved-clipboard-upper';
    const mask=lower?'<rect x="558" y="1342" width="100" height="52" rx="4"/>':'<path d="M264 82 384 77 407 48 433 34 465 35 495 51 515 77 650 80 653 134 263 136Z"/><path d="M74 192 108 86 118 74 140 75 150 85 148 107 104 199 88 204Z"/>';
    return `<svg class="${lower?'tablet-approval-fastener':'tablet-original-fasteners'}" viewBox="${lower?'0 1348 910 380':'0 0 910 1348'}" preserveAspectRatio="none" aria-hidden="true"><defs><clipPath id="${id}">${mask}</clipPath></defs><image href="assets/ui/wardrobe/weapon-tablet-blank.webp" width="910" height="1728" clip-path="url(#${id})"/></svg>`;
}
function renderWardrobeItemDetail(item) {
    const panel=document.getElementById('wardrobe-item-detail'); if (!panel) return;
    panel.classList.remove('hidden'); panel.dataset.slot=item?.slot||wardrobeSlot;
    if (!item) { panel.innerHTML=`<div class="archive-tablet empty-tablet">${archiveInstitution()}<div class="tablet-empty"><h4>${ARCHIVE_SLOT_LABELS[wardrobeSlot]||'Карточка'}</h4><p>В этом разделе пока нет доступных предметов.</p></div></div>`;return; }
    if (['hair','beard','face'].includes(item.slot)) {
        const equipped=selectedPaperDollItem(item.slot)?.id===item.id;
        panel.innerHTML=`<div class="archive-cosmetic-action"><strong>${escapeHTML(item.name)}</strong><button type="button" data-wardrobe-action="${escapeHTML(item.id)}"${item.slot==='hair'&&equipped?' disabled':''}>${equipped?item.slot==='hair'?'Выбрано':'Снять':'Выбрать'}</button></div>`;
        panel.querySelector('[data-wardrobe-action]').addEventListener('click',applyWardrobeItemAction);return;
    }
    if(item.slot==='weapon'&&weaponInventoryItem(item)&&Object.hasOwn(WEAPON_MODELS,weaponInventoryItem(item).modelId)){renderArchiveWeaponTablet(item,panel);return;}
    const instance=weaponInventoryItem(item), profile=instance?calculateWeaponStats(instance):null;
    const equipped=selectedPaperDollItem(item.slot)?.id===item.id, owned=isPaperDollItemOwned(item), source=wardrobeItemImage(item);
    const label=instance?archiveWeaponLabel(instance):item.name;
    const reference=inventory.find(i=>instance?i.instanceId===instance.instanceId:i.name===item.inventoryName&&i.category===item.inventoryCategory);
    const offer=instance?weaponUpgradeOffer(instance):null;
    const percentages=n=>`${Math.round(n*100)}%`;
    const description=reference?.desc||item.description||({"gear-aks":'Укороченный автомат бывшей охраны лечебницы.',"gear-knife":'Самодельный нож из обломка медицинского шпателя.',"gear-pm":'Табельный пистолет дежурной охраны.'})[instance?.modelId]||'Архивная карточка предмета.';
    panel.innerHTML=`<button type="button" class="archive-detail-close" onclick="document.querySelector('.archive-wardrobe').removeAttribute('data-inspecting')">← Назад</button><article class="archive-tablet" data-instance-id="${escapeHTML(instance?.instanceId||'')}" data-weapon-kind="${item.slot==='weapon'?archiveWeaponKind(item):''}" data-rarity="${instance?.rarity||'common'}"><section class="tablet-main-sheet"><div class="tablet-paper-face document-paper" aria-hidden="true"></div>${archiveClipboardHardware()}
        ${archiveInstitution()}<header class="tablet-title"><h4 id="wardrobe-detail-title">${escapeHTML(label)}</h4>${instance?`<span class="rarity-tag" data-rarity="${instance.rarity}" data-i18n="rarity.${instance.rarity}">${PalataI18n.t("rarity."+instance.rarity)}</span>`:`<span>${ARCHIVE_SLOT_LABELS[item.slot]}</span>`}</header>
        <div class="tablet-weapon-mount rarity-frame" data-rarity="${instance?.rarity||'common'}"><document-stamp class="tablet-use-stamp" type="archive" label="${equipped?'documents.inUse':'documents.archive'}" rotate="-3"></document-stamp>${instance?.rarity==='experimental'?'<small class="weapon-sample-mark">ОСОБЫЙ ОБРАЗЕЦ</small>':instance?.rarity==='rare'?'<small class="weapon-sample-mark">АРХИВ · III</small>':''}${instance?archiveRarityMark(instance.rarity):''}${source?`<img src="${escapeHTML(source)}" alt="${escapeHTML(item.name)}">`:iconHTML(item.icon,'large')}</div>
        ${instance?`<div class="weapon-progress" aria-label="Улучшение +${instance.upgradeLevel}">${['I','II','III','IV','V'].map((n,i)=>`<span class="${instance.upgradeLevel>i?'completed':''}">${n}</span>`).join('')}<span class="absolute-star${instance.absolute?' complete':''}" aria-label="${instance.absolute?'Абсолют':'Абсолют доступен после +5'}">${instance.absolute?'★':'☆'}</span></div>
        <dl class="weapon-stat-grid"><div><dt data-i18n="insert.damage"></dt><dd>${profile.weaponDamage}</dd></div><div><dt data-i18n="insert.cooldown"></dt><dd>${profile.cooldown.toFixed(1)} с</dd></div><div><dt data-i18n="insert.miss"></dt><dd>${percentages(profile.miss)}</dd></div><div><dt data-i18n="insert.critical"></dt><dd>${percentages(profile.critical)}</dd></div><div><dt data-i18n="insert.magazine"></dt><dd>${profile.capacity||'—'}</dd></div><div><dt data-i18n="insert.reload"></dt><dd>${profile.capacity?profile.reload.toFixed(1)+' с':'—'}</dd></div></dl>
        <dl class="tablet-weapon-info"><div><dt data-i18n="insert.type"></dt><dd data-i18n="insert.${archiveWeaponKind(item)}"></dd></div><div><dt data-i18n="insert.assignment"></dt><dd data-i18n="insert.duty.${archiveWeaponKind(item)}"></dd></div></dl>`:`<div class="tablet-description"><p>${escapeHTML(reference?.desc||item.description||ARCHIVE_SLOT_LABELS[item.slot])}</p>${reference?.armorBonus?`<p>Броня: +${reference.armorBonus}</p>`:''}<p class="wardrobe-image-note hidden" data-paper-image-item="${escapeHTML(item.id)}" data-paper-image-detail role="status"></p></div>`}
        <div class="tablet-actions"><button type="button" class="archive-paper-action" data-wardrobe-action="${escapeHTML(item.id)}"${!owned?' disabled':''}>${equipped?'Снять':'Надеть'}</button>${instance?`<button type="button" class="archive-paper-action weapon-upgrade" data-weapon-upgrade="${instance.instanceId}"${!offer||!owned||isBattleActive?' disabled':''}>${offer?offer.label:'АБСОЛЮТ ★'}</button>`:''}</div>
        </section><section class="tablet-approval-sheet"><div class="tablet-paper-face document-paper" aria-hidden="true"></div>${archiveClipboardHardware(true)}
        <img class="tablet-hospital-engraving" src="assets/ui/documents/hospital-engraving.png" alt="" aria-hidden="true">
        <div class="tablet-archive-heading"><span data-i18n="documents.name1"></span><span data-i18n="documents.name2"></span><small>АРХИВНЫЙ ВКЛАДЫШ К ИСТОРИИ БОЛЕЗНИ</small></div>
        <strong class="tablet-approval-status"><span>${escapeHTML(archiveInsertTitle(instance))}</span><small class="archive-handwritten">${escapeHTML(archiveInsertStage(instance))}</small></strong>
        <dl class="tablet-case-fields"><div><dt>Карта №:</dt><dd class="archive-handwritten" title="${escapeHTML(instance?.instanceId||item.id)}">${escapeHTML(archiveCaseId(instance,item))}</dd></div><div><dt>Пациент:</dt><dd class="archive-handwritten" title="${escapeHTML(playerName)}">${escapeHTML(playerName==='Пацієнт #404'?'Пациент №404':playerName)}</dd></div><div><dt>Отделение:</dt><dd class="archive-handwritten">${escapeHTML((currentRoom?.name||'Палата №404').replace('Палата #','Палата №'))}</dd></div><div><dt>Лист:</dt><dd class="archive-handwritten">1 из 1</dd></div></dl>
        <small class="tablet-file-date archive-handwritten">${new Date().toLocaleDateString('ru-RU')} · см. д. ${escapeHTML(archiveCaseId(instance,item))}</small>
        <div class="tablet-hand-notes archive-handwritten"><span>Сохр. модиф. ✓</span><span>Экз. №1</span></div>
        <div class="tablet-archive-imprint">АРХИВ<br>БОЛЬНИЦЫ №404</div>
        <div class="tablet-inspection-copy"><p ${instance&&["gear-aks","gear-pm","gear-knife"].includes(instance.modelId)?`data-i18n="insert.desc.${instance.modelId}"`:""}>${escapeHTML(description)}</p>${profile?`<p data-i18n="documents.weaponFacts" data-i18n-params="${escapeHTML(JSON.stringify({damage:profile.weaponDamage,total:calculateWeaponStats(instance,{damage:stats.baseDamage}).damage,critical:profile.criticalMultiplier}))}"></p>`:''}</div>
        <div class="tablet-responsible"><div class="tablet-doctor-line"><span data-i18n="documents.responsible"></span><span class="tablet-redacted" aria-label="Имя скрыто">████████</span></div><svg class="tablet-signature" viewBox="0 285 887 330" role="img" aria-label="Утверждённая подпись врача"><image href="assets/ui/wardrobe/weapon-doctor-signature.svg" width="887" height="887"/></svg></div><document-stamp class="tablet-seal" type="seal" rotate="-5"></document-stamp>
        </section>
    </article>`;
    PalataI18n.refresh(panel);
    PalataI18n.refresh(document.getElementById("wardrobe-container"));
    panel.querySelector('[data-wardrobe-action]')?.addEventListener('click',applyWardrobeItemAction);
    panel.querySelector('[data-weapon-upgrade]')?.addEventListener('click',()=>openWeaponUpgrade(instance.instanceId));


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
    categories.innerHTML=wardrobeSlot==='weapon'?Object.entries(ARCHIVE_WEAPON_TYPES).map(([id,label])=>`<button type="button" data-weapon-type="${id}" aria-pressed="${archiveWeaponType===id}">${label}</button>`).join(''):'';
    categories.querySelectorAll('[data-weapon-type]').forEach(button=>button.onclick=()=>{archiveWeaponType=button.dataset.weaponType;wardrobeSelectedItemId=null;document.querySelector('.archive-wardrobe')?.removeAttribute('data-inspecting');container.scrollTop=0;renderWardrobe();});
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
    document.getElementById('archive-resources').innerHTML=[['silver','Серебро',stats.silver],['parts','Детали',stats.equipmentParts],['experimental','Эксп. компоненты',stats.experimentalComponents]].map(([id,label,value],i)=>`<span class="archive-resource" title="${label}" aria-label="${label}: ${value}"><i style="--resource-position:${i*50}%" aria-hidden="true"></i><span>${value}</span></span>`).join('');
    document.getElementById('archive-draft-note').textContent=wardrobeHasChanges()?'Есть неприменённые изменения':'Комплект готов к осмотру';
    renderPaperDoll(); renderPaperDollControls(false);
}

function toggleArchiveCatalog(){document.getElementById('wardrobe-items')?.classList.toggle('expanded')}
