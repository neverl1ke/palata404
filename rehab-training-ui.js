/* Temporary functional test panel. Authored room art is independently approved. */
(function(){
'use strict';
const R=PalataRehabRules;let active=null,root=null,context=null,timer=null;
function status(text){root?.querySelector('[role="status"]')?.replaceChildren(document.createTextNode(text));}
function stop(message){clearInterval(timer);timer=null;active=null;if(context?.allowed())context.refresh();status(message);}
function begin(id){
 if(active||!context.allowed())return;
 updateEnergyTimer();const check=R.finish(stats.rehabTraining,id,stats.energy);
 if(!check.ok){status(check.error);return;}
 active={id,start:performance.now(),duration:R.equipment[id].duration};context.refresh();
 timer=setInterval(()=>{
  if(!context.allowed()){stop('Вправу перервано. Енергію не списано.');return;}
  const elapsed=performance.now()-active.start;
  const bar=root?.querySelector('[data-session-progress]');if(bar)bar.value=Math.min(100,elapsed/active.duration*100);
  if(elapsed<active.duration)return;
  const id=active.id;clearInterval(timer);timer=null;active=null;updateEnergyTimer();
  // The pre-existing profile transaction journals the full snapshot first.
  const result=weaponTransaction(()=>{
   const next=R.finish(stats.rehabTraining,id,stats.energy);if(!next.ok)return next;
   stats.rehabTraining=next.progress;stats.energy-=next.cost;stats.maxEnergy+=next.energyBonus;
   return{ok:true,rank:next.rank,rankUp:next.rankUp};
  });
  context.refresh();status(result.ok?(result.rankUp?'Новий ранг '+result.rank+'! Постійний бонус застосовано.':'Вправу завершено: +10 прогресу.')+(result.pendingSave?' Результат у журналі; збереження повторюється.':''):result.error);
 },100);
}
window.PalataRehabUI=Object.freeze({render(host,ctx){
 context=ctx;root=document.createElement('section');root.className='rehab-training';root.setAttribute('aria-label','Постійні тренування');
 const heading=document.createElement('h4');heading.textContent='Тренування · тест погодженого балансу';root.append(heading);
 const note=document.createElement('p');note.textContent='Тимчасова панель: нові снаряди на зображенні ще не встановлено. Прогрес спільний для Пацієнта й Трипу. 10 вправ на ранг, максимум 5 рангів. Енергія списується після завершення. Перерва між вправами на одному снаряді — 60 секунд.';root.append(note);
 const saved=R.normalize(stats.rehabTraining);
 for(const [id,spec]of Object.entries(R.equipment)){
  const p=saved[id],rank=Math.floor(p.completed/10),card=document.createElement('section'),label=document.createElement('p'),bar=document.createElement('progress'),button=document.createElement('button');
  label.textContent=spec.name+' · ранг '+rank+'/5 · '+spec.effect;bar.max=100;bar.value=p.completed===50?100:(p.completed%10)*10;bar.setAttribute('aria-label',spec.name+' — прогрес до рангу');
  button.textContent='Тренуватися · '+spec.duration/1000+' с · '+spec.energy+' енергії';button.dataset.train=id;button.disabled=!!active||p.completed>=50||!ctx.allowed();button.onclick=()=>begin(id);card.append(label,bar,button);root.append(card);
 }
 const message=document.createElement('p');message.setAttribute('role','status');root.append(message);
 if(active){message.textContent='Триває: '+R.equipment[active.id].name+'. Не виходьте з кімнати.';const bar=document.createElement('progress');bar.max=100;bar.value=0;bar.dataset.sessionProgress='';bar.setAttribute('aria-label','Виконання вправи');const cancel=document.createElement('button');cancel.textContent='Скасувати без витрат';cancel.onclick=()=>stop('Вправу скасовано. Енергію не списано.');root.append(bar,cancel);}
 host.append(root);
}});
})();
