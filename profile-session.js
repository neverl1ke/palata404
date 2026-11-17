/* One live writer per origin. The shell acquires ownership before loading saves. */
(function(root,factory){
 'use strict';
 const api=factory();
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.PalataProfileSession=api.create({locks:root.navigator?.locks,onState:renderState});
 function renderState(state){
  const panel=document.getElementById('profile-session-notice');if(!panel)return;
  panel.hidden=state.status==='owner';
  document.body.dataset.profileSession=state.status;
  const texts={
   pending:['Загрузка сохранения','Проверяем, что игра не открыта в другой вкладке.'],
   occupied:['Игра уже открыта','Продолжайте в первой вкладке. Чтобы играть здесь, закройте её и нажмите «Загрузить игру». Сохранение не изменено.'],
   restored:['Загрузите актуальное сохранение','Эта страница восстановлена из истории браузера. Загрузите игру заново, чтобы продолжить с актуальным прогрессом.'],
   unsupported:['Не удалось безопасно открыть сохранение','Для защиты прогресса нужен браузер с поддержкой Web Locks. Откройте игру через HTTPS в актуальном Chrome, Firefox или Safari. Сохранение не изменено.'],
   unavailable:['Не удалось открыть сохранение','Браузер не предоставил доступ к игровой сессии. Повторите загрузку; сохранение не изменено.']
  };
  const [title,message]=texts[state.reason]||texts.unavailable;
  document.getElementById('profile-session-title').textContent=title;
  document.getElementById('profile-session-message').textContent=message;
  document.getElementById('profile-session-reload').hidden=state.status==='pending';
  const frame=document.getElementById('game-canvas');if(frame&&state.status!=='owner')frame.inert=true;
 }
})(globalThis,function(){
 'use strict';
 const lockName='palata404:profile-writer:v1';
 function create({locks,onState=()=>{}}={}){
  let status='pending',reason='pending',frame=null,started=false,release=null,held=false;
  let readyResolve;const ready=new Promise(resolve=>{readyResolve=resolve;});
  const snapshot=()=>Object.freeze({status,reason});
  function publish(){onState(snapshot());if(status!=='pending')readyResolve(snapshot());}
  function block(why){
   status='blocked';reason=why;held=false;
   if(release){release();release=null;}
   publish();
  }
  function start(target,load){
   if(started)return ready;started=true;frame=target;publish();
   if(!locks||typeof locks.request!=='function'){block('unsupported');return ready;}
   try{
    Promise.resolve(locks.request(lockName,{mode:'exclusive',ifAvailable:true},async lock=>{
     if(!lock){block('occupied');return;}
     // A restored document cannot start again or retain a released lock.
     if(status==='blocked')return;
     const lifetime=new Promise(resolve=>{release=resolve;});
     held=true;status='owner';reason='owner';publish();
     try{load();}catch(_){block('unavailable');}
     await lifetime;
     held=false;
    })).catch(()=>block('unavailable'));
   }catch(_){block('unavailable');}
   return ready;
  }
  function canWrite(caller){return status==='owner'&&held&&!!frame&&caller===frame.contentWindow;}
  function restored(caller){if(!caller||caller===frame?.contentWindow)block('restored');}
  return Object.freeze({start,canWrite,restored,state:snapshot,ready});
 }
 return Object.freeze({create,lockName});
});
