/* Presentation draft: existing game state remains the sole source of data. */
(function(){
'use strict';
const byId=id=>document.getElementById(id);
function portrait(){const host=byId('hud-portrait');if(host)renderPaperDollAt(host,'hud-');}
function equippedProfile(){
 // The chart describes the saved outfit currently shown in the room. Trying
 // another outfit must not change the chart or the authoritative combat gear.
 const state=wardrobeSession?.savedState||paperDollState;
 const loadout=state[state.activeViewMode==='combat'?'combatLoadout':'patientLoadout'];
 const visual=slot=>PAPER_DOLL_ITEMS.find(item=>item.id===loadout[slot]&&item.slot===slot&&isPaperDollItemOwned(item)&&paperDollItemSupportsGender(item,state.selectedGender));
 const armorBonus=slot=>{const item=visual(slot);return inventory.find(entry=>entry.category===item?.inventoryCategory&&entry.name===item?.inventoryName&&entry.count>0)?.armorBonus||0;};
 return {...calculateWeaponStats(weaponInventoryItem(visual('weapon')),{damage:stats.baseDamage}),armor:stats.baseArmor+armorBonus('headwear')+armorBonus('armor')};
}
function sync(){
 if(playerName==='Пацієнт #404')byId('player-name').textContent='Пациент №404';
 const sanity=Math.max(0,Math.min(100,100-stats.madness));
 byId('hud-sanity-value').textContent=sanity+' / 100';
 const board=byId('patient-card'),compact=board?.dataset.cardMode==='compact';
 const energy=Math.max(0,Math.min(100,100*stats.energy/Math.max(1,stats.maxEnergy)));
 board?.style.setProperty('--hud-sanity',sanity);board?.style.setProperty('--hud-energy',energy);
 board?.querySelector('.hud-compact-sanity')?.setAttribute('aria-valuenow',String(sanity));
 board?.querySelector('.hud-compact-energy')?.setAttribute('aria-valuenow',String(energy));
 byId('loc-title-label').textContent=stats.madness>=100?'СИСТЕМНЫЙ СБОЙ':'ТЕКУЩАЯ ЛОКАЦИЯ';
 if(stats.madness>=100)byId('current-location-name').textContent='ОШИБКА 404: Неизвестно';
 byId('hud-health-value').textContent=stats.hp;
 byId('hud-health-value').title=stats.hp+' / '+stats.maxHp;
 byId('hud-exp-percent').textContent=(Math.min(100,100*stats.exp/Math.max(1,stats.nextLvlExp))).toLocaleString('ru-RU',{maximumFractionDigits:1})+'%';
 const equipment=equippedProfile();
 byId('damage-val').textContent=equipment.damage;
 byId('armor-val').textContent=equipment.armor;
 byId('hud-critical-value').textContent='×'+equipment.criticalMultiplier.toLocaleString('ru-RU',{maximumFractionDigits:2});
 const identity=getPlayerUniqueId().id;
 document.querySelectorAll('[data-hud-case]').forEach(n=>n.textContent=identity);
 // Keep large balances and XP inside the same painted receipt/ribbon areas.
 ['silver-val','pills-val','bucks-val','exp-val','damage-val','armor-val','hud-health-value','hud-critical-value'].forEach(id=>{
  const el=byId(id),base=Number(el.style.getPropertyValue(compact?'--cf':'--font')),width=Number(el.style.getPropertyValue(compact?'--cw':'--w'));
  const size=Math.min(base,width/Math.max(1,el.textContent.length*.64));
  el.style.fontSize='calc('+size+' / '+(compact?1902:971)+' * 100cqw)';
 });
 const name=byId('player-name'),nameField=name.parentElement;
 if(compact){
  const base=Number(nameField.style.getPropertyValue('--cf')),width=Number(nameField.style.getPropertyValue('--cw'));
  nameField.style.fontSize='calc('+Math.min(base,width/Math.max(1,name.textContent.length*.64))+' / 1902 * 100cqw)';
 }else nameField.style.removeProperty('font-size');
 if(window.PalataRoom)window.PalataRoom.refresh();
 portrait();
}
const priorUpdateUI=updateUI;
updateUI=function(){const result=priorUpdateUI.apply(this,arguments);sync();return result;};
window.addEventListener('paper-doll-render',portrait);
const paths=[...document.querySelectorAll('[data-hud-wave]')],reduced=matchMedia('(prefers-reduced-motion: reduce)');
let timer=null;
function wave(t,kind){
 const points=[];
 for(let x=0;x<=180;x+=1.5){
  let y;
  if(kind==='sanity')y=30+6*Math.sin(x*.19+t*2)+4*Math.sin(x*.47-t*4)+2*Math.cos(x*.87+t*3);
  else {const k=((x+t*25)%55)/55;y=32-25*Math.exp(-Math.pow((k-.35)/.025,2))+12*Math.exp(-Math.pow((k-.39)/.03,2))-3*Math.exp(-Math.pow((k-.57)/.1,2));}
  points.push((x?'L':'M')+x.toFixed(1)+' '+y.toFixed(1));
 }
 return points.join(' ');
}
function paint(){const t=reduced.matches?0:performance.now()/1000;paths.forEach(p=>p.setAttribute('d',wave(t,p.dataset.hudWave)));}
function playback(){if(timer){clearInterval(timer);timer=null;}paint();if(!document.hidden&&!reduced.matches)timer=setInterval(paint,100);}
reduced.addEventListener('change',playback);document.addEventListener('visibilitychange',playback);window.addEventListener('pagehide',()=>{clearInterval(timer);timer=null;});window.addEventListener('pageshow',playback);
sync();playback();
window.PalataHUD=Object.freeze({refresh:sync});
})();
