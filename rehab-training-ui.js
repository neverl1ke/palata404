/* Real scene objects and document controls share one training transaction. */
(function(){
'use strict';
const R=PalataRehabRules;let active=null,root=null,context=null,timer=null,selected='rope',lastFinish=null;
const name=id=>id==='bag'&&context?.mode==='trip'?'Манекен':R.equipment[id].name;
function status(text){root?.querySelector('[role="status"]')?.replaceChildren(document.createTextNode(text));}
function stop(message){PalataRehabScene.setTraining(null);clearInterval(timer);timer=null;active=null;if(context?.allowed())context.refresh();status(message);}
function begin(id,manual=false){
 if(active||!context.allowed())return;
 updateEnergyTimer();const check=R.finish(stats.rehabTraining,id,stats.energy);
 if(!check.ok){status(check.error);return;}
 lastFinish=null;selected=id;active={id,start:performance.now(),duration:R.equipment[id].duration,manual,manualProgress:0};context.refresh();PalataRehabScene.setTraining(id);
 timer=setInterval(()=>{
  if(!context.allowed()){stop('Вправу перервано. Енергію не списано.');return;}
  const elapsed=performance.now()-active.start,progress=active.manual?active.manualProgress:elapsed/active.duration;
  const bar=root?.querySelector('[data-session-progress]');if(bar)bar.value=Math.min(100,progress*100);
  if(progress<1)return;
  const id=active.id;PalataRehabScene.setTraining(null);clearInterval(timer);timer=null;active=null;updateEnergyTimer();
  // The pre-existing profile transaction journals the full snapshot first.
  const result=weaponTransaction(()=>{
   const next=R.finish(stats.rehabTraining,id,stats.energy);if(!next.ok)return next;
   stats.rehabTraining=next.progress;stats.energy-=next.cost;stats.maxEnergy+=next.energyBonus;
   return{ok:true,rank:next.rank,rankUp:next.rankUp};
  });
  lastFinish=result;context.refresh();status(result.ok?(result.rankUp?'Новий ранг '+result.rank+'! Постійний бонус застосовано.':'Вправу завершено: +10 прогресу.')+(result.pendingSave?' Результат у журналі; збереження повторюється.':''):result.error);
 },100);
}
window.PalataRehabUI=Object.freeze({startPullups(){begin('pullup',true);return active?.id==='pullup'&&active.manual;},advancePullups(value){if(active?.id==='pullup'&&active.manual&&context.allowed()&&Number.isFinite(value))active.manualProgress=Math.max(active.manualProgress,Math.min(1,Math.max(0,value)));},cancelPullups(){if(active?.id==='pullup'&&active.manual)stop('Вправу скасовано. Енергію не списано.');},pullupState(){return{active:active?.id==='pullup'&&active.manual,success:!!lastFinish?.ok,message:root?.querySelector('[role="status"]')?.textContent||''};},startBoxing(){begin('bag');return active?.id==='bag';},cancelBoxing(){if(active?.id==='bag')stop('Вправу скасовано. Енергію не списано.');},boxingState(){return{active:active?.id==='bag',progress:active?.id==='bag'?Math.min(100,(performance.now()-active.start)/active.duration*100):0,success:!!lastFinish?.ok,message:root?.querySelector('[role="status"]')?.textContent||''};},select(id){if(!Object.hasOwn(R.equipment,id))return;selected=id;if(context)context.reveal();},render(host,ctx){
 context=ctx;root=document.createElement('section');root.className='rehab-training';root.setAttribute('aria-label','Постійні тренування');
 const heading=document.createElement('h4');heading.textContent='Реабілітація · тренування';root.append(heading);
 const note=document.createElement('p');note.textContent='Оберіть снаряд у кімнаті або зі списку. Прогрес спільний для Пацієнта й Трипу. 10 вправ на ранг, максимум 5 рангів. Енергія списується після завершення. Перерва між вправами на одному снаряді — 60 секунд.';root.append(note);
 const saved=R.normalize(stats.rehabTraining);
 const nav=document.createElement('nav');nav.setAttribute('aria-label','Снаряди');for(const id of Object.keys(R.equipment)){const b=document.createElement('button');b.type='button';b.textContent=name(id);b.dataset.selectEquipment=id;b.setAttribute('aria-pressed',String(id===selected));b.onclick=()=>{selected=id;context.refresh();};nav.append(b);}root.append(nav);
 const message=document.createElement('p');message.setAttribute('role','status');root.append(message);
 for(const [id,spec]of Object.entries(R.equipment)){
  if(id!==selected)continue;const p=saved[id],rank=Math.floor(p.completed/10),card=document.createElement('section'),label=document.createElement('p'),bar=document.createElement('progress'),button=document.createElement('button');
  label.textContent=name(id)+' · ранг '+rank+'/5 · '+spec.effect;bar.max=100;bar.value=p.completed===50?100:(p.completed%10)*10;bar.setAttribute('aria-label',name(id)+' — прогрес до рангу');
  button.textContent=id==='pullup'?'Почати · 5 підтягувань · 10 енергії':'Тренуватися · '+spec.duration/1000+' с · '+spec.energy+' енергії';button.dataset.train=id;button.disabled=!!active||p.completed>=50||!ctx.allowed();button.onclick=()=>id==='pullup'?PalataPullups.open(context.mode):begin(id);card.append(label,bar,button);root.append(card);
 }
 if(active){message.textContent='Триває: '+name(active.id)+'. Не виходьте з кімнати.';const bar=document.createElement('progress');bar.max=100;bar.value=0;bar.dataset.sessionProgress='';bar.setAttribute('aria-label','Виконання вправи');const cancel=document.createElement('button');cancel.textContent='Скасувати без витрат';cancel.onclick=()=>stop('Вправу скасовано. Енергію не списано.');root.append(bar,cancel);}
 host.insertBefore(root,host.querySelector('.quest-note'));if(active)PalataRehabScene.setTraining(active.id);
}});
})();
