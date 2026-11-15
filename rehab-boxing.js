/* Separate transparent sprites: the wall never moves with a punch. */
(function(){
'use strict';
let current=null;
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
function sprite(file,viewBox,width,height,cls){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg'),image=document.createElementNS(ns,'image');
 svg.setAttribute('viewBox',viewBox);svg.style.overflow='hidden';svg.setAttribute('aria-hidden','true');svg.classList.add(cls);image.setAttribute('href',file);image.setAttribute('width',width);image.setAttribute('height',height);svg.append(image);return svg;
}
function open(mode){
 if(current)return;
 const previous=document.activeElement,dialog=document.createElement('dialog');dialog.className='rehab-boxing';dialog.dataset.mode=mode;
 dialog.setAttribute('aria-label',mode==='trip'?'Тренування з манекеном':'Тренування з боксерською грушею');
 const toolbar=document.createElement('header'),back=document.createElement('button'),start=document.createElement('button'),notice=document.createElement('p'),progress=document.createElement('progress');
 back.textContent='Назад до кімнати';back.dataset.boxingBack='';start.textContent='Почати вправу · 10 с · 8 енергії';start.dataset.boxingStart='';notice.setAttribute('role','status');notice.textContent='Клацайте по цілі: права рука → ліва рука.';progress.max=100;progress.value=0;progress.setAttribute('aria-label','Прогрес вправи');toolbar.append(back,start,progress,notice);
 const stage=document.createElement('div');stage.className='boxing-stage';
 const background=sprite('assets/rehabilitation/boxing-backgrounds.png',mode==='trip'?'0 0 1672 486':'0 494 1672 447',1672,941,'boxing-background');
 background.setAttribute('preserveAspectRatio','xMidYMid slice');
 const target=document.createElement('button');target.className='boxing-target';target.dataset.boxingTarget='';target.setAttribute('aria-label','Ударити '+(mode==='trip'?'манекен':'грушу'));
 target.append(sprite('assets/rehabilitation/boxing-targets.png',mode==='trip'?'330 0 340 941':'1000 0 360 941',1671,941,'boxing-target-art'));
 const left=sprite('assets/rehabilitation/boxing-fists.png','0 65 887 820',1774,887,'boxing-fist'),right=sprite('assets/rehabilitation/boxing-fists.png','887 65 887 820',1774,887,'boxing-fist');left.classList.add('left');right.classList.add('right');left.setAttribute('preserveAspectRatio','xMidYMax meet');right.setAttribute('preserveAspectRatio','xMidYMax meet');
 const light=document.createElement('div');light.className='boxing-light';stage.append(background,target,left,right,light);dialog.append(toolbar,stage);document.body.append(dialog);
 let raf=0,disposed=false,last=0,punch=null,next='right',angle=0,velocity=0,hits=0,started=false,wasActive=false;
 function close(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);window.PalataRehabUI.cancelBoxing();dialog.close();dialog.remove();current=null;window.PalataRehabScene.resume();if(previous?.isConnected)previous.focus();else document.querySelector('[data-rehab-equipment=bag]')?.focus();}
 current={close};back.onclick=close;dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
 start.onclick=()=>{if(window.PalataRehabUI.startBoxing()){started=true;wasActive=true;start.disabled=true;}else notice.textContent='Вправа зараз недоступна: перевірте енергію, перерву між вправами або поточне тренування.';};
 function throwPunch(){
  if(punch||disposed||target.disabled)return;
  punch={hand:next,time:performance.now(),contact:false};next=next==='right'?'left':'right';dialog.dataset.boxingHand=punch.hand;dialog.dataset.boxingPhase='forward';
 }
 target.onclick=throwPunch;stage.onclick=()=>{if(!target.disabled)throwPunch();};
 function frame(time){
  if(disposed)return;
  if(!dialog.isConnected){close();return;}
  const dt=Math.min(.032,last?(time-last)/1000:0);last=time;
  if(punch){
   const elapsed=Math.max(0,time-punch.time),hand=punch.hand==='right'?right:left,sign=punch.hand==='right'?-1:1;
   const reach=elapsed<210?1-Math.pow(1-elapsed/210,3):Math.max(0,1-(elapsed-210)/300);
   hand.style.transform=reduced.matches?'none':`translate(${sign*stage.clientWidth*.235*reach}px,${-stage.clientHeight*(stage.clientWidth<stage.clientHeight?.10:.19)*reach}px) rotate(${sign*-13*reach}deg) scale(${1+.08*reach})`;
   if(elapsed>=210&&!punch.contact){punch.contact=true;hits++;velocity+=punch.hand==='right'?1.05:-1.05;dialog.dataset.boxingImpact=punch.hand;dialog.dataset.boxingHits=String(hits);dialog.dataset.boxingPhase='return';notice.textContent=(punch.hand==='right'?'Удар правою — ціль відхиляється вліво.':'Удар лівою — ціль відхиляється вправо.')+' Ударів: '+hits;}
   if(elapsed>=510){hand.style.transform='';punch=null;dialog.dataset.boxingPhase='ready';}
  }
  velocity+=(-24*angle-4.5*velocity)*dt;angle+=velocity*dt;angle=Math.max(-.2,Math.min(.2,angle));
  target.style.transform=reduced.matches?'none':`rotate(${angle*180/Math.PI}deg)`;dialog.dataset.boxingAngle=angle.toFixed(5);
  const phase=time%14000,dip=phase>7600&&phase<8350?Math.sin((phase-7600)/750*Math.PI):phase>8550&&phase<9200?.65*Math.sin((phase-8550)/650*Math.PI):0;
  light.style.opacity=reduced.matches?'0':String(dip*(mode==='trip'?.25:.12));
  const session=window.PalataRehabUI.boxingState();
  if(session.active){progress.value=session.progress;wasActive=true;}
  else if(started&&wasActive){progress.value=session.success?100:0;notice.textContent=session.message||'Вправу зупинено.';started=false;wasActive=false;start.disabled=false;}
  raf=requestAnimationFrame(frame);
 }
 target.disabled=true;start.disabled=true;notice.textContent='Завантаження тренування…';
 dialog.showModal();raf=requestAnimationFrame(frame);
 Promise.all(['boxing-backgrounds.png','boxing-targets.png','boxing-fists.png'].map(file=>{const image=new Image();image.src='assets/rehabilitation/'+file;return image.decode();})).then(()=>{
  if(disposed)return;dialog.dataset.boxingReady='true';target.disabled=false;start.disabled=false;notice.textContent='Клацайте в зоні тренування: права рука → ліва рука.';target.focus();
 }).catch(()=>{if(!disposed){dialog.dataset.boxingReady='error';notice.textContent='Не вдалося завантажити зображення. Поверніться до кімнати й спробуйте ще раз.';}});
}
window.PalataBoxing=Object.freeze({open,close:()=>current?.close()});
})();
