/* First-person pull-ups: the approved scene shifts rigidly as the body rises. */
(function(){
'use strict';
let current=null;
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),M=PalataPullupModel;
function open(mode){
 if(current)return;const previous=document.activeElement,dialog=document.createElement('dialog');dialog.className='rehab-pullups';dialog.dataset.mode=mode;dialog.setAttribute('aria-label','Підтягування на турніку');
 const header=document.createElement('header'),back=document.createElement('button'),start=document.createElement('button'),status=document.createElement('p');back.textContent='Назад до кімнати';back.dataset.pullupBack='';start.textContent='Почати · 5 підтягувань · 10 енергії';start.dataset.pullupStart='';start.disabled=true;status.setAttribute('role','status');status.textContent='Завантаження турніка…';header.append(back,start,status);
 const meters=document.createElement('section');meters.className='pullup-meters';
 const count=document.createElement('label'),progress=document.createElement('progress'),effortLabel=document.createElement('label'),effort=document.createElement('progress');count.textContent='Підтягування: 0 / 5';count.dataset.pullupCount='';progress.max=100;progress.value=0;progress.setAttribute('aria-label','Прогрес підходу');effortLabel.textContent='Зусилля';effort.max=100;effort.value=0;effort.setAttribute('aria-label','Зусилля від кліків');meters.append(count,progress,effortLabel,effort);
 const viewport=document.createElement('section');viewport.className='pullup-viewport';const view=document.createElement('button');view.className='pullup-view';view.disabled=true;view.dataset.pullupView='';view.setAttribute('aria-label','Тягнутися вгору — натискайте частіше');const image=document.createElement('img');image.className='pullup-main';image.src='assets/rehabilitation/pullup-'+(mode==='trip'?'trip':'patient')+'.png';image.alt='Руки тримають вигнуті кінці турніка; погляд угору';image.draggable=false;const ceiling=document.createElement('img');ceiling.className='pullup-ceiling';ceiling.src=image.src;ceiling.alt='';ceiling.setAttribute('aria-hidden','true');const world=document.createElement('span');world.className='pullup-world';world.append(image,ceiling);const canvas=document.createElement('canvas');canvas.className='pullup-sleeves';canvas.width=1672;canvas.height=941;canvas.setAttribute('aria-hidden','true');view.append(world,canvas);viewport.append(view);dialog.append(header,meters,viewport);document.body.append(dialog);
 let art=null;try{art=PalataPullupArt.create(canvas,mode);}catch(error){canvas.remove();}
 let model=M.initial(),active=false,disposed=false,ready=false,raf=0,last=0;
 function close(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);document.removeEventListener('visibilitychange',hidden);art?.dispose();PalataRehabUI.cancelPullups();dialog.close();dialog.remove();current=null;PalataRehabScene.resume();if(previous?.isConnected)previous.focus();else document.querySelector('[data-rehab-equipment=pullup]')?.focus();}
 current={close};back.onclick=close;dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
 start.onclick=()=>{if(PalataRehabUI.startPullups()){model=M.initial();active=true;last=performance.now();start.disabled=true;view.focus();status.textContent='Швидко натискайте на зображення або пробіл. Темп упав — починаєте опускатися. На піку — автоматичний спуск.';}else status.textContent='Підхід недоступний: перевірте енергію, перерву між вправами або інше активне тренування.';};
 view.addEventListener('keydown',e=>{if(e.repeat&&[' ','Enter'].includes(e.key))e.preventDefault();});
 view.onclick=()=>{advance(performance.now());if(active&&M.tap(model)){dialog.dataset.pullupClicks=String(model.taps);}};
 function advance(time){
  time=Math.max(last,time);
  const dt=last?(time-last)/1000:0;last=time;
  if(active||model.phase==='down')M.step(model,dt);
  if(active){
   PalataRehabUI.advancePullups(model.reps/model.target);
   const session=PalataRehabUI.pullupState();
   if(!session.active){active=false;status.textContent=session.message||'Підхід зупинено.';}
  }
  start.disabled=!ready||active||model.phase==='down';
 }
 function frame(time){
  if(disposed)return;if(!dialog.isConnected){close();return;}advance(time);
  count.textContent='Підтягування: '+model.reps+' / '+model.target;
  progress.value=(model.reps+(model.phase==='up'?model.lift:0))/model.target*100;effort.value=model.effort*100;
  const pose=PalataPullupArt.projection(model.lift);
  world.style.transform=reduced.matches?'none':`translateY(${pose.shift*100}%) scale(${pose.scale})`;
  ceiling.style.visibility=reduced.matches?'hidden':'visible';
  if(ready)art?.draw(model.lift,!reduced.matches);
  dialog.dataset.pullupLift=model.lift.toFixed(4);dialog.dataset.pullupReps=String(model.reps);dialog.dataset.pullupPhase=model.phase;dialog.dataset.pullupMotion=model.motion;dialog.dataset.pullupEffort=model.effort.toFixed(4);
  raf=requestAnimationFrame(frame);
 }
 function hidden(){if(document.hidden){model.effort=0;model.lastTap=-Infinity;last=0;}}
 document.addEventListener('visibilitychange',hidden);
 dialog.showModal();raf=requestAnimationFrame(frame);
 Promise.all([image.decode(),art?.ready]).then(()=>{if(disposed)return;ready=true;dialog.dataset.pullupReady='true';dialog.dataset.pullupRenderer=art?'webgl':'image';start.disabled=false;view.disabled=false;status.textContent='Почніть підхід. Часті кліки наповнюють шкалу зусилля.';}).catch(()=>{if(!disposed){dialog.dataset.pullupReady='error';status.textContent='Не вдалося завантажити сцену. Поверніться до кімнати й спробуйте знову.';}});
}
window.PalataPullups=Object.freeze({open,close:()=>current?.close()});
})();
