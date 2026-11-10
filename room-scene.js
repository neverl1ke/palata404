/* Scene entrances animate the existing dialogs; saves and gameplay remain authoritative. */
(function(){
'use strict';
const root=document.querySelector('.hospital-hud');if(!root)return;
const button=root.querySelector('.room-trip-switch'),announcement=root.querySelector('.room-mode-announcement');
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),entrances=[];let pressTimer=0;
function makeEntrance(actionSelector,assemblySelector,leafSelector,modalId,reveal,duration){
 const action=root.querySelector(actionSelector),assembly=root.querySelector(assemblySelector),leaf=assembly.querySelector(leafSelector),modal=document.getElementById(modalId);
 let state='closed',timer=0,previewTimer=0;
 function clearPreview(immediate=false){
  clearTimeout(previewTimer);assembly.classList.remove('is-peeking');assembly.dataset.preview='false';
  if(state!=='closed')return;
  assembly.classList.remove('is-handle-pressed');
  if(immediate||reduced.matches)assembly.classList.remove('is-revealed');
  else previewTimer=setTimeout(()=>{if(state==='closed'&&!assembly.classList.contains('is-peeking'))assembly.classList.remove('is-revealed');},duration+140);
 }
 function peek(){
  if(state!=='closed'||root.dataset.scenePaused==='true'||reduced.matches||entrances.some(e=>e.state!=='closed'))return;
  entrances.forEach(e=>e.clearPreview());clearTimeout(previewTimer);
  assembly.classList.add('is-revealed','is-peeking','is-handle-pressed');assembly.dataset.preview='true';
 }
 function closed(){
  clearTimeout(timer);clearTimeout(previewTimer);timer=0;state='closed';assembly.classList.remove('is-open','is-revealed','is-peeking','is-handle-pressed');assembly.dataset.state=state;assembly.dataset.preview='false';action.disabled=false;action.setAttribute('aria-busy','false');
 }
 function close(){
  if(state==='closed'||state==='closing')return;
  clearTimeout(timer);clearTimeout(previewTimer);state='closing';assembly.dataset.state=state;assembly.classList.remove('is-open','is-peeking');
  if(reduced.matches)closed();else timer=setTimeout(closed,duration+140);
 }
 function show(){
  if(state!=='opening')return;
  clearTimeout(timer);timer=0;state='open';assembly.dataset.state=state;action.setAttribute('aria-busy','false');reveal();if(modal.classList.contains('hidden'))close();
 }
 function open(){
  if(entrances.some(e=>e.state!=='closed'))return false;
  if(closeOtherModals([])===false)return false;
  entrances.forEach(e=>e.clearPreview());clearTimeout(previewTimer);
  state='opening';assembly.dataset.state=state;assembly.dataset.preview='false';action.disabled=true;action.setAttribute('aria-busy','true');
  assembly.classList.remove('is-peeking');assembly.classList.add('is-revealed','is-open','is-handle-pressed');
  if(reduced.matches)show();else timer=setTimeout(show,duration+140);return true;
 }
 leaf.addEventListener('transitionend',e=>{if(e.target!==leaf||e.propertyName!=='transform')return;if(state==='opening')show();else if(state==='closing')closed();});
 action.addEventListener('click',open);action.addEventListener('pointerenter',peek);action.addEventListener('pointerleave',()=>clearPreview());action.addEventListener('focus',peek);action.addEventListener('blur',()=>clearPreview());assembly.dataset.state=state;
 const entry={get state(){return state;},open,close,peek,clearPreview,settleReduced(){clearPreview(true);if(state==='opening')show();else if(state==='closing')closed();},sync(){if(state==='open'&&modal.classList.contains('hidden'))close();},reset:closed};entrances.push(entry);return entry;
}
const door=makeEntrance('.room-door-action','.room-door-assembly','.room-door-leaf','map-modal',()=>toggleMapModal(true),820);
const cabinet=makeEntrance('.room-cabinet-action','.room-cabinet-assembly','.room-cabinet-leaf-right','custom-modal',openCustomization,1140);
// The SVG pane is an actual aperture: the fixed scene is seen through it.
// A bounded motion sample adds a little optical smear only while it turns.
const doorAssembly=root.querySelector('.room-door-assembly'),doorLeaf=doorAssembly.querySelector('.room-door-leaf');
const doorGlass=doorAssembly.querySelector('.room-door-glass');
let glassFrame=0,glassAngle=0,glassTime=0;
function updateDoorGlass(now){
 const rotation=new DOMMatrix(getComputedStyle(doorLeaf).transform);
 const angle=Math.abs(Math.atan2(rotation.m31,rotation.m11));
 const moving=!reduced.matches&&doorLeaf.getAnimations().some(a=>a.transitionProperty==='transform'&&a.playState==='running');
 const elapsed=now-glassTime;
 const motion=moving&&elapsed>0&&elapsed<100?Math.min(1,Math.abs(angle-glassAngle)*1000/elapsed/6):0;
 doorGlass.style.setProperty('--glass-motion',motion.toFixed(5));
 doorGlass.dataset.angle=(angle*180/Math.PI).toFixed(2);
 glassAngle=angle;glassTime=now;
 return moving;
}
function trackDoorGlass(){
 if(glassFrame||document.hidden)return;
 glassFrame=requestAnimationFrame(now=>{glassFrame=0;if(updateDoorGlass(now))trackDoorGlass();});
}
doorLeaf.addEventListener('transitionrun',trackDoorGlass);
doorLeaf.addEventListener('transitionend',trackDoorGlass);
doorLeaf.addEventListener('transitioncancel',trackDoorGlass);
new MutationObserver(trackDoorGlass).observe(doorAssembly,{attributes:true,attributeFilter:['class']});
new ResizeObserver(trackDoorGlass).observe(doorAssembly);
reduced.addEventListener('change',trackDoorGlass);
window.addEventListener('pagehide',()=>{cancelAnimationFrame(glassFrame);glassFrame=0;doorGlass.style.setProperty('--glass-motion','0');});
window.addEventListener('pageshow',trackDoorGlass);updateDoorGlass(performance.now());
function refresh(){
 const trip=stats.madness>=100;root.dataset.roomMode=trip?'trip':'patient';button.setAttribute('aria-pressed',String(trip));const label=trip?'Выйти из Трипа':'Войти в Трип';button.setAttribute('aria-label',label);button.querySelector('.room-action-label').textContent=label;button.disabled=isBattleActive;
}
const dialogs=[...document.querySelectorAll('[role="dialog"],.modal,.modal-overlay,.map-modal-overlay')];
function pause(){
 const open=dialogs.some(n=>!n.classList.contains('hidden')&&n.getClientRects().length>0),value=String(document.hidden||open);
 if(root.dataset.scenePaused!==value)root.dataset.scenePaused=value;
 if(open)entrances.forEach(e=>e.clearPreview());
}
function toggleTrip(){
 if(entrances.some(e=>e.state==='opening'||e.state==='closing'))return false;
 if(isBattleActive){showCustomToast('Смена режима доступна после боя.');return false;}
 if(closeOtherModals([])===false)return false;
 const trip=stats.madness<100;stats.madness=trip?100:0;setPaperDollView(trip?'combat':'patient');updateUI();refresh();button.classList.add('is-pressing');clearTimeout(pressTimer);pressTimer=setTimeout(()=>button.classList.remove('is-pressing'),180);announcement.textContent=trip?'Режим Трип включён.':'Режим Трип выключен.';return true;
}
button.addEventListener('click',toggleTrip);root.querySelector('.room-tasks-action').addEventListener('click',openTasks);
const observer=new MutationObserver(()=>{entrances.forEach(e=>e.sync());pause();});dialogs.forEach(n=>observer.observe(n,{attributes:true,attributeFilter:['class','style','hidden']}));
const portal=root.querySelector('.room-cabinet-portal'),texture=portal.querySelector('img');
function fitCabinet(){const w=portal.clientWidth,h=portal.clientHeight;if(!w||!h)return;const transform=PalataRoomProjection.rectangleToQuad(w,h,[[0,h*19/467],[w*140/142,0],[w,h],[w*3/142,h*445/467]]);if(transform)texture.style.transform=transform;}
new ResizeObserver(fitCabinet).observe(portal);fitCabinet();document.addEventListener('visibilitychange',pause);
reduced.addEventListener('change',()=>{if(reduced.matches)entrances.forEach(e=>e.settleReduced());});
window.addEventListener('pagehide',()=>{clearTimeout(pressTimer);entrances.forEach(e=>e.reset());root.dataset.scenePaused='true';});window.addEventListener('pageshow',()=>{refresh();pause();fitCabinet();});
window.PalataRoom=Object.freeze({refresh,openDoor:door.open,openCabinet:cabinet.open,peekDoor:door.peek,peekCabinet:cabinet.peek,toggleTrip});refresh();pause();
})();
