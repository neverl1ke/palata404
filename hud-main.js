/* Presentation draft: existing game state remains the sole source of data. */
(function(){
'use strict';
const byId=id=>document.getElementById(id);
function portrait(){const host=byId('hud-portrait');if(host)renderPaperDollAt(host,'hud-');}
function sync(){
 if(playerName==='Пацієнт #404')byId('player-name').textContent='Пациент №404';
 const sanity=Math.max(0,Math.min(100,100-stats.madness));
 byId('hud-sanity-value').textContent=sanity+' / 100';
 byId('loc-title-label').textContent=stats.madness>=100?'СИСТЕМНЫЙ СБОЙ':'ТЕКУЩАЯ ЛОКАЦИЯ';
 if(stats.madness>=100)byId('current-location-name').textContent='ОШИБКА 404: Неизвестно';
 byId('hud-health-value').textContent=stats.hp;
 byId('hud-health-value').title=stats.hp+' / '+stats.maxHp;
 byId('hud-exp-percent').textContent=(Math.min(100,100*stats.exp/Math.max(1,stats.nextLvlExp))).toLocaleString('ru-RU',{maximumFractionDigits:1})+'%';
 byId('hud-critical-value').textContent='×'+getCombatWeaponStats().criticalMultiplier.toLocaleString('ru-RU',{maximumFractionDigits:2});
 const identity=getPlayerUniqueId().id;
 document.querySelectorAll('[data-hud-case]').forEach(n=>n.textContent=identity);
 // Keep large balances and XP inside the same painted receipt/ribbon areas.
 ['silver-val','pills-val','bucks-val','exp-val','damage-val','armor-val','hud-health-value','hud-critical-value'].forEach(id=>{
  const el=byId(id),base=Number(el.style.getPropertyValue('--font')),width=Number(el.style.getPropertyValue('--w'));
  const size=Math.min(base,width/Math.max(1,el.textContent.length*.64));
  el.style.fontSize='calc('+size+' / 971 * 100cqw)';
 });
 const map=byId('nav-map-btn');map.disabled=false;map.setAttribute('aria-disabled','false');
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
