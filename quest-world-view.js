/* Visible consequences read the durable floor ledger. Room artwork is unchanged. */
(function(){
'use strict';
function element(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);return e;}
function tag(scene,effect){
 if(effect.kind==='linen'){
  const preparing=!!effect.preparationStarted&&!effect.prepared,marker=element('span','quest-bed-service-tag');marker.dataset.worldItem=preparing?'preparing-linen':effect.prepared?'prepared-linen':'delivered-linen';marker.setAttribute('aria-hidden','true');
  marker.append(element('strong','','406'),element('small','',preparing?'СМЕНА БЕЛЬЯ · '+(effect.placed||[]).length+'/2':effect.prepared?'БЕЛЬЁ СМЕНЕНО':'БЕЛЬЁ ПЕРЕДАНО'));scene.append(marker);
 }else if(effect.kind==='call'){
  const physical=typeof effect.verified==='boolean',working=physical?effect.verified:effect.report==='working',confirmed=!!effect.report,pendingControl=physical&&effect.needsRetest;
  const marker=element('span','quest-call-service-tag',working?'✓':pendingControl||!confirmed?'?':'!');marker.dataset.callRoom=effect.room;marker.dataset.callReport=effect.report||'pending';
  if(physical){marker.dataset.callVerified=String(effect.verified);marker.dataset.callPhysicalStatus=working?'verified':pendingControl?'awaiting-retest':'unverified';marker.title=working?(confirmed?'Фактический ответ поста получен. Подписанный акт хранится отдельно.':'Ответ поста получен; акт ещё не подписан.'):pendingControl?'Обслуживание выполнено; нужен контрольный вызов из палаты.':'Работа системы ещё не подтверждена контрольным ответом поста.';}
  else marker.title=!confirmed?'Проверка выполнена; акт ещё не подписан.':working?(effect.reviewed?'Ответ поста подтверждён врачом.':'Ответ поста получен; акт подготовлен для врача.'):(effect.reviewed?'Проверка зарегистрирована; обслуживание и повторная проверка ещё не подтверждены.':'Результат требует внимания врача; передайте акт.');
  marker.setAttribute('aria-hidden','true');scene.append(marker);
 }
}
function observation(scene,state){
 if(state.room!=='A'||!state.jobs.d3?.active||![2,3].includes(state.jobs.d3.revision))return;
 const mark=window.PalataQuestEngine.observation(state).mark;if(!['Круг','Полоса','Крест'].includes(mark))return;
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 40 40');svg.classList.add('quest-observation-physical-mark');svg.dataset.observationMark=mark;svg.setAttribute('role','img');svg.setAttribute('aria-label','Отметка на металлической табличке: '+mark);
 const path=document.createElementNS(svg.namespaceURI,mark==='Круг'?'circle':'path');
 for(const [key,value]of Object.entries(mark==='Круг'?{cx:20,cy:20,r:12}:{d:mark==='Крест'?'M9 9 31 31M31 9 9 31':'M8 20H32'}))path.setAttribute(key,value);
 svg.append(path);scene.append(svg);
}
function render(scene,info,state){
 observation(scene,state);
 for(const outcome of window.PalataQuestStateView?.forRoom(window.PalataQuestEngine,state,state.room)||[]){
  if(!['passage','reserve'].includes(outcome.kind))continue;
  const card=element('section','quest-world-effect');card.dataset.worldEffect=outcome.id;card.dataset.outcomeStatus=outcome.status;
  card.append(element('h4','',outcome.label),element('p','',outcome.text));info.insertBefore(card,info.querySelector('.quest-note'));
  if(outcome.kind==='passage'&&new URLSearchParams(location.search).get('reviewPassageTags')==='1'){
   const marker=element('span','quest-passage-service-tag',state.room==='A'?'Засов освобождён':'Замок открыт');marker.dataset.artPreview='passage-tags';marker.dataset.passageState='open';marker.dataset.artPreview='passage-tags';marker.dataset.passageRoom=state.room;marker.setAttribute('role','img');marker.setAttribute('aria-label',outcome.label);scene.append(marker);
  }
 }

 const bed=state.room==='ward406'&&state.mode==='patient'?window.PalataQuestEngine.bedPresentation?.(state):null;
 if(bed){const overlay=window.PalataQuestBedView?.createRoomLayer({mode:state.mode,preparationStarted:bed.preparationStarted,placed:bed.placed||[]});if(overlay)scene.append(overlay);}
 if(state.room==='ward406'&&state.mode==='patient'&&state.cargo.includes('linen')){
  const placed=state.jobs.k2?.work?.placed||[],remaining=['sheet','pillowcase'].filter(id=>!placed.includes(id));
  if(remaining.length){
   const parcel=element('div','quest-bed-pending-linen');parcel.dataset.worldItem='pending-bed-linen';parcel.dataset.pendingPieces=remaining.join(',');parcel.setAttribute('role','img');
   parcel.setAttribute('aria-label',remaining.length===2?'Принесённые простыня и наволочка перед сменой белья':remaining[0]==='sheet'?'Принесённая простыня; наволочка уже размещена':'Принесённая наволочка; простыня уже размещена');
   const artwork=window.PalataQuestBedView?.enabled();if(artwork)parcel.classList.add('has-bed-pieces-art');
   for(const type of remaining){const holder=element('span','quest-bed-pending-piece');holder.dataset.pendingPiece=type;const image=window.PalataQuestWorkbench?.linenIllustration(type);if(image)holder.append(image);if(artwork){const style=window.PalataQuestBedView.pendingStyle(type);if(style)for(const[key,value]of Object.entries(style))holder.style[key]=value;}parcel.append(holder);}
   scene.append(parcel);
  }
 }
 for(const effect of window.PalataQuestEngine.roomEffects?.(state,state.room,state.mode)||[]){
  const card=element('section','quest-world-effect');card.dataset.worldEffect=effect.id;card.dataset.worldOrder=String(effect.order||0);card.setAttribute('aria-label',effect.title||'Результат поручения');
  for(const [field,value]of Object.entries({prepared:effect.prepared,reviewed:effect.reviewed,maintenance:effect.maintenance,preparationStarted:effect.preparationStarted,previousPrepared:effect.previousPrepared,verified:effect.verified,serviced:effect.serviced,retested:effect.retested,needsRetest:effect.needsRetest}))if(typeof value==='boolean')card.dataset['world'+field[0].toUpperCase()+field.slice(1)]=String(value);
  const title=element('h4','',effect.title||'Результат поручения');const text=element('p','quest-world-effect-text',effect.text||'');card.append(title,text);
  if(effect.response){const response=element('p','quest-world-post-response',effect.response);response.dataset.postResponse='';card.append(response);}
  info.insertBefore(card,info.querySelector('.quest-note'));tag(scene,effect);
 }
}
window.PalataQuestWorldView=Object.freeze({render});
})();
