/* Read-only presentation of confirmed consequences. No save fields or rewards. */
(function(root){
'use strict';
function forRoom(E,state,room,mode=state.mode){
 const result=[],f=state.flags||{},steps=state.interactions||{};
 if(mode==='trip'){
  if(room==='A'&&f.unlockB)result.push({id:'passage:AB',kind:'passage',status:'open',mark:'✓',label:'Переход A/B разблокирован',text:'Засов освобождён. '+(f.tripHandle||steps.unlockB>=2?'Аварийная рукоять установлена в приводе.':'Проход в секцию B открыт.')});
  if(room==='B'&&f.unlockC)result.push({id:'passage:BC',kind:'passage',status:'open',mark:'✓',label:'Переход B/C разблокирован',text:'Замок отперт. Проход в секцию C свободен.'+(steps.unlockC>=3?' Служебный ключ оставлен в замке.':'')});
  if(room==='collector'&&f.tripHandle)result.push({id:'reserve:handle',kind:'reserve',status:'collected',mark:'↓',label:'Аварийная рукоять взята',text:f.unlockB||steps.unlockB>=2?'Рукоять установлена в аварийном приводе A/B.':'Рукоять взята из хозяйственного резерва для перехода A/B.'});
 }
 for(const effect of E.roomEffects?.(state,room,mode)||[]){
  if(effect.kind==='linen'){
   const status=effect.preparationStarted?'preparing':effect.prepared?'prepared':'delivered';
   result.push({id:effect.id,kind:'linen',status,mark:status==='preparing'?(effect.placed||[]).length+'/2':status==='prepared'?'✓':'↓',label:effect.title,text:effect.text});
  }else if(effect.kind==='call'){
   const status=effect.verified?'verified':effect.needsRetest?'retest':effect.needsService?'attention':'observed';
   result.push({id:effect.id,kind:'call',status,mark:status==='verified'?'✓':status==='attention'?'!':'?',label:effect.title,text:effect.text});
  }
 }
 return Object.freeze(result.map(item=>Object.freeze(item)));
}
const api=Object.freeze({forRoom});
if(typeof module==='object'&&module.exports)module.exports=api;
root.PalataQuestStateView=api;
})(typeof window==='object'?window:globalThis);
