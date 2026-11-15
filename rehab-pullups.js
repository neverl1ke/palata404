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
 const viewport=document.createElement('section');viewport.className='pullup-viewport';const view=document.createElement('button');view.className='pullup-view';view.disabled=true;view.dataset.pullupView='';view.setAttribute('aria-label','Тягнутися вгору — натискайте частіше');const image=document.createElement('img');image.className='pullup-main';image.src='assets/rehabilitation/pullup-'+(mode==='trip'?'trip':'patient')+'.png';image.alt='Руки тримають вигнуті кінці турніка; погляд угору';image.draggable=false;const ceiling=document.createElement('img');ceiling.className='pullup-ceiling';ceiling.src=image.src;ceiling.alt='';ceiling.setAttribute('aria-hidden','true');view.append(image,ceiling);viewport.append(view);dialog.append(header,meters,viewport);document.body.append(dialog);
 let model=M.initial(),active=false,disposed=false,raf=0,last=0;
 function close(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);document.removeEventListener('visibilitychange',hidden);PalataRehabUI.cancelPullups();dialog.close();dialog.remove();current=null;PalataRehabScene.resume();if(previous?.isConnected)previous.focus();else document.querySelector('[data-rehab-equipment=pullup]')?.focus();}
 current={close};back.onclick=close;dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
 start.onclick=()=>{if(PalataRehabUI.startPullups()){model=M.initial();active=true;start.disabled=true;view.focus();status.textContent='Натискайте на зображення або пробіл. Частіше натискаєте — швидше підіймаєтесь.';}else status.textContent='Підхід недоступний: перевірте енергію, перерву між вправами або інше активне тренування.';};
 view.addEventListener('keydown',e=>{if(e.repeat&&[' ','Enter'].includes(e.key))e.preventDefault();});
 view.onclick=()=>{if(active&&M.tap(model)){dialog.dataset.pullupClicks=String(model.taps);}};
 function frame(time){
  if(disposed)return;if(!dialog.isConnected){close();return;}const dt=last?(time-last)/1000:0;last=time;
  if(active){
   M.step(model,dt);PalataRehabUI.advancePullups(model.reps/model.target);
   const session=PalataRehabUI.pullupState();
   if(!session.active){active=false;start.disabled=false;status.textContent=session.message||'Підхід зупинено.';}
  }
  count.textContent='Підтягування: '+model.reps+' / '+model.target;
  progress.value=(model.reps+(model.phase==='up'?model.lift:0))/model.target*100;effort.value=model.effort*100;
  image.style.transform=reduced.matches?'none':`translateY(${model.lift*8}%)`;
  ceiling.style.visibility=reduced.matches?'hidden':'visible';ceiling.style.transform=`translateY(${-100+model.lift*8}%) scaleY(-1)`;
  dialog.dataset.pullupLift=model.lift.toFixed(4);dialog.dataset.pullupReps=String(model.reps);dialog.dataset.pullupPhase=model.phase;dialog.dataset.pullupEffort=model.effort.toFixed(4);
  raf=requestAnimationFrame(frame);
 }
 function hidden(){if(document.hidden){model.effort=0;last=0;}}
 document.addEventListener('visibilitychange',hidden);
 dialog.showModal();raf=requestAnimationFrame(frame);
 image.decode().then(()=>{if(disposed)return;dialog.dataset.pullupReady='true';start.disabled=false;view.disabled=false;status.textContent='Почніть підхід. Часті кліки наповнюють шкалу зусилля.';}).catch(()=>{if(!disposed){dialog.dataset.pullupReady='error';status.textContent='Не вдалося завантажити сцену. Поверніться до кімнати й спробуйте знову.';}});
}
window.PalataPullups=Object.freeze({open,close:()=>current?.close()});
})();
