// Approved second clipboard composition connected to existing weapon state and actions.
(function(){
'use strict';
const materials={common:{file:'assets/ui/wardrobe/clipboard-v2/tablet-frame-I.webp',aspect:'2108/568',label:'ОБЫЧНЫЙ',color:'#514a3a',title:'УЧЁТНЫЙ ОБРАЗЕЦ'},improved:{file:'assets/ui/wardrobe/clipboard-v2/tablet-frame-II.webp',aspect:'2114/568',label:'УЛУЧШЕННЫЙ',color:'#65601d',title:'ТЕХНИЧЕСКОЕ УЛУЧШЕНИЕ'},rare:{file:'assets/ui/wardrobe/clipboard-v2/tablet-frame-III.webp',aspect:'2111/568',label:'РЕДКИЙ',color:'#24534d',title:'АРХИВНАЯ МОДИФИКАЦИЯ'},experimental:{file:'assets/ui/wardrobe/clipboard-v2/tablet-frame-IV.webp',aspect:'2108/568',label:'ЭКСПЕРИМЕНТАЛЬНЫЙ',color:'#793029',title:'ОПЫТНЫЙ ОБРАЗЕЦ'}};
const esc=v=>escapeHTML(v);
const asset=path=>esc(path);
const labels=['I','II','III','IV','V'];
// Resize only presentation tracks; original artwork keeps its fixed aspect ratio.
const clipboardTrackObserver=new ResizeObserver(entries=>{
for(const entry of entries){const {width,height}=entry.contentRect;entry.target.style.setProperty('--archive-tablet-track',Math.min(height*1054/1492*1.042/1.022,width*.38)+'px');}
});
let observedClipboardLayout=null;

window.renderArchiveWeaponTablet=function(item,panel){
const instance=weaponInventoryItem(item),profile=calculateWeaponStats(instance);
const rarity=instance.rarity,m=materials[rarity]||materials.common;
const e={name:archiveWeaponLabel(instance),level:instance.upgradeLevel,absolute:instance.absolute,damage:profile.weaponDamage,total:calculateWeaponStats(instance,{damage:stats.baseDamage}).damage,cooldown:profile.cooldown,miss:profile.miss,critical:profile.critical,capacity:profile.capacity,reload:profile.reload};
const equipped=selectedPaperDollItem('weapon')?.id===item.id,owned=isPaperDollItemOwned(item),offer=weaponUpgradeOffer(instance);
const kind=({rifles:'Автомат',pistols:'Пистолет',melee:'Холодное оружие'})[archiveWeaponKind(item)]||'Оружие';
const duty=({rifles:'Кольцевая охрана лечебницы',pistols:'Дежурная охрана',melee:'Ближний бой'})[archiveWeaponKind(item)]||'Оснащение';
const title=e.absolute?'ПРЕДЕЛЬНАЯ МОДИФИКАЦИЯ':m.title,series=({common:'УЧЁТНАЯ СЕРИЯ',improved:'УЛУЧШЕННАЯ СЕРИЯ',rare:'РЕДКАЯ СЕРИЯ',experimental:'ЭКСПЕРИМЕНТАЛЬНАЯ СЕРИЯ'})[rarity]+(e.level?' · '+labels[e.level-1]:'');
const markup=(()=>{return `<article class="p404 p404-board archive-unified-tablet" data-selected-rarity="${rarity}" style="--rarity-color:${m.color};--frame-aspect:${m.aspect};--concept-actions:url(assets/ui/wardrobe/clipboard-v2/action-plaque.webp)" aria-label="Карточка оружия">
<img class="p404-backing" src="${asset('assets/ui/wardrobe/clipboard-v2/backing.webp')}" alt=""><img class="p404-board-art" src="${asset('assets/ui/wardrobe/clipboard-v2/board-original.png')}" alt="">
<svg class="p404-splash splash-1" viewBox="0 0 627 627" aria-hidden="true"><image href="${asset('assets/ui/wardrobe/clipboard-v2/splash-sprites.webp')}" width="1254" height="1254"/></svg><svg class="p404-splash splash-2" viewBox="627 0 627 627" aria-hidden="true"><image href="${asset('assets/ui/wardrobe/clipboard-v2/splash-sprites.webp')}" width="1254" height="1254"/></svg><svg class="p404-splash splash-3" viewBox="0 627 627 627" aria-hidden="true"><image href="${asset('assets/ui/wardrobe/clipboard-v2/splash-sprites.webp')}" width="1254" height="1254"/></svg><svg class="p404-splash splash-4" viewBox="627 627 627 627" aria-hidden="true"><image href="${asset('assets/ui/wardrobe/clipboard-v2/splash-sprites.webp')}" width="1254" height="1254"/></svg>
<div class="p404-use-stamp">${equipped?'ИСПОЛЬЗУЕТСЯ':'АРХИВ'}</div><header class="p404-institution"><div class="p404-logo-row"><img src="assets/ui/wardrobe/requested-header-emblem.webp" alt="Утверждённая эмблема"></div><small class="p404-ministry">МИНИСТЕРСТВО ЗДРАВООХРАНЕНИЯ</small><h3 class="p404-hospital-name"><span>ЦЕНТР ИНТЕНСИВНОГО ЛЕЧЕНИЯ</span><span>ПСИХИЧЕСКИХ РАССТРОЙСТВ №404</span></h3><small class="p404-department">ОТДЕЛ УЧЁТА ВООРУЖЕНИЯ</small></header>
<h4 id="wardrobe-detail-title" class="p404-weapon-title">${esc(e.name)}</h4><div class="p404-weapon-subtitle">${m.label}</div>
<div class="p404-mount"><img class="p404-mount-art" src="${asset(m.file)}" alt=""><img class="p404-mount-gun" src="${esc(wardrobeItemImage(item))}" alt="${esc(e.name)}"><span class="p404-rarity-label">${m.label}</span></div>
<div class="p404-progress" aria-label="Улучшение +${e.level}">${labels.map((n,i)=>`<span class="${e.level>i?'completed':''}">${n}</span>`).join('')}<span class="p404-star">${e.absolute?'★':'☆'}</span></div>
<dl class="p404-info"><div><dt>Тип</dt><dd>${kind}</dd></div><div><dt>Назначение</dt><dd>${duty}</dd></div></dl>
<dl class="p404-stats"><div><dt>Урон</dt><dd>${e.damage}</dd></div><div><dt>КД атаки</dt><dd>${e.cooldown.toFixed(1)} с</dd></div><div><dt>Промах</dt><dd>${e.miss*100}%</dd></div><div><dt>Крит</dt><dd>${e.critical*100}%</dd></div><div><dt>Магазин</dt><dd>${e.capacity||'—'}</dd></div><div><dt>Перезарядка</dt><dd>${e.capacity?e.reload.toFixed(1)+' с':'—'}</dd></div></dl>
<div class="p404-actions"><button type="button" data-wardrobe-action="${esc(item.id)}"${!owned?' disabled':''}>${equipped?'Снять':'Надеть'}</button><button type="button" data-weapon-upgrade="${esc(instance.instanceId)}"${!offer||!owned||isBattleActive?' disabled':''}>${esc(offer?.label||'АБСОЛЮТ ★')}</button></div>
<section class="p404-slip"><img class="p404-slip-art" src="${asset('assets/ui/wardrobe/clipboard-v2/slip-matched.webp')}" alt=""><img class="p404-coffee" src="${asset('assets/ui/wardrobe/clipboard-v2/coffee-arc.webp')}" alt="" aria-hidden="true"><div class="p404-slip-content">
<header class="p404-slip-document-header"><img class="p404-slip-logo" src="assets/ui/wardrobe/requested-header-emblem.webp" alt="Утверждённая эмблема учреждения"><div class="p404-slip-header-text"><small class="p404-slip-ministry">МИНИСТЕРСТВО ЗДРАВООХРАНЕНИЯ</small><div class="p404-slip-institution"><span>ЦЕНТР ИНТЕНСИВНОГО ЛЕЧЕНИЯ</span><span>ПСИХИЧЕСКИХ РАССТРОЙСТВ №404</span></div><small class="p404-slip-department">ОТДЕЛ УЧЁТА ВООРУЖЕНИЯ</small></div></header><strong class="p404-slip-title">${esc(title)}</strong><svg class="p404-title-underline" viewBox="0 0 500 14" preserveAspectRatio="none" aria-hidden="true"><path d="M5 8 C106 6 179 10 258 7 S399 6 493 8"/><path d="M14 11 C141 10 237 12 356 10 S449 10 480 11"/></svg><div class="p404-slip-series p404-hand">${series}</div>
<h5 class="p404-slip-service">СЛУЖЕБНАЯ ЗАПИСЬ</h5>
<dl class="p404-case"><div><dt>ПАРТИЯ №</dt><dd class="p404-hand">${esc(archiveCaseId(instance,item))}</dd></div><div><dt>ПАЦИЕНТ:</dt><dd class="p404-hand" title="${esc(playerName)}">${esc(playerName.replace('Пацієнт','Пациент'))}</dd></div><div><dt>ОТДЕЛЕНИЕ:</dt><dd class="p404-hand" title="${esc(currentRoom?.name||'Палата №404')}">${esc(currentRoom?.name||'Палата №404')}</dd></div><div><dt>ЛИСТ №</dt><dd class="p404-hand">1</dd></div></dl>
<div class="p404-copy"><p>Урон оружия: ${e.damage}.</p><p>С постоянными бонусами: ${e.total}.</p><p>Критический множитель: ×${String(profile.criticalMultiplier).replace('.',',')}.</p><small class="p404-copy-note">Модификация сохраняется для этого экземпляра.</small></div>
<div class="p404-slip-footer-rule" aria-hidden="true"></div><div class="p404-slip-footer-divider" aria-hidden="true"></div><div class="p404-date">Дата записи: <span class="p404-hand">${new Date().toLocaleDateString('ru-RU')}</span></div>
<div class="p404-signoff"><div class="p404-doctor">Ответственный врач:<svg class="p404-redacted" viewBox="0 0 120 28" role="img" aria-label="Имя врача замазано ручкой"><g fill="none" stroke="#181511" stroke-linecap="round" stroke-linejoin="round"><path opacity=".35" stroke-width="1.6" d="M5 18 Q14 3 22 17 T38 15 T54 14 T71 16 T90 13 T113 14"/><path stroke-width="3" d="M4 7 113 5 7 11 116 8 3 15 115 12 6 19 117 16 4 23 111 21 12 25 115 23"/><path stroke-width="2.2" d="M9 4 6 23 21 5 18 25 31 4 29 23 43 6 41 25 55 4 53 24 68 5 65 25 79 4 77 23 92 5 89 25 103 4 101 23 114 6 111 24"/><path opacity=".8" stroke-width="1.4" d="M2 9 118 6 M3 18 115 13 M8 26 117 20"/></g></svg></div></div><svg class="p404-signature" viewBox="0 285 887 330" role="img" aria-label="Утверждённая подпись"><image href="assets/ui/wardrobe/weapon-doctor-signature.svg" width="887" height="887"/></svg>
<img class="p404-slip-seal" src="assets/ui/wardrobe/weapon-red-seal.svg" alt="Утверждённая печать учреждения"></div></section></article>`;})();
const layout=panel.closest('.wardrobe-layout');
if(layout&&layout!==observedClipboardLayout){if(observedClipboardLayout)clipboardTrackObserver.unobserve(observedClipboardLayout);clipboardTrackObserver.observe(layout);observedClipboardLayout=layout;}
panel.innerHTML='<button type="button" class="archive-detail-close" aria-label="Вернуться к списку оружия">← Назад</button>'+markup;
PalataI18n.refresh(document.getElementById('wardrobe-container'));
panel.querySelector('.archive-detail-close').addEventListener('click',()=>document.querySelector('.archive-wardrobe').removeAttribute('data-inspecting'));
panel.querySelector('[data-wardrobe-action]').addEventListener('click',applyWardrobeItemAction);
panel.querySelector('[data-weapon-upgrade]').addEventListener('click',()=>openWeaponUpgrade(instance.instanceId));
};
})();
