'use strict';
// Test driver based solely on visible work-order evidence. It does not read the
// model's private answer generators or submit a legacy answer for a new task.
function difference(a,b){const values=new Map(b.map(x=>[x.id,x.value]));return a.filter(x=>x.value!==values.get(x.id)).map(x=>x.id);}
function toggleTowards(current,wanted,op){const remove=current.find(x=>!wanted.includes(x));if(remove)return{op,value:remove};const add=wanted.find(x=>!current.includes(x));return add?{op,value:add}:{op:'submit'};}
function nextOperation(b){
 if(!b)return null;
 switch(b.kind){
  case 'inspection':{
   const hidden=b.items.find(x=>!x.inspected);if(hidden)return{op:'inspect',value:hidden.id};
   const match=b.items.find(x=>x.details?.kit===b.request.kit&&x.details?.lot===b.request.lot&&x.details?.seal==='целая');
   if(!match)throw Error('The inspected containers do not contain the requested intact kit.');
   return toggleTowards(b.selected,[match.id],'select');
  }
  case 'packing':{
   if(b.request.missingComponent&&!b.reserveGranted)return !b.shortageNoted?{op:'noteShortage'}:{navigate:'nurse',action:'job:linenReserve',resume:'job:linen',resumeRoom:'linen'};
   const desired=b.request.components.map(type=>b.items.find(x=>x.type===type&&!x.unavailable&&(x.size===b.request.size||x.id===b.authorizedSubstitution?.itemId)&&x.condition==='чистая упаковка'));
   if(desired.some(x=>!x))throw Error('No clean packing selection matches the written request.');
   return toggleTowards(b.selected,desired.map(x=>x.id),'select');
  }
  case 'delivery':return{op:'deliver'};
  case 'bedmaking':{
   if(b.revision>=4&&!b.preparationStarted)return{op:'startBedPreparation'};
   if(b.draftScene?.required&&!b.draftScene.method)return{op:'chooseMethod',value:'window'};
   const item=b.items.find(x=>!b.placed.includes(x.id));if(!item)throw Error('No unplaced item remains in an unfinished bed preparation.');
   if(b.selectedPiece!==item.id)return{op:'selectPiece',value:item.id};
   if(item.id==='sheet'&&b.draftScene?.required&&!b.draftScene.spread)return{op:'spreadSheet'};
   return{op:'place',value:item.id==='sheet'?'sheetZone':'pillowZone'};
  }
  case 'clarification':{
   const choice=b.options.find(x=>x.measure===b.request.neededMeasure);if(!choice)throw Error('No reserve item matches the requested physical size.');
   return b.selected[0]===choice.id?{op:'submit'}:{op:'select',value:choice.id};
  }
  case 'compare':return toggleTowards(b.marked,difference(b.documents[0].fields,b.documents[1].fields),'mark');
  case 'caseCompare':{
   if(!b.sourcesRead)return{op:'readSources'};
   const document=id=>{const source=b.documents.find(item=>item.id===id);if(!source)throw Error('The case is missing an identified source '+id);return Object.fromEntries(source.fields.map(field=>[field.id,field.value]));};
   const direction=document('source-1'),original=document('source-2'),copy=document('source-3');
   // An appointment is a plan, not proof of the time the procedure occurred.
   const room=direction.ward&&original.ward&&copy.ward&&direction.ward===original.ward?(copy.ward===original.ward?'matches':'differs'):'unknown';
   const time=original.fact&&copy.fact?(original.fact===copy.fact?'matchesActual':'error'):'unknown';
   const unreadable=value=>!value||/нера[зс]борчив|не установлен|неизвест|^—$/i.test(value);
   const author=unreadable(original.signature)||unreadable(copy.signature)?'unknown':original.signature===copy.signature&&original.signature==='Клара'?'clara':original.signature!==copy.signature?'other':'unknown';
   for(const [field,choice]of Object.entries({room,time,author})){
    const issue=b.issues.find(item=>item.id===field);
    if(!issue?.choices.some(option=>option.id===choice))throw Error('No case conclusion matches the visible sources for '+field);
    if(b.conclusions[field]!==choice)return{op:'conclude',value:{field,choice}};
   }
   return{op:'submit'};
  }
  case 'diagnostic':{
   if(!b.inspected)return{op:'inspect',value:'connector'};
   if(!b.tested)return{op:'test'};
   const report=b.connector.connected===null?'unassessed':!b.connector.connected?'disconnected':b.indicator==='on'&&/вызов принят/.test(b.response||'')?'working':'noResponse';
   if(!b.reports.some(x=>x.id===report))throw Error('No report describes the observed call response.');
   return b.selected[0]===report?{op:'submit'}:{op:'select',value:report};
  }
  case 'callReview':return{op:'authorize'};
  case 'callService':{
   if(!b.inspected)return{op:'inspectEvidence'};
   const choice=b.options.find(x=>['equipmentId','connector','postAddress'].every(key=>x[key]===b.evidence[key]));
   if(!choice)throw Error('No authorized service matches all observed equipment fields.');
   return b.selected[0]===choice.id?{op:'submit'}:{op:'select',value:choice.id};
  }
  case 'callRetest':return{op:b.tested?'confirm':'test'};
  case 'timeline':{
   const unreadable=b.cards.filter(card=>card.time===null);
   const unread=unreadable.find(card=>!card.reverseRead);
   if(unread)return{op:'readReverse',value:unread.id};
   const readable=b.cards.filter(card=>typeof card.time==='string').sort((a,z)=>a.time.localeCompare(z.time));
   const desired=readable.map(card=>card.id);
   for(const card of unreadable){
    if(typeof card.reverseText!=='string')throw Error('An unreadable time has no inspected ordering source.');
    const after=readable.filter(item=>card.reverseText.includes(item.room)&&/проверк[аи] сигнала/i.test(item.note));
    const before=readable.filter(item=>card.reverseText.includes(item.room)&&/передача белья/i.test(item.note));
    if(after.length!==1||before.length!==1||desired.indexOf(after[0].id)>=desired.indexOf(before[0].id))throw Error('The visible reverse does not establish an unambiguous ordering.');
    desired.splice(desired.indexOf(after[0].id)+1,0,card.id);
   }
   const mismatch=b.order.findIndex((x,i)=>desired[i]!==x);
   if(mismatch>=0)return{op:'remove',value:b.order[mismatch]};
   return b.order.length<desired.length?{op:'place',value:desired[b.order.length]}:{op:'submit'};
  }
  case 'subjectChoice':{
   if(b.selected){
    const subject=b.options.find(option=>option.id===b.selected);
    if(!subject)throw Error('Selected observation has no room.');
    return{navigate:subject.room,action:'job:baseline',completeOnly:true};
   }
   const subject=b.options.find(option=>option.available);
   if(!subject)throw Error('No available observation subject.');
   return{op:'chooseSubject',value:subject.id};
  }
  case 'subjectBaseline':return{op:b.details.length?'record':b.actionOp};
  case 'subjectDifference':{
   if(!b.observationCaptured)return{op:b.actionOp};
   if(b.replies.length){
    const received=b.current.find(row=>row.id==='reply');
    const choice=b.replies.find(option=>option.label===received?.value);
    if(!choice)throw Error('No answer matches the displayed call response.');
    return b.replySelected===choice.id?{op:'submit'}:{op:'selectReply',value:choice.id};
   }
   const changed=difference(b.baseline,b.current);
   if(!changed.length)return{op:b.noChanges?'submit':'noChanges'};
   return toggleTowards(b.marked,changed,'mark');
  }
  case 'baseline':return{op:'record'};
  case 'difference':{
   const changed=difference(b.baseline,b.current);
   if(b.allowNoChanges&&!changed.length)return{op:b.noChanges?'submit':'noChanges'};
   return toggleTowards(b.marked,changed,'mark');
  }
  default:throw Error('Unknown workbench kind '+b.kind);
 }
}
module.exports={nextOperation};
