/* A physical folder slides out of the left edge, changes format offscreen, and returns. */
(function(){
'use strict';
const board=document.getElementById('patient-card');if(!board)return;
const button=board.querySelector('.hud-card-toggle'),label=button.querySelector('span'),arrow=button.querySelector('b');
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),key='palata404_hud_card';
let busy=false,animation=null;
function apply(mode,persist=false){
 board.dataset.cardMode=mode;const full=mode==='full';
 button.setAttribute('aria-expanded',String(full));button.setAttribute('aria-label',(full?'Свернуть':'Развернуть')+' карту пациента');
 label.textContent=full?'СВЕРНУТЬ':'РАЗВЕРНУТЬ';arrow.textContent=full?'‹':'⌄';
 if(persist)safeStorageSet(key,mode);
 window.PalataHUD?.refresh();
}
async function toggle(){
 if(busy)return false;
 const next=board.dataset.cardMode==='full'?'compact':'full',focused=document.activeElement===button;
 busy=true;button.disabled=true;board.inert=true;board.dataset.cardMotion='leaving';
 try{
  if(!reduced.matches){
   animation=board.animate([{translate:'0 0',opacity:1},{translate:'-112% 0',opacity:.94}],{duration:210,easing:'cubic-bezier(.4,0,.8,.2)',fill:'both'});
   await animation.finished;
  }
  apply(next,true);board.dataset.cardMotion='entering';
  const previous=animation;
  if(!reduced.matches){
   animation=board.animate([{translate:'-112% 0',opacity:.96},{translate:'0 0',opacity:1}],{duration:380,easing:'cubic-bezier(.16,1,.3,1)',fill:'both'});
   previous?.cancel();await animation.finished;
  }
 }catch(_){/* Page teardown cancels an in-flight transition without touching game state. */}
 finally{
  animation?.cancel();animation=null;busy=false;button.disabled=false;board.inert=false;delete board.dataset.cardMotion;
  if(focused)button.focus({preventScroll:true});
 }
 return true;
}
button.addEventListener('click',toggle);
reduced.addEventListener('change',()=>{if(reduced.matches)animation?.finish();});
window.addEventListener('pagehide',()=>animation?.cancel());
apply(safeStorageGet(key)==='full'?'full':'compact');
window.PalataHudCard=Object.freeze({toggle,get mode(){return board.dataset.cardMode;},get moving(){return busy;}});
})();
