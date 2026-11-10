/* Existing game dialogs/state remain authoritative; entrances own only their animation. */
(function(){
'use strict';
const root=document.querySelector('.hospital-hud');if(!root)return;
const button=root.querySelector('.room-trip-switch'),announcement=root.querySelector('.room-mode-announcement');
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),entrances=[];
let pressTimer=0;
function makeEntrance(actionSelector,assemblySelector,leafSelector,modalId,reveal,duration){
 const action=root.querySelector(actionSelector),assembly=root.querySelector(assemblySelector),leaf=assembly.querySelector(leafSelector),modal=document.getElementById(modalId);
 let state='closed',timer=0;
 function closed(){
  clearTimeout(timer);timer=0;state='closed';assembly.classList.remove('is-open','is-revealed');assembly.dataset.state=state;
  action.disabled=false;action.setAttribute('aria-busy','false');
 }
 function close(){
  if(state==='closed'||state==='closing')return;
  clearTimeout(timer);state='closing';assembly.dataset.state=state;
  // Keep the opening in front of the baked closed door until the moving leaf settles.
  assembly.classList.remove('is-open');
  if(reduced.matches)closed();else timer=setTimeout(closed,duration+140);
 }
 function show(){
  if(state!=='opening')return;
  clearTimeout(timer);timer=0;state='open';assembly.dataset.state=state;action.setAttribute('aria-busy','false');
  reveal();if(modal.classList.contains('hidden'))close();
 }
 function open(){
  if(entrances.some(e=>e.state!=='closed'))return false;
  if(closeOtherModals([])===false)return false;
  state='opening';assembly.dataset.state=state;action.disabled=true;action.setAttribute('aria-busy','true');
  assembly.classList.add('is-revealed','is-open');
  if(reduced.matches)show();else timer=setTimeout(show,duration+140);
  return true;
 }
 leaf.addEventListener('transitionend',e=>{if(e.target!==leaf||e.propertyName!=='transform')return;if(state==='opening')show();else if(state==='closing')closed();});
 action.addEventListener('click',open);assembly.dataset.state=state;
 const entry={get state(){return state;},open,close,settleReduced(){if(state==='opening')show();else if(state==='closing')closed();},sync(){if(state==='open'&&modal.classList.contains('hidden'))close();},reset(){clearTimeout(timer);closed();}};
 entrances.push(entry);return entry;
}
const door=makeEntrance('.room-door-action','.room-door-assembly','.room-door-leaf','map-modal',()=>toggleMapModal(true),820);
const cabinet=makeEntrance('.room-cabinet-action','.room-cabinet-assembly','.room-cabinet-leaf-right','custom-modal',openCustomization,1140);
function refresh(){
 const trip=stats.madness>=100;root.dataset.roomMode=trip?'trip':'patient';button.setAttribute('aria-pressed',String(trip));
 const label=trip?'Выйти из Трипа':'Войти в Трип';button.setAttribute('aria-label',label);button.querySelector('.room-action-label').textContent=label;button.disabled=isBattleActive;
}
function pause(){
 const open=[...document.querySelectorAll('.modal,.map-modal-overlay')].some(n=>!n.classList.contains('hidden')&&getComputedStyle(n).display!=='none');
 root.dataset.scenePaused=String(document.hidden||open);
}
function toggleTrip(){
 if(entrances.some(e=>e.state==='opening'||e.state==='closing'))return false;
 if(isBattleActive){showCustomToast('Смена режима доступна после боя.');return false;}
 if(closeOtherModals([])===false)return false;
 const trip=stats.madness<100;stats.madness=trip?100:0;setPaperDollView(trip?'combat':'patient');updateUI();refresh();
 button.classList.add('is-pressing');clearTimeout(pressTimer);pressTimer=setTimeout(()=>button.classList.remove('is-pressing'),180);
 announcement.textContent=trip?'Режим Трип включён.':'Режим Трип выключен.';return true;
}
button.addEventListener('click',toggleTrip);
root.querySelector('.room-tasks-action').addEventListener('click',openTasks);
const observer=new MutationObserver(()=>{entrances.forEach(e=>e.sync());pause();});
document.querySelectorAll('.modal,.map-modal-overlay').forEach(n=>observer.observe(n,{attributes:true,attributeFilter:['class','style']}));
const portal=root.querySelector('.room-cabinet-portal'),texture=portal.querySelector('img');
function fitCabinet(){
 const w=portal.clientWidth,h=portal.clientHeight;if(!w||!h)return;
 const transform=PalataRoomProjection.rectangleToQuad(w,h,[[0,h*19/467],[w*140/142,0],[w,h],[w*3/142,h*445/467]]);
 if(transform)texture.style.transform=transform;
}
new ResizeObserver(fitCabinet).observe(portal);fitCabinet();
document.addEventListener('visibilitychange',pause);
reduced.addEventListener('change',()=>{if(reduced.matches)entrances.forEach(e=>e.settleReduced());});
window.addEventListener('pagehide',()=>{clearTimeout(pressTimer);entrances.forEach(e=>e.reset());root.dataset.scenePaused='true';});
window.addEventListener('pageshow',()=>{refresh();pause();fitCabinet();});
window.PalataRoom=Object.freeze({refresh,openDoor:door.open,openCabinet:cabinet.open,toggleTrip});refresh();pause();
})();
