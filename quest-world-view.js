/* Visible consequences read the durable floor ledger. Room artwork is unchanged. */
(function(){
'use strict';
function element(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);return e;}
function tag(scene,effect){
 if(effect.kind==='linen'){
  const marker=element('span','quest-bed-service-tag');marker.dataset.worldItem=effect.prepared?'prepared-linen':'delivered-linen';marker.setAttribute('aria-hidden','true');
  marker.append(element('strong','','406'),element('small','',effect.prepared?'БЕЛЬЁ СМЕНЕНО':'БЕЛЬЁ ПЕРЕДАНО'));scene.append(marker);
 }else if(effect.kind==='call'){
  const working=effect.report==='working',confirmed=!!effect.report;
  const marker=element('span','quest-call-service-tag',confirmed?(working?'✓':'!'):'?');marker.dataset.callRoom=effect.room;marker.dataset.callReport=effect.report||'pending';marker.title=!confirmed?'Проверка выполнена; акт ещё не подписан.':working?(effect.reviewed?'Ответ поста подтверждён врачом.':'Ответ поста получен; акт подготовлен для врача.'):(effect.reviewed?'Проверка зарегистрирована; обслуживание и повторная проверка ещё не подтверждены.':'Результат требует внимания врача; передайте акт.');marker.setAttribute('aria-hidden','true');scene.append(marker);
 }
}
function observation(scene,state){
 if(state.room!=='A'||!state.jobs.d3?.active||state.jobs.d3.revision!==2)return;
 const mark=window.PalataQuestEngine.observation(state).mark;if(!['Круг','Полоса','Крест'].includes(mark))return;
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 40 40');svg.classList.add('quest-observation-physical-mark');svg.dataset.observationMark=mark;svg.setAttribute('role','img');svg.setAttribute('aria-label','Отметка на металлической табличке: '+mark);
 const path=document.createElementNS(svg.namespaceURI,mark==='Круг'?'circle':'path');
 for(const [key,value]of Object.entries(mark==='Круг'?{cx:20,cy:20,r:12}:{d:mark==='Крест'?'M9 9 31 31M31 9 9 31':'M8 20H32'}))path.setAttribute(key,value);
 svg.append(path);scene.append(svg);
}
function render(scene,info,state){
 observation(scene,state);
 if(state.room==='ward406'&&state.mode==='patient'&&state.cargo.includes('linen')){
  const placed=state.jobs.k2?.work?.placed||[],remaining=['sheet','pillowcase'].filter(id=>!placed.includes(id));
  if(remaining.length){
   const parcel=element('div','quest-bed-pending-linen');parcel.dataset.worldItem='pending-bed-linen';parcel.dataset.pendingPieces=remaining.join(',');parcel.setAttribute('role','img');
   parcel.setAttribute('aria-label',remaining.length===2?'Принесённые простыня и наволочка перед сменой белья':remaining[0]==='sheet'?'Принесённая простыня; наволочка уже размещена':'Принесённая наволочка; простыня уже размещена');
   // Reuse the original painted fold as a linen illustration, not an invented
   // rectangular patch. The two item copies follow the actual remaining pieces.
   const fold=(x,y,w,h)=>'<svg x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" viewBox="300 540 330 90"><image href="assets/quest-scenes/linen.webp" width="1536" height="1024" clip-path="url(#quest-pending-painted-fold)"/></svg>';
   parcel.innerHTML='<svg viewBox="0 0 260 125" aria-hidden="true"><defs><clipPath id="quest-pending-painted-fold" clipPathUnits="userSpaceOnUse"><path d="M313 581C315 573 322 569 333 565L354 563C367 561 382 563 399 564L449 564C476 560 501 557 523 554L550 550 566 554C588 553 608 568 610 582C614 592 608 604 603 608L409 619 357 621C340 619 324 614 317 606C309 598 308 587 313 581Z"/></clipPath></defs>'+(remaining.includes('sheet')?fold(0,36,260,80):'')+(remaining.includes('pillowcase')?fold(38,remaining.includes('sheet')?0:56,190,58):'')+'</svg>';
   scene.append(parcel);
  }
 }
 for(const effect of window.PalataQuestEngine.roomEffects?.(state,state.room,state.mode)||[]){
  const card=element('section','quest-world-effect');card.dataset.worldEffect=effect.id;card.dataset.worldOrder=String(effect.order||0);card.setAttribute('aria-label',effect.title||'Результат поручения');
  for(const [field,value]of Object.entries({prepared:effect.prepared,reviewed:effect.reviewed,maintenance:effect.maintenance}))if(typeof value==='boolean')card.dataset['world'+field[0].toUpperCase()+field.slice(1)]=String(value);
  const title=element('h4','',effect.title||'Результат поручения');const text=element('p','quest-world-effect-text',effect.text||'');card.append(title,text);
  if(effect.response){const response=element('p','quest-world-post-response',effect.response);response.dataset.postResponse='';card.append(response);}
  info.insertBefore(card,info.querySelector('.quest-note'));tag(scene,effect);
 }
}
window.PalataQuestWorldView=Object.freeze({render});
})();
