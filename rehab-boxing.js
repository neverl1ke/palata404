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
 const left=sprite('assets/rehabilitation/boxing-fists-painted.png','0 0 887 887',1774,887,'boxing-fist'),right=sprite('assets/rehabilitation/boxing-fists-painted.png','887 0 887 887',1774,887,'boxing-fist');left.classList.add('left');right.classList.add('right');left.setAttribute('preserveAspectRatio','xMidYMax meet');right.setAttribute('preserveAspectRatio','xMidYMax meet');
 const impact=document.createElement('div');impact.className='boxing-impact';impact.setAttribute('aria-hidden','true');
 impact.innerHTML='<svg viewBox="0 0 100 100"><g fill="none" stroke="#e8dab8" stroke-width="3" stroke-linecap="round"><path d="M15 30L31 39M12 60L29 55M40 10L44 28M72 16L62 32M88 43L73 46M80 78L67 66M45 89L47 73"/></g><ellipse cx="51" cy="51" rx="15" ry="12" fill="#cab88e" opacity=".22"/></svg>';
 const light=document.createElement('div');light.className='boxing-light';stage.append(background,target,left,right,impact,light);dialog.append(toolbar,stage);document.body.append(dialog);
 let raf=0,disposed=false,last=0,punch=null,next='right',angle=0,velocity=0,hits=0,started=false,wasActive=false,restUntil=0,impactAt=-Infinity;
 function close(){if(disposed)return;disposed=true;cancelAnimationFrame(raf);window.PalataRehabUI.cancelBoxing();dialog.close();dialog.remove();current=null;window.PalataRehabScene.resume();if(previous?.isConnected)previous.focus();else document.querySelector('[data-rehab-equipment=bag]')?.focus();}
 current={close};back.onclick=close;dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
 start.onclick=()=>{if(window.PalataRehabUI.startBoxing()){started=true;wasActive=true;start.disabled=true;}else notice.textContent='Вправа зараз недоступна: перевірте енергію, перерву між вправами або поточне тренування.';};
 function throwPunch(){
  if(punch||disposed||target.disabled||performance.now()<restUntil)return;
  punch={hand:next,time:performance.now(),contact:false};next=next==='right'?'left':'right';dialog.dataset.boxingHand=punch.hand;dialog.dataset.boxingPhase='windup';
 }
 target.onclick=throwPunch;stage.onclick=()=>{if(!target.disabled)throwPunch();};
 function frame(time){
  if(disposed)return;
  if(!dialog.isConnected){close();return;}
  const dt=Math.min(.032,last?(time-last)/1000:0);last=time;
  const poses={left:{x:0,y:0,r:0,s:1},right:{x:0,y:0,r:0,s:1}};
  if(punch){
   const elapsed=Math.max(0,time-punch.time),sign=punch.hand==='right'?-1:1,pose=poses[punch.hand];
   const backward=Math.min(1,elapsed/150),reach=elapsed<150?0:elapsed<350?1-Math.pow(1-(elapsed-150)/200,3):Math.max(0,1-(elapsed-350)/300);
   const windup=elapsed<150?backward:elapsed<350?1-reach:0;
   pose.x=sign*stage.clientWidth*(.235*reach-.07*windup);
   pose.y=stage.clientHeight*(.12*windup-(stage.clientWidth<stage.clientHeight?.10:.19)*reach);
   pose.r=sign*(-13*reach+7*windup);pose.s=1+.08*reach-.04*windup;
   if(elapsed>=150&&elapsed<350)dialog.dataset.boxingPhase='forward';
   if(elapsed>=350&&!punch.contact){
    punch.contact=true;hits++;velocity+=punch.hand==='right'?1.05:-1.05;impactAt=time;
    const rect=target.getBoundingClientRect(),room=stage.getBoundingClientRect();
    impact.style.left=(rect.left-room.left+rect.width*(punch.hand==='right'?.55:.45))+'px';impact.style.top=(rect.top-room.top+rect.height*(stage.clientWidth<stage.clientHeight?.66:.51))+'px';
    dialog.dataset.boxingImpact=punch.hand;dialog.dataset.boxingHits=String(hits);dialog.dataset.boxingPhase='return';
    notice.textContent=(punch.hand==='right'?'Удар правою — ціль відхиляється вліво.':'Удар лівою — ціль відхиляється вправо.')+' Ударів: '+hits;
   }
   if(elapsed>=650){
    punch=null;
    if(hits%2===0){restUntil=time+1000;dialog.dataset.boxingRestStarted=String(time);dialog.dataset.boxingPhase='cooldown';notice.textContent='Два удари. Пауза — 1 секунда.';}
    else dialog.dataset.boxingPhase='ready';
   }
  }
  if(!punch&&restUntil&&time>=restUntil){restUntil=0;dialog.dataset.boxingPhase='ready';notice.textContent='Наступна серія: права рука → ліва рука.';}
  dialog.dataset.boxingRest=String(Math.max(0,Math.ceil(restUntil-time)));
  for(const [id,hand]of [['left',left],['right',right]]){
   const pose=poses[id],breathX=Math.sin(time/850+(id==='left'?0:.4))*2,breathY=Math.sin(time/610+(id==='left'?0:.25))*3;
   hand.style.transform=reduced.matches?'none':`translate(${pose.x+breathX}px,${pose.y+breathY}px) rotate(${pose.r}deg) scale(${pose.s})`;
  }
  const impactAge=time-impactAt,impactVisible=!reduced.matches&&impactAge>=0&&impactAge<190;
  impact.style.opacity=impactVisible?String(1-impactAge/190):'0';impact.style.transform=`translate(-50%,-50%) scale(${.7+Math.min(1,impactAge/190)*.5})`;
  dialog.dataset.boxingEffect=impactVisible?'impact':'none';
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
 Promise.all(['boxing-backgrounds.png','boxing-targets.png','boxing-fists-painted.png'].map(file=>{const image=new Image();image.src='assets/rehabilitation/'+file;return image.decode();})).then(()=>{
  if(disposed)return;dialog.dataset.boxingReady='true';target.disabled=false;start.disabled=false;notice.textContent='Клік — удар. Права → ліва → пауза 1 с.';target.focus();
 }).catch(()=>{if(!disposed){dialog.dataset.boxingReady='error';notice.textContent='Не вдалося завантажити зображення. Поверніться до кімнати й спробуйте ще раз.';}});
}
window.PalataBoxing=Object.freeze({open,close:()=>current?.close()});
})();
