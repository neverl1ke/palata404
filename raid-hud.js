/* The journal describes real raid events. It never schedules player attacks. */
(function(){
'use strict';
const $=id=>document.getElementById(id),esc=escapeHTML,arena=$('battle-arena-screen'),modal=$('nurse-battle-modal');
const russianBoss=()=>({nurse:'Сестра Клара',doctor:'Дежурный врач'})[currentBossKey]||bossesDatabase[currentBossKey]?.name||'Босс';
const ring='<svg viewBox="0 0 44 44"><circle class="raid-cd-track" cx="22" cy="22" r="18"/><circle class="raid-cd-fill" cx="22" cy="22" r="18" pathLength="100"/></svg><span class="raid-cooldown-label"></span>';
let pointer=null,frame=0,weaponSignature='',lastPortrait='',currentSection=null;
function toggle(section){
 currentSection=currentSection===section?null:section;
 for(const kind of ['members','actions']){
  const open=currentSection===kind,head=$('raid-'+kind+'-toggle'),panel=$(kind==='members'?'battle-raid-panel':'raid-actions-panel');
  head.setAttribute('aria-expanded',String(open));head.querySelector('span').textContent=open?'−':'+';
  panel.classList.toggle('hidden',!open);panel.closest('.raid-accordion').classList.toggle('open',open);
 }
 if(currentSection==='members')updateRaidListUI();if(currentSection==='actions')renderLog();
}
function log(text){
 if(!currentBattleSession)return;
 if(!Array.isArray(currentBattleSession.log))currentBattleSession.log=[];
 currentBattleSession.log.push({at:Date.now(),text:String(text).slice(0,400)});
 currentBattleSession.log=currentBattleSession.log.slice(-200);renderLog();
}
function renderLog(){
 const rows=(Array.isArray(currentBattleSession?.log)?currentBattleSession.log:[]).filter(r=>r&&Number.isFinite(r.at)&&typeof r.text==='string').slice(-200);
 const list=$('raid-actions-list'),nearEnd=list.parentElement.scrollHeight-list.parentElement.scrollTop-list.parentElement.clientHeight<40;
 list.innerHTML=rows.length?rows.map(row=>{const elapsed=Math.max(0,row.at-(currentBattleSession?.startedAt||row.at)),sec=Math.floor(elapsed/1000);return `<li><time>+${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')}</time>${esc(row.text)}</li>`;}).join(''):'<li>Действий пока нет.</li>';
 if(nearEnd)list.parentElement.scrollTop=list.parentElement.scrollHeight;
}
function renderMembers(){
 $('raid-members-container').innerHTML=raidMembers.filter(m=>m.isPlayer||m.called).map(m=>`<article class="raid-member"><div><span class="raid-member-name">${esc(m.name)}</span><small>${m.damage} урона</small></div>${m.isPlayer?`<small>HP ${stats.hp} / ${stats.maxHp}</small><div class="raid-health-track"><div style="width:${Math.max(0,Math.min(100,stats.hp/stats.maxHp*100))}%"></div></div>`:'<small>Союзник · в бою</small>'}</article>`).join('');
}
// Crop only transparent thumbnail margins for the card; source PNGs stay intact.
function weaponThumbnail(source){
 const crops={'avatar-core/assets/weapons/knife-view-20261025/knife-view.thumb.png':[6,30,242,62,256,128],'avatar-core/assets/weapons/user-ak47-20261026/ak47-thumb.png':[0,29,319,104,320,160]};
 const c=crops[source?.split('?')[0]];
 return c?`<svg viewBox="${c.slice(0,4).join(' ')}" aria-hidden="true"><image href="${esc(source)}" width="${c[4]}" height="${c[5]}"/></svg>`:`<img src="${esc(source)}" alt="" draggable="false">`;
}
function renderWeapons(){
 const snapshot=battleWeaponSnapshot(),signature=JSON.stringify([snapshot?.active,...['ranged','melee'].map(k=>{const s=snapshot?.slots[k];const i=weaponInventoryItem(s?.itemId);return [s?.itemId,i?.rarity,i?.upgradeLevel,i?.absolute];})]);
 if(signature!==weaponSignature){
  weaponSignature=signature;
  $('raid-weapon-cards').innerHTML=['ranged','melee'].map(kind=>{
   const s=snapshot?.slots[kind],item=weaponInventoryItem(s?.itemId),descriptor=PAPER_DOLL_ITEMS.find(i=>i.id===s?.descriptorId),rarity=item?.rarity||'common',source=descriptor?wardrobeItemImage(descriptor):null;
   const label=item?archiveWeaponLabel(item):kind==='ranged'?'Нет огнестрельного оружия':'Нет холодного оружия';
   return `<article class="raid-weapon-slot" data-raid-slot="${kind}"><button type="button" class="wardrobe-item-card raid-weapon-select" data-rarity="${esc(rarity)}" data-raid-weapon="${kind}" aria-pressed="${snapshot?.active===kind}" aria-label="${esc(label)}: выбрать"${!s?' disabled':''}><span class="wardrobe-item-image weapon-icon-frame">${source?weaponThumbnail(source):item?iconHTML(item.icon||'knife'):'—'}</span><strong class="wardrobe-item-name">${esc(label)}</strong>${s?`<span class="archive-rarity-mark"><b>${({common:'I',improved:'II',rare:'III',experimental:'IV'})[rarity]}</b><small>${esc(WEAPON_RARITIES[rarity].label)}</small></span>`:''}<span class="raid-weapon-caption"></span></button><div class="raid-cooldown hidden" aria-hidden="true">${ring}</div></article>`;
  }).join('');
  $('raid-weapon-cards').querySelectorAll('[data-raid-weapon]').forEach(b=>b.onclick=()=>selectBattleWeapon(b.dataset.raidWeapon));
 }
 for(const kind of ['ranged','melee']){
  const s=snapshot?.slots[kind],caption=document.querySelector(`[data-raid-slot="${kind}"] .raid-weapon-caption`);
  if(caption)caption.textContent=s?(s.profile.capacity?(s.reloadAt>Date.now()?'Перезарядка…':`Магазин ${s.ammo} / ${s.profile.capacity}`):'Ближний бой'):'Выберите в гардеробе';
 }
 const state=$('weapon-battle-state');state.style.left=battleWeaponSlot==='melee'?'51.3%':'27.2%';state.classList.toggle('hidden',!battleWeaponSlot||!getBattleAttackProfile().capacity);
}
function portrait(){
 const identity=JSON.stringify([paperDollState.selectedGender,paperDollState.appearance]);if(identity===lastPortrait)return;
 lastPortrait=identity;renderPaperDollAt($('raid-player-portrait'),'raid-portrait-');
}
function sync(){
 $('battle-boss-name').textContent=russianBoss();portrait();renderMembers();renderWeapons();
 for(const [kind,name] of [['small',MEDICAL_ITEMS.hp_10.name],['big',MEDICAL_ITEMS.hp_full.name]]){
  const n=inventory.find(i=>i.name===name&&i.category==='meds')?.count||0;
  $('medkit-count-'+kind).textContent=String(n);$('medkit-btn-'+kind).disabled=!isBattleActive||!n||stats.hp>=stats.maxHp;
 }
}
const begin=beginBattleMetrics;beginBattleMetrics=function(){const result=begin.apply(this,arguments);currentBattleSession.log=[];currentSection=null;toggle(null);pointer=null;weaponSignature='';log('Рейд начат. '+russianBoss()+'.');return result;};
const record=recordBattleEvent;recordBattleEvent=function(id,member,delta){
 const ok=record.apply(this,arguments);if(!ok)return ok;
 if(Number.isFinite(delta.damage))log(`${member.name}: ${delta.damage?`атака −${delta.damage} HP`:'промах'}.`);
 if(delta.damageTaken)log(`${russianBoss()}: −${delta.damageTaken} HP у ${member.name}.`);
 if(delta.healing)log(`${member.name}: восстановлено ${delta.healing} HP.`);
 return ok;
};
const ui=updateBattleUI;updateBattleUI=function(){const result=ui.apply(this,arguments);sync();return result;};
updateRaidListUI=renderMembers;toggleRaidPanel=()=>toggle('members');
const attack=performPlayerAttack;performPlayerAttack=function(event){
 const before=attackCooldownEndsAt,result=attack.apply(this,arguments);
 if(attackCooldownEndsAt>before){if(event&&Number.isFinite(event.clientX)&&Number.isFinite(event.clientY))pointer={x:event.clientX,y:event.clientY};if(currentBattleSession)currentBattleSession.attackCooldownMs=Math.max(1,attackCooldownEndsAt-Date.now());}
 return result;
};
const invite=openFriendInviteModal;openFriendInviteModal=function(){const r=invite.apply(this,arguments);$('friend-invite-modal').querySelector('input')?.focus();return r;};
const selected=callSelectedFriends;callSelectedFriends=function(){const before=raidMembers.filter(m=>m.called).map(m=>m.id),r=selected.apply(this,arguments);raidMembers.filter(m=>m.called&&!before.includes(m.id)).forEach(m=>log(m.name+': присоединился к рейду.'));window.dispatchEvent(new Event('raid-weapon-state'));return r;};
const all=callAllFriends;callAllFriends=function(){const before=raidMembers.filter(m=>m.called).map(m=>m.id),r=all.apply(this,arguments);raidMembers.filter(m=>m.called&&!before.includes(m.id)).forEach(m=>log(m.name+': присоединился к рейду.'));window.dispatchEvent(new Event('raid-weapon-state'));return r;};
function paintRing(host,remaining,total,label){
 host.classList.toggle('hidden',remaining<=0);if(remaining<=0)return;
 host.querySelector('.raid-cd-fill').style.strokeDashoffset=String(100*Math.min(1,remaining/Math.max(1,total)));
 const text=host.querySelector('.raid-cooldown-label');if(text)text.textContent=label+(remaining/1000).toFixed(1);
}
function animate(){
 if(isBattleActive&&!modal.classList.contains('hidden')&&!document.hidden){
  const now=Date.now(),left=Math.max(0,raidEndsAt-now),sec=Math.floor(left/1000);
  $('battle-timer-display').textContent=`${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')}.${String(Math.floor(left%1000)).padStart(3,'0')}`;
  if(left<=0)updateRaidTimerTick();
  const cooldown=Math.max(0,attackCooldownEndsAt-now),duration=currentBattleSession?.attackCooldownMs||getBattleAttackProfile().cooldown*1000;
  for(const kind of ['ranged','melee']){
   const s=battleWeaponSlots?.[kind],reload=Math.max(0,(s?.reloadAt||0)-now),active=battleWeaponSlot===kind,remaining=Math.max(active?cooldown:0,reload),total=reload>cooldown?s?.profile.reload*1000:duration;
   const host=document.querySelector(`[data-raid-slot="${kind}"] .raid-cooldown`);if(host)paintRing(host,remaining,total,reload>cooldown?'R':'');
  }
  const remaining=Math.max(cooldown,weaponReloadEndsAt-now,0),cursor=$('raid-cursor-cooldown');paintRing(cursor,remaining,weaponReloadEndsAt-now>cooldown?getBattleAttackProfile().reload*1000:duration,'');
  cursor.classList.toggle('hidden',remaining<=0||!pointer);if(pointer){cursor.style.left=pointer.x+'px';cursor.style.top=pointer.y+'px';}
 }
 frame=requestAnimationFrame(animate);
}
arena.tabIndex=0;arena.setAttribute('aria-label','Арена: нажмите для атаки');
arena.addEventListener('pointermove',e=>{pointer={x:e.clientX,y:e.clientY};});
arena.addEventListener('pointerleave',()=>{pointer=null;});
arena.addEventListener('keydown',e=>{if(e.target===arena&&[' ','Enter'].includes(e.key)){e.preventDefault();if(!e.repeat)performPlayerAttack();}});
document.addEventListener('keydown',e=>{
 if(!isBattleActive||modal.classList.contains('hidden')||!$('friend-invite-modal').classList.contains('hidden')||e.repeat||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName))return;
 if(e.code==='Digit1'||e.code==='Digit2'){e.preventDefault();selectBattleWeapon(e.code==='Digit1'?'ranged':'melee');}
 if(e.code==='KeyR'){e.preventDefault();startWeaponReload();}
});
window.addEventListener('pagehide',()=>cancelAnimationFrame(frame));window.addEventListener('pageshow',()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(animate);});
window.PalataRaidHUD=Object.freeze({toggle,renderWeapons,sync});
sync();renderLog();frame=requestAnimationFrame(animate);
})();
